"""Dose GUI for TDD: main script / entry point."""
import sys, pipes
from dose._legacy import DoseMainWindow


def main_wx(test_command=None):
    import wx

    class DoseApp(wx.App):

        def OnInit(self): # Called by wxPython
            self.SetAppName("dose")
            wnd = DoseMainWindow(None)
            wnd.Show()
            self.SetTopWindow(wnd)
            return True # Needed by wxPython

    app = DoseApp(redirect=False) # Don't redirect sys.stdout / sys.stderr
    if test_command:
        app.GetTopWindow().auto_start(test_command)
    app.MainLoop()


def main(*args):
    if not args:
        if len(sys.argv) > 2:
            args = map(pipes.quote, sys.argv[1:])
        else:
            args = sys.argv[1:]
    main_wx(test_command=" ".join(args))


if __name__ == "__main__": # Not a "from dose import __main__"
    main()
