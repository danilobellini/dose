"""Dose GUI for TDD: compatibility utilities."""
import functools, importlib
from .misc import LazyAccess, kw_map


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
        for k, replacement in self._phoenix2classic_attr[full_name].items():
            decorator, value_name = replacement
            names = value_name.split(".")[1:]
            value = functools.reduce(getattr, names, wx)
            setattr(result, k, value if decorator is None
                                     else decorator(value))
        return result

    _not_in_classic = ["wx.adv"]
    _imports = ["wx.adv", "wx.html"]
    _phoenix2classic = {
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
    _phoenix_names = _not_in_classic + list(_phoenix2classic) \
                                     + list(_phoenix2classic_attr)


wx = LazyWx("wx")
