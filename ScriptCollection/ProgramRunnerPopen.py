from subprocess import PIPE, Popen
from datetime import datetime
from .GeneralUtilities import GeneralUtilities
from .ProgramRunnerBase import ProgramRunnerBase


class ProgramRunnerPopen(ProgramRunnerBase):
    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self,program:str, arguments_as_array: list[str], working_directory: str) -> tuple[int, str, str, int]:
        arguments_for_process = [program]
        arguments_for_process.extend(arguments_as_array)
        with Popen(arguments_for_process, stdout=PIPE, stderr=PIPE, cwd=working_directory, shell=False) as process:
            pid = process.pid
            stdout, stderr = process.communicate()
            exit_code = process.wait()
            stdout = GeneralUtilities.bytes_to_string(stdout).replace('\r', '')
            stderr = GeneralUtilities.bytes_to_string(stderr).replace('\r', '')
            result = (exit_code, stdout, stderr, pid)
            return result

    @GeneralUtilities.check_arguments
    def run_program(self, program:str,arguments: str, working_directory: str) -> tuple[int, str, str, int]:
        arguments_for_process = [program]
        arguments_for_process.extend(GeneralUtilities.arguments_to_array(arguments))
        with Popen(arguments_for_process, stdout=PIPE, stderr=PIPE, cwd=working_directory, shell=False) as process:
            pid = process.pid
            stdout, stderr = process.communicate()
            exit_code = process.wait()
            stdout = GeneralUtilities.bytes_to_string(stdout).replace('\r', '')
            stderr = GeneralUtilities.bytes_to_string(stderr).replace('\r', '')
            result = (exit_code, stdout, stderr, pid)
            return result

    @GeneralUtilities.check_arguments
    def run_program_argsasarray_async(self,program:str, arguments_as_array: list[str], working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def run_program_async(self, program:str,arguments: str, working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError
