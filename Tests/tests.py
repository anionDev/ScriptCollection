import os
import unittest
from ScriptCollection.core import get_ScriptCollection_version, string_is_none_or_whitespace, string_is_none_or_empty, write_lines_to_file, read_lines_from_file, ScriptCollection

testfileprefix = "testfile_"
encoding = "utf-8"
version = "2.0.3"


class MiscellaneousTests(unittest.TestCase):

    def test_version(self)->None:
        assert version == get_ScriptCollection_version()

    def test_string_is_none_or_whitespace(self)->None:
        assert string_is_none_or_whitespace(None)
        assert string_is_none_or_whitespace("")
        assert string_is_none_or_whitespace(" ")
        assert string_is_none_or_whitespace("   ")
        assert not string_is_none_or_whitespace("not empty string")

    def test_string_is_none_or_empty(self)->None:
        assert string_is_none_or_empty(None)
        assert string_is_none_or_empty("")
        assert not string_is_none_or_empty(" ")
        assert not string_is_none_or_empty("   ")
        assert not string_is_none_or_empty("not empty string")

    def test_write_read_file(self)->None:
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


class OrganizeLinesInFileTests(unittest.TestCase):

    def test_sc_organize_lines_in_file_test_basic(self)->None:
        # arrange
        testfile = testfileprefix+"test_sc_organize_lines_in_file_test_basic.txt"
        try:
            example_input = ["line1", "line2", "line3"]
            expected_output = ["line1", "line2", "line3"]
            write_lines_to_file(testfile, example_input)

            # act
            ScriptCollection().sc_organize_lines_in_file(testfile, encoding, True, True, True, True)  # sort,remove_duplicated_lines,ignore_first_line,remove_empty_lines

            # assert
            assert expected_output == read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_sc_organize_lines_in_file_test_emptylineandignorefirstline(self)->None:
        # arrange
        testfile = testfileprefix+"test_sc_organize_lines_in_file_test_emptylineandignorefirstline.txt"
        try:
            example_input = ["line1", "", "line3"]
            expected_output = ["line1", "line3"]
            write_lines_to_file(testfile, example_input)

            # act
            ScriptCollection().sc_organize_lines_in_file(testfile, encoding, True, True, True, True)  # sort,remove_duplicated_lines,ignore_first_line,remove_empty_lines

            # assert
            assert expected_output == read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_sc_organize_lines_in_file_test_emptyline(self)->None:
        # arrange
        testfile = testfileprefix+"test_sc_organize_lines_in_file_test_emptyline.txt"
        try:
            example_input = ["line1", "", "line3"]
            expected_output = ["line1", "line3"]
            write_lines_to_file(testfile, example_input)

            # act
            ScriptCollection().sc_organize_lines_in_file(testfile, encoding, True, True, False, True)  # sort,remove_duplicated_lines,ignore_first_line,remove_empty_lines

            # assert
            assert expected_output == read_lines_from_file(testfile)
        finally:
            os.remove(testfile)


class ExecuteProgramTests(unittest.TestCase):

    def test_simple_program_call_is_mockable(self)->None:
        # arrange
        sc = ScriptCollection()
        sc.mock_program_calls = True
        sc.register_mock_program_call("p", "a1", "/tmp", 0, "out 1", "err 1", 40)
        sc.register_mock_program_call("p", "a2", "/tmp", 0, "out 2", "err 2", 44)

        # act
        result1 = sc.start_program_synchronously("p", "a1", "/tmp", 3600, 1, False, None, False, None, True, True)
        result2 = sc.start_program_synchronously("p", "a2", "/tmp", 3600, 1, False, None, False, None, True, False)

        # assert
        assert result1 == (0, "out 1", "err 1", 40)
        assert result2 == (0, "out 2", "err 2", 44)
        sc.verify_no_pending_mock_program_calls()
