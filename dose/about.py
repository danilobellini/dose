"""Dose GUI for TDD: about dialog box."""
import wx, itertools
from pkg_resources import Requirement, resource_string
from . import __version__, __author__, __author_email__, __url__
from .rest import single_line_block
from .misc import snake2ucamel


def get_shared(fname):
    """
    Using the setuptools package resources, gets the string data from a
    text file that was packaged as a data file in the distribution.
    """
    return resource_string(Requirement("dose"), "share/dose/" + fname)


README = get_shared("README.rst").splitlines()
CONTRIBUTORS = get_shared("CONTRIBUTORS.txt").splitlines()


metadata = {
  "copyright": single_line_block("copyright", README),
  "developers": CONTRIBUTORS,
  "description": single_line_block("summary", README),
  "version": __version__,
  "name": "Dose",
  "license": get_shared("COPYING.txt").replace("\r", ""),
  "web_site": __url__,
}


def about_box():
    """A simple about box dialog using the distribution data files."""
    about_info = wx.AboutDialogInfo()
    for k, v in metadata.items():
        setattr(about_info, snake2ucamel(k), v)
    wx.AboutBox(about_info)
