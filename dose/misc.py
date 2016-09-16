"""Dose GUI for TDD: miscellaneous functions."""
import inspect, string, itertools, functools, io

# Be careful: this file is imported by setup.py!


def not_eq(value):
    """Partial evaluation of ``!=``, ``not_eq(a)(b)`` is ``a != b``."""
    return lambda el: value != el


def tail(iterable):
    """Iterator for the given iterable that skips its first item."""
    iterator = iter(iterable)
    try:
        next(iterator)
    except StopIteration:
        pass
    return iterator


def snake2ucamel(value):
    """Casts a snake_case string to an UpperCamelCase string."""
    UNDER, LETTER, OTHER = object(), object(), object()
    def group_key_function(char):
        if char == "_":
            return UNDER
        if char in string.ascii_letters:
            return LETTER
        return OTHER
    def process_group(idx, key, chars):
        if key is LETTER:
            return "".join([chars[0].upper()] + chars[1:])
        if key is OTHER     \
        or len(chars) != 1  \
        or idx in [0, last] \
        or LETTER not in (groups[idx-1][1], groups[idx+1][1]):
            return "".join(chars)
        return ""
    raw_groups_gen = itertools.groupby(value, key=group_key_function)
    groups = [(idx, key, list(group_gen))
              for idx, (key, group_gen) in enumerate(raw_groups_gen)]
    last = len(groups) - 1
    return "".join(itertools.starmap(process_group, groups))


def attr_item_call_auto_cache(func):
    """
    Decorator for a a single positional argument function to cache
    its results and to make ``f("a") == f["a"] == f.a``.
    """
    def __missing__(self, key):
        result = self[key] = func(key)
        return result
    wrapper = type(snake2ucamel(func.__name__), (dict,), {
      "__missing__": __missing__,
      "__call__": dict.__getitem__,
      "__getattr__": dict.__getitem__,
      "__doc__": func.__doc__, # Class docstring can't be updated afterwards
      "__module__": func.__module__,
    })()
    for k, v in vars(func).items():
        setattr(wrapper, k, v)
    return wrapper


def ucamel_method(func):
    """
    Decorator to ensure the given snake_case method is also written in
    UpperCamelCase in the given namespace. That was mainly written to
    avoid confusion when using wxPython and its UpperCamelCaseMethods.
    """
    frame_locals = inspect.currentframe().f_back.f_locals
    frame_locals[snake2ucamel(func.__name__)] = func
    return func


class LazyAccess(object):
    """
    Lazy access to the object attributes. Create it with a
    parameterless constructor like ``LazyAccess(lambda: my_object)``.
    """
    def __init__(self, parameterless_constructor):
        self._parameterless_constructor = parameterless_constructor

    def _cache(self, name, value):
        setattr(self, name, value)
        return value

    def __getattr__(self, name):
        if name == "_obj": # Only once
            return self._cache(name, self._parameterless_constructor())
        return self._cache(name, getattr(self._obj, name))


def kw_map(**kws):
    """
    Decorator for renamed keyword arguments, given a keyword argument
    mapping "actual_name: kwarg_rename" for each keyword parameter to
    be renamed.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for actual_name, kwarg_rename in kws.items():
                if kwarg_rename in kwargs:
                    kwargs[actual_name] = kwargs[kwarg_rename]
                    del kwargs[kwarg_rename]
            return func(*args, **kwargs)
        return wrapper
    return decorator


def read_plain_text(fname, encoding="utf-8"):
    """Reads a file as a list of strings."""
    with io.open(fname, encoding=encoding) as f:
        result = list(f)
    if result:
        if result[-1][-1:] == "\n":
            result.append("\n")
        else:
            result[-1] += "\n"
        return [line[:-1] for line in result]
    return []
