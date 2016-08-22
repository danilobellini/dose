"""Dose GUI for TDD: help dialog box and its underlying HTML processing."""
import itertools, wx, wx.html, docutils.core
from .rest import all_but_blocks
from .shared import README, CHANGES
from .misc import ucamel_method


help_data = {}

help_data["rst"] = list(itertools.chain(
  all_but_blocks(("copyright", "not-in-help"), README, newline=None),
  CHANGES
))

help_data["body"] = docutils.core.publish_parts(
  source = "\n".join(help_data["rst"]),
  writer_name = "html",
)["html_body"].encode("utf-8")

# wx.html.HtmlWindow only renders a HTML subset
help_data["html"] = '<body bgcolor="#000000" text="#bbbbbb" link="#7fbbff">' \
                    "{body}</body>".format(body=help_data["body"])


class HtmlHelp(wx.html.HtmlWindow):
    """
    Help widget object that renders the HTML content and opens the
    default browser when a link is clicked.
    """
    @ucamel_method
    def on_link_clicked(self, link):
        wx.LaunchDefaultBrowser(link.Href)

    page = property(fset = lambda self, value: self.SetPage(value))


def help_box():
    """A simple HTML help dialog box using the distribution data files."""
    style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
    dialog_box = wx.Dialog(None, wx.ID_ANY, "Dose Help",
                           style=style, size=(620, 450))
    html_widget = HtmlHelp(dialog_box, wx.ID_ANY)
    html_widget.page = help_data["html"].decode("utf-8")
    dialog_box.ShowModal()
    dialog_box.Destroy()
