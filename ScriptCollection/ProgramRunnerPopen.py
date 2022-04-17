from .GeneralUtilities import GeneralUtilities
from .ProgramRunnerBase import ProgramRunnerBase


class ProgramRunnerPopen(ProgramRunnerBase):
    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> tuple[int, str, str, int]:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def run_program(self, arguments: str, working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> tuple[int, str, str, int]:
        raise NotImplementedError
