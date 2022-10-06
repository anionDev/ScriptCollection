import os
from datetime import datetime
import unittest
from ..ScriptCollection.GeneralUtilities import GeneralUtilities


class GeneralUtilitiesTests(unittest.TestCase):
    testfileprefix = "testfile_"

    def test_string_to_lines(self) -> None:
        # arrange
        test_string = "a\r\nb\n"
        expected = ["a", "b", ""]

        # act
        actual = GeneralUtilities.string_to_lines(test_string)

        # assert
        assert actual == expected

    def test_datetime_to_string_to_datetime(self) -> None:
        # arrange
        expected = datetime(2022, 10, 6, 19, 26, 1)

        # act
        actual = GeneralUtilities.string_to_datetime(GeneralUtilities.datetime_to_string(expected))

        # assert
        assert actual == expected

    def test_string_to_datetime_to_string(self) -> None:
        # arrange
        expected = "2022-10-06T19:26:01"

        # act
        actual = GeneralUtilities.datetime_to_string(GeneralUtilities.string_to_datetime(expected))

        # assert
        assert actual == expected

    def test_datetime_to_string(self) -> None:
        # arrange
        expected = "2022-10-06T19:26:01"
        test_input = datetime(2022, 10, 6, 19, 26, 1)

        # act
        actual = GeneralUtilities.datetime_to_string(test_input)

        # assert
        assert actual == expected

    def test_string_to_datetime(self) -> None:
        # arrange
        expected = datetime(2022, 10, 6, 19, 26, 1)
        test_input = "2022-10-06T19:26:01"

        # act
        actual = GeneralUtilities.string_to_datetime(test_input)

        # assert
        assert actual == expected

    def test_string_is_none_or_whitespace(self) -> None:
        assert GeneralUtilities.string_is_none_or_whitespace(None)
        assert GeneralUtilities.string_is_none_or_whitespace("")
        assert GeneralUtilities.string_is_none_or_whitespace(" ")
        assert GeneralUtilities.string_is_none_or_whitespace("   ")
        assert not GeneralUtilities.string_is_none_or_whitespace("not empty string")

    def test_string_is_none_or_empty(self) -> None:
        assert GeneralUtilities.string_is_none_or_empty(None)
        assert GeneralUtilities.string_is_none_or_empty("")
        assert not GeneralUtilities.string_is_none_or_empty(" ")
        assert not GeneralUtilities.string_is_none_or_empty("   ")
        assert not GeneralUtilities.string_is_none_or_empty("not empty string")

    def test_write_read_file(self) -> None:
        # arrange
        testfile = GeneralUtilitiesTests.testfileprefix+"test_write_read_file.txt"
        try:
            expected = ["a", "bö", "testß\\testend"]

            # act
            GeneralUtilities.write_lines_to_file(testfile, expected)
            actual = GeneralUtilities.read_lines_from_file(testfile)

            # assert
            assert expected == actual
        finally:
            os.remove(testfile)

    def test_get_next_square_number_0(self) -> None:
        assert GeneralUtilities.get_next_square_number(0) == 1

    def test_get_next_square_number_1(self) -> None:
        assert GeneralUtilities.get_next_square_number(1) == 1

    def test_get_next_square_number_2(self) -> None:
        assert GeneralUtilities.get_next_square_number(2) == 4

    def test_get_next_square_number_3(self) -> None:
        assert GeneralUtilities.get_next_square_number(3) == 4

    def test_get_next_square_number_15(self) -> None:
        assert GeneralUtilities.get_next_square_number(15) == 16

    def test_get_next_square_number_16(self) -> None:
        assert GeneralUtilities.get_next_square_number(16) == 16

    def test_get_next_square_number_17(self) -> None:
        assert GeneralUtilities.get_next_square_number(17) == 25

    def test_internal_ends_with_newline_character_empty_string(self) -> None:
        # pylint: disable=W0212
        assert GeneralUtilities._ends_with_newline_character("".encode()) is False

    def test_internal_ends_with_newline_character_nonempty_string_true(self) -> None:
        # pylint: disable=W0212
        assert GeneralUtilities._ends_with_newline_character("a\n".encode()) is True

    def test_internal_ends_with_newline_character_nonempty_string_false(self) -> None:
        # pylint: disable=W0212
        assert GeneralUtilities._ends_with_newline_character("ab".encode()) is False
