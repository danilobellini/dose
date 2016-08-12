"""Dose GUI for TDD: README.rst processing functions."""
import itertools

# Be careful: this file is imported by setup.py!

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"


def not_eq(value):
    """Partial evaluation of ``!=`` for currying"""
    return lambda el: el != value


def get_block(name, data, newline="\n"):
    """
    Joined multiline string block from a list of strings data. The
    BLOCK_START and BLOCK_END delimiters are selected with the given
    name and aren't included in the result.
    """
    lines = itertools.dropwhile(not_eq(BLOCK_START % name), data)
    next(lines) # Skip the start line, raise an error if there's no start line
    return newline.join(itertools.takewhile(not_eq(BLOCK_END % name), lines))


def all_but_block(name, data, newline="\n", remove_empty_next=True):
    """
    Joined multiline string from a list of strings data, removing a
    block with the given name and its delimiters. Removes the empty
    line after BLOCK_END when ``remove_empty_next`` is True.
    """
    it = iter(data)
    before = list(itertools.takewhile(not_eq(BLOCK_START % name), it))
    after = list(itertools.dropwhile(not_eq(BLOCK_END % name), it))[1:]
    if remove_empty_next and after and after[0].strip() == "":
        return newline.join(before + after[1:])
    return newline.join(before + after)


def single_line(value):
    """Returns the given string joined to a single line and trimmed."""
    return " ".join(filter(None, map(str.strip, value.splitlines())))


def single_line_block(name, data):
    """Single line version of get_block."""
    return single_line(get_block(name, data))
