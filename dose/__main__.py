"""Dose GUI for TDD: main script / entry point."""
import colorama, click
from dose._legacy import DoseMainWindow
from dose.misc import ucamel_method
from dose.compat import wx, quote


def main_wx(test_command=None):

    class DoseApp(wx.App):

        @ucamel_method
        def on_init(self): # Called by wxPython
            self.SetAppName("dose")
            wnd = DoseMainWindow(None)
            wnd.Show()
            self.SetTopWindow(wnd)
            return True # Needed by wxPython

    # At least wx.html should be imported before the wx.App instance is
    # created, else wx.html.HtmlWindow instances won't render properly
    # https://github.com/wxWidgets/Phoenix/blob/db8957f/etg/_html.py#L23
    import wx.html as unused # NOQA

    app = DoseApp(redirect=False) # Don't redirect sys.stdout / sys.stderr
    if test_command:
        app.GetTopWindow().auto_start(test_command)
    app.MainLoop()


@click.command(context_settings={
    "allow_interspersed_args": False
})
@click.argument('test', nargs=-1, required=False, type=click.UNPROCESSED)
def main(test):
    """
    TEST: test command with options/arguments
    """
    colorama.init() # Replaces sys.stdout / sys.stderr to
                    # accept ANSI escape codes on Windows
    if len(test) > 1:
        test = map(quote, test)
    main_wx(test_command=" ".join(test))


if __name__ == "__main__": # Not a "from dose import __main__"
    main()
