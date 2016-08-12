"""Dose GUI for TDD: miscellaneous functions."""


def snake2ucamel(value):
    """Casts a snake_case string to an UpperCamelCase string."""
    return "".join(el.capitalize() for el in value.split("_"))


def attr_item_call_auto_cache(func):
    """
    Decorator for a a single positional argument function to cache
    its results and to make ``f("a") == f["a"] == f.a``.
    """
    return type(snake2ucamel(func.__name__), (dict,), {
      "__missing__": staticmethod(func),
      "__call__": dict.__getitem__,
      "__getattr__": dict.__getitem__,
      "__doc__": func.__doc__, # Class docstring can't be updated afterwards
      "__module__": func.__module__,
    })()
