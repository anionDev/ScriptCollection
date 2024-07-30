import time
from datetime import timedelta, datetime
import json
import binascii
import filecmp
import hashlib
from io import BufferedReader, BytesIO
import itertools
import math
import os
from pathlib import Path
from random import randrange
from subprocess import Popen
import re
import shutil
import traceback
import uuid
import tempfile
import io
import requests
import ntplib
import yaml
import qrcode
import pycdlib
import send2trash
import PyPDF2
from .GeneralUtilities import GeneralUtilities
from .ProgramRunnerBase import ProgramRunnerBase
from .ProgramRunnerPopen import ProgramRunnerPopen
from .ProgramRunnerEpew import ProgramRunnerEpew, CustomEpewArgument

version = "3.5.10"
__version__ = version


class ScriptCollectionCore:

    # The purpose of this property is to use it when testing your code which uses scriptcollection for external program-calls.
    # Do not change this value for productive environments.
    mock_program_calls: bool = False
    # The purpose of this property is to use it when testing your code which uses scriptcollection for external program-calls.
    execute_program_really_if_no_mock_call_is_defined: bool = False
    __mocked_program_calls: list = list()
    program_runner: ProgramRunnerBase = None

    def __init__(self):
        self.program_runner = ProgramRunnerPopen()

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_scriptcollection_version() -> str:
        return __version__

    @GeneralUtilities.check_arguments
    def python_file_has_errors(self, file: str, working_directory: str, treat_warnings_as_errors: bool = True) -> tuple[bool, list[str]]:
        errors = list()
        filename = os.path.relpath(file, working_directory)
        if treat_warnings_as_errors:
            errorsonly_argument = ""
        else:
            errorsonly_argument = " --errors-only"
        (exit_code, stdout, stderr, _) = self.run_program("pylint", filename +
                                                          errorsonly_argument, working_directory, throw_exception_if_exitcode_is_not_zero=False)
        if (exit_code != 0):
            errors.append(f"Linting-issues of {file}:")
            errors.append(f"Pylint-exitcode: {exit_code}")
            for line in GeneralUtilities.string_to_lines(stdout):
                errors.append(line)
            for line in GeneralUtilities.string_to_lines(stderr):
                errors.append(line)
            return (True, errors)

        return (False, errors)

    @GeneralUtilities.check_arguments
    def replace_version_in_dockerfile_file(self, dockerfile: str, new_version_value: str) -> None:
        GeneralUtilities.write_text_to_file(dockerfile, re.sub(
            "ARG Version=\"\\d+\\.\\d+\\.\\d+\"", f"ARG Version=\"{new_version_value}\"", GeneralUtilities.read_text_from_file(dockerfile)))

    @GeneralUtilities.check_arguments
    def replace_version_in_python_file(self, file: str, new_version_value: str):
        GeneralUtilities.write_text_to_file(file, re.sub(
            "version = \"\\d+\\.\\d+\\.\\d+\"", f"version = \"{new_version_value}\"", GeneralUtilities.read_text_from_file(file)))

    @GeneralUtilities.check_arguments
    def replace_version_in_ini_file(self, file: str, new_version_value: str):
        GeneralUtilities.write_text_to_file(file, re.sub(
            "version = \\d+\\.\\d+\\.\\d+", f"version = {new_version_value}", GeneralUtilities.read_text_from_file(file)))

    @GeneralUtilities.check_arguments
    def replace_version_in_nuspec_file(self, nuspec_file: str, new_version: str) -> None:
        # TODO use XSLT instead
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(new_version):
            GeneralUtilities.write_text_to_file(nuspec_file, re.sub(f"<version>{versionregex}<\\/version>", f"<version>{new_version}</version>", GeneralUtilities.read_text_from_file(nuspec_file)))
        else:
            raise ValueError(
                f"Version '{new_version}' does not match version-regex '{versiononlyregex}'")

    @GeneralUtilities.check_arguments
    def replace_version_in_csproj_file(self, csproj_file: str, current_version: str):
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(current_version):
            for tag in ["Version", "AssemblyVersion", "FileVersion"]:
                GeneralUtilities.write_text_to_file(csproj_file, re.sub(
                    f"<{tag}>{versionregex}(.\\d+)?<\\/{tag}>", f"<{tag}>{current_version}</{tag}>", GeneralUtilities.read_text_from_file(csproj_file)))
        else:
            raise ValueError(
                f"Version '{current_version}' does not match version-regex '{versiononlyregex}'")

    @GeneralUtilities.check_arguments
    def push_nuget_build_artifact(self, nupkg_file: str, registry_address: str, api_key: str, verbosity: int = 1):
        nupkg_file_name = os.path.basename(nupkg_file)
        nupkg_file_folder = os.path.dirname(nupkg_file)
        self.run_program(
            "dotnet", f"nuget push {nupkg_file_name} --force-english-output --source {registry_address} --api-key {api_key}", nupkg_file_folder, verbosity)

    @GeneralUtilities.check_arguments
    def dotnet_build(self, repository_folder: str, projectname: str, configuration: str):
        self.run_program(
            "dotnet", f"clean -c {configuration}", repository_folder)
        self.run_program(
            "dotnet", f"build {projectname}/{projectname}.csproj -c {configuration}", repository_folder)

    @GeneralUtilities.check_arguments
    def find_file_by_extension(self, folder: str, extension: str):
        result = [file for file in GeneralUtilities.get_direct_files_of_folder(folder) if file.endswith(f".{extension}")]
        result_length = len(result)
        if result_length == 0:
            raise FileNotFoundError(f"No file available in folder '{folder}' with extension '{extension}'.")
        if result_length == 1:
            return result[0]
        else:
            raise ValueError(f"Multiple values available in folder '{folder}' with extension '{extension}'.")

    @GeneralUtilities.check_arguments
    def commit_is_signed_by_key(self, repository_folder: str, revision_identifier: str, key: str) -> bool:
        result = self.run_program(
            "git", f"verify-commit {revision_identifier}", repository_folder, throw_exception_if_exitcode_is_not_zero=False)
        if (result[0] != 0):
            return False
        if (not GeneralUtilities.contains_line(result[1].splitlines(), f"gpg\\:\\ using\\ [A-Za-z0-9]+\\ key\\ [A-Za-z0-9]+{key}")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        if (not GeneralUtilities.contains_line(result[1].splitlines(), "gpg\\:\\ Good\\ signature\\ from")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        return True

    @GeneralUtilities.check_arguments
    def get_parent_commit_ids_of_commit(self, repository_folder: str, commit_id: str) -> str:
        return self.run_program("git", f'log --pretty=%P -n 1 "{commit_id}"', repository_folder, throw_exception_if_exitcode_is_not_zero=True)[1].replace("\r", "").replace("\n", "").split(" ")

    @GeneralUtilities.check_arguments
    def get_all_authors_and_committers_of_repository(self, repository_folder: str, subfolder: str = None, verbosity: int = 1) -> list[tuple[str, str]]:
        space_character = "_"
        if subfolder is None:
            subfolder_argument = ""
        else:
            subfolder_argument = f" -- {subfolder}"
        log_result = self.run_program(
            "git", f'log --pretty=%aN{space_character}%aE%n%cN{space_character}%cE HEAD{subfolder_argument}', repository_folder, verbosity=0)
        plain_content: list[str] = list(
            set([line for line in log_result[1].split("\n") if len(line) > 0]))
        result: list[tuple[str, str]] = []
        for item in plain_content:
            if len(re.findall(space_character, item)) == 1:
                splitted = item.split(space_character)
                result.append((splitted[0], splitted[1]))
            else:
                raise ValueError(f'Unexpected author: "{item}"')
        return result

    @GeneralUtilities.check_arguments
    def get_commit_ids_between_dates(self, repository_folder: str, since: datetime, until: datetime, ignore_commits_which_are_not_in_history_of_head: bool = True) -> None:
        since_as_string = self.__datetime_to_string_for_git(since)
        until_as_string = self.__datetime_to_string_for_git(until)
        result = filter(lambda line: not GeneralUtilities.string_is_none_or_whitespace(line), self.run_program(
            "git", f'log --since "{since_as_string}" --until "{until_as_string}" --pretty=format:"%H" --no-patch', repository_folder, throw_exception_if_exitcode_is_not_zero=True)[1].split("\n").replace("\r", ""))
        if ignore_commits_which_are_not_in_history_of_head:
            result = [commit_id for commit_id in result if self.git_commit_is_ancestor(
                repository_folder, commit_id)]
        return result

    @GeneralUtilities.check_arguments
    def __datetime_to_string_for_git(self, datetime_object: datetime) -> str:
        return datetime_object.strftime('%Y-%m-%d %H:%M:%S')

    @GeneralUtilities.check_arguments
    def git_commit_is_ancestor(self, repository_folder: str,  ancestor: str, descendant: str = "HEAD") -> bool:
        exit_code = self.run_program_argsasarray(
            "git", ["merge-base", "--is-ancestor", ancestor, descendant], repository_folder, throw_exception_if_exitcode_is_not_zero=False)[0]
        if exit_code == 0:
            return True
        elif exit_code == 1:
            return False
        else:
            raise ValueError(f"Can not calculate if {ancestor} is an ancestor of {descendant} in repository {repository_folder}.")

    @GeneralUtilities.check_arguments
    def __git_changes_helper(self, repository_folder: str, arguments_as_array: list[str]) -> bool:
        lines = GeneralUtilities.string_to_lines(self.run_program_argsasarray(
            "git", arguments_as_array, repository_folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)[1], False)
        for line in lines:
            if GeneralUtilities.string_has_content(line):
                return True
        return False

    @GeneralUtilities.check_arguments
    def git_repository_has_new_untracked_files(self, repositoryFolder: str):
        return self.__git_changes_helper(repositoryFolder, ["ls-files", "--exclude-standard", "--others"])

    @GeneralUtilities.check_arguments
    def git_repository_has_unstaged_changes_of_tracked_files(self, repositoryFolder: str):
        return self.__git_changes_helper(repositoryFolder, ["diff"])

    @GeneralUtilities.check_arguments
    def git_repository_has_staged_changes(self, repositoryFolder: str):
        return self.__git_changes_helper(repositoryFolder, ["diff", "--cached"])

    @GeneralUtilities.check_arguments
    def git_repository_has_uncommitted_changes(self, repositoryFolder: str) -> bool:
        if (self.git_repository_has_unstaged_changes(repositoryFolder)):
            return True
        if (self.git_repository_has_staged_changes(repositoryFolder)):
            return True
        return False

    @GeneralUtilities.check_arguments
    def git_repository_has_unstaged_changes(self, repository_folder: str) -> bool:
        if (self.git_repository_has_unstaged_changes_of_tracked_files(repository_folder)):
            return True
        if (self.git_repository_has_new_untracked_files(repository_folder)):
            return True
        return False

    @GeneralUtilities.check_arguments
    def git_get_commit_id(self, repository_folder: str, commit: str = "HEAD") -> str:
        result: tuple[int, str, str, int] = self.run_program_argsasarray("git", ["rev-parse", "--verify", commit], repository_folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        return result[1].replace('\n', '')

    @GeneralUtilities.check_arguments
    def git_get_commit_date(self, repository_folder: str, commit: str = "HEAD") -> datetime:
        result: tuple[int, str, str, int] = self.run_program_argsasarray(
            "git", ["show", "-s", "--format=%ci", commit], repository_folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        date_as_string = result[1].replace('\n', '')
        result = datetime.strptime(date_as_string, '%Y-%m-%d %H:%M:%S %z')
        return result

    @GeneralUtilities.check_arguments
    def git_fetch(self, folder: str, remotename: str = "--all") -> None:
        self.run_program_argsasarray("git", ["fetch", remotename, "--tags", "--prune"], folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_fetch_in_bare_repository(self, folder: str, remotename, localbranch: str, remotebranch: str) -> None:
        self.run_program_argsasarray("git", ["fetch", remotename, f"{remotebranch}:{localbranch}"], folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_remove_branch(self, folder: str, branchname: str) -> None:
        self.run_program("git", f"branch -D {branchname}", folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_push(self, folder: str, remotename: str, localbranchname: str, remotebranchname: str, forcepush: bool = False, pushalltags: bool = True, verbosity: int = 0) -> None:
        argument = ["push", "--recurse-submodules=on-demand", remotename, f"{localbranchname}:{remotebranchname}"]
        if (forcepush):
            argument.append("--force")
        if (pushalltags):
            argument.append("--tags")
        result: tuple[int, str, str, int] = self.run_program_argsasarray("git", argument, folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=verbosity, print_errors_as_information=True)
        return result[1].replace('\r', '').replace('\n', '')

    @GeneralUtilities.check_arguments
    def git_pull(self, folder: str, remote: str, localbranchname: str, remotebranchname: str) -> None:
        self.run_program("git", f"pull {remote} {remotebranchname}:{localbranchname}", folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_list_remote_branches(self, folder: str, remote: str, fetch: bool) -> list[str]:
        if fetch:
            self.git_fetch(folder, remote)
        run_program_result = self.run_program("git", f"branch -rl {remote}/*", folder, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        output = GeneralUtilities.string_to_lines(run_program_result[1])
        result = list[str]()
        for item in output:
            striped_item = item.strip()
            if GeneralUtilities.string_has_content(striped_item):
                branch: str = None
                if " " in striped_item:
                    branch = striped_item.split(" ")[0]
                else:
                    branch = striped_item
                branchname = branch[len(remote)+1:]
                if branchname != "HEAD":
                    result.append(branchname)
        return result

    @GeneralUtilities.check_arguments
    def git_clone(self, clone_target_folder: str, remote_repository_path: str, include_submodules: bool = True, mirror: bool = False) -> None:
        if (os.path.isdir(clone_target_folder)):
            pass  # TODO throw error
        else:
            args = ["clone", remote_repository_path, clone_target_folder]
            if include_submodules:
                args.append("--recurse-submodules")
                args.append("--remote-submodules")
            if mirror:
                args.append("--mirror")
            self.run_program_argsasarray("git", args, os.getcwd(), throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_get_all_remote_names(self, directory: str) -> list[str]:
        result = GeneralUtilities.string_to_lines(self.run_program_argsasarray("git", ["remote"], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)[1], False)
        return result

    @GeneralUtilities.check_arguments
    def git_get_remote_url(self, directory: str, remote_name: str) -> str:
        result = GeneralUtilities.string_to_lines(self.run_program_argsasarray("git", ["remote", "get-url", remote_name], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)[1], False)
        return result[0].replace('\n', '')

    @GeneralUtilities.check_arguments
    def repository_has_remote_with_specific_name(self, directory: str, remote_name: str) -> bool:
        return remote_name in self.git_get_all_remote_names(directory)

    @GeneralUtilities.check_arguments
    def git_add_or_set_remote_address(self, directory: str, remote_name: str, remote_address: str) -> None:
        if (self.repository_has_remote_with_specific_name(directory, remote_name)):
            self.run_program_argsasarray("git", ['remote', 'set-url', 'remote_name', remote_address], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        else:
            self.run_program_argsasarray("git", ['remote', 'add', remote_name, remote_address], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_stage_all_changes(self, directory: str) -> None:
        self.run_program_argsasarray("git", ["add", "-A"], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_unstage_all_changes(self, directory: str) -> None:
        self.run_program_argsasarray("git", ["reset"], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_stage_file(self, directory: str, file: str) -> None:
        self.run_program_argsasarray("git", ['stage', file], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_unstage_file(self, directory: str, file: str) -> None:
        self.run_program_argsasarray("git", ['reset', file], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_discard_unstaged_changes_of_file(self, directory: str, file: str) -> None:
        """Caution: This method works really only for 'changed' files yet. So this method does not work properly for new or renamed files."""
        self.run_program_argsasarray("git", ['checkout', file], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_discard_all_unstaged_changes(self, directory: str) -> None:
        """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
        self.run_program_argsasarray("git", ['clean', '-df'], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        self.run_program_argsasarray("git", ['checkout', '.'], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_commit(self, directory: str, message: str, author_name: str = None, author_email: str = None, stage_all_changes: bool = True,
                   no_changes_behavior: int = 0) -> str:
        # no_changes_behavior=0 => No commit
        # no_changes_behavior=1 => Commit anyway
        # no_changes_behavior=2 => Exception
        author_name = GeneralUtilities.str_none_safe(author_name).strip()
        author_email = GeneralUtilities.str_none_safe(author_email).strip()
        argument = ['commit', '--quiet', '--allow-empty', '--message', message]
        if (GeneralUtilities.string_has_content(author_name)):
            argument.append(f'--author="{author_name} <{author_email}>"')
        git_repository_has_uncommitted_changes = self.git_repository_has_uncommitted_changes(directory)

        if git_repository_has_uncommitted_changes:
            do_commit = True
            if stage_all_changes:
                self.git_stage_all_changes(directory)
        else:
            if no_changes_behavior == 0:
                GeneralUtilities.write_message_to_stdout(f"Commit '{message}' will not be done because there are no changes to commit in repository '{directory}'")
                do_commit = False
            elif no_changes_behavior == 1:
                GeneralUtilities.write_message_to_stdout(f"There are no changes to commit in repository '{directory}'. Commit '{message}' will be done anyway.")
                do_commit = True
            elif no_changes_behavior == 2:
                raise RuntimeError(f"There are no changes to commit in repository '{directory}'. Commit '{message}' will not be done.")
            else:
                raise ValueError(f"Unknown value for no_changes_behavior: {GeneralUtilities.str_none_safe(no_changes_behavior)}")

        if do_commit:
            GeneralUtilities.write_message_to_stdout(f"Commit changes in '{directory}'")
            self.run_program_argsasarray("git", argument, directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

        return self.git_get_commit_id(directory)

    @GeneralUtilities.check_arguments
    def git_create_tag(self, directory: str, target_for_tag: str, tag: str, sign: bool = False, message: str = None) -> None:
        argument = ["tag", tag, target_for_tag]
        if sign:
            if message is None:
                message = f"Created {target_for_tag}"
            argument.extend(["-s", '-m', message])
        self.run_program_argsasarray(
            "git", argument, directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_delete_tag(self, directory: str, tag: str) -> None:
        self.run_program_argsasarray("git", ["tag", "--delete", tag], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_checkout(self, directory: str, branch: str) -> None:
        self.run_program_argsasarray("git", ["checkout", branch], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        self.run_program_argsasarray("git", ["submodule", "update", "--recursive"],                                     directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_merge_abort(self, directory: str) -> None:
        self.run_program_argsasarray("git", ["merge", "--abort"], directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_merge(self, directory: str, sourcebranch: str, targetbranch: str, fastforward: bool = True, commit: bool = True, commit_message: str = None) -> str:
        self.git_checkout(directory, targetbranch)
        args = ["merge"]
        if not commit:
            args.append("--no-commit")
        if not fastforward:
            args.append("--no-ff")
        if commit_message is not None:
            args.append("-m")
            args.append(commit_message)
        args.append(sourcebranch)
        self.run_program_argsasarray(
            "git", args, directory, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        return self.git_get_commit_id(directory)

    @GeneralUtilities.check_arguments
    def git_undo_all_changes(self, directory: str) -> None:
        """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
        self.git_unstage_all_changes(directory)
        self.git_discard_all_unstaged_changes(directory)

    @GeneralUtilities.check_arguments
    def git_fetch_or_clone_all_in_directory(self, source_directory: str, target_directory: str) -> None:
        for subfolder in GeneralUtilities.get_direct_folders_of_folder(source_directory):
            foldername = os.path.basename(subfolder)
            if self.is_git_repository(subfolder):
                source_repository = subfolder
                target_repository = os.path.join(target_directory, foldername)
                if os.path.isdir(target_directory):
                    # fetch
                    self.git_fetch(target_directory)
                else:
                    # clone
                    self.git_clone(target_repository, source_repository,                                   include_submodules=True, mirror=True)

    def get_git_submodules(self, folder: str) -> list[str]:
        e = self.run_program("git", "submodule status", folder)
        result = []
        for submodule_line in GeneralUtilities.string_to_lines(e[1], False, True):
            result.append(submodule_line.split(' ')[1])
        return result

    @GeneralUtilities.check_arguments
    def is_git_repository(self, folder: str) -> bool:
        combined = os.path.join(folder, ".git")
        # TODO consider check for bare-repositories
        return os.path.isdir(combined) or os.path.isfile(combined)

    @GeneralUtilities.check_arguments
    def file_is_git_ignored(self, file_in_repository: str, repositorybasefolder: str) -> None:
        exit_code = self.run_program_argsasarray("git", ['check-ignore', file_in_repository], repositorybasefolder, throw_exception_if_exitcode_is_not_zero=False, verbosity=0)[0]
        if (exit_code == 0):
            return True
        if (exit_code == 1):
            return False
        raise ValueError(
            f"Unable to calculate whether '{file_in_repository}' in repository '{repositorybasefolder}' is ignored due to git-exitcode {exit_code}.")

    @GeneralUtilities.check_arguments
    def git_discard_all_changes(self, repository: str) -> None:
        self.run_program_argsasarray("git", ["reset", "HEAD", "."], repository, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        self.run_program_argsasarray("git", ["checkout", "."], repository, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)

    @GeneralUtilities.check_arguments
    def git_get_current_branch_name(self, repository: str) -> str:
        result = self.run_program_argsasarray("git", ["rev-parse", "--abbrev-ref", "HEAD"], repository, throw_exception_if_exitcode_is_not_zero=True, verbosity=0)
        return result[1].replace("\r", "").replace("\n", "")

    @GeneralUtilities.check_arguments
    def git_get_commitid_of_tag(self, repository: str, tag: str) -> str:
        stdout = self.run_program_argsasarray("git", ["rev-list", "-n", "1", tag], repository, verbosity=0)
        result = stdout[1].replace("\r", "").replace("\n", "")
        return result

    @GeneralUtilities.check_arguments
    def git_get_tags(self, repository: str) -> list[str]:
        tags = [line.replace("\r", "") for line in self.run_program_argsasarray(
            "git", ["tag"], repository)[1].split("\n") if len(line) > 0]
        return tags

    @GeneralUtilities.check_arguments
    def git_move_tags_to_another_branch(self, repository: str, tag_source_branch: str, tag_target_branch: str, sign: bool = False, message: str = None) -> None:
        tags = self.git_get_tags(repository)
        tags_count = len(tags)
        counter = 0
        for tag in tags:
            counter = counter+1
            GeneralUtilities.write_message_to_stdout(f"Process tag {counter}/{tags_count}.")
            # tag is on source-branch
            if self.git_commit_is_ancestor(repository, tag, tag_source_branch):
                commit_id_old = self.git_get_commitid_of_tag(repository, tag)
                commit_date: datetime = self.git_get_commit_date(repository, commit_id_old)
                date_as_string = self.__datetime_to_string_for_git(commit_date)
                search_commit_result = self.run_program_argsasarray("git", ["log", f'--after="{date_as_string}"', f'--before="{date_as_string}"', "--pretty=format:%H", tag_target_branch], repository, throw_exception_if_exitcode_is_not_zero=False)
                if search_commit_result[0] != 0 or not GeneralUtilities.string_has_nonwhitespace_content(search_commit_result[1]):
                    raise ValueError(f"Can not calculate corresponding commit for tag '{tag}'.")
                commit_id_new = search_commit_result[1]
                self.git_delete_tag(repository, tag)
                self.git_create_tag(repository, commit_id_new, tag, sign, message)

    @GeneralUtilities.check_arguments
    def get_current_git_branch_has_tag(self, repository_folder: str) -> bool:
        result = self.run_program_argsasarray("git", ["describe", "--tags", "--abbrev=0"], repository_folder, verbosity=0, throw_exception_if_exitcode_is_not_zero=False)
        return result[0] == 0

    @GeneralUtilities.check_arguments
    def get_latest_git_tag(self, repository_folder: str) -> str:
        result = self.run_program_argsasarray(
            "git", ["describe", "--tags", "--abbrev=0"], repository_folder, verbosity=0)
        result = result[1].replace("\r", "").replace("\n", "")
        return result

    @GeneralUtilities.check_arguments
    def get_staged_or_committed_git_ignored_files(self, repository_folder: str) -> list[str]:
        tresult = self.run_program_argsasarray("git", ["ls-files", "-i", "-c", "--exclude-standard"], repository_folder, verbosity=0)
        tresult = tresult[1].replace("\r", "")
        result = [line for line in tresult.split("\n") if len(line) > 0]
        return result

    @GeneralUtilities.check_arguments
    def git_repository_has_commits(self, repository_folder: str) -> bool:
        return self.run_program_argsasarray("git", ["rev-parse", "--verify", "HEAD"], repository_folder, throw_exception_if_exitcode_is_not_zero=False)[0] == 0

    @GeneralUtilities.check_arguments
    def export_filemetadata(self, folder: str, target_file: str, encoding: str = "utf-8", filter_function=None) -> None:
        folder = GeneralUtilities.resolve_relative_path_from_current_working_directory(folder)
        lines = list()
        path_prefix = len(folder)+1
        items = dict()
        for item in GeneralUtilities.get_all_folders_of_folder(folder):
            items[item] = "d"
        for item in GeneralUtilities.get_all_files_of_folder(folder):
            items[item] = "f"
        for file_or_folder, item_type in items.items():
            truncated_file = file_or_folder[path_prefix:]
            if (filter_function is None or filter_function(folder, truncated_file)):
                owner_and_permisssion = self.get_file_owner_and_file_permission(
                    file_or_folder)
                user = owner_and_permisssion[0]
                permissions = owner_and_permisssion[1]
                lines.append(f"{truncated_file};{item_type};{user};{permissions}")
        lines = sorted(lines, key=str.casefold)
        with open(target_file, "w", encoding=encoding) as file_object:
            file_object.write("\n".join(lines))

    def escape_git_repositories_in_folder(self, folder: str) -> dict[str, str]:
        return self.__escape_git_repositories_in_folder_internal(folder, dict[str, str]())

    def __escape_git_repositories_in_folder_internal(self, folder: str, renamed_items: dict[str, str]) -> dict[str, str]:
        for file in GeneralUtilities.get_direct_files_of_folder(folder):
            filename = os.path.basename(file)
            if ".git" in filename:
                new_name = filename.replace(".git", ".gitx")
                target = os.path.join(folder, new_name)
                os.rename(file, target)
                renamed_items[target] = file
        for subfolder in GeneralUtilities.get_direct_folders_of_folder(folder):
            foldername = os.path.basename(subfolder)
            if ".git" in foldername:
                new_name = foldername.replace(".git", ".gitx")
                subfolder2 = os.path.join(
                    str(Path(subfolder).parent), new_name)
                os.rename(subfolder, subfolder2)
                renamed_items[subfolder2] = subfolder
            else:
                subfolder2 = subfolder
            self.__escape_git_repositories_in_folder_internal(subfolder2, renamed_items)
        return renamed_items

    def deescape_git_repositories_in_folder(self, renamed_items: dict[str, str]):
        for renamed_item, original_name in renamed_items.items():
            os.rename(renamed_item, original_name)

    def __sort_fmd(self, line: str):
        splitted: list = line.split(";")
        filetype: str = splitted[1]
        if filetype == "d":
            return -1
        if filetype == "f":
            return 1
        return 0

    @GeneralUtilities.check_arguments
    def restore_filemetadata(self, folder: str, source_file: str, strict=False, encoding: str = "utf-8", create_folder_is_not_exist: bool = True) -> None:
        lines = GeneralUtilities.read_lines_from_file(source_file, encoding)
        lines.sort(key=self.__sort_fmd)
        for line in lines:
            splitted: list = line.split(";")
            full_path_of_file_or_folder: str = os.path.join(folder, splitted[0])
            filetype: str = splitted[1]
            user: str = splitted[2]
            permissions: str = splitted[3]
            if filetype == "d" and create_folder_is_not_exist and not os.path.isdir(full_path_of_file_or_folder):
                GeneralUtilities.ensure_directory_exists(full_path_of_file_or_folder)
            if (filetype == "f" and os.path.isfile(full_path_of_file_or_folder)) or (filetype == "d" and os.path.isdir(full_path_of_file_or_folder)):
                self.set_owner(full_path_of_file_or_folder, user, os.name != 'nt')
                self.set_permission(full_path_of_file_or_folder, permissions)
            else:
                if strict:
                    if filetype == "f":
                        filetype_full = "File"
                    elif filetype == "d":
                        filetype_full = "Directory"
                    else:
                        raise ValueError(f"Unknown filetype: {GeneralUtilities.str_none_safe(filetype)}")
                    raise ValueError(f"{filetype_full} '{full_path_of_file_or_folder}' does not exist")

    @GeneralUtilities.check_arguments
    def __calculate_lengh_in_seconds(self, filename: str, folder: str) -> float:
        argument = ['-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', filename]
        result = self.run_program_argsasarray("ffprobe", argument, folder, throw_exception_if_exitcode_is_not_zero=True)
        return float(result[1].replace('\n', ''))

    @GeneralUtilities.check_arguments
    def __create_thumbnails(self, filename: str, fps: str, folder: str, tempname_for_thumbnails: str) -> None:
        argument = ['-i', filename, '-r', str(fps), '-vf', 'scale=-1:120',
                    '-vcodec', 'png', f'{tempname_for_thumbnails}-%002d.png']
        self.run_program_argsasarray("ffmpeg", argument, folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def __create_thumbnail(self, outputfilename: str, folder: str, length_in_seconds: float, tempname_for_thumbnails: str, amount_of_images: int) -> None:
        duration = timedelta(seconds=length_in_seconds)
        info = GeneralUtilities.timedelta_to_simple_string(duration)
        next_square_number = str(int(math.sqrt(GeneralUtilities.get_next_square_number(amount_of_images))))
        argument = ['-title', f'"{outputfilename} ({info})"', '-tile', f'{next_square_number}x{next_square_number}',
                    f'{tempname_for_thumbnails}*.png', f'{outputfilename}.png']
        self.run_program_argsasarray(
            "montage", argument, folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def roundup(self, x: float, places: int) -> int:
        d = 10 ** places
        if x < 0:
            return math.floor(x * d) / d
        else:
            return math.ceil(x * d) / d

    @GeneralUtilities.check_arguments
    def generate_thumbnail(self, file: str, frames_per_second: str, tempname_for_thumbnails: str = None) -> None:
        if tempname_for_thumbnails is None:
            tempname_for_thumbnails = "t"+str(uuid.uuid4())

        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        filename = os.path.basename(file)
        folder = os.path.dirname(file)
        filename_without_extension = Path(file).stem

        try:
            length_in_seconds = self.__calculate_lengh_in_seconds(filename, folder)
            if (frames_per_second.endswith("fps")):
                # frames per second, example: frames_per_second="20fps" => 20 frames per second
                x = self.roundup(float(frames_per_second[:-3]), 2)
                frames_per_secondx = str(x)
                amounf_of_previewframes = int(math.floor(length_in_seconds*x))
            else:
                # concrete amount of frame, examples: frames_per_second="16" => 16 frames for entire video
                amounf_of_previewframes = int(float(frames_per_second))
                # self.roundup((amounf_of_previewframes-2)/length_in_seconds, 2)
                frames_per_secondx = f"{amounf_of_previewframes-2}/{length_in_seconds}"
            self.__create_thumbnails(filename, frames_per_secondx, folder, tempname_for_thumbnails)
            self.__create_thumbnail(filename_without_extension, folder, length_in_seconds, tempname_for_thumbnails, amounf_of_previewframes)
        finally:
            for thumbnail_to_delete in Path(folder).rglob(tempname_for_thumbnails+"-*"):
                file = str(thumbnail_to_delete)
                os.remove(file)

    @GeneralUtilities.check_arguments
    def extract_pdf_pages(self, file: str, from_page: int, to_page: int, outputfile: str) -> None:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        start = from_page
        end = to_page
        while start <= end:
            pdf_writer.add_page(pdf_reader.pages[start-1])
            start += 1
        with open(outputfile, 'wb') as out:
            pdf_writer.write(out)

    @GeneralUtilities.check_arguments
    def merge_pdf_files(self, files: list[str], outputfile: str) -> None:
        # TODO add wildcard-option
        pdfFileMerger = PyPDF2.PdfFileMerger()
        for file in files:
            pdfFileMerger.append(file.strip())
        pdfFileMerger.write(outputfile)
        pdfFileMerger.close()

    @GeneralUtilities.check_arguments
    def pdf_to_image(self, file: str, outputfilename_without_extension: str) -> None:
        raise ValueError("Function currently not available")
        # PyMuPDF can be used for that but sometimes it throws
        # "ImportError: DLL load failed while importing _fitz: Das angegebene Modul wurde nicht gefunden."

        # doc = None  # fitz.open(file)
        # for i, page in enumerate(doc):
        #     pix = page.get_pixmap()
        #     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        #     img.save(f"{outputfilename_without_extension}_{i}.png", "PNG")

    @GeneralUtilities.check_arguments
    def show_missing_files(self, folderA: str, folderB: str):
        for file in GeneralUtilities.get_missing_files(folderA, folderB):
            GeneralUtilities.write_message_to_stdout(file)

    @GeneralUtilities.check_arguments
    def SCCreateEmptyFileWithSpecificSize(self, name: str, size_string: str) -> int:
        if size_string.isdigit():
            size = int(size_string)
        else:
            if len(size_string) >= 3:
                if (size_string.endswith("kb")):
                    size = int(size_string[:-2]) * pow(10, 3)
                elif (size_string.endswith("mb")):
                    size = int(size_string[:-2]) * pow(10, 6)
                elif (size_string.endswith("gb")):
                    size = int(size_string[:-2]) * pow(10, 9)
                elif (size_string.endswith("kib")):
                    size = int(size_string[:-3]) * pow(2, 10)
                elif (size_string.endswith("mib")):
                    size = int(size_string[:-3]) * pow(2, 20)
                elif (size_string.endswith("gib")):
                    size = int(size_string[:-3]) * pow(2, 30)
                else:
                    GeneralUtilities.write_message_to_stderr("Wrong format")
                    return 1
            else:
                GeneralUtilities.write_message_to_stderr("Wrong format")
                return 1
        with open(name, "wb") as f:
            f.seek(size-1)
            f.write(b"\0")
        return 0

    @GeneralUtilities.check_arguments
    def SCCreateHashOfAllFiles(self, folder: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            with open(file+".sha256", "w+", encoding="utf-8") as f:
                f.write(GeneralUtilities.get_sha256_of_file(file))

    @GeneralUtilities.check_arguments
    def SCCreateSimpleMergeWithoutRelease(self, repository: str, sourcebranch: str, targetbranch: str, remotename: str, remove_source_branch: bool) -> None:
        commitid = self.git_merge(repository, sourcebranch, targetbranch, False, True)
        self.git_merge(repository, targetbranch, sourcebranch, True, True)
        created_version = self.get_semver_version_from_gitversion(repository)
        self.git_create_tag(repository, commitid, f"v{created_version}", True)
        self.git_push(repository, remotename, targetbranch, targetbranch, False, True)
        if (GeneralUtilities.string_has_nonwhitespace_content(remotename)):
            self.git_push(repository, remotename, sourcebranch, sourcebranch, False, True)
        if (remove_source_branch):
            self.git_remove_branch(repository, sourcebranch)

    @GeneralUtilities.check_arguments
    def sc_organize_lines_in_file(self, file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False, remove_empty_lines: bool = True, ignored_start_character: list = list()) -> int:
        if os.path.isfile(file):

            # read file
            lines = GeneralUtilities.read_lines_from_file(file, encoding)
            if (len(lines) == 0):
                return 0

            # store first line if desiredpopd

            if (ignore_first_line):
                first_line = lines.pop(0)

            # remove empty lines if desired
            if remove_empty_lines:
                temp = lines
                lines = []
                for line in temp:
                    if (not (GeneralUtilities.string_is_none_or_whitespace(line))):
                        lines.append(line)

            # remove duplicated lines if desired
            if remove_duplicated_lines:
                lines = GeneralUtilities.remove_duplicates(lines)

            # sort lines if desired
            if sort:
                lines = sorted(lines, key=lambda singleline: self.__adapt_line_for_sorting(singleline, ignored_start_character))

            # reinsert first line
            if ignore_first_line:
                lines.insert(0, first_line)

            # write result to file
            GeneralUtilities.write_lines_to_file(file, lines, encoding)

            return 0
        else:
            GeneralUtilities.write_message_to_stdout(f"File '{file}' does not exist")
            return 1

    @GeneralUtilities.check_arguments
    def __adapt_line_for_sorting(self, line: str, ignored_start_characters: list):
        result = line.lower()
        while len(result) > 0 and result[0] in ignored_start_characters:
            result = result[1:]
        return result

    @GeneralUtilities.check_arguments
    def SCGenerateSnkFiles(self, outputfolder, keysize=4096, amountofkeys=10) -> int:
        GeneralUtilities.ensure_directory_exists(outputfolder)
        for _ in range(amountofkeys):
            file = os.path.join(outputfolder, str(uuid.uuid4())+".snk")
            argument = f"-k {keysize} {file}"
            self.run_program("sn", argument, outputfolder)

    @GeneralUtilities.check_arguments
    def __merge_files(self, sourcefile: str, targetfile: str) -> None:
        with open(sourcefile, "rb") as f:
            source_data = f.read()
        with open(targetfile, "ab") as fout:
            merge_separator = [0x0A]
            fout.write(bytes(merge_separator))
            fout.write(source_data)

    @GeneralUtilities.check_arguments
    def __process_file(self, file: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
        new_filename = os.path.join(os.path.dirname(file), os.path.basename(file).replace(substringInFilename, newSubstringInFilename))
        if file != new_filename:
            if os.path.isfile(new_filename):
                if filecmp.cmp(file, new_filename):
                    send2trash.send2trash(file)
                else:
                    if conflictResolveMode == "ignore":
                        pass
                    elif conflictResolveMode == "preservenewest":
                        if (os.path.getmtime(file) - os.path.getmtime(new_filename) > 0):
                            send2trash.send2trash(file)
                        else:
                            send2trash.send2trash(new_filename)
                            os.rename(file, new_filename)
                    elif (conflictResolveMode == "merge"):
                        self.__merge_files(file, new_filename)
                        send2trash.send2trash(file)
                    else:
                        raise ValueError('Unknown conflict resolve mode')
            else:
                os.rename(file, new_filename)

    @GeneralUtilities.check_arguments
    def SCReplaceSubstringsInFilenames(self, folder: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            self.__process_file(file, substringInFilename, newSubstringInFilename, conflictResolveMode)

    @GeneralUtilities.check_arguments
    def __check_file(self, file: str, searchstring: str) -> None:
        bytes_ascii = bytes(searchstring, "ascii")
        # often called "unicode-encoding"
        bytes_utf16 = bytes(searchstring, "utf-16")
        bytes_utf8 = bytes(searchstring, "utf-8")
        with open(file, mode='rb') as file_object:
            content = file_object.read()
            if bytes_ascii in content:
                GeneralUtilities.write_message_to_stdout(file)
            elif bytes_utf16 in content:
                GeneralUtilities.write_message_to_stdout(file)
            elif bytes_utf8 in content:
                GeneralUtilities.write_message_to_stdout(file)

    @GeneralUtilities.check_arguments
    def SCSearchInFiles(self, folder: str, searchstring: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            self.__check_file(file, searchstring)

    @GeneralUtilities.check_arguments
    def __print_qr_code_by_csv_line(self, displayname: str, website: str, emailaddress: str, key: str, period: str) -> None:
        qrcode_content = f"otpauth://totp/{website}:{emailaddress}?secret={key}&issuer={displayname}&period={period}"
        GeneralUtilities.write_message_to_stdout(
            f"{displayname} ({emailaddress}):")
        GeneralUtilities.write_message_to_stdout(qrcode_content)
        qr = qrcode.QRCode()
        qr.add_data(qrcode_content)
        f = io.StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        GeneralUtilities.write_message_to_stdout(f.read())

    @GeneralUtilities.check_arguments
    def SCShow2FAAsQRCode(self, csvfile: str) -> None:
        separator_line = "--------------------------------------------------------"
        lines = GeneralUtilities.read_csv_file(csvfile, True)
        lines.sort(key=lambda items: ''.join(items).lower())
        for line in lines:
            GeneralUtilities.write_message_to_stdout(separator_line)
            self.__print_qr_code_by_csv_line(
                line[0], line[1], line[2], line[3], line[4])
        GeneralUtilities.write_message_to_stdout(separator_line)

    @GeneralUtilities.check_arguments
    def SCUploadFileToFileHost(self, file: str, host: str) -> int:
        try:
            GeneralUtilities.write_message_to_stdout(
                self.upload_file_to_file_host(file, host))
            return 0
        except Exception as exception:
            GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback)
            return 1

    @GeneralUtilities.check_arguments
    def SCFileIsAvailableOnFileHost(self, file: str) -> int:
        try:
            if self.file_is_available_on_file_host(file):
                GeneralUtilities.write_message_to_stdout(f"'{file}' is available")
                return 0
            else:
                GeneralUtilities.write_message_to_stdout(f"'{file}' is not available")
                return 1
        except Exception as exception:
            GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback)
            return 2

    @GeneralUtilities.check_arguments
    def SCCalculateBitcoinBlockHash(self, block_version_number: str, previousblockhash: str, transactionsmerkleroot: str, timestamp: str, target: str, nonce: str) -> str:
        # Example-values:
        # block_version_number: "00000020"
        # previousblockhash: "66720b99e07d284bd4fe67ff8c49a5db1dd8514fcdab61000000000000000000"
        # transactionsmerkleroot: "7829844f4c3a41a537b3131ca992643eaa9d093b2383e4cdc060ad7dc5481187"
        # timestamp: "51eb505a"
        # target: "c1910018"
        # nonce: "de19b302"
        header = str(block_version_number + previousblockhash + transactionsmerkleroot + timestamp + target + nonce)
        return binascii.hexlify(hashlib.sha256(hashlib.sha256(binascii.unhexlify(header)).digest()).digest()[::-1]).decode('utf-8')

    @GeneralUtilities.check_arguments
    def SCChangeHashOfProgram(self, inputfile: str) -> None:
        valuetoappend = str(uuid.uuid4())

        outputfile = inputfile + '.modified'

        shutil.copy2(inputfile, outputfile)
        with open(outputfile, 'a', encoding="utf-8") as file:
            # TODO use rcedit for .exe-files instead of appending valuetoappend ( https://github.com/electron/rcedit/ )
            # background: you can retrieve the "original-filename" from the .exe-file like discussed here:
            # https://security.stackexchange.com/questions/210843/ is-it-possible-to-change-original-filename-of-an-exe
            # so removing the original filename with rcedit is probably a better way to make it more difficult to detect the programname.
            # this would obviously also change the hashvalue of the program so appending a whitespace is not required anymore.
            file.write(valuetoappend)

    @GeneralUtilities.check_arguments
    def __adjust_folder_name(self, folder: str) -> str:
        result = os.path.dirname(folder).replace("\\", "/")
        if result == "/":
            return ""
        else:
            return result

    @GeneralUtilities.check_arguments
    def __create_iso(self, folder, iso_file) -> None:
        created_directories = []
        files_directory = "FILES"
        iso = pycdlib.PyCdlib()
        iso.new()
        files_directory = files_directory.upper()
        iso.add_directory("/" + files_directory)
        created_directories.append("/" + files_directory)
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                with (open(full_path, "rb").read()) as text_io_wrapper:
                    content = text_io_wrapper
                    path_in_iso = '/' + files_directory + \
                        self.__adjust_folder_name(
                            full_path[len(folder)::1]).upper()
                    if path_in_iso not in created_directories:
                        iso.add_directory(path_in_iso)
                        created_directories.append(path_in_iso)
                    iso.add_fp(BytesIO(content), len(content),
                               path_in_iso + '/' + file.upper() + ';1')
        iso.write(iso_file)
        iso.close()

    @GeneralUtilities.check_arguments
    def SCCreateISOFileWithObfuscatedFiles(self, inputfolder: str, outputfile: str, printtableheadline, createisofile, extensions) -> None:
        if (os.path.isdir(inputfolder)):
            namemappingfile = "name_map.csv"
            files_directory = inputfolder
            files_directory_obf = f"{files_directory}_Obfuscated"
            self.SCObfuscateFilesFolder(
                inputfolder, printtableheadline, namemappingfile, extensions)
            os.rename(namemappingfile, os.path.join(
                files_directory_obf, namemappingfile))
            if createisofile:
                self.__create_iso(files_directory_obf, outputfile)
                shutil.rmtree(files_directory_obf)
        else:
            raise ValueError(f"Directory not found: '{inputfolder}'")

    @GeneralUtilities.check_arguments
    def SCFilenameObfuscator(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if (obfuscate_all_files):
            obfuscate_file_extensions = None
        else:
            obfuscate_file_extensions = extensions.split(",")
        if (os.path.isdir(inputfolder)):
            printtableheadline = GeneralUtilities.string_to_boolean(
                printtableheadline)
            files = []
            if not os.path.isfile(namemappingfile):
                with open(namemappingfile, "a", encoding="utf-8"):
                    pass
            if printtableheadline:
                GeneralUtilities.append_line_to_file(
                    namemappingfile, "Original filename;new filename;SHA2-hash of file")
            for file in GeneralUtilities.absolute_file_paths(inputfolder):
                if os.path.isfile(os.path.join(inputfolder, file)):
                    if obfuscate_all_files or self.__extension_matchs(file, obfuscate_file_extensions):
                        files.append(file)
            for file in files:
                hash_value = GeneralUtilities.get_sha256_of_file(file)
                extension = Path(file).suffix
                new_file_name_without_path = str(uuid.uuid4())[0:8] + extension
                new_file_name = os.path.join(
                    os.path.dirname(file), new_file_name_without_path)
                os.rename(file, new_file_name)
                GeneralUtilities.append_line_to_file(namemappingfile, os.path.basename(
                    file) + ";" + new_file_name_without_path + ";" + hash_value)
        else:
            raise ValueError(f"Directory not found: '{inputfolder}'")

    @GeneralUtilities.check_arguments
    def __extension_matchs(self, file: str, obfuscate_file_extensions) -> bool:
        for extension in obfuscate_file_extensions:
            if file.lower().endswith("."+extension.lower()):
                return True
        return False

    @GeneralUtilities.check_arguments
    def SCHealthcheck(self, file: str) -> int:
        lines = GeneralUtilities.read_lines_from_file(file)
        for line in reversed(lines):
            if not GeneralUtilities.string_is_none_or_whitespace(line):
                if "RunningHealthy (" in line:  # TODO use regex
                    GeneralUtilities.write_message_to_stderr(
                        f"Healthy running due to line '{line}' in file '{file}'.")
                    return 0
                else:
                    GeneralUtilities.write_message_to_stderr(
                        f"Not healthy running due to line '{line}' in file '{file}'.")
                    return 1
        GeneralUtilities.write_message_to_stderr(
            f"No valid line found for healthycheck in file '{file}'.")
        return 2

    @GeneralUtilities.check_arguments
    def SCObfuscateFilesFolder(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if (obfuscate_all_files):
            obfuscate_file_extensions = None
        else:
            if "," in extensions:
                obfuscate_file_extensions = extensions.split(",")
            else:
                obfuscate_file_extensions = [extensions]
        newd = inputfolder+"_Obfuscated"
        shutil.copytree(inputfolder, newd)
        inputfolder = newd
        if (os.path.isdir(inputfolder)):
            for file in GeneralUtilities.absolute_file_paths(inputfolder):
                if obfuscate_all_files or self.__extension_matchs(file, obfuscate_file_extensions):
                    self.SCChangeHashOfProgram(file)
                    os.remove(file)
                    os.rename(file + ".modified", file)
            self.SCFilenameObfuscator(inputfolder, printtableheadline, namemappingfile, extensions)
        else:
            raise ValueError(f"Directory not found: '{inputfolder}'")

    @GeneralUtilities.check_arguments
    def get_services_from_yaml_file(self, yaml_file: str) -> list[str]:
        with open(yaml_file, encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
            services = loaded["services"]
            result = list(services.keys())
            return result

    @GeneralUtilities.check_arguments
    def kill_docker_container(self, container_name: str) -> None:
        self.run_program("docker", f"container rm -f {container_name}")

    @GeneralUtilities.check_arguments
    def get_docker_debian_version(self, image_tag: str) -> str:
        result = ScriptCollectionCore().run_program_argsasarray(
            "docker", ['run', f'debian:{image_tag}', 'bash', '-c', 'apt-get -y update && apt-get -y install lsb-release && lsb_release -cs'])
        result_line = GeneralUtilities.string_to_lines(result[1])[-2]
        return result_line

    @GeneralUtilities.check_arguments
    def get_latest_tor_version_of_debian_repository(self, debian_version: str) -> str:
        package_url: str = f"https://deb.torproject.org/torproject.org/dists/{debian_version}/main/binary-amd64/Packages"
        r = requests.get(package_url, timeout=5)
        if r.status_code != 200:
            raise ValueError(f"Checking for latest tor package resulted in HTTP-response-code {r.status_code}.")
        lines = GeneralUtilities.string_to_lines(GeneralUtilities.bytes_to_string(r.content))
        version_line_prefix = "Version: "
        version_content_line = [line for line in lines if line.startswith(version_line_prefix)][1]
        version_with_overhead = version_content_line[len(version_line_prefix):]
        tor_version = version_with_overhead.split("~")[0]
        return tor_version

    @GeneralUtilities.check_arguments
    def upload_file_to_file_host(self, file: str, host: str) -> int:
        if (host is None):
            return self.upload_file_to_random_filesharing_service(file)
        elif host == "anonfiles.com":
            return self.upload_file_to_anonfiles(file)
        elif host == "bayfiles.com":
            return self.upload_file_to_bayfiles(file)
        GeneralUtilities.write_message_to_stderr("Unknown host: "+host)
        return 1

    @GeneralUtilities.check_arguments
    def upload_file_to_random_filesharing_service(self, file: str) -> int:
        host = randrange(2)
        if host == 0:
            return self.upload_file_to_anonfiles(file)
        if host == 1:
            return self.upload_file_to_bayfiles(file)
        return 1

    @GeneralUtilities.check_arguments
    def upload_file_to_anonfiles(self, file) -> int:
        return self.upload_file_by_using_simple_curl_request("https://api.anonfiles.com/upload", file)

    @GeneralUtilities.check_arguments
    def upload_file_to_bayfiles(self, file) -> int:
        return self.upload_file_by_using_simple_curl_request("https://api.bayfiles.com/upload", file)

    @GeneralUtilities.check_arguments
    def upload_file_by_using_simple_curl_request(self, api_url: str, file: str) -> int:
        # TODO implement
        return 1

    @GeneralUtilities.check_arguments
    def file_is_available_on_file_host(self, file) -> int:
        # TODO implement
        return 1

    def run_testcases_for_python_project(self, repository_folder: str):
        self.run_program("coverage", "run -m pytest", repository_folder)
        self.run_program("coverage", "xml", repository_folder)
        GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder, "Other/TestCoverage"))
        coveragefile = os.path.join(repository_folder, "Other/TestCoverage/TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder,                "coverage.xml"), coveragefile)

    @GeneralUtilities.check_arguments
    def get_file_permission(self, file: str) -> str:
        """This function returns an usual octet-triple, for example "0700"."""
        ls_output = self.__ls(file)
        return self.__get_file_permission_helper(ls_output)

    @GeneralUtilities.check_arguments
    def __get_file_permission_helper(self, ls_output: str) -> str:
        permissions = ' '.join(ls_output.split()).split(' ')[0][1:]
        return str(self.__to_octet(permissions[0:3]))+str(self.__to_octet(permissions[3:6]))+str(self.__to_octet(permissions[6:9]))

    @GeneralUtilities.check_arguments
    def __to_octet(self, string: str) -> int:
        return int(self.__to_octet_helper(string[0])+self.__to_octet_helper(string[1])+self.__to_octet_helper(string[2]), 2)

    @GeneralUtilities.check_arguments
    def __to_octet_helper(self, string: str) -> str:
        if (string == "-"):
            return "0"
        else:
            return "1"

    @GeneralUtilities.check_arguments
    def get_file_owner(self, file: str) -> str:
        """This function returns the user and the group in the format "user:group"."""
        ls_output = self.__ls(file)
        return self.__get_file_owner_helper(ls_output)

    @GeneralUtilities.check_arguments
    def __get_file_owner_helper(self, ls_output: str) -> str:
        try:
            splitted = ' '.join(ls_output.split()).split(' ')
            return f"{splitted[2]}:{splitted[3]}"
        except Exception as exception:
            raise ValueError(
                f"ls-output '{ls_output}' not parsable") from exception

    @GeneralUtilities.check_arguments
    def get_file_owner_and_file_permission(self, file: str) -> str:
        ls_output = self.__ls(file)
        return [self.__get_file_owner_helper(ls_output), self.__get_file_permission_helper(ls_output)]

    @GeneralUtilities.check_arguments
    def __ls(self, file: str) -> str:
        file = file.replace("\\", "/")
        GeneralUtilities.assert_condition(os.path.isfile(file) or os.path.isdir(
            file), f"Can not execute 'ls' because '{file}' does not exist")
        result = self.run_program_argsasarray("ls", ["-ld", file])
        GeneralUtilities.assert_condition(result[0] == 0, f"'ls -ld {file}' resulted in exitcode {str(result[0])}. StdErr: {result[2]}")
        GeneralUtilities.assert_condition(not GeneralUtilities.string_is_none_or_whitespace(
            result[1]), f"'ls' of '{file}' had an empty output. StdErr: '{result[2]}'")
        return result[1]

    @GeneralUtilities.check_arguments
    def set_permission(self, file_or_folder: str, permissions: str, recursive: bool = False) -> None:
        """This function expects an usual octet-triple, for example "700"."""
        args = []
        if recursive:
            args.append("--recursive")
        args.append(permissions)
        args.append(file_or_folder)
        self.run_program_argsasarray("chmod", args)

    @GeneralUtilities.check_arguments
    def set_owner(self, file_or_folder: str, owner: str, recursive: bool = False, follow_symlinks: bool = False) -> None:
        """This function expects the user and the group in the format "user:group"."""
        args = []
        if recursive:
            args.append("--recursive")
        if follow_symlinks:
            args.append("--no-dereference")
        args.append(owner)
        args.append(file_or_folder)
        self.run_program_argsasarray("chown", args)

    # <run programs>

    @GeneralUtilities.check_arguments
    def __run_program_argsasarray_async_helper(self, program: str, arguments_as_array: list[str] = [], working_directory: str = None, verbosity: int = 1, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, custom_argument: object = None, interactive: bool = False) -> Popen:
        # Verbosity:
        # 0=Quiet (No output will be printed.)
        # 1=Normal (If the exitcode of the executed program is not 0 then the StdErr will be printed.)
        # 2=Full (Prints StdOut and StdErr of the executed program.)
        # 3=Verbose (Same as "Full" but with some more information.)

        if isinstance(self.program_runner, ProgramRunnerEpew):
            custom_argument = CustomEpewArgument(print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, verbosity, arguments_for_log)
        popen: Popen = self.program_runner.run_program_argsasarray_async_helper(program, arguments_as_array, working_directory, custom_argument, interactive)
        return popen

    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid

    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self, program: str, arguments_as_array: list[str] = [], working_directory: str = None, verbosity: int = 1, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, throw_exception_if_exitcode_is_not_zero: bool = True, custom_argument: object = None, interactive: bool = False) -> tuple[int, str, str, int]:
        # verbosity 1: No output will be logged.
        # verbosity 2: If the exitcode of the executed program is not 0 then the StdErr will be logged. This is supposed to be the default verbosity-level.
        # verbosity 3: Logs and prints StdOut and StdErr of the executed program in realtime.
        # verbosity 4: Same as loglevel 3 but with some more overhead-information.
        try:
            arguments_as_str = ' '.join(arguments_as_array)
            mock_loader_result = self.__try_load_mock(program, arguments_as_str, working_directory)
            if mock_loader_result[0]:
                return mock_loader_result[1]

            working_directory = self.__adapt_workingdirectory(working_directory)

            if arguments_for_log is None:
                arguments_for_log = arguments_as_array

            arguments_for_log_as_string: str = ' '.join(arguments_for_log)
            cmd = f'{working_directory}>{program} {arguments_for_log_as_string}'

            if GeneralUtilities.string_is_none_or_whitespace(title):
                info_for_log = cmd
            else:
                info_for_log = title

            if verbosity >= 3:
                GeneralUtilities.write_message_to_stdout(f"Run '{info_for_log}'.")
            with self.__run_program_argsasarray_async_helper(program, arguments_as_array, working_directory, verbosity, print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, custom_argument, interactive) as process:
                pid = process.pid

                stdout_lines = list[str]()
                stderr_lines = list[str]()

                live_console_output_printing = 2 < verbosity and interactive

                log_to_file = log_file is not None
                if log_to_file:
                    GeneralUtilities.ensure_file_exists(log_file)

                if interactive:
                    # there are 2 issues in this part:
                    # 1.: ctrl+c
                    # 2.: sometimes this function does not terminate even if the started process exited
                    def stream_process(process) -> bool:
                        try:
                            go: bool = process.poll() is None

                            stdoutreader: BufferedReader = process.stdout
                            if stdoutreader.readable():
                                stdoutresultb: bytes = stdoutreader.read()
                                stdoutresult = GeneralUtilities.bytes_to_string(
                                    stdoutresultb)
                                stdoutlines = GeneralUtilities.string_to_lines(stdoutresult)
                                for line in stdoutlines:
                                    line_stripped = line.replace("\r", "").strip()
                                    if len(line_stripped) > 0:
                                        line_str = line_stripped
                                        stdout_lines.append(line_str)
                                        if live_console_output_printing:
                                            GeneralUtilities.write_message_to_stdout(line_str)
                                        if log_to_file:
                                            GeneralUtilities.append_line_to_file(
                                                log_file, line_str)

                            stderrreader: BufferedReader = process.stderr
                            if stderrreader.readable():
                                stderrresultb: bytes = stderrreader.read()
                                stderrresult = GeneralUtilities.bytes_to_string(stderrresultb)
                                stderrlines = GeneralUtilities.string_to_lines(stderrresult)
                                for line in stderrlines:
                                    line_stripped = line.replace("\r", "").strip()
                                    if len(line_stripped) > 0:
                                        line_str = line_stripped
                                        stderr_lines.append(line_str)
                                        if live_console_output_printing:
                                            if print_errors_as_information:
                                                GeneralUtilities.write_message_to_stdout(line_str)
                                            else:
                                                GeneralUtilities.write_message_to_stderr(line_str)
                                        if log_to_file:
                                            GeneralUtilities.append_line_to_file(log_file, line_str)

                            return go
                        except Exception:
                            return False

                    while stream_process(process):
                        time.sleep(0.1)

                    exit_code = process.poll()
                    stdout = '\n'.join(stdout_lines)
                    stderr = '\n'.join(stderr_lines)
                else:
                    stdout, stderr = process.communicate()
                    exit_code = process.wait()
                    stdout = GeneralUtilities.bytes_to_string(stdout).replace('\r', '')
                    stderr = GeneralUtilities.bytes_to_string(stderr).replace('\r', '')

                if throw_exception_if_exitcode_is_not_zero and exit_code != 0:
                    raise ValueError(f"Program '{working_directory}>{program} {arguments_for_log_as_string}' resulted in exitcode {exit_code}. (StdOut: '{stdout}', StdErr: '{stderr}')")

                result = (exit_code, stdout, stderr, pid)
                return result
        except Exception as e:
            raise e

    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @GeneralUtilities.check_arguments
    def run_program(self, program: str, arguments:  str = "", working_directory: str = None, verbosity: int = 1, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, throw_exception_if_exitcode_is_not_zero: bool = True, custom_argument: object = None, interactive: bool = False) -> tuple[int, str, str, int]:
        return self.run_program_argsasarray(program, GeneralUtilities.arguments_to_array(arguments), working_directory, verbosity, print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, throw_exception_if_exitcode_is_not_zero, custom_argument, interactive)

    # Return-values program_runner: Pid
    @GeneralUtilities.check_arguments
    def run_program_argsasarray_async(self, program: str, arguments_as_array: list[str] = [], working_directory: str = None, verbosity: int = 1, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, custom_argument: object = None, interactive: bool = False) -> int:
        mock_loader_result = self.__try_load_mock(program, ' '.join(arguments_as_array), working_directory)
        if mock_loader_result[0]:
            return mock_loader_result[1]
        process: Popen = self.__run_program_argsasarray_async_helper(program, arguments_as_array, working_directory, verbosity, print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, custom_argument, interactive)
        return process.pid

    # Return-values program_runner: Pid
    @GeneralUtilities.check_arguments
    def run_program_async(self, program: str, arguments: str = "",  working_directory: str = None, verbosity: int = 1, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, custom_argument: object = None, interactive: bool = False) -> int:
        return self.run_program_argsasarray_async(program, GeneralUtilities.arguments_to_array(arguments), working_directory, verbosity, print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, custom_argument, interactive)

    @GeneralUtilities.check_arguments
    def __try_load_mock(self, program: str, arguments: str, working_directory: str) -> tuple[bool, tuple[int, str, str, int]]:
        if self.mock_program_calls:
            try:
                return [True, self.__get_mock_program_call(program, arguments, working_directory)]
            except LookupError:
                if not self.execute_program_really_if_no_mock_call_is_defined:
                    raise
        return [False, None]

    @GeneralUtilities.check_arguments
    def __adapt_workingdirectory(self, workingdirectory: str) -> str:
        if workingdirectory is None:
            return os.getcwd()
        else:
            return GeneralUtilities.resolve_relative_path_from_current_working_directory(workingdirectory)

    @GeneralUtilities.check_arguments
    def verify_no_pending_mock_program_calls(self):
        if (len(self.__mocked_program_calls) > 0):
            raise AssertionError(
                "The following mock-calls were not called:\n"+",\n    ".join([self.__format_mock_program_call(r) for r in self.__mocked_program_calls]))

    @GeneralUtilities.check_arguments
    def __format_mock_program_call(self, r) -> str:
        r: ScriptCollectionCore.__MockProgramCall = r
        return f"'{r.workingdirectory}>{r.program} {r.argument}' (" \
            f"exitcode: {GeneralUtilities.str_none_safe(str(r.exit_code))}, " \
            f"pid: {GeneralUtilities.str_none_safe(str(r.pid))}, "\
            f"stdout: {GeneralUtilities.str_none_safe(str(r.stdout))}, " \
            f"stderr: {GeneralUtilities.str_none_safe(str(r.stderr))})"

    @GeneralUtilities.check_arguments
    def register_mock_program_call(self, program: str, argument: str, workingdirectory: str, result_exit_code: int, result_stdout: str, result_stderr: str, result_pid: int, amount_of_expected_calls=1):
        "This function is for test-purposes only"
        for _ in itertools.repeat(None, amount_of_expected_calls):
            mock_call = ScriptCollectionCore.__MockProgramCall()
            mock_call.program = program
            mock_call.argument = argument
            mock_call.workingdirectory = workingdirectory
            mock_call.exit_code = result_exit_code
            mock_call.stdout = result_stdout
            mock_call.stderr = result_stderr
            mock_call.pid = result_pid
            self.__mocked_program_calls.append(mock_call)

    @GeneralUtilities.check_arguments
    def __get_mock_program_call(self, program: str, argument: str, workingdirectory: str):
        result: ScriptCollectionCore.__MockProgramCall = None
        for mock_call in self.__mocked_program_calls:
            if ((re.match(mock_call.program, program) is not None)
               and (re.match(mock_call.argument, argument) is not None)
               and (re.match(mock_call.workingdirectory, workingdirectory) is not None)):
                result = mock_call
                break
        if result is None:
            raise LookupError(
                f"Tried to execute mock-call '{workingdirectory}>{program} {argument}' but no mock-call was defined for that execution")
        else:
            self.__mocked_program_calls.remove(result)
            return (result.exit_code, result.stdout, result.stderr, result.pid)

    @GeneralUtilities.check_arguments
    class __MockProgramCall:
        program: str
        argument: str
        workingdirectory: str
        exit_code: int
        stdout: str
        stderr: str
        pid: int

    # </run programs>

    @GeneralUtilities.check_arguments
    def extract_archive_with_7z(self, unzip_program_file: str, zipfile: str, password: str, output_directory: str) -> None:
        password_set = not password is None
        file_name = Path(zipfile).name
        file_folder = os.path.dirname(zipfile)
        argument = "x"
        if password_set:
            argument = f"{argument} -p\"{password}\""
        argument = f"{argument} -o {output_directory}"
        argument = f"{argument} {file_name}"
        return self.run_program(unzip_program_file, argument, file_folder)

    @GeneralUtilities.check_arguments
    def get_internet_time(self) -> datetime:
        response = ntplib.NTPClient().request('pool.ntp.org')
        return datetime.fromtimestamp(response.tx_time)

    @GeneralUtilities.check_arguments
    def system_time_equals_internet_time(self, maximal_tolerance_difference: timedelta) -> bool:
        return abs(datetime.now() - self.get_internet_time()) < maximal_tolerance_difference

    @GeneralUtilities.check_arguments
    def system_time_equals_internet_time_with_default_tolerance(self) -> bool:
        return self.system_time_equals_internet_time(self.__get_default_tolerance_for_system_time_equals_internet_time())

    @GeneralUtilities.check_arguments
    def check_system_time(self, maximal_tolerance_difference: timedelta):
        if not self.system_time_equals_internet_time(maximal_tolerance_difference):
            raise ValueError("System time may be wrong")

    @GeneralUtilities.check_arguments
    def check_system_time_with_default_tolerance(self) -> None:
        self.check_system_time(
            self.__get_default_tolerance_for_system_time_equals_internet_time())

    @GeneralUtilities.check_arguments
    def __get_default_tolerance_for_system_time_equals_internet_time(self) -> timedelta:
        return timedelta(hours=0, minutes=0, seconds=3)

    @GeneralUtilities.check_arguments
    def increment_version(self, input_version: str, increment_major: bool, increment_minor: bool, increment_patch: bool) -> str:
        splitted = input_version.split(".")
        GeneralUtilities.assert_condition(len(splitted) == 3, f"Version '{input_version}' does not have the 'major.minor.patch'-pattern.")
        major = int(splitted[0])
        minor = int(splitted[1])
        patch = int(splitted[2])
        if increment_major:
            major = major+1
        if increment_minor:
            minor = minor+1
        if increment_patch:
            patch = patch+1
        return f"{major}.{minor}.{patch}"

    @GeneralUtilities.check_arguments
    def get_semver_version_from_gitversion(self, repository_folder: str) -> str:
        if (self.git_repository_has_commits(repository_folder)):
            result = self.get_version_from_gitversion(repository_folder, "MajorMinorPatch")
            if self.git_repository_has_uncommitted_changes(repository_folder):
                if self.get_current_git_branch_has_tag(repository_folder):
                    id_of_latest_tag = self.git_get_commitid_of_tag(
                        repository_folder, self.get_latest_git_tag(repository_folder))
                    current_commit = self.git_get_commit_id(repository_folder)
                    current_commit_is_on_latest_tag = id_of_latest_tag == current_commit
                    if current_commit_is_on_latest_tag:
                        result = self.increment_version(
                            result, False, False, True)
        else:
            result = "0.1.0"
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def is_patch_version(version_string: str) -> bool:
        return not version_string.endswith(".0")

    @GeneralUtilities.check_arguments
    def get_version_from_gitversion(self, folder: str, variable: str) -> str:
        # called twice as workaround for issue 1877 in gitversion ( https://github.com/GitTools/GitVersion/issues/1877 )
        result = self.run_program_argsasarray("gitversion", ["/showVariable", variable], folder, verbosity=0)
        result = self.run_program_argsasarray("gitversion", ["/showVariable", variable], folder, verbosity=0)
        result = GeneralUtilities.strip_new_line_character(result[1])

        return result

    @GeneralUtilities.check_arguments
    def generate_certificate_authority(self, folder: str, name: str, subj_c: str, subj_st: str, subj_l: str, subj_o: str, subj_ou: str, days_until_expire: int = None, password: str = None) -> None:
        if days_until_expire is None:
            days_until_expire = 1825
        if password is None:
            password = GeneralUtilities.generate_password()
        GeneralUtilities.ensure_directory_exists(folder)
        self.run_program("openssl", f'req -new -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -days {days_until_expire} -nodes -x509 -subj /C={subj_c}/ST={subj_st}/L={subj_l}/O={subj_o}/CN={name}/OU={subj_ou} -passout pass:{password} -keyout {name}.key -out {name}.crt', folder)

    @GeneralUtilities.check_arguments
    def generate_certificate(self, folder: str,  domain: str, filename: str, subj_c: str, subj_st: str, subj_l: str, subj_o: str, subj_ou: str, days_until_expire: int = None, password: str = None) -> None:
        if days_until_expire is None:
            days_until_expire = 397
        if password is None:
            password = GeneralUtilities.generate_password()
        rsa_key_length = 4096
        self.run_program("openssl", f'genrsa -out {filename}.key {rsa_key_length}', folder)
        self.run_program("openssl", f'req -new -subj /C={subj_c}/ST={subj_st}/L={subj_l}/O={subj_o}/CN={domain}/OU={subj_ou} -x509 -key {filename}.key -out {filename}.unsigned.crt -days {days_until_expire}', folder)
        self.run_program("openssl", f'pkcs12 -export -out {filename}.selfsigned.pfx -password pass:{password} -inkey {filename}.key -in {filename}.unsigned.crt', folder)
        GeneralUtilities.write_text_to_file(
            os.path.join(folder, f"{filename}.password"), password)
        GeneralUtilities.write_text_to_file(os.path.join(folder, f"{filename}.san.conf"), f"""[ req ]
default_bits        = {rsa_key_length}
distinguished_name  = req_distinguished_name
req_extensions      = v3_req
default_md          = sha256
dirstring_type      = nombstr
prompt              = no

[ req_distinguished_name ]
countryName         = {subj_c}
stateOrProvinceName = {subj_st}
localityName        = {subj_l}
organizationName    = {subj_o}
organizationUnit    = {subj_ou}
commonName          = {domain}

[v3_req]
subjectAltName      = @subject_alt_name

[ subject_alt_name ]
DNS                 = {domain}
""")

    @GeneralUtilities.check_arguments
    def generate_certificate_sign_request(self, folder: str, domain: str, filename: str, subj_c: str, subj_st: str, subj_l: str, subj_o: str, subj_ou: str) -> None:
        self.run_program(
            "openssl", f'req -new -subj /C={subj_c}/ST={subj_st}/L={subj_l}/O={subj_o}/CN={domain}/OU={subj_ou} -key {filename}.key -out {filename}.csr -config {filename}.san.conf', folder)

    @GeneralUtilities.check_arguments
    def sign_certificate(self, folder: str, ca_folder: str, ca_name: str, domain: str, filename: str, days_until_expire: int = None) -> None:
        if days_until_expire is None:
            days_until_expire = 397
        ca = os.path.join(ca_folder, ca_name)
        password_file = os.path.join(folder, f"{filename}.password")
        password = GeneralUtilities.read_text_from_file(password_file)
        self.run_program("openssl", f'x509 -req -in {filename}.csr -CA {ca}.crt -CAkey {ca}.key -CAcreateserial -CAserial {ca}.srl -out {filename}.crt -days {days_until_expire} -sha256 -extensions v3_req -extfile {filename}.san.conf', folder)
        self.run_program("openssl", f'pkcs12 -export -out {filename}.pfx -inkey {filename}.key -in {filename}.crt -password pass:{password}', folder)

    @GeneralUtilities.check_arguments
    def update_dependencies_of_python_in_requirementstxt_file(self, file: str, verbosity: int):
        lines = GeneralUtilities.read_lines_from_file(file)
        new_lines = []
        for line in lines:
            if GeneralUtilities.string_has_content(line):
                new_lines.append(self.__get_updated_line_for_python_requirements(line.strip()))
        GeneralUtilities.write_lines_to_file(file, new_lines)

    @GeneralUtilities.check_arguments
    def __get_updated_line_for_python_requirements(self, line: str) -> str:
        if "==" in line or "<" in line:
            return line
        elif ">" in line:
            try:
                # line is something like "cyclonedx-bom>=2.0.2" and the function must return with the updated version
                # (something like "cyclonedx-bom>=3.11.0" for example)
                package = line.split(">")[0]
                operator = ">=" if ">=" in line else ">"
                response = requests.get(f'https://pypi.org/pypi/{package}/json', timeout=5)
                latest_version = response.json()['info']['version']
                return package+operator+latest_version
            except:
                return line
        else:
            raise ValueError(f'Unexpected line in requirements-file: "{line}"')

    @GeneralUtilities.check_arguments
    def update_dependencies_of_python_in_setupcfg_file(self, setup_cfg_file: str, verbosity: int):
        lines = GeneralUtilities.read_lines_from_file(setup_cfg_file)
        new_lines = []
        requirement_parsing_mode = False
        for line in lines:
            new_line = line
            if (requirement_parsing_mode):
                if ("<" in line or "=" in line or ">" in line):
                    updated_line = f"    {self.__get_updated_line_for_python_requirements(line.strip())}"
                    new_line = updated_line
                else:
                    requirement_parsing_mode = False
            else:
                if line.startswith("install_requires ="):
                    requirement_parsing_mode = True
            new_lines.append(new_line)
        GeneralUtilities.write_lines_to_file(setup_cfg_file, new_lines)

    @GeneralUtilities.check_arguments
    def update_dependencies_of_dotnet_project(self, csproj_file: str, verbosity: int, ignored_dependencies: list[str]):
        folder = os.path.dirname(csproj_file)
        csproj_filename = os.path.basename(csproj_file)
        GeneralUtilities.write_message_to_stderr(f"Check for updates in {csproj_filename}")
        result = self.run_program("dotnet", f"list {csproj_filename} package --outdated", folder)
        for line in result[1].replace("\r", "").split("\n"):
            # Relevant output-lines are something like "    > NJsonSchema             10.7.0        10.7.0      10.9.0"
            if ">" in line:
                package_name = line.replace(">", "").strip().split(" ")[0]
                if not (ignored_dependencies in package_name):
                    GeneralUtilities.write_message_to_stderr(f"Update package {package_name}")
                    self.run_program("dotnet", f"add {csproj_filename} package {package_name}", folder)

    @GeneralUtilities.check_arguments
    def create_deb_package(self, toolname: str, binary_folder: str, control_file_content: str, deb_output_folder: str, verbosity: int, permission_of_executable_file_as_octet_triple: int) -> None:

        # prepare
        GeneralUtilities.ensure_directory_exists(deb_output_folder)
        temp_folder = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        GeneralUtilities.ensure_directory_exists(temp_folder)
        bin_folder = binary_folder
        tool_content_folder_name = toolname+"Content"

        # create folder
        GeneralUtilities.ensure_directory_exists(temp_folder)
        control_content_folder_name = "controlcontent"
        packagecontent_control_folder = os.path.join(temp_folder, control_content_folder_name)
        GeneralUtilities.ensure_directory_exists(packagecontent_control_folder)
        data_content_folder_name = "datacontent"
        packagecontent_data_folder = os.path.join(temp_folder, data_content_folder_name)
        GeneralUtilities.ensure_directory_exists(packagecontent_data_folder)
        entireresult_content_folder_name = "entireresultcontent"
        packagecontent_entireresult_folder = os.path.join(temp_folder, entireresult_content_folder_name)
        GeneralUtilities.ensure_directory_exists(packagecontent_entireresult_folder)

        # create "debian-binary"-file
        debianbinary_file = os.path.join(
            packagecontent_entireresult_folder, "debian-binary")
        GeneralUtilities.ensure_file_exists(debianbinary_file)
        GeneralUtilities.write_text_to_file(debianbinary_file, "2.0\n")

        # create control-content

        #  conffiles
        conffiles_file = os.path.join(packagecontent_control_folder, "conffiles")
        GeneralUtilities.ensure_file_exists(conffiles_file)

        #  postinst-script
        postinst_file = os.path.join(packagecontent_control_folder, "postinst")
        GeneralUtilities.ensure_file_exists(postinst_file)
        exe_file = f"/usr/bin/{tool_content_folder_name}/{toolname}"
        link_file = f"/usr/bin/{toolname.lower()}"
        permission = str(permission_of_executable_file_as_octet_triple)
        GeneralUtilities.write_text_to_file(postinst_file, f"""#!/bin/sh
    ln -s {exe_file} {link_file}
    chmod {permission} {exe_file}
    chmod {permission} {link_file}
    """)

        #  control
        control_file = os.path.join(packagecontent_control_folder, "control")
        GeneralUtilities.ensure_file_exists(control_file)
        GeneralUtilities.write_text_to_file(control_file, control_file_content)

        #  md5sums
        md5sums_file = os.path.join(packagecontent_control_folder, "md5sums")
        GeneralUtilities.ensure_file_exists(md5sums_file)

        # create data-content

        #  copy binaries
        usr_bin_folder = os.path.join(packagecontent_data_folder, "usr/bin")
        GeneralUtilities.ensure_directory_exists(usr_bin_folder)
        usr_bin_content_folder = os.path.join(
            usr_bin_folder, tool_content_folder_name)
        GeneralUtilities.copy_content_of_folder(bin_folder, usr_bin_content_folder)

        # create debfile
        deb_filename = f"{toolname}.deb"
        self.run_program_argsasarray("tar", ["czf", f"../{entireresult_content_folder_name}/control.tar.gz", "*"], packagecontent_control_folder, verbosity=verbosity)
        self.run_program_argsasarray("tar", ["czf", f"../{entireresult_content_folder_name}/data.tar.gz", "*"], packagecontent_data_folder, verbosity=verbosity)
        self.run_program_argsasarray("ar", ["r", deb_filename, "debian-binary", "control.tar.gz",
                                     "data.tar.gz"], packagecontent_entireresult_folder, verbosity=verbosity)
        result_file = os.path.join(packagecontent_entireresult_folder, deb_filename)
        shutil.copy(result_file, os.path.join(deb_output_folder, deb_filename))

        # cleanup
        GeneralUtilities.ensure_directory_does_not_exist(temp_folder)

    @GeneralUtilities.check_arguments
    def update_year_in_copyright_tags(self, file: str) -> None:
        current_year = str(datetime.now().year)
        lines = GeneralUtilities.read_lines_from_file(file)
        lines_result = []
        for line in lines:
            if match := re.search("(.*<[Cc]opyright>.*)\\d\\d\\d\\d(.*<\\/[Cc]opyright>.*)", line):
                part1 = match.group(1)
                part2 = match.group(2)
                adapted = part1+current_year+part2
            else:
                adapted = line
            lines_result.append(adapted)
        GeneralUtilities.write_lines_to_file(file, lines_result)

    @GeneralUtilities.check_arguments
    def update_year_in_first_line_of_file(self, file: str) -> None:
        current_year = str(datetime.now().year)
        lines = GeneralUtilities.read_lines_from_file(file)
        lines[0] = re.sub("\\d\\d\\d\\d", current_year, lines[0])
        GeneralUtilities.write_lines_to_file(file, lines)

    @GeneralUtilities.check_arguments
    def get_external_ip(self, proxy: str) -> str:
        information = self.get_externalnetworkinformation_as_json_string(proxy)
        parsed = json.loads(information)
        return parsed.ip

    @GeneralUtilities.check_arguments
    def get_country_of_external_ip(self, proxy: str) -> str:
        information = self.get_externalnetworkinformation_as_json_string(proxy)
        parsed = json.loads(information)
        return parsed.country

    @GeneralUtilities.check_arguments
    def get_externalnetworkinformation_as_json_string(self, proxy: str) -> str:
        proxies = None
        if GeneralUtilities.string_has_content(proxy):
            proxies = {"http": proxy}
        response = requests.get('https://ipinfo.io',
                                proxies=proxies, timeout=5)
        network_information_as_json_string = GeneralUtilities.bytes_to_string(
            response.content)
        return network_information_as_json_string
