from ScriptCollection.core import get_ScriptCollection_version, string_is_none_or_whitespace, string_is_none_or_empty, write_lines_to_file, read_lines_from_file, SCOrganizeLinesInFile
import pytest
import os
import unittest

testfileprefix = "testfile_"
encoding = "utf-8"
version = "1.12.20"


class MiscellaneousTests(unittest.TestCase):

    def test_version(self):
        assert version == get_ScriptCollection_version()

    def test_string_is_none_or_whitespace(self):
        assert string_is_none_or_whitespace(None)
        assert string_is_none_or_whitespace("")
        assert string_is_none_or_whitespace(" ")
        assert string_is_none_or_whitespace("   ")
        assert not string_is_none_or_whitespace("not empty string")

    def test_string_is_none_or_empty(self):
        assert string_is_none_or_empty(None)
        assert string_is_none_or_empty("")
        assert not string_is_none_or_empty(" ")
        assert not string_is_none_or_empty("   ")
        assert not string_is_none_or_empty("not empty string")

    def test_write_read_file(self):
        # arrange
        testfile = testfileprefix+"test_write_read_file.txt"
        try:
            expected = ["a", "bö", "testß\\testend"]

            # act
            write_lines_to_file(testfile, expected)
            actual = read_lines_from_file(testfile)

            # assert
            assert expected == actual
        finally:
            os.remove(testfile)


class SCOrganizeLinesInFileTests(unittest.TestCase):

    def test_SCOrganizeLinesInFile_test_basic(self):
        # arrange
        testfile = testfileprefix+"test_SCOrganizeLinesInFile_test_basic.txt"
        try:
            input = ["line1", "line2", "line3"]
            expected_output = ["line1", "line2", "line3"]
            write_lines_to_file(testfile, input)

            # act
            SCOrganizeLinesInFile(testfile, encoding, True, True, True, True)  # sort,remove_duplicated_lines,ignore_first_line,remove_empty_lines

            # assert
            assert expected_output == read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_SCOrganizeLinesInFile_test_emptylineandignorefirstline(self):
        # arrange
        testfile = testfileprefix+"test_SCOrganizeLinesInFile_test_emptylineandignorefirstline.txt"
        try:
            input = ["line1", "", "line3"]
            expected_output = ["line1", "line3"]
            write_lines_to_file(testfile, input)

            # act
            SCOrganizeLinesInFile(testfile, encoding, True, True, True, True)  # sort,remove_duplicated_lines,ignore_first_line,remove_empty_lines

            # assert
            assert expected_output == read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_SCOrganizeLinesInFile_test_emptyline(self):
        # arrange
        testfile = testfileprefix+"test_SCOrganizeLinesInFile_test_emptyline.txt"
        try:
            input = ["line1", "", "line3"]
            expected_output = ["line1", "line3"]
            write_lines_to_file(testfile, input)

            # act
            SCOrganizeLinesInFile(testfile, encoding, True, True, False, True)  # sort,remove_duplicated_lines,ignore_first_line,remove_empty_lines

            # assert
            assert expected_output == read_lines_from_file(testfile)
        finally:
            os.remove(testfile)
