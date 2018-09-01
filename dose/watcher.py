"""Dose GUI for TDD: file system event watcher."""
import sys, os, contextlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .compat import UNICODE


def to_unicode(path, errors="replace"):
    """Given a bytestring/unicode path, return it as unicode."""
    if isinstance(path, UNICODE):
        return path
    return path.decode(sys.getfilesystemencoding(), errors)


class GeneralEventHandler(FileSystemEventHandler):

    def __init__(self, path, selector, handler):
        self.path = path
        self.selector = selector
        self.handler = handler

    def on_any_event(self, evt):
        evt.path = os.path.relpath(to_unicode(evt.src_path), self.path)
        if self.selector(evt):
            self.handler(evt)


@contextlib.contextmanager
def watcher(path, selector, handler):
    path = to_unicode(path)
    observer = Observer()
    cls_handler = GeneralEventHandler(path, selector, handler)
    observer.schedule(cls_handler, path, recursive=True)
    observer.start()
    yield observer
    observer.stop()
    observer.join()
