"""Dose GUI for TDD: help dialog box and its underlying HTML processing."""
import locale # docutils.core calls these locale functions on import time
try: # Fix this issue: https://bugs.python.org/issue18378
    locale.getdefaultlocale()
except ValueError: # Usually with the message "unknown locale: UTF-8"
    locale.getdefaultlocale = lambda: (None, locale.getpreferredencoding())
try:
    locale.getlocale()
except ValueError: # The same, on Python 3
    locale.getlocale = locale.getdefaultlocale

import sys, docutils.core, docutils.nodes
from . import __url__
from .rest import all_but_blocks
from .shared import README, CHANGES
from .compat import wx


HELP_TITLE = "Dose Help" # Dialog/modal window title
HELP_BG_COLOR = "#000000"
HELP_FG_COLOR = "#bbbbbb"
HELP_LINK_COLOR = "#7fbbff"
HELP_LITERAL_COLOR = "#ffffff"
HELP_INDENT_WIDTH = "2em" # For literal blocks


class Doctree2HtmlForWx(docutils.nodes.GenericNodeVisitor):
    """
    Translator from a docutils document (doctree) to a
    ``wx.html.HtmlWindow`` compatible HTML.

    It's a visitor whose ``body`` and ``toc`` attributes are updated
    on traversing a doctree. The former attribute has the HTML as a
    list of strings to be joined, the latter has an HTML alike but
    with a generated table of contents. The result has anchors/links
    to the different sections.
    """
    escape = { # HTML escape codes
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "&": "&amp;",
    }
    tags = { # Maps from a doctree node tag name to an HTML element tag name
      "bullet_list": "ul",
      "emphasis": "i",
      "paragraph": "p",
      "list_item": "li",
      "reference": "a",
      "strong": "b",
    }
    tags_depart = {k: v.join(["</", ">"]) for k, v in tags.items()}
    tags_visit = {k: v.join("<>") for k, v in tags.items()}
    tags_visit["transition"] = "<hr/>"
    return_to_toc = '<p><a href="#0">&lt;&lt; Return &lt;&lt;</a></p>'

    def __init__(self, document):
        docutils.nodes.GenericNodeVisitor.__init__(self, document)
        self.body = []
        self.toc = []
        self.target = 0
        self.level = 0
        self.ul_level = 0

    @property
    def htag(self):
        return "h%d" % self.level

    def html_escape(self, text):
        return "".join(self.escape.get(ch, ch) for ch in text)

    def default_visit(self, node):
        if node.tagname == "#text":
            self.body.append(self.html_escape(node.astext()))
        elif node.tagname not in ["document", "comment", "target"]:
            self.body.append(self.tags_visit[node.tagname])

    def default_departure(self, node):
        if node.tagname not in ["#text", "transition", "comment", "target"]:
            self.body.append(self.tags_depart[node.tagname])

    def visit_reference(self, node):
        self.body.append('<a href="{0}">'.format(node["refuri"]))

    def depart_bullet_list(self, node):
        self.body.append("\n</ul>\n") # Both "\n" are required here for
                                      # wx.html.HtmlWindow to properly render

    def visit_literal(self, node):
        self.body.append('<font color="{0}"><tt>'.format(HELP_LITERAL_COLOR))

    def depart_literal(self, node):
        self.body.append("</tt></font>")

    def visit_literal_block(self, node):
        self.body.append('<font color="{0}"><table border="0"><tr>'
                           '<td width="{1}"></td>'
                           '<td><pre>'
                         .format(HELP_LITERAL_COLOR, HELP_INDENT_WIDTH))

    def depart_literal_block(self, node):
        self.body.append("</pre></td></tr></table></font>")

    def visit_section(self, node):
        if self.level == self.ul_level:
            if self.ul_level == 0: # The first section starts now
                self.sectionless = self.body
                self.body = []
                self.toc.append("<p/>")
            self.toc.append("<ul>")
            self.ul_level += 1
        self.level += 1

    def depart_section(self, node):
        if self.level == self.ul_level - 1:
            self.toc.append("\n</ul>\n")
            self.ul_level -= 1
        self.level -= 1

    def visit_title(self, node):
        if self.target != 0:
            self.body.extend([self.return_to_toc, "<hr/>"])
        self.target += 1
        self.body.append('<a name="{0}"><{1}>'.format(self.target, self.htag))
        value = self.html_escape(node[0].astext())
        self.toc.append('<li><a href="#{0}">{1}</li>'.format(self.target,
                                                             value))

    def depart_title(self, node):
        self.body.append("</{0}></a>".format(self.htag))

    def depart_document(self, node):
        self.body.append(self.return_to_toc)
        self.toc.append("\n</ul>\n")


def build_help_html():
    """Build the help HTML using the shared resources."""
    remove_from_help = ["not-in-help", "copyright"]
    if sys.platform in ["win32", "cygwin"]:
        remove_from_help.extend(["osx", "linux"])
    elif sys.platform == "darwin":
        remove_from_help.extend(["linux", "windows", "linux-windows"])
    else:
        remove_from_help.extend(["osx", "windows"])
    readme_part_gen = all_but_blocks(remove_from_help, README, newline=None)
    rst_body = "\n".join(list(readme_part_gen) + CHANGES)
    doctree = docutils.core.publish_doctree(rst_body)
    visitor = Doctree2HtmlForWx(doctree)
    doctree.walkabout(visitor) # Fills visitor.body and visitor.toc
    return ( # wx.html.HtmlWindow only renders a HTML subset
      u'<body bgcolor="{bg}" text="{fg}" link="{link}">'
      u'<a name="0"><h1>{title}</h1></a>'
      u"{sectionless}"
      u"{toc}"
      u"<p>This help was generated using selected information from the\n"
      u"Dose <tt>README.rst</tt> and <tt>CHANGES.rst</tt> project files.</p>"
      u'<p><a href="{url}">{url}</a></p><hr/>'
      u"{body}</body>"
    ).format(bg=HELP_BG_COLOR, fg=HELP_FG_COLOR, link=HELP_LINK_COLOR,
             title=HELP_TITLE, sectionless=u"".join(visitor.sectionless),
             toc=u"".join(visitor.toc), url=__url__,
             body=u"".join(visitor.body))


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

    page = property(fset=wx.html.HtmlWindow.SetPage)


def help_box():
    """A simple HTML help dialog box using the distribution data files."""
    style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
    dialog_box = wx.Dialog(None, wx.ID_ANY, HELP_TITLE,
                           style=style, size=(620, 450))
    html_widget = HtmlHelp(dialog_box, wx.ID_ANY)
    html_widget.page = build_help_html()
    dialog_box.ShowModal()
    dialog_box.Destroy()
