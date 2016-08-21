"""Dose GUI for TDD: help dialog box and its underlying HTML processing."""
import wx, wx.html, docutils.core
from .rest import all_but_block
from .shared import README, CHANGES


help_data = {}

help_data["rst"] = "\n".join([all_but_block("copyright", README), ""] +
                             CHANGES)

help_data["body"] = docutils.core.publish_parts(
  source = help_data["rst"],
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
    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())


def help_box():
    """A simple HTML help dialog box using the distribution data files."""
    style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
    dialog_box = wx.Dialog(None, wx.ID_ANY, "Dose Help",
                           style=style, size=(620, 450))
    html_widget = HtmlHelp(dialog_box, wx.ID_ANY)
    html_widget.SetPage(help_data["html"].decode("utf-8"))
    dialog_box.ShowModal()
    dialog_box.Destroy()
