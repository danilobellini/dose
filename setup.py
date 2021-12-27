#!/usr/bin/env python
"""Dose GUI for TDD: setup script."""
import distutils.filelist
import os
import setuptools

import dose, dose.rest, dose.shared


SDIST_PATH = os.path.dirname(__file__) # That's also sys.path[0]
if SDIST_PATH:           # The setuptools.setup function requires this to
    os.chdir(SDIST_PATH) # work properly when called from otherwhere


def parse_manifest():
    """List of file names included by the MANIFEST.in template lines."""
    manifest_files = distutils.filelist.FileList()
    for line in dose.shared.get_shared("MANIFEST.in").splitlines():
        if line.strip():
            manifest_files.process_template_line(line)
    return manifest_files.files


README = dose.rest.abs_urls(dose.shared.README,
                            image_url = "/".join([dose.__url__, "raw",
                                                  dose.__version__]),
                            target_url = dose.__url__)


metadata = {
  "name": "dose",
  "version": dose.__version__,
  "author": dose.__author__,
  "author_email": dose.__author_email__,
  "url": dose.__url__,
  "description": dose.rest.single_line_block("summary", README),
  "long_description": dose.rest.all_but_blocks("summary", README),
  "license": "GPLv3",
  "packages": setuptools.find_packages(),
  "install_requires": ["watchdog>=0.9.0",
                       "colorama>=0.3.7",
                       "docutils>=0.12",
                       "wxPython"],
  "entry_points": {"console_scripts": ["dose = dose.__main__:main"]},
  "data_files": [("share/dose/v" + dose.__version__, parse_manifest())],
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
Programming Language :: Python :: 3
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.3
Programming Language :: Python :: Implementation :: CPython
Topic :: Education
Topic :: Education :: Testing
Topic :: Software Development
Topic :: Software Development :: Testing
""".strip().splitlines()

setuptools.setup(**metadata)
