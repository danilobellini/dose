"""Dose GUI for TDD: colored terminal."""
from __future__ import print_function
import os, sys, subprocess, signal, colorama
from .misc import attr_item_call_auto_cache


DEFAULT_TERMINAL_WIDTH = 80


class TerminalSize(object):
    r"""
    Console/terminal width information getter.

    There should be only one instance for this class, and it's the
    ``terminal_size`` object in this module, whose ``width``
    attribute has the desired terminal width. The ``usable_width``
    read-only property has the width that can be safely used with a
    ``"\n"`` at the end without skipping a line.

    The ``retrieve_width`` method can be called to update the ``width``
    attribute, but there's also a SIGWINCH (SIGnal: WINdow CHanged)
    signal handler updating the width if that's a valid signal in the
    operating system.

    Several strategies for getting the terminal width are combined
    in this class, all of them are tried until a width is found. When
    a strategy returns ``0`` or ``None``, it means it wasn't able to
    collect the console width.

    Note: The ``terminal_size`` object should have been created in the
    main thread of execution.
    """
    width = DEFAULT_TERMINAL_WIDTH # Fallback

    # Strategies are (method name without the "from_" prefix, arguments list)
    if sys.platform == "win32":
        strategies = [
          ("windows_handle", [subprocess.STD_INPUT_HANDLE]),
          ("windows_handle", [subprocess.STD_OUTPUT_HANDLE]),
          ("windows_handle", [subprocess.STD_ERROR_HANDLE]),
        ]
        @property
        def usable_width(self):
            return self.width - 1
    else: # Linux, OS X and Cygwin
        strategies = [
          ("io_control", [sys.stdin]),
          ("io_control", [sys.stdout]),
          ("io_control", [sys.stderr]),
          ("tty_io_control", []),
        ]
        @property
        def usable_width(self):
            return self.width
    strategies.extend([
      ("tput_subprocess", []), # Cygwin "tput" works on other Windows consoles
      ("environment_variable", []),
    ])

    def __init__(self):
        try:
            signal.signal(signal.SIGWINCH, self.retrieve_width)
        except (AttributeError, ValueError): # There's no SIGWINCH in Windows
            pass
        self.retrieve_width()

    def retrieve_width(self, signum=None, frame=None):
        """
        Stores the terminal width into ``self.width``, if possible.
        This function is also the SIGWINCH event handler.
        """
        for method_name, args in self.strategies:
            method = getattr(self, "from_" + method_name)
            width = method(*args)
            if width and width > 0:
                self.width = width
                break # Found!
        os.environ["COLUMNS"] = str(self.width) # A hint for the next test job

    @staticmethod
    def from_environment_variable():
        """Gets the width from the ``COLUMNS`` environment variable."""
        return int(os.environ.get("COLUMNS", "0"))

    @staticmethod
    def from_io_control(fobj):
        """
        Call TIOCGWINSZ (Terminal I/O Control to Get the WINdow SiZe)
        where ``fobj`` is a file object (e.g. ``sys.stdout``),
        returning the terminal width assigned to that file.

        See the ``ioctl``, ``ioctl_list`` and tty_ioctl`` man pages
        for more information.
        """
        import fcntl, termios, array
        winsize = array.array("H", [0] * 4) # row, col, xpixel, ypixel
        if not fcntl.ioctl(fobj.fileno(), termios.TIOCGWINSZ, winsize, True):
            return winsize[1]

    @classmethod
    def from_tty_io_control(cls):
        """Calls cls.from_io_control for the tty file descriptor."""
        with open(os.ctermid(), "rb") as fobj:
            return cls.from_io_control(fobj)

    @staticmethod
    def from_tput_subprocess():
        """
        Gets the terminal width from the ``tput`` shell command,
        usually available in Linux, OS X and Cygwin (Windows).
        """
        try:
            # Windows require shell=True to avoid the tput extension
            return int(subprocess.check_output("tput cols", shell=True))
        except (OSError,                        # tput not found
                subprocess.CalledProcessError): # tput didn't return 0
            return 0

    @staticmethod
    def from_windows_handle(std_handle):
        """
        Use the Windows Console Handles API to get the console width,
        where ``std_handle`` is the WINAPI ``GetStdHandle`` input
        (e.g. STD_INPUT_HANDLE).

        https://msdn.microsoft.com/library/windows/desktop/ms682075
        """
        from ctypes import windll, c_ushort
        # https://msdn.microsoft.com/library/windows/desktop/ms683231
        handle = windll.kernel32.GetStdHandle(std_handle)
        # https://msdn.microsoft.com/library/windows/desktop/ms682093
        info = (c_ushort * 11)() # It's a CONSOLE_SCREEN_BUFFER_INFO:
            # xsize, ysize,             | COORD      dwSize
            # xcursor, ycursor,         | COORD      dwCursorPosition
            # attributes,               | WORD       wAttributes
            # left, top, right, bottom, | SMALL_RECT srWindow
            # xmax, ymax                | COORD      dwMaximumWindowSize
        # https://msdn.microsoft.com/library/windows/desktop/ms683171
        if windll.kernel32.GetConsoleScreenBufferInfo(handle, info):
            return info[7] - info[5] + 1


terminal_size = TerminalSize()


@attr_item_call_auto_cache
def fg(color):
    """
    Foreground color formatter function factory.

    Each function casts from a unicode string to a colored bytestring
    with the respective foreground color and foreground reset ANSI
    escape codes. You can also use the ``fg.color`` or ``fg[color]``
    directly as attributes/items.

    The colors are the names of the ``colorama.Fore`` attributes
    (case insensitive). For more information, see:

    https://pypi.python.org/pypi/colorama

    https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    """
    ansi_code = [getattr(colorama.Fore, color.upper()), colorama.Fore.RESET]
    return lambda msg: msg.join(ansi_code)


@attr_item_call_auto_cache
def log(color):
    """
    Function factory for foreground-colored loggers (printers).

    The ``log.color(msg)`` and ``print(fg.color(msg))`` are the
    same. On Windows, the ANSI escape codes for colors are mapped to
    ``SetConsoleTextAttribute`` Windows Console Handles API function
    calls by the ``colorama`` package.

    https://msdn.microsoft.com/library/windows/desktop/ms686047

    The colorama initialization is on the ``dose.__main__`` module.
    See ``fg`` for more information.
    """
    foreground = fg(color)
    return lambda msg: print(foreground(msg))


@attr_item_call_auto_cache
def hr(color):
    """
    Colored horizontal rule printer/logger factory.

    The resulting function prints an entire terminal row with the given
    symbol repeated. It's a terminal version of the HTML ``<hr/>``.
    """
    logger = log(color)
    return lambda symbol: logger(symbol * terminal_size.usable_width)


def centralize(msg):
    """Add spaces to centralize the string in the terminal."""
    return msg.center(terminal_size.usable_width)


@attr_item_call_auto_cache
def clog(color):
    """Same to ``log``, but this one centralizes the message first."""
    logger = log(color)
    return lambda msg: logger(centralize(msg).rstrip())
