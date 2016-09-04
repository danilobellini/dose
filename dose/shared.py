"""Dose GUI for TDD: shared resources."""
import sys, os
from . import __version__

# This module can't be used by the setup.py script!

def get_shared(fname):
    """
    Loads the string data from a text file that was packaged as a
    data file in the distribution.

    Uses the setuptools ``pkg_resources.resource_string`` function as
    a fallback, as installing Dose with it directly instead of using
    wheel/pip would store the setup.py ``data_files`` otherwhere. For
    more information, see this:

    https://github.com/pypa/setuptools/issues/130
    """
    relative_path = "share/dose/v{0}/{1}".format(__version__, fname)
    prefixed_path = os.path.join(sys.prefix, *relative_path.split("/"))

    # Look for the file directly on sys.prefix
    try:
        with open(prefixed_path) as f:
            return f.read()
    except IOError:
        pass

    # Fallback: look for the file using setuptools (perhaps it's still
    # compressed inside an egg file or stored otherwhere)
    from pkg_resources import Requirement, resource_string
    return resource_string(Requirement.parse("dose"), relative_path)


README = get_shared("README.rst").splitlines()
CHANGES = get_shared("CHANGES.rst").splitlines()
CONTRIBUTORS = get_shared("CONTRIBUTORS.txt").splitlines()
LICENSE = get_shared("COPYING.txt").replace("\r", "")
