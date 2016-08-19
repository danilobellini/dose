"""Dose GUI for TDD: test job runner."""
import os, subprocess, threading, sys, contextlib, time, codecs, traceback
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
def runner(test_command, work_dir=None):
    """
    Internal test job runner context manager.

    Run the test_command in a subprocess and instantiates 2
    FlushStreamThread, one for each standard stream (output/stdout
    and error/stderr).

    It yields the subprocess.Popen instance that was spawned to
    run the given test command in the given working directory.

    Leaving the context manager kills the process and joins the
    flushing threads. Use the ``process.wait`` method to avoid that.
    """
    process = subprocess.Popen(test_command, bufsize=0, shell=True,
                               cwd=work_dir,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with flush_stream_threads(process):
        try:
            yield process
        finally:
            if process.poll() is None:
                process.terminate()


class RunnerThreadCallback(threading.Thread):
    """
    Test job runner as 3 threads + 1 subprocess.

    This is the main test job runner thread, the other 2 are for the
    standard output/error flushing (one for each stream).

    You can use 3 callback functions for this thread.

    - before: Called just before spawning the subprocess, when it's
              certain that it won't be aborted ("pre-killed"). This
              callback will be called with no parameters;
    - after: Called with the result as the only parameter just after
             obtaining it. For aborted subprocesses, the parameter is
             None. Killed ones depends on the operating system;
    - exception: When an internal exception is raised in the main
                 runner thread, this gets called with 3 positional
                 arguments from ``sys.exc_info``: the exception type,
                 the exception itself and the traceback.

    For these callbacks, you should use thread-safe functions or some
    event sender/emitter that would delegate the handling action to
    other thread.
    """

    def __init__(self, test_command, work_dir=None,
                 before=None, after=None, exception=None):
        self.test_command = test_command
        self.work_dir = work_dir
        if before is not None:
            self.before = before
        if after is not None:
            self.after = after
        if exception is not None:
            self.exception = exception
        self.killed = False
        super(RunnerThreadCallback, self).__init__()
        self.start()

    def kill(self):
        """
        Terminate the test job.

        Kill the subprocess if it was spawned, abort the spawning
        process otherwise. This information can be collected afterwards
        by reading the self.killed and self.spawned flags.

        Also join the 3 related threads to the caller thread. This can
        be safely called from any thread.

        This method behaves as self.join() when the thread isn't alive,
        i.e., it doesn't raise an exception.
        """
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

    @property
    def runner_kwargs(self):
        return {
          "test_command" : self.test_command,
          "work_dir": self.work_dir,
        }

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
                with runner(**self.runner_kwargs) as self.process:
                    time.sleep(KILL_DELAY)
                    self.process.wait()
            self.after(self.process.returncode if self.spawned else None)
        except:
            try:
                self.exception(*sys.exc_info())
            except:
                RunnerThreadCallback.exception(*sys.exc_info())

    # Default callbacks
    before = staticmethod(lambda: None)
    after = staticmethod(lambda result: None)
    exception = staticmethod(traceback.print_exception)
