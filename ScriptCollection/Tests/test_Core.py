import os
import unittest
from pathlib import Path
import tempfile
import re
import uuid
from ..Utilities import GeneralUtilities
from ..Core import ScriptCollectionCore


class ScriptCollectionCoreTests(unittest.TestCase):

    encoding = "utf-8"
    testfileprefix = "testfile_"

    def test_dummy(self)->None:
        sc=ScriptCollectionCore()
        sc.register_mock_program_call("test","","",0,"","",0,0)
        GeneralUtilities.string_is_none_or_whitespace("")
        assert True is True

    def test_generate_thumbnail(self) -> None:
        # arrange
        fd, temporary_file = tempfile.mkstemp()
        sc = ScriptCollectionCore()
        try:
            folder = os.path.dirname(temporary_file)
            filename = os.path.basename(temporary_file)
            sc.mock_program_calls = True
            video_length_as_string = "42.123"
            info = "00:00:42"
            tempname_for_thumbnails = "t_helperfile"
            sc.register_mock_program_call("ffprobe",
                                          re.escape(f'-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filename}"'),
                                          re.escape(folder), 0, video_length_as_string, "", 40)  # Mock calculating length of video file which should
            # be video_length_as_string seconds in this case and exits without errors (exitcode 0)

            sc.register_mock_program_call("ffmpeg",
                                          re.escape(f'-i "{filename}" -r 0.38 -vf scale=-1:120 -vcodec png {tempname_for_thumbnails}-%002d.png'),
                                          re.escape(folder), 0, video_length_as_string, "", 40)  # Mock generating single the thumbnail-files

            sc.register_mock_program_call("montage",
                                          re.escape(f'-title "{filename} ({info})" -geometry +4+4 {tempname_for_thumbnails}*.png "{filename}.png"'),
                                          re.escape(folder), 0, video_length_as_string, "", 40)  # Mock generating the entire result-thumbnail-file

            # act
            sc.generate_thumbnail(temporary_file, "16", tempname_for_thumbnails)

            # assert
            sc.verify_no_pending_mock_program_calls()
        finally:
            os.close(fd)
            os.remove(temporary_file)

    def test_generate_thumbnail_fps(self) -> None:
        # arrange
        fd, temporary_file = tempfile.mkstemp()
        sc = ScriptCollectionCore()
        try:
            folder = os.path.dirname(temporary_file)
            filename = os.path.basename(temporary_file)
            sc.mock_program_calls = True
            video_length_as_string = "70.123"
            info = "00:01:10"
            tempname_for_thumbnails = "t_helperfile"
            sc.register_mock_program_call("ffprobe",
                                          re.escape(f'-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filename}"'),
                                          re.escape(folder), 0, video_length_as_string, "", 40)  # Mock calculating length of video file which should
            # be video_length_as_string seconds in this case and exits without errors (exitcode 0)

            sc.register_mock_program_call("ffmpeg",
                                          re.escape(f'-i "{filename}" -r 0.33 -vf scale=-1:120 -vcodec png {tempname_for_thumbnails}-%002d.png'),
                                          re.escape(folder), 0, video_length_as_string, "", 40)  # Mock generating single the thumbnail-files

            sc.register_mock_program_call("montage",
                                          re.escape(f'-title "{filename} ({info})" -geometry +5+5 {tempname_for_thumbnails}*.png "{filename}.png"'),
                                          re.escape(folder), 0, video_length_as_string, "", 40)  # Mock generating the entire result-thumbnail-file

            # act
            sc.generate_thumbnail(temporary_file, "0.3333fps", tempname_for_thumbnails)

            # assert
            sc.verify_no_pending_mock_program_calls()
        finally:
            os.close(fd)
            os.remove(temporary_file)

    def test_to_list_none(self):
        # arrange
        testinput = None
        expected = []

        # act
        actual = GeneralUtilities.to_list(testinput, ",")

        # assert
        assert expected == actual

    def test_to_list_empty(self):
        # arrange
        testinput = "   "
        expected = []

        # act
        actual = GeneralUtilities.to_list(testinput, ",")

        # assert
        assert expected == actual

    def test_to_list_one_item(self):
        # arrange
        testinput = " a "
        expected = ["a"]

        # act
        actual = GeneralUtilities.to_list(testinput, ",")

        # assert
        assert expected == actual

    def test_to_list_multiple_items(self):
        # arrange
        testinput = " a , b , c "
        expected = ["a", "b", "c"]

        # act
        actual = GeneralUtilities.to_list(testinput, ",")

        # assert
        assert expected == actual

    def test_get_advanced_errormessage_for_os_error_FileNotFoundError(self):
        # arrange
        filename = "somefile.txt"
        exception = FileNotFoundError()
        exception.filename = filename
        assert isinstance(exception, OSError)
        expected = f"Related path(s): {filename}"

        # act
        actual = GeneralUtilities.get_advanced_errormessage_for_os_error(exception)

        # assert
        assert expected == actual

    def test_get_advanced_errormessage_for_os_error_NotADirectoryError(self):
        # arrange
        filename = "somedirectory"
        exception = NotADirectoryError()
        exception.filename = filename
        assert isinstance(exception, OSError)
        expected = f"Related path(s): {filename}"

        # act
        actual = GeneralUtilities.get_advanced_errormessage_for_os_error(exception)

        # assert
        assert expected == actual


    def test_sc_organize_lines_in_file_test_basic(self) -> None:
        # arrange
        testfile = ScriptCollectionCoreTests.testfileprefix+"test_sc_organize_lines_in_file_test_basic.txt"
        try:
            example_input = ["line1", "line2", "line3"]
            expected_output = ["line1", "line2", "line3"]
            GeneralUtilities.write_lines_to_file(testfile, example_input)

            # act
            ScriptCollectionCore().sc_organize_lines_in_file(testfile, ScriptCollectionCoreTests.encoding, True, True, True, True)
            # arguments: sort ,remove_duplicated_lines, ignore_first_line, remove_empty_lines, ignored_character

            # assert
            assert expected_output == GeneralUtilities.read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_sc_organize_lines_in_file_test_emptylineandignorefirstline(self) -> None:
        # arrange
        testfile = ScriptCollectionCoreTests.testfileprefix+"test_sc_organize_lines_in_file_test_emptylineandignorefirstline.txt"
        try:
            example_input = ["line1", "", "line3"]
            expected_output = ["line1", "line3"]
            GeneralUtilities.write_lines_to_file(testfile, example_input)

            # act
            ScriptCollectionCore().sc_organize_lines_in_file(testfile,ScriptCollectionCoreTests. encoding, True, True, True, True)
            # arguments: sort ,remove_duplicated_lines, ignore_first_line, remove_empty_lines, ignored_character

            # assert
            assert expected_output == GeneralUtilities.read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_sc_organize_lines_in_file_test_emptyline(self) -> None:
        # arrange
        testfile =ScriptCollectionCoreTests.testfileprefix+"test_sc_organize_lines_in_file_test_emptyline.txt"
        try:
            example_input = ["line1", "", "line3"]
            expected_output = ["line1", "line3"]
            GeneralUtilities.write_lines_to_file(testfile, example_input)

            # act
            ScriptCollectionCore().sc_organize_lines_in_file(testfile, ScriptCollectionCoreTests.encoding, True, True, False, True, [])
            # arguments: sort ,remove_duplicated_lines, ignore_first_line, remove_empty_lines, ignored_character

            # assert
            assert expected_output ==GeneralUtilities. read_lines_from_file(testfile)
        finally:
            os.remove(testfile)

    def test_sc_organize_lines_in_file_with_ignored_character(self) -> None:
        # arrange
        testfile = ScriptCollectionCoreTests.testfileprefix+"test_sc_organize_lines_in_file_test_emptyline.txt"
        try:
            example_input = ["line5", " line4", "line3", "#line2", "# line6", "line7", "line1"]
            expected_output = ["line1", "#line2", "line3", " line4", "line5", "# line6", "line7"]
            GeneralUtilities.write_lines_to_file(testfile, example_input)

            # act
            ScriptCollectionCore().sc_organize_lines_in_file(testfile,  ScriptCollectionCoreTests.encoding, True, True, False, True, ["#", " "])
            # arguments: sort ,remove_duplicated_lines, ignore_first_line, remove_empty_lines, ignored_character

            # assert
            assert expected_output == GeneralUtilities.read_lines_from_file(testfile)
        finally:
            os.remove(testfile)


    def test_simple_program_call_is_mockable(self) -> None:
        # arrange
        sc = ScriptCollectionCore()
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

    def test_simple_program_call_prevent(self) -> None:
        # arrange
        sc = ScriptCollectionCore()
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # act
        (exit_code, _, _2, _3) = sc.start_program_synchronously("git", "status", dir_path, throw_exception_if_exitcode_is_not_zero=False, verbosity=3, prevent_using_epew=True)

        # assert
        assert exit_code == 0

    def test_file_is_git_ignored_1(self) -> None:
        # arrange
        sc = ScriptCollectionCore()
        repository = str(Path(__file__).parent.parent.absolute())

        # act
        result = sc.file_is_git_ignored("Tests/tests.py", repository)

        # assert
        assert result is False

    def test_file_is_git_ignored_2(self) -> None:
        tests_folder = tempfile.gettempdir()+os.path.sep+str(uuid.uuid4())
        GeneralUtilities.ensure_directory_exists(tests_folder)
        sc = ScriptCollectionCore()
        sc.start_program_synchronously("git", "init", tests_folder)

        ignored_logfolder_name = "logfolder"
        ignored_logfolder = tests_folder+os.path.sep+ignored_logfolder_name
        GeneralUtilities.ensure_directory_exists(ignored_logfolder)

        gitignore_file = tests_folder+os.path.sep+".gitignore"
        GeneralUtilities.ensure_file_exists(gitignore_file)
        GeneralUtilities.write_lines_to_file(gitignore_file, [ignored_logfolder_name+"/**", "!"+ignored_logfolder_name+"/.gitkeep"])

        gitkeep_file = ignored_logfolder+os.path.sep+".gitkeep"
        GeneralUtilities.ensure_file_exists(gitkeep_file)

        log_file = ignored_logfolder+os.path.sep+"logfile.log"
        GeneralUtilities.ensure_file_exists(log_file)

        assert not sc.file_is_git_ignored(".gitignore", tests_folder)
        assert not sc.file_is_git_ignored(".gitkeep", tests_folder)
        assert sc.file_is_git_ignored(ignored_logfolder_name+os.path.sep+"logfile.log", tests_folder)

        GeneralUtilities.ensure_directory_does_not_exist(tests_folder)

    def test_simple_program_call_prevent_argsasarray(self) -> None:
        # arrange
        sc = ScriptCollectionCore()
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # act
        (exit_code, _, _2, _3) = sc.start_program_synchronously_argsasarray("git", ["status"],
                                                                            dir_path, throw_exception_if_exitcode_is_not_zero=False, verbosity=3, prevent_using_epew=True)

        # assert
        assert exit_code == 0

    def test_simple_program_call_prevent_argsasarray_wiith_folder(self) -> None:
        try:
            # arrange
            sc = ScriptCollectionCore()
            dir_path = os.path.dirname(os.path.realpath(__file__))
            tests_folder = tempfile.gettempdir()+os.path.sep+str(uuid.uuid4())
            GeneralUtilities.ensure_directory_exists(tests_folder)

            # act
            (exit_code, _, _2, _3) = sc.start_program_synchronously("ls", f"-ld {tests_folder}",
                                                                    dir_path, throw_exception_if_exitcode_is_not_zero=False, verbosity=3, prevent_using_epew=True)

            # assert
            assert exit_code == 0
        finally:
            GeneralUtilities.ensure_directory_does_not_exist(tests_folder)

    def test_export_filemetadata(self) -> None:
        # arrange
        try:
            sc = ScriptCollectionCore()
            tests_folder = tempfile.gettempdir()+os.path.sep+str(uuid.uuid4())
            GeneralUtilities.ensure_directory_exists(tests_folder)
            target_file = os.path.join(tests_folder, "test.csv")
            assert not os.path.isfile(target_file)
            dir_path = os.path.dirname(os.path.realpath(__file__))
            folder_for_export = GeneralUtilities.resolve_relative_path("..", dir_path)

            # act
            sc.export_filemetadata(folder_for_export, target_file)

            # assert
            assert os.path.isfile(target_file)
            # TODO add more assertions
        finally:
            GeneralUtilities.ensure_file_does_not_exist(target_file)

# TODO all testcases should be independent of epew
