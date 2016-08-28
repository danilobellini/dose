"""Dose GUI for TDD: test module for the reStructuredText stuff."""
import pytest, collections
from dose.rest import (indent_size, get_block, single_line, single_line_block,
                       section_header)


class TestIndentSize(object):

    def test_zero(self):
        assert indent_size("") == 0
        assert indent_size("t") == 0
        assert indent_size("test") == 0
        assert indent_size("Something here") == 0

    @pytest.mark.parametrize("n", [1, 2, 4, 7])
    def test_n(self, n):
        indent = " " * n
        assert indent_size(indent) == n
        assert indent_size(indent + "t") == n
        assert indent_size(indent + "test") == n
        assert indent_size(indent + "Something here") == n


class TestGetBlock(object):
    lines = "\n\n".join([
      "This is",
      ".. blah",
      "some text",
      ".. blah end",
    ])
    data = lines.splitlines()
    double_data = lines.replace("some", "another").splitlines() + data

    def test_simple_named_block(self):
        assert get_block("blah", self.data) == "\nsome text\n"

    def test_simple_named_block_custom_newline(self):
        assert get_block("blah", self.data, newline="\r\n") \
               == "\r\nsome text\r\n"

    def test_simple_named_block_generator(self):
        blk = get_block("blah", self.data, newline=None)
        assert isinstance(blk, collections.Iterator)
        assert list(blk) == ["", "some text", ""]

    def test_block_not_found(self):
        assert get_block("something_not_used", self.data) == ""

    def test_block_not_found_generator(self):
        blk = get_block("something_not_used", self.data, newline=None)
        assert isinstance(blk, collections.Iterator)
        assert list(blk) == []

    def test_twice_gets_only_first(self):
        assert get_block("blah", self.double_data) == "\nanother text\n"

    def test_twice_gets_only_first_generator(self):
        blk = get_block("blah", self.double_data, newline=None)
        assert isinstance(blk, collections.Iterator)
        assert list(blk) == ["", "another text", ""]


def test_single_line():
    assert single_line(["", "this", "   is", "  a    ", "test ", "   "]) \
           == "this is a test"


def test_single_line_block():
    assert single_line_block("blah", TestGetBlock.data) == "some text"
    assert single_line_block("blah",
                             TestGetBlock.double_data) == "another text"


def test_section_header():
    assert section_header("") == ["", ""]
    assert section_header("T") == ["T", "="]
    assert section_header("est", "-") == ["est", "---"]
    assert section_header("Some stuff", "~") == ["Some stuff", "~" * 10]
