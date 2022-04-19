from abc import abstractmethod
from .GeneralUtilities import GeneralUtilities


class ProgramRunnerBase:

    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @abstractmethod
    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self, program:str, arguments_as_array: list[str], working_directory: str) -> tuple[int, str, str, int]:
        raise NotImplementedError

    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @abstractmethod
    @GeneralUtilities.check_arguments
    def run_program(self, program:str,arguments:  str, working_directory: str ) -> tuple[int, str, str, int]:
        raise NotImplementedError

    # Return-values program_runner: Pid
    @abstractmethod
    @GeneralUtilities.check_arguments
    def run_program_argsasarray_async(self, program:str, arguments_as_array: list[str], working_directory: str ) -> tuple[int, str, str, int]:
        raise NotImplementedError

    # Return-values program_runner: Pid
    @abstractmethod
    @GeneralUtilities.check_arguments
    def run_program_async(self, program:str,arguments: str,  working_directory: str ) -> tuple[int, str, str, int]:
        raise NotImplementedError
