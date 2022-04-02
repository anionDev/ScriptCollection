import os
import unittest
from ..Utilities import GeneralUtilities


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
