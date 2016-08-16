#!/usr/bin/env python2
"""Dose GUI for TDD: setup script."""
import os, setuptools, dose, dose.rest

with open(os.path.join(os.path.dirname(__file__), "README.rst"), "r") as f:
    README = f.read().splitlines()

metadata = {
  "name": "dose",
  "version": dose.__version__,
  "author": dose.__author__,
  "author_email": dose.__author_email__,
  "url": dose.__url__,
  "description": dose.rest.single_line_block("summary", README),
  "long_description": dose.rest.all_but_block("summary", README),
  "license": "GPLv3",
  "packages": ["dose"],
  "install_requires": ["watchdog>=0.6.0",
                       "setuptools>=25"], # Needs wxPython as well
  "entry_points": {"console_scripts": ["dose = dose.__main__:main"]},
  "data_files": [("share/dose", ["COPYING.txt", "README.rst",
                                 "CONTRIBUTORS.txt", "CHANGES.rst"])],
}

metadata["classifiers"] = """
Development Status :: 4 - Beta
Environment :: MacOS X
Environment :: Win32 (MS Windows)
Environment :: X11 Applications
Intended Audience :: Developers
Intended Audience :: Education
License :: OSI Approved :: GNU General Public License v3 (GPLv3)
Operating System :: MacOS :: MacOS X
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
