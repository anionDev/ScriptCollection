from ScriptCollection.core import *
import pytest
import os

testfileprefix = "testfile_"
encoding = "utf-8"

# <miscellaneous>


def test_string_is_none_or_whitespace():
    assert string_is_none_or_whitespace(None)
    assert string_is_none_or_whitespace("")
    assert string_is_none_or_whitespace(" ")
    assert string_is_none_or_whitespace("   ")
    assert not string_is_none_or_whitespace("not empty string")


def test_string_is_none_or_empty():
    assert string_is_none_or_empty(None)
    assert string_is_none_or_empty("")
    assert not string_is_none_or_empty(" ")
    assert not string_is_none_or_empty("   ")
    assert not string_is_none_or_empty("not empty string")


def test_write_read_file():
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

# </miscellaneous>

# <SCOrganizeLinesInFile>


def test_SCOrganizeLinesInFile_test_basic():
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


def test_SCOrganizeLinesInFile_test_emptylineandignorefirstline():
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


def test_SCOrganizeLinesInFile_test_emptyline():
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

# </SCOrganizeLinesInFile>
