#!/usr/bin/env python
"""Dose GUI for TDD: setup script."""
import distutils.filelist
import os
import setuptools
import sys

import dose
dose._from_setup = True
import dose.rest
import dose.shared


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


README = dose.rest.abs_urls(
    dose.shared.README,
    image_url="/".join([dose.__url__, "raw", "v" + dose.__version__]),
    target_url=dose.__url__,
)

dose_install_reqs = ["docutils>=0.12", "wxPython"]
watchdog_req = "watchdog>=0.9"
colorama_req = "colorama>=0.3.7"
if sys.version_info[:2] == (3, 3):
    watchdog_req += ",<0.10"
    colorama_req += ",<0.4"
    dose_install_reqs.append("pyyaml<4")  # Indirect, for watchdog
    dose_install_reqs.append("numpy<1.12")  # Indirect, for wxPython
else:
    if sys.version_info[0] == 2:
        dose_install_reqs.append("pyyaml<6")  # Indirect, for watchdog
    elif sys.version_info[:2] == (3, 4):
        dose_install_reqs.append("pyyaml<5.3")  # Indirect, for watchdog
        colorama_req += ",<0.4.2"
    if sys.version_info < (3, 6):
        watchdog_req += ",<1"
dose_install_reqs.extend([watchdog_req, colorama_req])

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
  "install_requires": dose_install_reqs,
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
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.10
Programming Language :: Python :: Implementation :: CPython
Topic :: Education
Topic :: Education :: Testing
Topic :: Software Development
Topic :: Software Development :: Testing
""".strip().splitlines()

setuptools.setup(**metadata)
