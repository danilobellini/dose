"""Dose GUI for TDD: README.rst processing functions."""
import itertools

# Be careful: this file is imported by setup.py!

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"


def not_eq(value):
    """Partial evaluation of ``!=`` for currying"""
    return lambda el: el != value


def indent_size(line):
    """Number of leading spaces in the given string."""
    return sum(1 for unused in itertools.takewhile(lambda c: c == " ", line))


def get_block(name, data, newline="\n"):
    """
    Joined multiline string block from a list of strings data. The
    BLOCK_START and BLOCK_END delimiters are selected with the given
    name and aren't included in the result.
    """
    lines = itertools.dropwhile(not_eq(BLOCK_START % name), data)
    next(lines) # Skip the start line, raise an error if there's no start line
    return newline.join(itertools.takewhile(not_eq(BLOCK_END % name), lines))


def all_but_blocks(names, data, newline="\n", remove_empty_next=True,
                   remove_comments=True):
    """
    Multiline string from a list of strings data, removing every
    block with any of the given names, as well as its delimiters.
    Removes the empty line after BLOCK_END when ``remove_empty_next``
    is True. Returns a joined string with the given newline, or a
    line generator if it's None. This function also removes comments,
    if desired.
    """
    def internal_generator():
        end = None
        skip_next = False
        skip_comment = False
        indent = 0
        for line in data:
            if skip_next:
                skip_next = False
                if not line.strip(): # Maybe this "next" line isn't empty
                    continue
            elif skip_comment:
                if line.strip() and indent_size(line) <= indent:
                    skip_comment = False
                else:
                    continue
            if end is None:
                if line in blocks:
                    end = blocks[line]
                elif remove_comments and line.lstrip().startswith("..") \
                                     and ":" not in line:
                    skip_comment = True
                    indent = indent_size(line)
                else:
                    yield line
            elif end == line:
                end = None
                skip_next = remove_empty_next

    all_names = [names] if isinstance(names, str) else names
    blocks = {BLOCK_START % name: BLOCK_END % name for name in all_names}
    gen = internal_generator()
    return gen if newline is None else newline.join(gen)


def single_line(value):
    """Returns the given string joined to a single line and trimmed."""
    return " ".join(filter(None, map(str.strip, value.splitlines())))


def single_line_block(name, data):
    """Single line version of get_block."""
    return single_line(get_block(name, data))
