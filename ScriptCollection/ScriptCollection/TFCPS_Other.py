from datetime import datetime
from graphlib import TopologicalSorter
import os
from pathlib import Path
import shutil
import re
import sys
import tempfile
import uuid
import requests
from packaging import version
from lxml import etree
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore
from .SCLog import  LogLevel

class TFCPS_Other:

    __sc:ScriptCollectionCore=ScriptCollectionCore()

    def __init__(self,sc:ScriptCollectionCore):
        self.__sc=sc

    @GeneralUtilities.check_arguments
    def codeunit_is_enabled(self, codeunit_file: str) -> bool:
        root: etree._ElementTree = etree.parse(codeunit_file)
        return GeneralUtilities.string_to_boolean(str(root.xpath('//cps:codeunit/@enabled', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0]))

    @GeneralUtilities.check_arguments
    def ensure_cyclonedxcli_is_available(self, target_folder: str) -> None:
        local_filename = "cyclonedx-cli"
        filename_on_github: str
        if GeneralUtilities.current_system_is_windows():
            filename_on_github = "cyclonedx-win-x64.exe"
            local_filename = local_filename+".exe"
        else:
            filename_on_github = "cyclonedx-linux-x64"
        self.ensure_file_from_github_assets_is_available_with_retry(target_folder, "CycloneDX", "cyclonedx-cli", "CycloneDXCLI", local_filename, lambda latest_version: filename_on_github)

    @GeneralUtilities.check_arguments
    def ensure_file_from_github_assets_is_available_with_retry(self, target_folder: str, githubuser: str, githubprojectname: str, resource_name: str, local_filename: str, get_filename_on_github, amount_of_attempts: int = 5) -> None:
        GeneralUtilities.retry_action(lambda: self.ensure_file_from_github_assets_is_available(target_folder, githubuser, githubprojectname, resource_name, local_filename, get_filename_on_github), amount_of_attempts)

    @GeneralUtilities.check_arguments
    def ensure_file_from_github_assets_is_available(self, target_folder: str, githubuser: str, githubprojectname: str, resource_name: str, local_filename: str, get_filename_on_github) -> None:
        resource_folder = os.path.join(target_folder, "Other", "Resources", resource_name)
        internet_connection_is_available = GeneralUtilities.internet_connection_is_available()
        file = f"{resource_folder}/{local_filename}"
        file_exists = os.path.isfile(file)
        self.__sc.log.log(f"Download Asset \"{githubuser}/{githubprojectname}: {resource_name}\" from GitHub...", LogLevel.Debug)
        if internet_connection_is_available:  # Load/Update
            GeneralUtilities.ensure_directory_does_not_exist(resource_folder)
            GeneralUtilities.ensure_directory_exists(resource_folder)
            headers = {'Cache-Control': 'no-cache', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Safari/537.36'}
            self.__add_github_api_key_if_available(headers)
            url = f"https://api.github.com/repos/{githubuser}/{githubprojectname}/releases/latest"
            self.__sc.log.log(f"Download \"{url}\"...", LogLevel.Diagnostic)
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=(10, 10))
            latest_version = response.json()["tag_name"]
            filename_on_github = get_filename_on_github(latest_version)
            link = f"https://github.com/{githubuser}/{githubprojectname}/releases/download/{latest_version}/{filename_on_github}"
            with requests.get(link, headers=headers, stream=True, allow_redirects=True,  timeout=(5, 300)) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        show_progress: bool = False
                        if show_progress:
                            downloaded += len(chunk)
                            if total_size:
                                percent = downloaded / total_size * 100
                                sys.stdout.write(f"\rDownload: {percent:.2f}%")
                                sys.stdout.flush()
            self.__sc.log.log(f"Downloaded \"{url}\".", LogLevel.Diagnostic)
        else:
            if file_exists:
                self.__sc.log.log(f"Can not check for updates of {resource_name} due to missing internet-connection.", LogLevel.Warning)
            else:
                raise ValueError(f"Can not download {resource_name}.")

    def __add_github_api_key_if_available(self, headers: dict):
        token = os.getenv("GITHUB_TOKEN")
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        else:
            user_folder = str(Path.home())
            github_token_file: str = str(os.path.join(user_folder, ".github", "token.txt"))
            if os.path.isfile(github_token_file):
                token = GeneralUtilities.read_text_from_file(github_token_file)
                headers["Authorization"] = f"Bearer {token}"
        return headers

    
    @GeneralUtilities.check_arguments
    def is_codeunit_folder(self, codeunit_folder: str) -> bool:
        repo_folder = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        if not self.__sc.is_git_repository(repo_folder):
            return False
        codeunit_name = os.path.basename(codeunit_folder)
        codeunit_file: str = os.path.join(codeunit_folder, f"{codeunit_name}.codeunit.xml")
        if not os.path.isfile(codeunit_file):
            return False
        return True

    @GeneralUtilities.check_arguments
    def assert_is_codeunit_folder(self, codeunit_folder: str) -> str:
        repo_folder = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        if not self.__sc.is_git_repository(repo_folder):
            raise ValueError(f"'{codeunit_folder}' can not be a valid codeunit-folder because '{repo_folder}' is not a git-repository.")
        codeunit_name = os.path.basename(codeunit_folder)
        codeunit_file: str = os.path.join(codeunit_folder, f"{codeunit_name}.codeunit.xml")
        if not os.path.isfile(codeunit_file):
            raise ValueError(f"'{codeunit_folder}' is no codeunit-folder because '{codeunit_file}' does not exist.")

    @GeneralUtilities.check_arguments
    def get_codeunits(self, repository_folder: str, ignore_disabled_codeunits: bool = True) -> list[str]:
        codeunits_with_dependent_codeunits: dict[str, set[str]] = dict[str, set[str]]()
        subfolders = GeneralUtilities.get_direct_folders_of_folder(repository_folder)
        for subfolder in subfolders:
            codeunit_name: str = os.path.basename(subfolder)
            codeunit_file = os.path.join(subfolder, f"{codeunit_name}.codeunit.xml")
            if os.path.exists(codeunit_file):
                if ignore_disabled_codeunits and not self.codeunit_is_enabled(codeunit_file):
                    continue
                codeunits_with_dependent_codeunits[codeunit_name] = self.get_dependent_code_units(codeunit_file)
        sorted_codeunits = self._internal_get_sorted_codeunits_by_dict(codeunits_with_dependent_codeunits)
        #TODO show warning somehow for enabled codeunits which depends on ignored codeunits
        return sorted_codeunits

    @GeneralUtilities.check_arguments
    def get_dependent_code_units(self, codeunit_file: str) -> list[str]:
        root: etree._ElementTree = etree.parse(codeunit_file)
        result = set(root.xpath('//cps:dependentcodeunit/text()', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'}))
        result = sorted(result)
        return result

    @GeneralUtilities.check_arguments
    def _internal_get_sorted_codeunits_by_dict(self, codeunits: dict[str, set[str]]) -> list[str]:
        sorted_codeunits = {
            node: sorted(codeunits[node])
            for node in sorted(codeunits)
        }

        ts = TopologicalSorter()
        for node, deps in sorted_codeunits.items():
            ts.add(node, *deps)

        result_typed = list(ts.static_order())
        result = [str(item) for item in result_typed]
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_sort_reference_folder(folder1: str, folder2: str) -> int:
        """Returns a value greater than 0 if and only if folder1 has a base-folder-name with a with a higher version than the base-folder-name of folder2.
        Returns a value lower than 0 if and only if folder1 has a base-folder-name with a with a lower version than the base-folder-name of folder2.
        Returns 0 if both values are equal."""
        if (folder1 == folder2):
            return 0

        version_identifier_1 = os.path.basename(folder1)
        if version_identifier_1 == "Latest":
            return -1
        version_identifier_1 = version_identifier_1[1:]

        version_identifier_2 = os.path.basename(folder2)
        if version_identifier_2 == "Latest":
            return 1
        version_identifier_2 = version_identifier_2[1:]

        if version.parse(version_identifier_1) < version.parse(version_identifier_2):
            return -1
        elif version.parse(version_identifier_1) > version.parse(version_identifier_2):
            return 1
        else:
            return 0

    @GeneralUtilities.check_arguments
    def dependent_codeunit_exists(self, repository: str, codeunit: str) -> None:
        codeunit_file = f"{repository}/{codeunit}/{codeunit}.codeunit.xml"
        return os.path.isfile(codeunit_file)

    @GeneralUtilities.check_arguments
    def get_all_authors_and_committers_of_repository(self, repository_folder: str, subfolder: str = None) -> list[tuple[str, str]]:
        self.__sc.is_git_or_bare_git_repository(repository_folder)
        space_character = "_"
        if subfolder is None:
            subfolder_argument = GeneralUtilities.empty_string
        else:
            subfolder_argument = f" -- {subfolder}"
        log_result = self.__sc.run_program("git", f'log --pretty=%aN{space_character}%aE%n%cN{space_character}%cE HEAD{subfolder_argument}', repository_folder)
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
    def copy_artifacts_from_dependent_code_units(self, repo_folder: str, codeunit_name: str) -> None:
        codeunit_file = os.path.join(repo_folder, codeunit_name, codeunit_name + ".codeunit.xml")
        dependent_codeunits = self.get_dependent_code_units(codeunit_file)
        if len(dependent_codeunits) > 0:
            self.__sc.log.log(f"Get dependent artifacts for codeunit {codeunit_name}.")
        dependent_codeunits_folder = os.path.join(repo_folder, codeunit_name, "Other", "Resources", "DependentCodeUnits")
        GeneralUtilities.ensure_directory_does_not_exist(dependent_codeunits_folder)
        for dependent_codeunit in dependent_codeunits:
            target_folder = os.path.join(dependent_codeunits_folder, dependent_codeunit)
            GeneralUtilities.ensure_directory_does_not_exist(target_folder)
            other_folder = os.path.join(repo_folder, dependent_codeunit, "Other")
            artifacts_folder = os.path.join(other_folder, "Artifacts")
            shutil.copytree(artifacts_folder, target_folder)


    @GeneralUtilities.check_arguments
    def write_version_to_codeunit_file(self, codeunit_file: str, current_version: str) -> None:
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(current_version):
            GeneralUtilities.write_text_to_file(codeunit_file, re.sub(f"<cps:version>{versionregex}<\\/cps:version>", f"<cps:version>{current_version}</cps:version>", GeneralUtilities.read_text_from_file(codeunit_file)))
        else:
            raise ValueError(f"Version '{current_version}' does not match version-regex '{versiononlyregex}'.")

    @GeneralUtilities.check_arguments
    def set_default_constants(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        self.set_constant_for_commitid(codeunit_folder)
        self.set_constant_for_commitdate(codeunit_folder)
        self.set_constant_for_codeunitname(codeunit_folder)
        self.set_constant_for_codeunitversion(codeunit_folder)
        self.set_constant_for_codeunitmajorversion(codeunit_folder)
        self.set_constant_for_description(codeunit_folder)

    @GeneralUtilities.check_arguments
    def set_constant_for_commitid(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        repository = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        commit_id = self.__sc.git_get_commit_id(repository)
        self.set_constant(codeunit_folder, "CommitId", commit_id)

    @GeneralUtilities.check_arguments
    def set_constant_for_commitdate(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        repository = GeneralUtilities.resolve_relative_path("..", codeunit_folder)
        commit_date: datetime = self.__sc.git_get_commit_date(repository)
        self.set_constant(codeunit_folder, "CommitDate", GeneralUtilities.datetime_to_string(commit_date))

    @GeneralUtilities.check_arguments
    def set_constant_for_codeunitname(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        codeunit_name: str = os.path.basename(codeunit_folder)
        self.set_constant(codeunit_folder, "CodeUnitName", codeunit_name) 

    @GeneralUtilities.check_arguments
    def set_constant_for_codeunitversion(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        codeunit_version: str = self.get_version_of_codeunit(os.path.join(codeunit_folder,f"{os.path.basename(codeunit_folder)}.codeunit.xml"))
        self.set_constant(codeunit_folder, "CodeUnitVersion", codeunit_version)

    @GeneralUtilities.check_arguments
    def set_constant_for_codeunitmajorversion(self, codeunit_folder: str) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        major_version = int(self.get_version_of_codeunit(os.path.join(codeunit_folder,f"{os.path.basename(codeunit_folder)}.codeunit.xml")).split(".")[0])
        self.set_constant(codeunit_folder, "CodeUnitMajorVersion", str(major_version))


    @GeneralUtilities.check_arguments
    def get_version_of_codeunit(self,codeunit_file:str) -> None:
        codeunit_file_content:str=GeneralUtilities.read_text_from_file(codeunit_file)
        root: etree._ElementTree = etree.fromstring(codeunit_file_content.encode("utf-8"))
        result = str(root.xpath('//cps:version/text()',  namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0])
        return result
    
    @GeneralUtilities.check_arguments
    def set_constant_for_description(self, codeunit_folder: str) -> None:
        codeunit_file:str=self.get_version_of_codeunit(os.path.join(codeunit_folder,f"{os.path.basename(codeunit_folder)}.codeunit.xml"))
        self.assert_is_codeunit_folder(codeunit_folder)
        codeunit_description: str = self.get_codeunit_description(codeunit_file)
        self.set_constant(codeunit_folder, "CodeUnitDescription", codeunit_description)

    @GeneralUtilities.check_arguments
    def get_codeunit_description(self,codeunit_file:str) -> bool:
        root: etree._ElementTree = etree.parse(codeunit_file)
        return str(root.xpath('//cps:properties/@description', namespaces={'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'})[0])

    @GeneralUtilities.check_arguments
    def set_constant(self, codeunit_folder: str, constantname: str, constant_value: str, documentationsummary: str = None, constants_valuefile: str = None) -> None:
        self.assert_is_codeunit_folder(codeunit_folder)
        if documentationsummary is None:
            documentationsummary = GeneralUtilities.empty_string
        constants_folder = os.path.join(codeunit_folder, "Other", "Resources", "Constants")
        GeneralUtilities.ensure_directory_exists(constants_folder)
        constants_metafile = os.path.join(constants_folder, f"{constantname}.constant.xml")
        if constants_valuefile is None:
            constants_valuefile_folder = constants_folder
            constants_valuefile_name = f"{constantname}.value.txt"
            constants_valuefiler_reference = f"./{constants_valuefile_name}"
        else:
            constants_valuefile_folder = os.path.dirname(constants_valuefile)
            constants_valuefile_name = os.path.basename(constants_valuefile)
            constants_valuefiler_reference = os.path.join(constants_valuefile_folder, constants_valuefile_name)

        # TODO implement usage of self.reference_latest_version_of_xsd_when_generating_xml
        GeneralUtilities.write_text_to_file(constants_metafile, f"""<?xml version="1.0" encoding="UTF-8" ?>
<cps:constant xmlns:cps="https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure" constantspecificationversion="1.1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/raw/main/Conventions/RepositoryStructure/CommonProjectStructure/constant.xsd">
    <cps:name>{constantname}</cps:name>
    <cps:documentationsummary>{documentationsummary}</cps:documentationsummary>
    <cps:path>{constants_valuefiler_reference}</cps:path>
</cps:constant>""")
        # TODO validate generated xml against xsd
        GeneralUtilities.write_text_to_file(os.path.join(constants_valuefile_folder, constants_valuefile_name), constant_value)

    @GeneralUtilities.check_arguments
    def get_constant_value(self, source_codeunit_folder: str, constant_name: str) -> str:
        self.assert_is_codeunit_folder(source_codeunit_folder)
        value_file_relative = self.__get_constant_helper(source_codeunit_folder, constant_name, "path")
        value_file = GeneralUtilities.resolve_relative_path(value_file_relative, os.path.join(source_codeunit_folder, "Other", "Resources", "Constants"))
        return GeneralUtilities.read_text_from_file(value_file)

    @GeneralUtilities.check_arguments
    def get_constant_documentation(self, source_codeunit_folder: str, constant_name: str) -> str:
        self.assert_is_codeunit_folder(source_codeunit_folder)
        return self.__get_constant_helper(source_codeunit_folder, constant_name, "documentationsummary")

    @GeneralUtilities.check_arguments
    def __get_constant_helper(self, source_codeunit_folder: str, constant_name: str, propertyname: str) -> str:
        self.assert_is_codeunit_folder(source_codeunit_folder)
        root: etree._ElementTree = etree.parse(os.path.join(source_codeunit_folder, "Other", "Resources", "Constants", f"{constant_name}.constant.xml"))
        results = root.xpath(f'//cps:{propertyname}/text()', namespaces={
            'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure'
        })
        length = len(results)
        if (length == 0):
            return ""
        elif length == 1:
            return results[0]
        else:
            raise ValueError("Too many results found.")

    @GeneralUtilities.check_arguments
    def copy_licence_file(self, codeunit_folder: str) -> None:
        folder_of_current_file = os.path.join(codeunit_folder,"Other")
        license_file = GeneralUtilities.resolve_relative_path("../../License.txt", folder_of_current_file)
        target_folder = GeneralUtilities.resolve_relative_path("Artifacts/License", folder_of_current_file)
        GeneralUtilities.ensure_directory_exists(target_folder)
        shutil.copy(license_file, target_folder)

    @GeneralUtilities.check_arguments
    def generate_diff_report(self, repository_folder: str, codeunit_name: str, current_version: str) -> None:
        self.__sc.assert_is_git_repository(repository_folder)
        codeunit_folder = os.path.join(repository_folder, codeunit_name)
        target_folder = GeneralUtilities.resolve_relative_path("Other/Artifacts/DiffReport", codeunit_folder)
        GeneralUtilities.ensure_directory_does_not_exist(target_folder)
        GeneralUtilities.ensure_directory_exists(target_folder)
        target_file_light = os.path.join(target_folder, "DiffReport.html").replace("\\", "/")
        target_file_dark = os.path.join(target_folder, "DiffReportDark.html").replace("\\", "/")
        src = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # hash/id of empty git-tree
        src_prefix = "Begin"
        if self.__sc.get_current_git_branch_has_tag(repository_folder):
            latest_tag = self.__sc.get_latest_git_tag(repository_folder)
            src = self.__sc.git_get_commitid_of_tag(repository_folder, latest_tag)
            src_prefix = latest_tag
        dst = "HEAD"
        dst_prefix = f"v{current_version}"

        temp_file = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        try:
            GeneralUtilities.ensure_file_does_not_exist(temp_file)
            GeneralUtilities.write_text_to_file(temp_file, self.__sc.run_program("git", f'--no-pager diff --src-prefix={src_prefix}/ --dst-prefix={dst_prefix}/ {src} {dst} -- {codeunit_name}', repository_folder)[1])
            self.__sc.run_program_argsasarray("pygmentize", ['-l', 'diff', '-f', 'html', '-O', 'full', '-o', target_file_light, '-P', 'style=default', temp_file], repository_folder)
            self.__sc.run_program_argsasarray("pygmentize", ['-l', 'diff', '-f', 'html', '-O', 'full', '-o', target_file_dark, '-P', 'style=github-dark', temp_file], repository_folder)
        finally:
            GeneralUtilities.ensure_file_does_not_exist(temp_file)

    @GeneralUtilities.check_arguments
    def get_version_of_project(self,repositoryfolder:str) -> str:
        self.__sc.assert_is_git_repository(repositoryfolder)
        return self.__sc.get_semver_version_from_gitversion(repositoryfolder)

    @GeneralUtilities.check_arguments
    def create_changelog_entry(self, repositoryfolder: str, message: str, commit: bool, force: bool):
        self.__sc.assert_is_git_repository(repositoryfolder)
        random_file = os.path.join(repositoryfolder, str(uuid.uuid4()))
        if force and not self.__sc.git_repository_has_uncommitted_changes(repositoryfolder):
            GeneralUtilities.ensure_file_exists(random_file)
        current_version = self.get_version_of_project(repositoryfolder)
        changelog_file = os.path.join(repositoryfolder, "Other", "Resources", "Changelog", f"v{current_version}.md")
        if os.path.isfile(changelog_file):
            self.__sc.log.log(f"Changelog-file '{changelog_file}' already exists.")
        else:
            GeneralUtilities.ensure_file_exists(changelog_file)
            GeneralUtilities.write_text_to_file(changelog_file, f"""# Release notes

## Changes

- {message}
""")
        GeneralUtilities.ensure_file_does_not_exist(random_file)
        if commit:
            self.__sc.git_commit(repositoryfolder, f"Added changelog-file for v{current_version}.")
