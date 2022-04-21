import os
import base64
import tempfile
from subprocess import Popen, call
from .GeneralUtilities import GeneralUtilities
from .ProgramRunnerBase import ProgramRunnerBase


class ProgramRunnerPopen(ProgramRunnerBase):

    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self,program:str, arguments_as_array: list[str], working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def run_program(self, program:str,arguments: str, working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def run_program_argsasarray_async(self,program:str, arguments_as_array: list[str], working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def run_program_async(self, program:str,arguments: str, working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def __get_number_from_filecontent(self, filecontent: str) -> int:
        for line in filecontent.splitlines():
            try:
                striped_line = GeneralUtilities.strip_new_line_character(line)
                result = int(striped_line)
                return result
            except:
                pass
        raise Exception(f"'{filecontent}' does not containe an int-line")

    @GeneralUtilities.check_arguments
    def __load_text(self, file: str) -> str:
        if os.path.isfile(file):
            content = GeneralUtilities.read_text_from_file(file).replace('\r', '')
            os.remove(file)
            return content
        else:
            raise Exception(f"File '{file}' does not exist")
