"""Dose GUI for TDD: help dialog box and its underlying HTML processing."""
import itertools, wx, wx.html, docutils.core
from . import __url__
from .rest import all_but_blocks, rst_toc, section_header
from .shared import README, CHANGES


help_data = {
  "title": "Dose Help",
  "toc_msg": [
    "This help was generated using selected information from the",
    "Dose ``README.rst`` and ``CHANGES.rst`` project files.",
    "",
    __url__,
  ]
}

help_data["rst_body"] = list(itertools.chain(
  all_but_blocks(("copyright", "not-in-help"), README, newline=None),
  CHANGES
))

help_data["toc"] = rst_toc(help_data["rst_body"])

help_data["rst"] = itertools.chain(
  section_header(help_data["title"]),
  [""],
  help_data["toc"],
  [""],
  help_data["toc_msg"],
  ["", "----", ""],
  help_data["rst_body"]
)

help_data["html_body"] = (docutils.core.publish_parts(
  source = "\n".join(help_data["rst"]),
  writer_name = "html",
)["html_body"].replace("<div", "<a")   # Hack to create link
              .replace("</div", "</a") # anchors for the ToC
              .replace('class="section" id=', "name=")
).encode("utf-8")

# wx.html.HtmlWindow only renders a HTML subset
help_data["html"] = '<body bgcolor="#000000" text="#bbbbbb" link="#7fbbff">' \
                    "{body}</body>".format(body=help_data["html_body"])


class HtmlHelp(wx.html.HtmlWindow):
    """
    Help widget object that renders the HTML content and opens the
    default browser when an external link is clicked.
    """
    def __init__(self, *arg, **kwargs):
        super(HtmlHelp, self).__init__(*arg, **kwargs)
        self.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.on_html_link_clicked)

    def on_html_link_clicked(self, evt):
        url = evt.GetLinkInfo().Href
        if "://" in url:
            wx.LaunchDefaultBrowser(url)
        else:
            evt.Skip()

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
