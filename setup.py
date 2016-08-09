#!/usr/bin/env python2
"""Dose GUI for TDD: setup script."""
import os, setuptools, itertools, ast

BLOCK_START = ".. %s"
BLOCK_END = ".. %s end"

SDIST_DIR = os.path.dirname(__file__)
METADATA_FILE = os.path.join(SDIST_DIR, os.path.join("dose", "__init__.py"))

with open(os.path.join(SDIST_DIR, "README.rst"), "r") as f:
    README = f.read().splitlines()

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

def get_assignment(fname, varname):
    """
    Gets the evaluated expression of a single assignment statement
    ``varname = expression`` in the referred file. The expression should
    not depend on previous values, as the context isn't evaluated.
    """
    with open(fname, "r") as f:
        for n in ast.parse(f.read(), filename=fname).body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                                         and n.targets[0].id == varname:
                return eval(compile(ast.Expression(n.value), fname, "eval"))

metadata = {
  "name": "dose",
  "version": get_assignment(METADATA_FILE, "__version__"),
  "author": get_assignment(METADATA_FILE, "__author__"),
  "author_email": get_assignment(METADATA_FILE, "__author_email__"),
  "url": get_assignment(METADATA_FILE, "__url__"),
  "description": single_line(get_block("summary", README)),
  "long_description": all_but_block("summary", README),
  "license": "GPLv3",
  "packages": ["dose"],
  "install_requires": ["watchdog>=0.6.0"], # Needs wxPython as well
  "entry_points": {"console_scripts": ["dose = dose.__main__:main"]},
}

metadata["classifiers"] = """
Development Status :: 4 - Beta
Environment :: Win32 (MS Windows)
Environment :: X11 Applications
Intended Audience :: Developers
Intended Audience :: Education
License :: OSI Approved :: GNU General Public License v3 (GPLv3)
Operating System :: Microsoft :: Windows
Operating System :: POSIX :: Linux
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 2 :: Only
Programming Language :: Python :: Implementation :: CPython
Topic :: Education
Topic :: Education :: Testing
Topic :: Software Development
Topic :: Software Development :: Testing
""".strip().splitlines()

setuptools.setup(**metadata)
