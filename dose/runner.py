#!/usr/bin/env python2
"""Dose GUI for TDD: test job runner."""
import os, subprocess, threading, sys, contextlib, time

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
FG_RED = b"\x1b[31m"
FG_YELLOW = b"\x1b[33m"
FG_MAGENTA = b"\x1b[35m"
FG_CYAN = b"\x1b[36m"
FG_RESET = b"\x1b[39m"

# Durations in seconds
POLLING_DELAY = 0.001 # Sleep duration on non-blocking polling loops
PRE_SPAWN_DELAY = 0.01 # Avoids spawning some subprocesses fated to be killed
KILL_DELAY = 0.05 # Minimum duration between spawning and killing a process


def run_stderr(process, stream, size=1):
    while process.poll() is None:
        stream.write(FG_RED + process.stderr.read(size) + FG_RESET)
    stream.write(FG_RED + process.stderr.read() + FG_RESET)

def run_stdout(process, stream, size=1):
    while process.poll() is None:
        stream.write(process.stdout.read(size))
    stream.write(process.stdout.read())


@contextlib.contextmanager
def flush_stream_thread(sname, **kwargs):
    kwargs["stream"], target = {"stdout": (sys.stdout, run_stdout),
                                "stderr": (sys.stderr, run_stderr)}[sname]
    th = threading.Thread(target=target, kwargs=kwargs)
    th.start()
    yield th
    th.join()


@contextlib.contextmanager
def runner(test_command):
    process = subprocess.Popen(test_command, bufsize=0, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with flush_stream_thread("stdout", process=process):
        with flush_stream_thread("stderr", process=process):
            try:
                yield process
            finally:
                if process.poll() is None:
                    process.terminate()


class RunnerThreadCallback(threading.Thread):

    def __init__(self, test_command, before=None, after=None, exception=None):
        def do_nothing(result=None): # Should have a default value to be used
            pass                     # as a valid self.before
        self.test_command = test_command
        self.before = do_nothing if before is None else before
        self.after = do_nothing if after is None else after
        self.exception = do_nothing if exception is None else exception
        self.killed = False
        super(RunnerThreadCallback, self).__init__()
        self.start()

    def kill(self):
        while self.is_alive():
            self.killed = True
            time.sleep(POLLING_DELAY) # "Was a process spawned?" polling
            if not self.spawned:
                continue # Either self.run returns or runner yields
            if self.process.poll() is None: # It's running
                self.process.terminate()
                os.waitpid(self.process.pid, os.WNOHANG)
            break # We already either killed or finished it
        self.join()

    @property
    def spawned(self):
        return hasattr(self, "process")

    def run(self):
        try:
            # Waits PRE_SPAWN_DELAY, but self might get killed before that
            start = time.time()
            while time.time() < start + PRE_SPAWN_DELAY:
                time.sleep(POLLING_DELAY)
                if self.killed:
                    break
            else: # Avoids an unrequired spawning
                self.before()
                with runner(self.test_command) as self.process:
                    time.sleep(KILL_DELAY)
                    self.process.wait()
        except Exception as exc:
            self.exception(exc)
        else:
            if self.spawned:
                self.after(self.process.returncode)
            else:
                self.after(None)


if __name__ == "__main__":
    # Manual test to see if the data really appears (colored) in real time
    import time
    with runner("python -c 'import time, itertools, sys          \n"
                           "for i in itertools.count():          \n"
                           "    if i % 2 == 0:                   \n"
                           "        stream = sys.stderr          \n"
                           "    else:                            \n"
                           "        stream = sys.stdout          \n"
                           '    stream.write("%g\\n" % (i / 10.))\n'
                           "    stream.flush()                   \n"
                           "    time.sleep(.1)'") as process:
        time.sleep(.05)
        for el in range(60):
            print(FG_YELLOW + b"[%f seconds]" % (el * .3 + .05) + FG_RESET)
            time.sleep(.3)
