"""Dose GUI for TDD: compatibility utilities."""
import functools, importlib, sys, warnings
from .misc import LazyAccess, kw_map

__all__ = ["wx", "quote", "PY2", "UNICODE"]


def _wx_two_step_creation_on_classic(cls):
    """
    Patch the wxPython Classic class to behave like a wxPython
    Phoenix class on a 2-step creation process.

    On wxPython Phoenix, the first step is the parameterless
    ``__init__``, and the second step is the ``Create`` method with
    the construction parameters, e.g.::

        class CustomFrame(wx.Frame):
            def __init__(self, parent):
                super(CustomFrame, self).__init__() # 1st step
                # [...]
                self.Create(parent) # 2nd step
                # [...]

    On wxPython Classic, the same would be written as::

        class CustomFrame(wx.Frame):
            def __init__(self, parent):
                pre = wx.PreFrame() # 1st step
                # [... using "pre" instead of "self" ...]
                pre.Create(parent) # 2nd step
                self.PostCreate(pre) # "3rd step"
                # [...]
    """
    cls_init = cls.__init__
    cls_create = cls.Create

    @functools.wraps(cls_init)
    def __init__(self, *args, **kwargs):
        if args or kwargs:
            cls_init(self, *args, **kwargs)
        else: # 2-step creation
            new_self = getattr(wx, "Pre" + cls.__name__)()
            for pair in vars(new_self).items():
                setattr(self, *pair)

    if sys.platform == "win32":
        # On Windows, the wx.Pre*.Create constructors calls the
        # EVT_WINDOW_CREATE handler before returning (i.e, it processes
        # the event instead of just adding a message to the queue), and
        # that shouldn't happen before the PostCreate call in this thread
        @functools.wraps(cls_create)
        def create(self, *args, **kwargs):
            self.SetEvtHandlerEnabled(False)
            result = cls_create(self, *args, **kwargs)
            self.SetEvtHandlerEnabled(True)
            if result:
                self.PostCreate(self)
                wx.PostEvent(self, wx.WindowCreateEvent(self))
            return result
    else:
        @functools.wraps(cls_create)
        def create(self, *args, **kwargs):
            result = cls_create(self, *args, **kwargs)
            if result:
                self.PostCreate(self)
            return result

    cls.__init__ = __init__
    cls.Create = create


class LazyWx(LazyAccess):
    """
    Lazy access to wxPython, normalized to work on its 2.8 (Classic),
    3.0 (Classic) and Phoenix versions using the Phoenix names.

    https://wxpython.org/Phoenix/docs/html/classic_vs_phoenix.html
    """
    def __init__(self, module_name, import_name=None):
        self._module_name = module_name
        if import_name is None:
            import_name = module_name
        super(LazyWx, self).__init__(lambda: importlib
                                             .import_module(import_name))

    def __getattr__(self, name):
        if name in ["_obj", "PlatformInfo"]: # Avoid an endless recursion loop
            return super(LazyWx, self).__getattr__(name)
        if name == "PHOENIX":
            return self._cache(name, "phoenix" in wx.PlatformInfo)
        full_name = ".".join([self._module_name, name])
        if not self.PHOENIX and full_name in self._phoenix_names:
            return self._get_classic_equivalent(name)
        if full_name in self._imports:
            return self._cache(name, LazyWx(full_name))
        return super(LazyWx, self).__getattr__(name)

    def _get_classic_equivalent(self, name):
        full_name = ".".join([self._module_name, name])
        if full_name in self._not_in_classic:
            return self._cache(name, LazyWx(full_name, "wx"))
        if full_name in self._phoenix2classic:
            names = self._phoenix2classic[full_name].split(".")[1:]
            return self._cache(name, functools.reduce(getattr, names, wx))
        # The result exists, but requires some patch
        result = super(LazyWx, self).__getattr__(name)
        attr_map = self._phoenix2classic_attr.get(full_name, {})
        for k, replacement in attr_map.items():
            decorator, value_name = replacement
            names = value_name.split(".")[1:]
            value = functools.reduce(getattr, names, wx)
            setattr(result, k, value if decorator is None
                                     else decorator(value))
        if full_name in self._has_two_step_creation:
            _wx_two_step_creation_on_classic(result)
        return result

    _not_in_classic = ["wx.adv"]
    _imports = ["wx.adv", "wx.html"]
    _phoenix2classic = {
      "wx.BG_STYLE_PAINT": "wx.BG_STYLE_CUSTOM",
      "wx.Region": "wx.RegionFromBitmap",
      "wx.adv.AboutBox": "wx.AboutBox",
      "wx.adv.AboutDialogInfo": "wx.AboutDialogInfo",
    }
    _phoenix2classic_attr = { # Each replacement/patch has 4 parts
                              #   obj: {attr: (decorator, value)}
                              # which behaves like
                              #   eval(obj).attr = decorator(eval(value))
      "wx.Bitmap": {
        "FromRGBA": (staticmethod, "wx.EmptyBitmapRGBA"),
      },
      "wx.Menu": {
        "Append": (None, "wx.Menu.AppendItem"),
      },
      "wx.TextEntryDialog": {
        "__init__": (kw_map(defaultValue="value"),
                     "wx.TextEntryDialog.__init__")
      },
    }
    _has_two_step_creation = ["wx.Frame"]
    _phoenix_names = _not_in_classic + list(_phoenix2classic) \
                                     + list(_phoenix2classic_attr) \
                                     + _has_two_step_creation


wx = LazyWx("wx")

if sys.version_info < (3, 3):
    from pipes import quote
else:
    from shlex import quote

PY2 = sys.version_info[0] == 2

if PY2:
    UNICODE = unicode # NOQA
else:
    UNICODE = str


def allow_implicit_stop(gen_func):
    """
    Fix the backwards-incompatible PEP-0479 gotcha/bug
    https://www.python.org/dev/peps/pep-0479
    """
    @functools.wraps(gen_func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            for cls in [DeprecationWarning, PendingDeprecationWarning]:
                warnings.filterwarnings(
                    action="ignore",
                    message=".* raised StopIteration",
                    category=cls,
                )
            try:
                for item in gen_func(*args, **kwargs):
                    yield item
            except RuntimeError as exc:
                if type(exc.__cause__) is StopIteration:
                    return
                raise
    return wrapper
