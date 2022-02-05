import codecs
import ctypes
import hashlib
import re
import os
import shutil
import stat
import sys
import traceback
from datetime import datetime
from os import listdir
from os.path import isfile, join, isdir
from pathlib import Path
from shutil import copyfile
from defusedxml.minidom import parse


class GeneralUtilities:

    @staticmethod
    def string_to_lines(string: str, add_empty_lines: bool = True, adapt_lines: bool = True) -> list[str]:
        result = list()
        if(string is not None):
            lines = list()
            if("\n" in string):
                lines = string.splitlines()
            else:
                lines.append(string)
        for rawline in lines:
            if adapt_lines:
                line = rawline.replace("\r", "\n").strip()
            else:
                line = rawline
            if GeneralUtilities.string_is_none_or_whitespace(line):
                if add_empty_lines:
                    result.append(line)
            else:
                result.append(line)
        return result

    @staticmethod
    def move_content_of_folder(srcDir, dstDir, overwrite_existing_files=False) -> None:
        srcDirFull = GeneralUtilities.resolve_relative_path_from_current_working_directory(srcDir)
        dstDirFull = GeneralUtilities.resolve_relative_path_from_current_working_directory(dstDir)
        if(os.path.isdir(srcDir)):
            GeneralUtilities.ensure_directory_exists(dstDir)
            for file in GeneralUtilities.get_direct_files_of_folder(srcDirFull):
                filename = os.path.basename(file)
                targetfile = os.path.join(dstDirFull, filename)
                if(os.path.isfile(targetfile)):
                    if overwrite_existing_files:
                        GeneralUtilities.ensure_file_does_not_exist(targetfile)
                    else:
                        raise ValueError(f"Targetfile {targetfile} does already exist")
                shutil.move(file, dstDirFull)
            for sub_folder in GeneralUtilities.get_direct_folders_of_folder(srcDirFull):
                foldername = os.path.basename(sub_folder)
                sub_target = os.path.join(dstDirFull, foldername)
                GeneralUtilities.move_content_of_folder(sub_folder, sub_target)
                GeneralUtilities.ensure_directory_does_not_exist(sub_folder)
        else:
            raise ValueError(f"Folder '{srcDir}' does not exist")

    @staticmethod
    def replace_regex_each_line_of_file(file: str, replace_from_regex: str, replace_to_regex: str, encoding="utf-8", verbose: bool = False) -> None:
        """This function iterates over each line in the file and replaces it by the line which applied regex.
        Note: The lines will be taken from open(...).readlines(). So the lines may contain '\\n' or '\\r\\n' for example."""
        if verbose:
            GeneralUtilities.write_message_to_stdout(f"Replace '{replace_from_regex}' to '{replace_to_regex}' in '{file}'")
        with open(file, encoding=encoding, mode="r") as f:
            lines = f.readlines()
            replaced_lines = []
            for line in lines:
                replaced_line = re.sub(replace_from_regex, replace_to_regex, line)
                replaced_lines.append(replaced_line)
        with open(file, encoding=encoding, mode="w") as f:
            f.writelines(replaced_lines)

    @staticmethod
    def replace_regex_in_file(file: str, replace_from_regex: str, replace_to_regex: str, encoding="utf-8") -> None:
        with open(file, encoding=encoding, mode="r") as f:
            content = f.read()
            content = re.sub(replace_from_regex, replace_to_regex, content)
        with open(file, encoding=encoding, mode="w") as f:
            f.write(content)

    @staticmethod
    def replace_xmltag_in_file(file: str, tag: str, new_value: str, encoding="utf-8") -> None:
        GeneralUtilities.replace_regex_in_file(file, f"<{tag}>.*</{tag}>", f"<{tag}>{new_value}</{tag}>", encoding)

    @staticmethod
    def update_version_in_csproj_file(file: str, target_version: str) -> None:
        GeneralUtilities.replace_xmltag_in_file(file, "Version", target_version)
        GeneralUtilities.replace_xmltag_in_file(file, "AssemblyVersion", target_version + ".0")
        GeneralUtilities.replace_xmltag_in_file(file, "FileVersion", target_version + ".0")

    @staticmethod
    def replace_underscores_in_text(text: str, replacements: dict) -> str:
        changed = True
        while changed:
            changed = False
            for key, value in replacements.items():
                previousValue = text
                text = text.replace(f"__{key}__", value)
                if(not text == previousValue):
                    changed = True
        return text

    @staticmethod
    def replace_underscores_in_file(file: str, replacements: dict, encoding: str = "utf-8"):
        text = GeneralUtilities.read_text_from_file(file, encoding)
        text = GeneralUtilities.replace_underscores_in_text(text, replacements)
        GeneralUtilities.write_text_to_file(file, text, encoding)

    @staticmethod
    def write_message_to_stdout(message: str):
        sys.stdout.write(GeneralUtilities.str_none_safe(message)+"\n")
        sys.stdout.flush()

    @staticmethod
    def write_message_to_stderr(message: str):
        sys.stderr.write(GeneralUtilities.str_none_safe(message)+"\n")
        sys.stderr.flush()

    @staticmethod
    def get_advanced_errormessage_for_os_error(os_error: OSError) -> str:
        if GeneralUtilities.string_has_content(os_error.filename2):
            secondpath = f" {os_error.filename2}"
        else:
            secondpath = ""
        return f"Related path(s): {os_error.filename}{secondpath}"

    @staticmethod
    def write_exception_to_stderr(exception: Exception, extra_message: str = None):
        GeneralUtilities.write_exception_to_stderr_with_traceback(exception, None, extra_message)

    @staticmethod
    def write_exception_to_stderr_with_traceback(exception: Exception, current_traceback=None, extra_message: str = None):
        GeneralUtilities.write_message_to_stderr("Exception(")
        GeneralUtilities.write_message_to_stderr("Type: "+str(type(exception)))
        GeneralUtilities.write_message_to_stderr("Message: "+str(exception))
        if str is not None:
            GeneralUtilities.write_message_to_stderr("Extra-message: "+str(extra_message))
        if isinstance(exception, OSError):
            GeneralUtilities.write_message_to_stderr(GeneralUtilities.get_advanced_errormessage_for_os_error(exception))
        if current_traceback is not None:
            GeneralUtilities.write_message_to_stderr("Traceback: "+current_traceback.format_exc())
        GeneralUtilities.write_message_to_stderr(")")

    @staticmethod
    def string_has_content(string: str) -> bool:
        if string is None:
            return False
        else:
            return len(string) > 0

    @staticmethod
    def datetime_to_string_for_logfile_name(datetime_object: datetime) -> str:
        return datetime_object.strftime('%Y-%m-%d_%H-%M-%S')

    @staticmethod
    def datetime_to_string_for_logfile_entry(datetime_object: datetime) -> str:
        return datetime_object.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def string_has_nonwhitespace_content(string: str) -> bool:
        if string is None:
            return False
        else:
            return len(string.strip()) > 0

    @staticmethod
    def string_is_none_or_empty(argument: str) -> bool:
        if argument is None:
            return True
        type_of_argument = type(argument)
        if type_of_argument == str:
            return argument == ""
        else:
            raise Exception(f"expected string-variable in argument of string_is_none_or_empty but the type was '{str(type_of_argument)}'")

    @staticmethod
    def string_is_none_or_whitespace(string: str) -> bool:
        if GeneralUtilities.string_is_none_or_empty(string):
            return True
        else:
            return string.strip() == ""

    @staticmethod
    def strip_new_line_character(value: str) -> str:
        return value.strip().strip('\n').strip('\r').strip()

    @staticmethod
    def append_line_to_file(file: str, line: str, encoding: str = "utf-8") -> None:
        if not GeneralUtilities.file_is_empty(file):
            line = os.linesep+line
        GeneralUtilities.append_to_file(file, line, encoding)

    @staticmethod
    def append_to_file(file: str, content: str, encoding: str = "utf-8") -> None:
        with open(file, "a", encoding=encoding) as fileObject:
            fileObject.write(content)

    @staticmethod
    def ensure_directory_exists(path: str) -> None:
        if not os.path.isdir(path):
            os.makedirs(path)

    @staticmethod
    def ensure_file_exists(path: str) -> None:
        if(not os.path.isfile(path)):
            with open(path, "a+", encoding="utf-8"):
                pass

    @staticmethod
    def __remove_readonly(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    @staticmethod
    def rmtree(directory:str)->None:
        shutil.rmtree(directory, onerror=GeneralUtilities.__remove_readonly)

    @staticmethod
    def ensure_directory_does_not_exist(path: str) -> None:
        if(os.path.isdir(path)):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    os.chmod(filename, stat.S_IWUSR)
                    os.remove(filename)
                for name in dirs:
                    GeneralUtilities.rmtree(os.path.join(root, name))
            GeneralUtilities.rmtree(path)

    @staticmethod
    def ensure_file_does_not_exist(path: str) -> None:
        if(os.path.isfile(path)):
            os.remove(path)

    @staticmethod
    def format_xml_file(filepath: str) -> None:
        GeneralUtilities.format_xml_file_with_encoding(filepath, "utf-8")

    @staticmethod
    def format_xml_file_with_encoding(filepath: str, encoding: str) -> None:
        with codecs.open(filepath, 'r', encoding=encoding) as file:
            text = file.read()
        text = parse(text).toprettyxml()
        with codecs.open(filepath, 'w', encoding=encoding) as file:
            file.write(text)

    @staticmethod
    def get_clusters_and_sectors_of_disk(diskpath: str) -> None:
        sectorsPerCluster = ctypes.c_ulonglong(0)
        bytesPerSector = ctypes.c_ulonglong(0)
        rootPathName = ctypes.c_wchar_p(diskpath)
        ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName, ctypes.pointer(sectorsPerCluster), ctypes.pointer(bytesPerSector), None, None)
        return (sectorsPerCluster.value, bytesPerSector.value)

    @staticmethod
    def ensure_path_is_not_quoted(path: str) -> str:
        if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
            path = path[1:]
            path = path[:-1]
            return path
        else:
            return path

    @staticmethod
    def get_missing_files(folderA: str, folderB: str) -> list:
        folderA_length = len(folderA)
        result = []
        for fileA in GeneralUtilities.absolute_file_paths(folderA):
            file = fileA[folderA_length:]
            fileB = folderB+file
            if not os.path.isfile(fileB):
                result.append(fileB)
        return result

    @staticmethod
    def write_lines_to_file(file: str, lines: list, encoding="utf-8") -> None:
        GeneralUtilities.write_text_to_file(file, os.linesep.join(lines), encoding)

    @staticmethod
    def write_text_to_file(file: str, content: str, encoding="utf-8") -> None:
        GeneralUtilities.write_binary_to_file(file, bytearray(content, encoding))

    @staticmethod
    def write_binary_to_file(file: str, content: bytearray) -> None:
        with open(file, "wb") as file_object:
            file_object.write(content)

    @staticmethod
    def read_lines_from_file(file: str, encoding="utf-8") -> list[str]:
        return GeneralUtilities.read_text_from_file(file, encoding).split(os.linesep)

    @staticmethod
    def read_text_from_file(file: str, encoding="utf-8") -> str:
        return GeneralUtilities.bytes_to_string(GeneralUtilities.read_binary_from_file(file), encoding)

    @staticmethod
    def read_binary_from_file(file: str) -> bytes:
        with open(file, "rb") as file_object:
            return file_object.read()

    @staticmethod
    def timedelta_to_simple_string(delta) -> str:
        return (datetime(1970, 1, 1, 0, 0, 0) + delta).strftime('%H:%M:%S')

    @staticmethod
    def resolve_relative_path_from_current_working_directory(path: str) -> str:
        return GeneralUtilities.resolve_relative_path(path, os.getcwd())

    @staticmethod
    def resolve_relative_path(path: str, base_path: str):
        if(os.path.isabs(path)):
            return path
        else:
            return str(Path(os.path.join(base_path, path)).resolve())

    @staticmethod
    def get_metadata_for_file_for_clone_folder_structure(file: str) -> str:
        size = os.path.getsize(file)
        last_modified_timestamp = os.path.getmtime(file)
        hash_value = GeneralUtilities.get_sha256_of_file(file)
        last_access_timestamp = os.path.getatime(file)
        return f'{{"size":"{size}","sha256":"{hash_value}","mtime":"{last_modified_timestamp}","atime":"{last_access_timestamp}"}}'

    @staticmethod
    def clone_folder_structure(source: str, target: str, copy_only_metadata: bool):
        source = GeneralUtilities.resolve_relative_path(source, os.getcwd())
        target = GeneralUtilities.resolve_relative_path(target, os.getcwd())
        length_of_source = len(source)
        for source_file in GeneralUtilities.absolute_file_paths(source):
            target_file = target+source_file[length_of_source:]
            GeneralUtilities.ensure_directory_exists(os.path.dirname(target_file))
            if copy_only_metadata:
                with open(target_file, 'w', encoding='utf8') as f:
                    f.write(GeneralUtilities.get_metadata_for_file_for_clone_folder_structure(source_file))
            else:
                copyfile(source_file, target_file)

    @staticmethod
    def current_user_has_elevated_privileges() -> bool:
        try:
            return os.getuid() == 0
        except AttributeError:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1

    @staticmethod
    def rename_names_of_all_files_and_folders(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
        for file in GeneralUtilities.get_direct_files_of_folder(folder):
            GeneralUtilities.replace_in_filename(file, replace_from, replace_to, replace_only_full_match)
        for sub_folder in GeneralUtilities.get_direct_folders_of_folder(folder):
            GeneralUtilities.rename_names_of_all_files_and_folders(sub_folder, replace_from, replace_to, replace_only_full_match)
        GeneralUtilities.replace_in_foldername(folder, replace_from, replace_to, replace_only_full_match)

    @staticmethod
    def get_direct_files_of_folder(folder: str) -> list[str]:
        result = [os.path.join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]
        return result

    @staticmethod
    def get_direct_folders_of_folder(folder: str) -> list[str]:
        result = [os.path.join(folder, f) for f in listdir(folder) if isdir(join(folder, f))]
        return result

    @staticmethod
    def get_all_files_of_folder(folder: str) -> list[str]:
        result = list()
        result.extend(GeneralUtilities.get_direct_files_of_folder(folder))
        for subfolder in GeneralUtilities.get_direct_folders_of_folder(folder):
            result.extend(GeneralUtilities.get_all_files_of_folder(subfolder))
        return result

    @staticmethod
    def get_all_folders_of_folder(folder: str) -> list[str]:
        result = list()
        subfolders = GeneralUtilities.get_direct_folders_of_folder(folder)
        result.extend(subfolders)
        for subfolder in subfolders:
            result.extend(GeneralUtilities.get_all_folders_of_folder(subfolder))
        return result

    @staticmethod
    def get_all_objects_of_folder(folder: str) -> list[str]:
        return GeneralUtilities.get_all_files_of_folder(folder) + GeneralUtilities.get_all_folders_of_folder(folder)

    @staticmethod
    def replace_in_filename(file: str, replace_from: str, replace_to: str, replace_only_full_match=False):
        filename = Path(file).name
        if(GeneralUtilities.__should_get_replaced(filename, replace_from, replace_only_full_match)):
            folder_of_file = os.path.dirname(file)
            os.rename(file, os.path.join(folder_of_file, filename.replace(replace_from, replace_to)))

    @staticmethod
    def replace_in_foldername(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
        foldername = Path(folder).name
        if(GeneralUtilities.__should_get_replaced(foldername, replace_from, replace_only_full_match)):
            folder_of_folder = os.path.dirname(folder)
            os.rename(folder, os.path.join(folder_of_folder, foldername.replace(replace_from, replace_to)))

    @staticmethod
    def __should_get_replaced(input_text, search_text, replace_only_full_match) -> bool:
        if replace_only_full_match:
            return input_text == search_text
        else:
            return search_text in input_text

    @staticmethod
    def str_none_safe(variable) -> str:
        if variable is None:
            return ''
        else:
            return str(variable)

    @staticmethod
    def arguments_to_array(arguments_as_string: str) -> list[str]:
        return arguments_as_string.split(" ")  # TODO this function should get improved to allow whitespaces in quote-substrings

    @staticmethod
    def get_sha256_of_file(file: str) -> str:
        sha256 = hashlib.sha256()
        with open(file, "rb") as fileObject:
            for chunk in iter(lambda: fileObject.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def remove_duplicates(input_list) -> list:
        result = []
        for item in input_list:
            if not item in result:
                result.append(item)
        return result

    @staticmethod
    def print_stacktrace() -> None:
        for line in traceback.format_stack():
            GeneralUtilities.write_message_to_stdout(line.strip())

    @staticmethod
    def string_to_boolean(value: str) -> bool:
        value = value.strip().lower()
        if value in ('yes', 'true', 't', 'y', '1'):
            return True
        elif value in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise Exception(f"Can not convert '{value}' to a boolean value")

    @staticmethod
    def file_is_empty(file: str) -> bool:
        return os.stat(file).st_size == 0

    @staticmethod
    def folder_is_empty(folder: str) -> bool:
        return len(GeneralUtilities.get_direct_files_of_folder(folder)) == 0 and len(GeneralUtilities.get_direct_folders_of_folder(folder)) == 0

    @staticmethod
    def get_time_based_logfile_by_folder(folder: str, name: str = "Log", in_utc: bool = False) -> str:
        return os.path.join(GeneralUtilities.resolve_relative_path_from_current_working_directory(folder), f"{GeneralUtilities.get_time_based_logfilename(name, in_utc)}.log")

    @staticmethod
    def get_time_based_logfilename(name: str = "Log", in_utc: bool = False) -> str:
        if(in_utc):
            d = datetime.utcnow()
        else:
            d = datetime.now()
        return f"{name}_{GeneralUtilities.datetime_to_string_for_logfile_name(d)}"

    @staticmethod
    def bytes_to_string(payload: bytes, encoding: str = 'utf-8') -> str:
        return payload.decode(encoding, errors="ignore")

    @staticmethod
    def string_to_bytes(payload: str, encoding: str = 'utf-8') -> bytes:
        return payload.encode(encoding, errors="ignore")

    @staticmethod
    def contains_line(lines, regex: str) -> bool:
        for line in lines:
            if(re.match(regex, line)):
                return True
        return False

    @staticmethod
    def read_csv_file(file: str, ignore_first_line: bool = False, treat_number_sign_at_begin_of_line_as_comment: bool = True, trim_values: bool = True,
                      encoding="utf-8", ignore_empty_lines: bool = True, separator_character: str = ";", values_are_surrounded_by_quotes: bool = False) -> list:
        lines = GeneralUtilities.read_lines_from_file(file, encoding)

        if ignore_first_line:
            lines = lines[1:]
        result = list()
        line: str
        for line_loopvariable in lines:
            use_line = True
            line = line_loopvariable

            if trim_values:
                line = line.strip()
            if ignore_empty_lines:
                if not GeneralUtilities.string_has_content(line):
                    use_line = False

            if treat_number_sign_at_begin_of_line_as_comment:
                if line.startswith("#"):
                    use_line = False

            if use_line:
                if separator_character in line:
                    raw_values_of_line = GeneralUtilities.to_list(line, separator_character)
                else:
                    raw_values_of_line = [line]
                if trim_values:
                    raw_values_of_line = [value.strip() for value in raw_values_of_line]
                values_of_line = []
                for raw_value_of_line in raw_values_of_line:
                    value_of_line = raw_value_of_line
                    if values_are_surrounded_by_quotes:
                        value_of_line = value_of_line[1:]
                        value_of_line = value_of_line[:-1]
                        value_of_line = value_of_line.replace('""', '"')
                    values_of_line.append(value_of_line)
                result.extend([values_of_line])
        return result

    @staticmethod
    def epew_is_available() -> bool:
        try:
            return shutil.which("epew") is not None
        except:
            return False

    @staticmethod
    def absolute_file_paths(directory: str) -> list:
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                yield os.path.abspath(os.path.join(dirpath, filename))

    @staticmethod
    def os_is_linux():
        return sys.platform in ('linux', 'linux2')

    @staticmethod
    def to_list(list_as_string: str, separator: str = ",") -> list:
        result = list()
        if list_as_string is not None:
            list_as_string = list_as_string.strip()
            if list_as_string == "":
                pass
            elif separator in list_as_string:
                for item in list_as_string.split(separator):
                    result.append(item.strip())
            else:
                result.append(list_as_string)
        return result

    @staticmethod
    def get_next_square_number(number: int):
        GeneralUtilities.assert_condition(number >= 0, "get_next_square_number is only applicable for nonnegative numbers")
        if number == 0:
            return 1
        root = 0
        square = 0
        while square < number:
            root = root+1
            square = root*root
        return root*root

    @staticmethod
    def assert_condition(condition: bool, information: str):
        if(not condition):
            raise ValueError("Condition failed. "+information)

class GitUtilities:
    pass
