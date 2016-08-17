"""Dose GUI for TDD: file system event watcher."""
import contextlib, platform

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


def _fix_watchdog_inotify():
    """
    On Linux, a fast directory creation/deletion loop for a
    directory with the same name crashes watchdog due to the way
    it caches the path names. This fix is for watchdog 0.8.3,
    hopefully future versions won't need this anymore.

    As a more detailed explanation, this avoids the watchdog
    issues 117 and 233. A trigger to this is a inotify event
    sequence for a single directory:

      IN_CREATE, IN_DELETE, IN_CREATE, IN_DELETE,
      IN_DELETE_SELF, IN_IGNORE, IN_DELETE_SELF, IN_IGNORE

    For each IN_CREATE, watchdog has a wd, but in the IN_IGNORE
    watchdog removes the wd based on the path, so the first
    IN_IGNORE removes the second wd and trying to read that wd
    afterwards crashes the watchdog thread. This function fixes
    that.
    """
    if platform.system() == "Linux":
        from watchdog.observers.inotify_c import Inotify
        from functools import wraps

        parser = Inotify._parse_event_buffer
        @staticmethod
        def _parse_event_buffer(event_buffer):
            for wd, mask, cookie, name in parser(event_buffer):
                Inotify._last_wd_parsed = wd
                yield wd, mask, cookie, name

        def _remove_watch_bookkeeping(self, path):
            del self._path_for_wd[Inotify._last_wd_parsed]
            if Inotify._last_wd_parsed == self._wd_for_path[path]:
                del self._wd_for_path[path]
            return Inotify._last_wd_parsed

        remover = Inotify.remove_watch
        def remove_watch(self, path):
            Inotify._last_wd_parsed = self._wd_for_path[path]
            remover(self, path)

        Inotify._parse_event_buffer = _parse_event_buffer
        Inotify._remove_watch_bookkeeping = _remove_watch_bookkeeping
        Inotify.remove_watch = remove_watch

_fix_watchdog_inotify()
