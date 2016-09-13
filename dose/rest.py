"""Dose GUI for TDD: reStructuredText processing functions."""
import itertools, functools, re
from .misc import not_eq, tail

# Be careful: this file is imported by setup.py!

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"
REGEX_ABS_URLS = re.compile(r"""
  (?<= ..\s)  \s* # Link targets and images starts like comments
  (image :: |     # \1 is either an image,
   _\S+  :  |     #              a link target without spaces,
   _`.+` :  ) \s* #           or a link target enclosed within backticks
  ([^:/][^:]*) $  # \2 is the url
""", re.VERBOSE)


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
    block with any of the given names, as well as their delimiters.
    Removes the empty lines after BLOCK_END when ``remove_empty_next``
    is True. Returns a joined string with the given newline, or a
    line generator if it's None. If desired, this function use
    ``commentless`` internally to remove the remaining comments.
    """
    def remove_blocks(name, iterable):
        start, end = BLOCK_START % name, BLOCK_END % name
        it = iter(iterable)
        while True:
            line = next(it)
            while line != start:
                yield line
                line = next(it)
            it = tail(itertools.dropwhile(not_eq(end), it))
            if remove_empty_next:
                it = itertools.dropwhile(lambda el: not el.strip(), it)
    if isinstance(names, str):
        names = [names]
    processors = [functools.partial(remove_blocks, name) for name in names]
    if remove_comments:
        processors.append(commentless)
    gen = functools.reduce(lambda result, func: func(result),
                           processors, data)
    return gen if newline is None else newline.join(gen)


def commentless(data):
    """
    Generator that removes from a list of strings the double dot
    reStructuredText comments and its contents based on indentation,
    removing trailing empty lines after each comment as well.
    """
    it = iter(data)
    while True:
        line = next(it)
        while ":" in line or not line.lstrip().startswith(".."):
            yield line
            line = next(it)
        indent = indent_size(line)
        it = itertools.dropwhile(lambda el: indent_size(el) > indent
                                            or not el.strip(), it)


def single_line(data):
    """Single trimmed line from a given list of strings."""
    return " ".join(filter(None, (line.strip() for line in data)))


def single_line_block(name, data):
    """Single line version of get_block."""
    return single_line(get_block(name, data, newline=None))


def abs_urls(data, url):
    """
    Filter for a list of reStructuredText lines that replaces relative
    link targets and image sources by absolute URLs given the base URL
    that should be used. Returns a list of strings.
    """
    replacement = r"\1 {0}/\2".format(url.rstrip("/"))
    return [REGEX_ABS_URLS.sub(replacement, line, count=1) for line in data]
