"""Dose GUI for TDD: reStructuredText processing functions."""
import itertools, functools, re
from .compat import allow_implicit_stop
from .misc import not_eq, tail

# Be careful: this file is imported by setup.py!

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"
REGEX_ABS_URLS_TARGET = re.compile(r"""
  (?<= ..\s)  \s* # Link targets and images starts like comments
  (_\S+  : |      # \1 is either a link target without spaces,
   _`.+` : )  \s* #           or a link target enclosed within backticks
  ([^:/][^:]*) $  # \2 is the url
""", re.VERBOSE)
REGEX_ABS_URLS_IMAGE = re.compile(r"""
  (?<= ..\s)  \s* # Link targets and images starts like comments
  (image ::)  \s* # \1 is an image "tag"
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
    @allow_implicit_stop
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


@allow_implicit_stop
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


def abs_urls(data, target_url, image_url):
    """
    Filter for a list of reStructuredText lines that replaces relative
    link targets and image sources by absolute URLs given the base
    URLs that should be used (``target_url`` for link targets,
    ``image_url``for image sources). Returns a list of strings.
    """
    def replacer(regex, url):
        replacement = r"\1 {0}/\2".format(url.rstrip("/"))
        return lambda line: regex.sub(replacement, line, count=1)
    replacers = [replacer(REGEX_ABS_URLS_TARGET, target_url),
                 replacer(REGEX_ABS_URLS_IMAGE, image_url)]
    return [functools.reduce(lambda el, func: func(el), replacers, line)
            for line in data]
