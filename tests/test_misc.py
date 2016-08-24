"""Dose GUI for TDD: test module for the miscellaneous functions."""
from dose.misc import snake2ucamel


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
