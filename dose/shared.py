"""Dose GUI for TDD: shared resources."""
import sys, os
from . import __version__
from .misc import read_plain_text

# This module can't be used by the setup.py script!

def get_shared(fname, encoding="utf-8"):
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
        return "\n".join(read_plain_text(prefixed_path, encoding=encoding))
    except IOError:
        pass

    # Homebrew (Mac OS X) stores the data in Cellar, a directory in
    # the system prefix. Calling "brew --prefix" returns that prefix,
    # and pip installs the shared resources there
    cellar_index = sys.prefix.find("/Cellar/")
    if cellar_index != -1: # Found!
        outside_cellar_path = os.path.join(sys.prefix[:cellar_index],
                                           *relative_path.split("/"))
        try:
            return "\n".join(read_plain_text(outside_cellar_path,
                                             encoding=encoding))
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
