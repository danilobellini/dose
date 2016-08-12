"""Dose GUI for TDD: test job runner."""
import os, subprocess, threading, sys, contextlib, time, codecs
from . import terminal

# Durations in seconds
POLLING_DELAY = 0.001 # Sleep duration on non-blocking polling loops
PRE_SPAWN_DELAY = 0.01 # Avoids spawning some subprocesses fated to be killed
KILL_DELAY = 0.05 # Minimum duration between spawning and killing a process


class FlushStreamThread(threading.Thread):
    """
    Thread for synchronizing/flushing a given process and the single
    standard stream name ("stdout" or "stderr"). The process
    output/error stream can be processed by the given formatter
    function before writting to the respective ``sys`` stream.
    """
    def __init__(self, process, stream_name, formatter=None, size=1):
        super(FlushStreamThread, self).__init__(target=self, kwargs=dict(
          process = process,
          stream_in = getattr(process, stream_name),
          stream_out = getattr(sys, stream_name),
          formatter = formatter,
          size = size,
        ))

    # As "run" can't be used with parameters, let's "call" a thread
    def __call__(self, process, stream_in, stream_out, formatter, size):
        SR = codecs.getreader(stream_out.encoding)
        reader = SR(stream_in, errors="ignore")
        if formatter is None:
            while process.poll() is None:
                stream_out.write(reader.read(size))
            stream_out.write(reader.read()) # Remaining data
        else:
            while process.poll() is None:
                stream_out.write(formatter(reader.read(size)))
            stream_out.write(formatter(reader.read())) # Remaining data


@contextlib.contextmanager
def flush_stream_threads(process, out_formatter=None,
                                  err_formatter=terminal.fg.red, size=1):
    """
    Context manager that creates 2 threads, one for each standard
    stream (stdout/stderr), updating in realtime the piped data.
    The formatters are callables that receives manipulates the data,
    e.g. coloring it before writing to a ``sys`` stream. See
    ``FlushStreamThread`` for more information.
    """
    out = FlushStreamThread(process=process, stream_name="stdout",
                            formatter=out_formatter, size=size)
    err = FlushStreamThread(process=process, stream_name="stderr",
                            formatter=err_formatter, size=size)
    out.start()
    err.start()
    yield out, err
    out.join()
    err.join()


@contextlib.contextmanager
def runner(test_command):
    process = subprocess.Popen(test_command, bufsize=0, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with flush_stream_threads(process):
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
