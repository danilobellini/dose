"""Dose GUI for TDD: test module for the reStructuredText stuff."""
import pytest, collections, itertools
from dose.rest import (indent_size, get_block, all_but_blocks, commentless,
                       single_line, single_line_block)


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


class ATestBlock(object):
    lines = "\n\n".join([
      "This is",
      ".. blah",
      "some text",
      ".. blah end",
    ])
    data = lines.splitlines()
    double_data = lines.replace("some", "another").splitlines() + data
    nested_data = lines.replace("blah", "outer") \
                       .replace("some text", lines).splitlines()
    blockless_data = ["Do you need", "", "some", "blockless data?"]
    tdn_data = lines.replace("blah", "first").splitlines() + data
    endless_data = itertools.cycle(["again", ".. some name",
                                             ".. some name end", ""])


class TestGetBlock(ATestBlock):

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


class TestAllButBlocks(ATestBlock):

    @pytest.mark.parametrize("names", ["blah", ("blah",), ("blah",) * 4])
    def test_0_to_2_blocks_with_default_and_custom_newline(self, names):
        assert all_but_blocks(names, self.blockless_data) \
               == "Do you need\n\nsome\nblockless data?"
        assert all_but_blocks(names, self.blockless_data, newline="!!") \
               == "Do you need!!!!some!!blockless data?"
        assert all_but_blocks(names, self.data) \
               == "This is\n"
        assert all_but_blocks(names, self.data, newline="-") \
               == "This is-"
        assert all_but_blocks(names, self.double_data) \
               == "This is\n\nThis is\n"
        assert all_but_blocks(names, self.double_data, newline="-") \
               == "This is--This is-"
        assert all_but_blocks(names, self.double_data, newline="") \
               == "This isThis is"

    @pytest.mark.parametrize("names", ["blah", ("blah", "blah")])
    def test_nested_block_remove_params(self, names):
        args = names, self.nested_data
        kw_remove = {"remove_empty_next": False, "remove_comments": False}
        assert all_but_blocks(*args) \
               == "This is\n\nThis is\n"
        assert all_but_blocks(*args, newline="~") \
               == "This is~~This is~"
        assert all_but_blocks(*args, remove_empty_next=False) \
               == "This is\n\nThis is\n\n"
        assert all_but_blocks(*args, newline="~", remove_empty_next=False) \
               == "This is~~This is~~"
        assert all_but_blocks(*args, remove_comments=False) \
               == "This is\n\n.. outer\n\nThis is\n\n.. outer end"
        assert all_but_blocks(*args, newline="~", remove_comments=False) \
               == "This is~~.. outer~~This is~~.. outer end"
        assert all_but_blocks(*args, **kw_remove) \
               == "This is\n\n.. outer\n\nThis is\n\n\n.. outer end"
        assert all_but_blocks(*args, newline="~", **kw_remove) \
               == "This is~~.. outer~~This is~~~.. outer end"

    def test_two_distinct_names(self):
        assert all_but_blocks(("first", "blah"), self.tdn_data) \
               == "This is\n\nThis is\n"
        assert all_but_blocks("first", self.tdn_data) \
               == "This is\n\nThis is\n\nsome text\n"
        assert all_but_blocks("blah", self.tdn_data) \
               == "This is\n\nsome text\n\nThis is\n"

    def test_generator_when_newline_is_none_and_data_is_endless(self):
        result = all_but_blocks("some name", self.endless_data, newline=None)
        assert isinstance(result, collections.Iterator)
        for unused in range(30):
            line = next(result)
            assert line == "again"


class TestCommentless(ATestBlock):

    def test_no_comments(self):
        data = ["128y9h12789y", "  s", "  ", "-..s", "  -.", "", "",
                ".. image: here.jpg", ""]
        assert list(commentless(data)) == data

    def test_single_line_comments_endless(self):
        result = commentless(self.endless_data)
        for idx, line in zip(range(30), result):
            assert line == "again"

    def test_multiline_comment_continuation_indented(self):
        result = commentless("  _" if line.endswith("end") else line
                             for line in self.endless_data)
        for idx, line in zip(range(30), result):
            assert line == "again"

    def test_multiline_unstable_indentation_with_empty_lines(self):
        result = commentless([
          ".. comment",
          "",
          "  indented data",
          "    ",
          "   more indented data",
          " ending",
          "continuation",
        ] * 3)
        assert isinstance(result, collections.Iterator)
        assert list(result) == ["continuation"] * 3

    def test_links_arent_comments(self):
        data = [
          "Text text text.",
          "",
          ".. _`some link`:",
          "  protocol://some.where.in/the/web",
          "",
          "",
          ".. some comment here",
          "",
          "Title",
          "-----",
        ]
        expected_once = data[:-4] + data[-2:]
        result = commentless(data * 2)
        assert isinstance(result, collections.Iterator)
        assert list(result) == expected_once * 2


def test_single_line():
    assert single_line(["", "this", "   is", "  a    ", "test ", "   "]) \
           == "this is a test"


def test_single_line_block():
    assert single_line_block("blah", TestGetBlock.data) == "some text"
    assert single_line_block("blah",
                             TestGetBlock.double_data) == "another text"
