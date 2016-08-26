"""Dose GUI for TDD: test module for the reStructuredText stuff."""
import collections
from dose.rest import get_block


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
