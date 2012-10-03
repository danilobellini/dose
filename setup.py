#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dose - Automated semaphore GUI showing the state in test driven development
Copyright (C) 2012 Danilo de Jesus da Silva Bellini

Dose is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Created on Sat Sep 29 2012
danilo [dot] bellini [at] gmail [dot] com
"""

from setuptools import setup

__version__ = "2012.10.03dev"

# Long description is all from README.txt, but the ending copyright message
with open("README.rst", "r") as f:
  long_description = f.read()
long_description = long_description.rsplit("----", 1)[0].strip()

classifiers = [
  "Development Status :: 3 - Alpha",
  "Environment :: Win32 (MS Windows)",
  "Environment :: X11 Applications :: GTK",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
  "Natural Language :: English",
  "Operating System :: Microsoft :: Windows",
  "Operating System :: POSIX :: Linux",
  "Programming Language :: Python",
  "Topic :: Software Development",
  "Topic :: Software Development :: Testing",
]

setup(name="dose",
      version=__version__,
      author="Danilo de Jesus da Silva Bellini",
      author_email="danilo.bellini@gmail.com",
      url='http://github.com/danilobellini/dose',
      description="Automated semaphore GUI showing the state in TDD",
      long_description=long_description,
      license="GPLv3",
      scripts=["dose.py"],
      classifiers=classifiers,
      install_requires=["watchdog"]
     )
