"""Dose GUI for TDD: reStructuredText processing functions."""
import itertools
from .misc import not_eq, tail

# Be careful: this file is imported by setup.py!

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"


def indent_size(line):
    """Number of leading spaces in the given string."""
    return sum(1 for unused in itertools.takewhile(lambda c: c == " ", line))


def get_block(name, data, newline="\n"):
    """
    First block in a list of one line strings containing
    reStructuredText data. The result is as a joined string with the
    given newline, or a line generator if it's None. The
    BLOCK_START and BLOCK_END delimiters are selected with the given
    name and aren't included in the result.
    """
    lines = itertools.dropwhile(not_eq(BLOCK_START % name), data)
    gen = itertools.takewhile(not_eq(BLOCK_END % name), tail(lines))
    return gen if newline is None else newline.join(gen)


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
    """Single trimmed line from a given list of strings."""
    return " ".join(filter(None, map(str.strip, value)))


def single_line_block(name, data):
    """Single line version of get_block."""
    return single_line(get_block(name, data, newline=None))


def get_sections(data):
    """
    List of tuples (section, symbol, contents) containing the given
    reStructuredText divided by its sections. The input should be a
    list of single line strings.
    """
    no_trail = [row.rstrip() for row in data]
    starts = [(r1, r2[0], idx)
              for idx, (r1, r2) in enumerate(zip(no_trail, no_trail[1:]))
              if r1 and len(r1) == len(r2) and all(ch == r2[0] for ch in r2)]
    if starts[0][2] != 0:
        starts.insert(0, (None, None, 0)) # Empty starting section
    starts.append((None, None, len(no_trail))) # Last section slice stop value
    return [(section, symbol, no_trail[start+2:stop]) # Skip section name
            for (section, symbol, start), (next_section, next_symbol, stop)
                in zip(starts, starts[1:])]


def rst_toc(data, with_links=True):
    """
    Creates a "Table of Contents" as a bullet list in reStructuredText.
    Returns a generator of lines.
    """
    fmt = "{indent}* `{name} <{name}_>`_" if with_links else "{indent}* {name}"
    for name, symbol, content in get_sections(data):
        indent = "  " if symbol == "-" else ""
        yield fmt.format(**locals())
        yield "" # Required when nesting


def section_header(title, symbol="="):
    """A 2-line reStructuredText section header as a list of lines."""
    return [title, symbol * len(title)]
