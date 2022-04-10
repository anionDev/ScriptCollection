from abc import abstractmethod
from .GeneralUtilities import GeneralUtilities


class GitRunnerBase:

    # Arguments of git_runner: scriptCollection, git-arguments, working-directory, throw_exception_if_exitcode_is_not_zero
    # Return-values git_runner: Exitcode, StdOut, StdErr, Pid
    @abstractmethod
    def run_git_argsasarray(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> tuple[int, str, str, int]:
        raise NotImplementedError

    # Arguments of git_runner: scriptCollection, git-arguments, working-directory, throw_exception_if_exitcode_is_not_zero
    # Return-values git_runner: Exitcode, StdOut, StdErr, Pid
    @GeneralUtilities.check_arguments
    def run_git(self, arguments: str, working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> tuple[int, str, str, int]:
        return self.run_git_argsasarray(GeneralUtilities.arguments_to_array(arguments), working_directory, throw_exception_if_exitcode_is_not_zero)
