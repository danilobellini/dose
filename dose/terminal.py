"""Dose GUI for TDD: colored terminal."""
from __future__ import unicode_literals, print_function
from .misc import attr_item_call_auto_cache

# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
ANSI_FG_COLOR = {
  "red": b"\x1b[31m",
  "yellow": b"\x1b[33m",
  "magenta": b"\x1b[35m",
  "cyan": b"\x1b[36m",
}
ANSI_FG_RESET = b"\x1b[39m"

TERMINAL_WIDTH = 79 # TODO: Get the actual terminal width


@attr_item_call_auto_cache
def fg(color):
    """
    Foreground color formatter function factory.

    Each function casts from a unicode string to a colored bytestring
    with the respective foreground color and foreground reset ANSI
    escape codes. You can also use the ``fg.color`` or ``fg[color]``
    directly as attributes/items.
    """
    ansi_code = [ANSI_FG_COLOR[color], ANSI_FG_RESET]
    return lambda msg: msg.join(ansi_code)


@attr_item_call_auto_cache
def log(color):
    """
    Function factory for foreground-colored loggers (printers).

    The ``log.color(msg)`` and ``print(fg.color(msg))`` are the
    same. See ``fg`` for more information.
    """
    foreground = fg(color)
    return lambda msg: print(foreground(msg))


@attr_item_call_auto_cache
def hr(color):
    """
    Colored horizontal rule printer/logger factory.

    The resulting function prints an entire terminal row with the given
    symbol repeated. It's a terminal version of the HTML ``<hr>``.
    """
    logger = log(color)
    return lambda symbol: logger(symbol * TERMINAL_WIDTH)


def centralize(msg):
    """Add spaces to centralize the string in the terminal."""
    return msg.center(TERMINAL_WIDTH)


@attr_item_call_auto_cache
def clog(color):
    """Same to ``log``, but this one centralizes the message first."""
    logger = log(color)
    return lambda msg: logger(centralize(msg))
