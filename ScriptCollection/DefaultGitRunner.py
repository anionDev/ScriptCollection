from .Core import ScriptCollectionCore
from .GitRunnerBase import GitRunnerBase

class DefaultGitRunner(GitRunnerBase):

    __sc: ScriptCollectionCore = ScriptCollectionCore()

    def run_git(self, arguments_as_array: list[str], working_directory: str, throw_exception_if_exitcode_is_not_zero: bool) -> list[int, str, str, int]:
        arguments_as_array_typed: list[str] = arguments_as_array
        working_directory_typed: str = working_directory
        return self.__sc.start_program_synchronously_argsasarray("git", arguments_as_array_typed, working_directory_typed,
                                                                 timeoutInSeconds=3600, verbosity=0,  prevent_using_epew=True,
                                                                 throw_exception_if_exitcode_is_not_zero=throw_exception_if_exitcode_is_not_zero)
