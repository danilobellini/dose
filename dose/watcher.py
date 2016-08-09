"""Dose GUI for TDD: file system event watcher."""
import contextlib

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class GeneralEventHandler(FileSystemEventHandler):

    def __init__(self, selector, handler):
        self.selector = selector
        self.handler = handler

    def on_any_event(self, evt):
        if self.selector(evt):
            self.handler(evt)


@contextlib.contextmanager
def watcher(path, selector, handler):
    observer = Observer()
    cls_handler = GeneralEventHandler(selector, handler)
    observer.schedule(cls_handler, path, recursive=True)
    observer.start()
    yield observer
    observer.stop()
    observer.join()
