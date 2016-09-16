"""Dose GUI for TDD: test module for the miscellaneous functions."""
import itertools, pytest
from dose.misc import (not_eq, tail, snake2ucamel, attr_item_call_auto_cache,
                       ucamel_method, LazyAccess, kw_map, read_plain_text)
from dose.compat import PY2


def test_not_eq():
    not_one = not_eq(1)
    assert not not_one(1)
    assert not_one(2)


class TestTail(object):

    def test_empty_result(self):
        assert list(tail({})) == []
        assert list(tail({55})) == []

    def test_few_items(self):
        assert list(tail(range(5))) == [1, 2, 3, 4]

    def test_from_endless_nested(self):
        result = tail(tail(itertools.cycle([-1, 2, 9])))
        expected = [9, -1, 2, 9, -1, 2, 9, -1, 2, 9]
        selected = [next(result) for unused in expected]
        assert selected == expected


class TestSnake2UCamel(object):

    def test_empty(self):
        assert snake2ucamel("") == ""

    def test_no_under(self):
        assert snake2ucamel("maxsize") == "Maxsize"
        assert snake2ucamel("abigname") == "Abigname"

    def test_has_under(self):
        assert snake2ucamel("max_size") == "MaxSize"
        assert snake2ucamel("a_big_name") == "ABigName"

    def test_has_numbers(self):
        assert snake2ucamel("convert2string") == "Convert2String"
        assert snake2ucamel("this_is_1_number") == "ThisIs1Number"

    def test_ends_with_numbers(self):
        assert snake2ucamel("testing2") == "Testing2"
        assert snake2ucamel("number_1") == "Number1"
        assert snake2ucamel("not_135") == "Not135"
        assert snake2ucamel("do_it_again2") == "DoItAgain2"

    def test_private_leading_underscore(self):
        assert snake2ucamel("_abigname") == "_Abigname"
        assert snake2ucamel("_a_big_name") == "_ABigName"

    def test_protected_leading_double_underscore(self):
        assert snake2ucamel("__maxsize") == "__Maxsize"
        assert snake2ucamel("__max_size") == "__MaxSize"

    def test_protected_name_mangling(self):
        assert snake2ucamel("_myattr__FromThisClass") \
               == "_Myattr__FromThisClass"
        assert snake2ucamel("_my_attr__FromThisClass") \
               == "_MyAttr__FromThisClass"

    def test_dunder(self):
        assert snake2ucamel("__magic__") == "__Magic__"
        assert snake2ucamel("__some_magic__") == "__SomeMagic__"

    def test_trailing_underscore(self):
        assert snake2ucamel("data_") == "Data_"
        assert snake2ucamel("another_data_") == "AnotherData_"

    def test_requires_underscores_as_separators(self):
        assert snake2ucamel("these_are_1_2_3_numbers") \
               == "TheseAre1_2_3Numbers"
        assert snake2ucamel("invalid%#_@s__123_456_name_") \
               == "Invalid%#_@S__123_456Name_"


class TestAttrItemCallAutoCache(object):

    def test_cache_len_and_assignments(self):
        def count():
            """A function that returns how many times it was called"""
            count.i = getattr(count, "i", 0) + 1
            return count.i

        @attr_item_call_auto_cache
        def mapping(value):
            return count()

        data = mapping("a"), mapping.b, mapping["c"]
        assert len(mapping) == 3
        assert data == (1, 2, 3)
        assert mapping("a") == mapping["a"] == mapping.a == 1
        assert mapping("b") == mapping["b"] == mapping.b == 2
        assert mapping("c") == mapping["c"] == mapping.c == 3 == count.i
        assert mapping("d") == mapping["d"] == mapping.d == 4 == count.i
        assert len(mapping) == 4
        del mapping["a"] # Remove from the cache
        assert mapping("a") == mapping["a"] == mapping.a == 5 == count.i
        assert count() == 6

    def test_keep_attributes(self):
        def old_func(value):
            """Empty function. At least it has a docstring!"""
        old_func.some_public_attr = "public data"
        old_func._internal_data = "internal data"
        new_func = attr_item_call_auto_cache(old_func)
        for attr in ["some_public_attr", "_internal_data",
                     "__module__", "__doc__"]:
            assert getattr(new_func, attr) == getattr(old_func, attr)


class TestUCamelMethod(object):

    def test_method(self):
        class ThisIsAClass(object):
            @ucamel_method
            def here_lies_a_method(self):
                return 22
        assert ThisIsAClass().HereLiesAMethod() == 22

    def test_function_in_locals(self):
        @ucamel_method
        def this_is_a_function():
            pass
        assert locals()["ThisIsAFunction"] is this_is_a_function


def test_lazy_access():
    class Once(object):
        some_attribute = "a string"
        count = 0

        def __init__(self):
            Once.count += 1
            assert Once.count == 1

        def some_method(self):
            return self.some_attribute

        @property
        def me(self):
            return self

    la = LazyAccess(Once)

    assert "some_method" not in vars(la)
    assert "some_attribute" not in vars(la)
    assert "_obj" not in vars(la)

    assert la.count == 1
    assert la.some_method() == la.some_attribute == "a string"

    if PY2:
        assert la.some_method.im_func is Once.some_method.im_func
    else:
        assert la.some_method.__func__ is Once.some_method

    assert "some_method" in vars(la)
    assert "some_attribute" in vars(la)
    assert "_obj" in vars(la)

    assert isinstance(la._obj, Once)
    assert "me" not in vars(la)
    assert la.me is la._obj
    assert "me" in vars(la)


class TestKwMap(object):

    def test_maps_names(self):
        @kw_map(a="first", b="second")
        def add(a, b):
            return a + b
        assert add(first=2, second=3) == 5

    def test_with_posargs(self):
        @kw_map(kwparam1="one")
        def params_as_tuple(param1, param2, kwparam1, kwparam2=None):
            return param1, param2, kwparam1, kwparam2
        assert params_as_tuple(1, 2, 3, 4) == (1, 2, 3, 4)
        assert params_as_tuple(1, 2, kwparam2=4, one=3) == (1, 2, 3, 4)
        assert params_as_tuple(2, 3, 4) == (2, 3, 4, None)
        assert params_as_tuple(2, 3, one=4) == (2, 3, 4, None)


class TestReadPlainText(object):

    def test_file_not_found(self):
        with pytest.raises(IOError):
            read_plain_text("/this __ / file / doesnt/exist")

    @pytest.mark.parametrize("data", [[],
                                      ["Single line data"],
                                      ["", "Empty first line"],
                                      ["Multi line", "", "data!", ""],
                                     ])
    def test_file_data(self, data, tmpdir):
        txt_file = tmpdir.join("temporary.txt")
        txt_file.write("\n".join(data))
        assert read_plain_text(txt_file.strpath) == data
