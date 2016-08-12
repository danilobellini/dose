"""Dose GUI for TDD: test job runner."""
import os, subprocess, threading, sys, contextlib, time
from . import terminal

# Durations in seconds
POLLING_DELAY = 0.001 # Sleep duration on non-blocking polling loops
PRE_SPAWN_DELAY = 0.01 # Avoids spawning some subprocesses fated to be killed
KILL_DELAY = 0.05 # Minimum duration between spawning and killing a process


def run_stderr(process, stream, size=1):
    formatter = terminal.fg.red
    while process.poll() is None:
        stream.write(formatter(process.stderr.read(size)))
    stream.write(formatter(process.stderr.read()))

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
