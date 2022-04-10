from typing import Callable
from .GitRunnerBase import GitRunnerBase
from .GeneralUtilities import GeneralUtilities


class GenericGitRunner(GitRunnerBase):
    custom_arguments: list[object] = None
    git_command_runner_function: Callable[[list[str], str, bool, list[object]], list[int, str, str, int]] = None

    def __init__(self, git_command_runner_function: Callable[[list[str], str, bool, list[object]], list[int, str, str, int]], custom_arguments: list[object]):
        self.git_command_runner_function = git_command_runner_function
        self.custom_arguments = custom_arguments

    @GeneralUtilities.check_arguments
    def run_git_argsasarray(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> list[int, str, str, int]:
        return self.git_command_runner_function(arguments_as_array, working_directory, throw_exception_if_exitcode_is_not_zero, self.custom_arguments)
