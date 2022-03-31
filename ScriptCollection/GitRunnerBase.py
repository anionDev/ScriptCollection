from abc import abstractmethod
from .Utilities import GeneralUtilities

class GitRunnerBase:
    # Arguments of git_runner: scriptCollection, git-arguments, working-directory, throw_exception_if_exitcode_is_not_zero
    # Return-values git_runner: Exitcode, StdOut, StdErr, Pid
    @abstractmethod
    def run_git(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> list[int, str, str, int]:
        raise NotImplementedError
    # Arguments of git_runner: scriptCollection, git-arguments, working-directory, throw_exception_if_exitcode_is_not_zero
    # Return-values git_runner: Exitcode, StdOut, StdErr, Pid

    def run_git_argsasarray(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> list[int, str, str, int]:
        return self.run_git(GeneralUtilities.arguments_to_array(arguments_as_array), working_directory, throw_exception_if_exitcode_is_not_zero)
