"""Dose GUI for TDD: shared resources."""

# This module can't be used by the setup.py script!

def get_shared(fname):
    """
    Using the setuptools package resources, gets the string data from a
    text file that was packaged as a data file in the distribution.
    """
    from pkg_resources import Requirement, resource_string
    return resource_string(Requirement("dose"), "share/dose/" + fname)


README = get_shared("README.rst").splitlines()
CHANGES = get_shared("CHANGES.rst").splitlines()
CONTRIBUTORS = get_shared("CONTRIBUTORS.txt").splitlines()
LICENSE = get_shared("COPYING.txt").replace("\r", "")
