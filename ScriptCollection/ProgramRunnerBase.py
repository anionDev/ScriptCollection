from abc import abstractmethod
from .GeneralUtilities import GeneralUtilities


class ProgramRunnerBase:

    # Arguments of program_runner: scriptCollection, git-arguments, working-directory, throw_exception_if_exitcode_is_not_zero
    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @abstractmethod
    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> tuple[int, str, str, int]:
        raise NotImplementedError

    # Arguments of program_runner: scriptCollection, git-arguments, working-directory, throw_exception_if_exitcode_is_not_zero
    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @abstractmethod
    @GeneralUtilities.check_arguments
    def run_program(self, arguments: str, working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> tuple[int, str, str, int]:
        raise NotImplementedError
