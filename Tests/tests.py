import os
import unittest
import tempfile
import re
from ScriptCollection.core import get_ScriptCollection_version, string_is_none_or_whitespace, string_is_none_or_empty, write_lines_to_file, read_lines_from_file, ScriptCollection, to_list

testfileprefix = "testfile_"
encoding = "utf-8"
version = "2.0.34"


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

    def test_generate_thumbnail(self)->None:
        # arrange
        fd, temporary_file  = tempfile.mkstemp()
        sc=ScriptCollection()
        try:
            folder=os.path.dirname(temporary_file)
            filename=os.path.basename(temporary_file)
            sc.mock_program_calls = True
            video_length_as_string="42.123"
            info="00:00:42"
            r_as_string=str(float(video_length_as_string)/(16-2))
            tempname_for_thumbnails="t_helperfile"
            sc.register_mock_program_call("ffprobe", re.escape(f'-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filename}"'),re.escape(folder), 0, video_length_as_string, "", 40) # Mock calculating length of video file which should be video_length_as_string seconds in this case and exits without errors (exitcode 0)
            sc.register_mock_program_call("ffmpeg", re.escape(f'-i "{filename}" -r 1/{r_as_string} -vf scale=-1:120 -vcodec png {tempname_for_thumbnails}-%002d.png'),re.escape(folder), 0, "42.123", "", 40) # Mock generating single the thumbnail-files
            sc.register_mock_program_call("montage", re.escape(f'-title "{filename} ({info})" -geometry +4+4 {tempname_for_thumbnails}*.png "{filename}.png"'),re.escape(folder), 0, "42.123", "", 40) # Mock generating the entire result-thumbnail-file

            # act
            sc.generate_thumbnail(temporary_file,tempname_for_thumbnails)

            # assert
            sc.verify_no_pending_mock_program_calls()
        finally:
            os.close(fd)
            os.remove(temporary_file)

    def test_to_list_none(self):
        # arrange
        input=None
        expected=[]

        # act
        actual=to_list(input,",")

        # assert
        assert expected==actual

    def test_to_list_empty(self):
        # arrange
        input="   "
        expected=[]

        # act
        actual=to_list(input,",")

        # assert
        assert expected==actual

    def test_to_list_one_item(self):
        # arrange
        input=" a "
        expected=["a"]

        # act
        actual=to_list(input,",")

        # assert
        assert expected==actual

    def test_to_list_multiple_items(self):
        # arrange
        input=" a , b , c "
        expected=["a","b","c"]

        # act
        actual=to_list(input,",")

        # assert
        assert expected==actual

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
