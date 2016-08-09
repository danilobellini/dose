#!/usr/bin/env python2
"""Dose GUI for TDD: test job runner."""
import subprocess, threading, sys, contextlib, errno, time

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
FG_RED = b"\x1b[31m"
FG_YELLOW = b"\x1b[33m"
FG_MAGENTA = b"\x1b[35m"
FG_CYAN = b"\x1b[36m"
FG_RESET = b"\x1b[39m"

SMALL_DURATION = 0.05 # Seconds, used for non-blocking polling loops


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

    def __init__(self, test_command, end_callback, exc_callback):
        self.test_command = test_command
        self.end_callback = end_callback
        self.exc_callback = exc_callback
        self.lock = threading.Lock()
        super(RunnerThreadCallback, self).__init__()

    def kill(self):
        while self.is_alive():
            with self.lock:
                if not hasattr(self, "process"):
                    time.sleep(SMALL_DURATION) # Still not initialized, wait
                    continue
                if self.process.poll() is None: # It's running
                    self.process.terminate()
            break # We already either killed or finished it
        self.join()

    def run(self):
        try:
            with runner(self.test_command) as self.process:
                result = None
                while result is None:
                    time.sleep(SMALL_DURATION)
                    with self.lock:
                        result = self.process.poll()
        except Exception as exc:
            self.exc_callback(exc)
        else:
            self.end_callback(result)


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
