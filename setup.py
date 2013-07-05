#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dose - Automated semaphore GUI showing the state in test driven development
Copyright (C) 2012 Danilo de Jesus da Silva Bellini

Dose is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

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
import os

path = os.path.split(__file__)[0]
script_file = "dose.py"

# Get metadata from the script file without actually importing it
metadata = {}
with open(os.path.join(path, script_file), "r") as f:
  for line in f:
    if line.startswith("__"):
      assignment = [side.strip() for side in line.split("=")]
      metadata[assignment[0].strip("_")] = eval(assignment[1])

# Description is all from README.txt, but the ending copyright message
with open(os.path.join(path, "README.rst"), "r") as f:
  readme_data = f.read()
readme_data = readme_data.replace("\r\n", "\n")
title, descr, ldescr = readme_data.split("\n\n", 2)
metadata["description"] = descr
metadata["long_description"] = "\n".join([title, ldescr]
                                        ).rsplit("----", 1)[0].strip()

# Classifiers and license
metadata["license"] = "GPLv3"
metadata["classifiers"] = [
  "Development Status :: 4 - Beta",
  "Environment :: Win32 (MS Windows)",
  "Environment :: X11 Applications :: GTK",
  "Intended Audience :: Developers",
  "Intended Audience :: Education",
  "License :: OSI Approved :: "
    "GNU General Public License v3 (GPLv3)",
  "Natural Language :: English",
  "Operating System :: Microsoft :: Windows",
  "Operating System :: POSIX :: Linux",
  "Programming Language :: Python",
  "Topic :: Software Development",
  "Topic :: Software Development :: Testing",
]

# Finish
metadata["name"] = "dose"
metadata["scripts"] = [script_file]
metadata["install_requires"] = ["watchdog>=0.6.0"] # Needs wxPython as well
setup(**metadata)
