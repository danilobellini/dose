"""Dose GUI for TDD: shared resources."""
import sys, os
from . import _from_setup, __version__
from .misc import read_plain_text


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
    paths = []

    # Look for the shared file based on current __file__,
    # this approach should work when importing this from setup.py,
    # but one should not rely on it elsewhere
    resource_path = os.path.join(os.path.dirname(__file__), "..", fname)
    if _from_setup:
        paths.append(resource_path)

    # Look for the file directly on sys.prefix
    paths.append(os.path.join(sys.prefix, *relative_path.split("/")))

    # Homebrew (Mac OS X) stores the data in Cellar, a directory in
    # the system prefix. Calling "brew --prefix" returns that prefix,
    # and pip installs the shared resources there
    cellar_index = sys.prefix.find("/Cellar/")
    if cellar_index != -1: # Found!
        paths.append(os.path.join(
            sys.prefix[:cellar_index],
            *relative_path.split("/")
        ))

    # Try to load directly from one of the selected file paths
    for path in paths:
        try:
            return "\n".join(read_plain_text(path, encoding=encoding))
        except IOError:
            pass

    # Fallback: look for the file using setuptools (perhaps it's still
    # compressed inside an egg file or stored otherwhere)
    from pkg_resources import (
        DistributionNotFound, Requirement, resource_string
    )
    try:
        return resource_string(Requirement.parse("dose"), relative_path)
    except (IOError, DistributionNotFound):
        if not _from_setup:  # Last resort when outside of setup.py
            return "\n".join(read_plain_text(resource_path, encoding=encoding))
        raise


README = get_shared("README.rst").splitlines()
CHANGES = get_shared("CHANGES.rst").splitlines()
CONTRIBUTORS = get_shared("CONTRIBUTORS.txt").splitlines()
LICENSE = get_shared("COPYING.txt").replace("\r", "")
