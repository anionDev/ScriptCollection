from datetime import timedelta, datetime
import base64
import binascii
from configparser import ConfigParser
import filecmp
import hashlib
from io import BytesIO
import itertools
import math
import os
from shutil import copyfile
from pathlib import Path
from random import randrange
import re
import shutil
from subprocess import PIPE, Popen, call
import tempfile
import traceback
import uuid
import ntplib
from lxml import etree
import pycdlib
import send2trash
from PyPDF2 import PdfFileMerger
from .Utilities import GeneralUtilities


version = "2.7.5"
__version__ = version


class ScriptCollectionCore:

    mock_program_calls: bool = False  # This property is for test-purposes only
    execute_programy_really_if_no_mock_call_is_defined: bool = False  # This property is for test-purposes only
    __mocked_program_calls: list = list()
    __epew_is_available: bool = False

    def __init__(self):
        self.__epew_is_available = GeneralUtilities.epew_is_available()

    @staticmethod
    def get_scriptcollection_version() -> str:
        return __version__
    # <Build>

    # TODO use typechecks everywhere like discussed here https://stackoverflow.com/questions/19684434/best-way-to-check-function-arguments/37961120
    def create_release(self, configurationfile: str) -> int:
        error_occurred = False
        try:
            current_release_information: dict[str, str] = {}
            configparser = ConfigParser()
            with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
                configparser.read_file(text_io_wrapper)

            repository = self.get_item_from_configuration(configparser, "general", "repository", current_release_information)
            releaserepository = self.get_item_from_configuration(configparser, "other", "releaserepository", current_release_information)

            if (self.__repository_has_changes(repository) or self.__repository_has_changes(releaserepository)):
                return 1

            srcbranch = self.get_item_from_configuration(configparser, 'prepare', 'sourcebranchname', current_release_information)
            trgbranch = self.get_item_from_configuration(configparser, 'prepare', 'targetbranchname', current_release_information)
            commitid = self.git_get_current_commit_id(repository, trgbranch)

            if(commitid == self.git_get_current_commit_id(repository, srcbranch)):
                GeneralUtilities.write_message_to_stderr(f"Can not create release because the main-branch and the development-branch are on the same commit (commit-id: {commitid})")
                return 1

            self.git_checkout(repository, srcbranch)
            self.execute_and_raise_exception_if_exit_code_is_not_zero("git", "clean -dfx", repository)
            self.__calculate_version(configparser, current_release_information)
            repository_version = self.get_version_for_buildscripts(configparser, current_release_information)

            GeneralUtilities.write_message_to_stdout(f"Create release v{repository_version} for repository {repository}")
            self.git_merge(repository, srcbranch, trgbranch, False, False)

            try:
                if self.get_boolean_value_from_configuration(configparser, 'general', 'createdotnetrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create .NET-release")
                    error_occurred = not self.__execute_and_return_boolean("create_dotnet_release",
                                                                           lambda: self.__create_dotnet_release_premerge(
                                                                               configurationfile, current_release_information))

                if self.get_boolean_value_from_configuration(configparser, 'general', 'createpythonrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create Python-release")
                    error_occurred = not self.__execute_and_return_boolean("python_create_wheel_release",
                                                                           lambda: self.python_create_wheel_release_premerge(
                                                                               configurationfile, current_release_information))

                if self.get_boolean_value_from_configuration(configparser, 'general', 'createdebrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create Deb-release")
                    error_occurred = not self.__execute_and_return_boolean("deb_create_installer_release",
                                                                           lambda: self.deb_create_installer_release_premerge(
                                                                               configurationfile, current_release_information))

                if self.get_boolean_value_from_configuration(configparser, 'general', 'createdockerrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create docker-release")
                    error_occurred = not self.__execute_and_return_boolean("docker_create_installer_release",
                                                                           lambda: self.docker_create_image_release_premerge(
                                                                               configurationfile, current_release_information))

                if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutterandroidrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create FlutterAndroid-release")
                    error_occurred = not self.__execute_and_return_boolean("flutterandroid_create_installer_release",
                                                                           lambda: self.flutterandroid_create_installer_release_premerge(
                                                                               configurationfile, current_release_information))

                if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutteriosrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create FlutterIOS-release")
                    error_occurred = not self.__execute_and_return_boolean("flutterios_create_installer_release",
                                                                           lambda: self.flutterios_create_installer_release_premerge(
                                                                               configurationfile, current_release_information))

                if self.get_boolean_value_from_configuration(configparser, 'general', 'createscriptrelease', current_release_information) and not error_occurred:
                    GeneralUtilities.write_message_to_stdout("Start to create Script-release")
                    error_occurred = not self.__execute_and_return_boolean("generic_create_installer_release",
                                                                           lambda: self.generic_create_script_release_premerge(
                                                                               configurationfile, current_release_information))

                if not error_occurred:
                    commit_id = self.git_commit(
                        repository, f"Merge branch '{self.get_item_from_configuration(configparser, 'prepare', 'sourcebranchname',current_release_information)}' "
                        f"into '{self.get_item_from_configuration(configparser, 'prepare', 'targetbranchname',current_release_information)}'")
                    current_release_information["builtin.mergecommitid"] = commit_id

                    # TODO allow multiple custom pre- (and post)-build-regex-replacements for files specified by glob-pattern
                    # (like "!\[Generic\ badge\]\(https://img\.shields\.io/badge/coverage\-\d(\d)?%25\-green\)"
                    # -> "![Generic badge](https://img.shields.io/badge/coverage-__testcoverage__%25-green)" in all "**/*.md"-files)

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createdotnetrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create .NET-release")
                        error_occurred = not self.__execute_and_return_boolean("create_dotnet_release",
                                                                               lambda: self.__create_dotnet_release_postmerge(
                                                                                   configurationfile, current_release_information))

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createpythonrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create Python-release")
                        error_occurred = not self.__execute_and_return_boolean("python_create_wheel_release",
                                                                               lambda: self.python_create_wheel_release_postmerge(
                                                                                   configurationfile, current_release_information))

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createdebrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create Deb-release")
                        error_occurred = not self.__execute_and_return_boolean("deb_create_installer_release",
                                                                               lambda: self.deb_create_installer_release_postmerge(
                                                                                   configurationfile, current_release_information))

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createdockerrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create docker-release")
                        error_occurred = not self.__execute_and_return_boolean("docker_create_installer_release",
                                                                               lambda: self.docker_create_image_release_postmerge(configurationfile,
                                                                                                                                  current_release_information))

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutterandroidrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create FlutterAndroid-release")
                        error_occurred = not self.__execute_and_return_boolean("flutterandroid_create_installer_release",
                                                                               lambda: self.flutterandroid_create_installer_release_postmerge(configurationfile,
                                                                                                                                              current_release_information))

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutteriosrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create FlutterIOS-release")
                        error_occurred = not self.__execute_and_return_boolean("flutterios_create_installer_release",
                                                                               lambda: self.flutterios_create_installer_release_postmerge(configurationfile,
                                                                                                                                          current_release_information))

                    if self.get_boolean_value_from_configuration(configparser, 'general', 'createscriptrelease', current_release_information) and not error_occurred:
                        GeneralUtilities.write_message_to_stdout("Start to create Script-release")
                        error_occurred = not self.__execute_and_return_boolean("generic_create_installer_release",
                                                                               lambda: self.generic_create_script_release_postmerge(
                                                                                   configurationfile, current_release_information))

            except Exception as exception:
                error_occurred = True
                GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback, f"Error occurred while creating release defined by '{configurationfile}'.")

            finally:
                GeneralUtilities.write_message_to_stdout("Finished to create release")

            if error_occurred:
                GeneralUtilities.write_message_to_stderr("Creating release was not successful")
                self.git_merge_abort(repository)
                self.__undo_changes(repository)
                self.__undo_changes(releaserepository)
                self.git_checkout(repository, self.get_item_from_configuration(configparser, 'prepare', 'sourcebranchname', current_release_information))
                return 1
            else:
                self.git_merge(repository, self.get_item_from_configuration(configparser, 'prepare', 'targetbranchname', current_release_information),
                               self.get_item_from_configuration(configparser, 'prepare', 'sourcebranchname', current_release_information), True)
                tag = self.get_item_from_configuration(configparser, 'prepare', 'gittagprefix', current_release_information) + repository_version
                tag_message = f"Created {tag}"
                self.git_create_tag(repository, commit_id,
                                    tag, self.get_boolean_value_from_configuration(configparser, 'other', 'signtags', current_release_information), tag_message)
                self.__push_branch_of_release(configparser, current_release_information, repository,
                    self.get_boolean_value_from_configuration(configparser, 'other', 'exportrepositorysourcebranch', current_release_information),
                    self.get_item_from_configuration(configparser, 'prepare', 'sourcebranchname', current_release_information))
                self.__push_branch_of_release(configparser, current_release_information, repository,
                    self.get_boolean_value_from_configuration(configparser, 'other', 'exportrepositorytargetbranch', current_release_information),
                    self.get_item_from_configuration(configparser, 'prepare', 'targetbranchname', current_release_information))
                GeneralUtilities.write_message_to_stdout("Creating release was successful")
                return 0

        except Exception as e:
            GeneralUtilities.write_exception_to_stderr_with_traceback(e, traceback, f"Fatal error occurred while creating release defined by '{configurationfile}'.")
            return 1

    def __push_branch_of_release(self,configparser:ConfigParser,current_release_information: dict[str, str],repository:str, export:bool, branch:str):
        if export:
            self.git_push(repository, self.get_item_from_configuration(configparser, 'other',
                            'exportrepositoryremotename', current_release_information), branch, branch, False, True)

    def dotnet_executable_build(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        verbosity = self.__get_verbosity_for_exuecutor(configparser)
        sign_things = self.__get_sign_things(configparser, current_release_information)
        config = self.get_item_from_configuration(configparser, 'dotnet', 'buildconfiguration', current_release_information)
        for runtime in self.get_items_from_configuration(configparser, 'dotnet', 'runtimes', current_release_information):
            self.dotnet_build(current_release_information, self.__get_csprojfile_folder(configparser, current_release_information),
                              self.__get_csprojfile_filename(configparser, current_release_information),
                              self.__get_buildoutputdirectory(configparser, runtime, current_release_information), config,
                              runtime, self.get_item_from_configuration(configparser, 'dotnet', 'dotnetframework', current_release_information), True,
                              verbosity, sign_things[0], sign_things[1])
        publishdirectory = self.get_item_from_configuration(configparser, 'dotnet', 'publishdirectory', current_release_information)
        GeneralUtilities.ensure_directory_does_not_exist(publishdirectory)
        shutil.copytree(self.get_item_from_configuration(configparser, 'dotnet', 'buildoutputdirectory', current_release_information), publishdirectory)

    def dotnet_executable_run_tests(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        verbosity = self.__get_verbosity_for_exuecutor(configparser)
        if self.get_boolean_value_from_configuration(configparser, 'other', 'hastestproject', current_release_information):
            self.dotnet_run_tests(configurationfile, current_release_information, verbosity)

    def __get_sign_things(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> tuple:
        files_to_sign_raw_value = self.get_item_from_configuration(configparser, 'dotnet', 'filestosign', current_release_information)
        if(GeneralUtilities.string_is_none_or_whitespace(files_to_sign_raw_value)):
            return [None, None]
        else:
            return [GeneralUtilities.to_list(files_to_sign_raw_value, ";"), self.get_item_from_configuration(configparser, 'dotnet', 'snkfile', current_release_information)]

    def dotnet_create_executable_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        repository_version = self.get_version_for_buildscripts(configparser, current_release_information)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'updateversionsincsprojfile', current_release_information):
            GeneralUtilities.update_version_in_csproj_file(self.get_item_from_configuration(configparser, 'dotnet', 'csprojfile', current_release_information), repository_version)
        self.dotnet_executable_run_tests(configurationfile, current_release_information)

    def dotnet_create_executable_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        self.dotnet_executable_build(configurationfile, current_release_information)
        self.dotnet_reference(configurationfile, current_release_information)

    def dotnet_create_nuget_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        repository_version = self.get_version_for_buildscripts(configparser, current_release_information)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'updateversionsincsprojfile', current_release_information):
            GeneralUtilities.update_version_in_csproj_file(self.get_item_from_configuration(configparser, 'dotnet', 'csprojfile', current_release_information), repository_version)
        self.dotnet_nuget_run_tests(configurationfile, current_release_information)

    def dotnet_create_nuget_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        self.dotnet_nuget_build(configurationfile, current_release_information)
        self.dotnet_reference(configurationfile, current_release_information)
        self.dotnet_release_nuget(configurationfile, current_release_information)

    __nuget_template = r"""<?xml version="1.0" encoding="utf-8"?>
    <package xmlns="http://schemas.microsoft.com/packaging/2011/10/nuspec.xsd">
      <metadata minClientVersion="2.12">
        <id>__.general.productname.__</id>
        <version>__.builtin.version.__</version>
        <title>__.general.productname.__</title>
        <authors>__.general.author.__</authors>
        <owners>__.general.author.__</owners>
        <requireLicenseAcceptance>true</requireLicenseAcceptance>
        <copyright>Copyright © __.builtin.year.__ by __.general.author.__</copyright>
        <description>__.general.description.__</description>
        <summary>__.general.description.__</summary>
        <license type="file">lib/__.dotnet.dotnetframework.__/__.general.productname.__.License.txt</license>
        <dependencies>
          <group targetFramework="__.dotnet.dotnetframework.__" />
        </dependencies>
        __.internal.projecturlentry.__
        __.internal.repositoryentry.__
        __.internal.iconentry.__
      </metadata>
      <files>
        <file src="Binary/__.general.productname.__.dll" target="lib/__.dotnet.dotnetframework.__" />
        <file src="Binary/__.general.productname.__.License.txt" target="lib/__.dotnet.dotnetframework.__" />
        __.internal.iconfileentry.__
      </files>
    </package>"""

    def dotnet_nuget_build(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        sign_things = self.__get_sign_things(configparser, current_release_information)
        config = self.get_item_from_configuration(configparser, 'dotnet', 'buildconfiguration', current_release_information)
        for runtime in self.get_items_from_configuration(configparser, 'dotnet', 'runtimes', current_release_information):
            self.dotnet_build(current_release_information, self.__get_csprojfile_folder(configparser, current_release_information),
                              self.__get_csprojfile_filename(configparser, current_release_information),
                              self.__get_buildoutputdirectory(configparser, runtime, current_release_information), config,
                              runtime, self.get_item_from_configuration(configparser, 'dotnet', 'dotnetframework', current_release_information), True,
                              self.__get_verbosity_for_exuecutor(configparser),
                              sign_things[0], sign_things[1])
        publishdirectory = self.get_item_from_configuration(configparser, 'dotnet', 'publishdirectory', current_release_information)
        publishdirectory_binary = publishdirectory+os.path.sep+"Binary"
        GeneralUtilities.ensure_directory_does_not_exist(publishdirectory)
        GeneralUtilities.ensure_directory_exists(publishdirectory_binary)
        shutil.copytree(self.get_item_from_configuration(configparser, 'dotnet', 'buildoutputdirectory', current_release_information), publishdirectory_binary)

        nuspec_content = self.__replace_underscores_for_buildconfiguration(self.__nuget_template, configparser, current_release_information)

        if(self.configuration_item_is_available(configparser, "other", "projecturl")):
            nuspec_content = nuspec_content.replace("__.internal.projecturlentry.__",
                                                    f"<projectUrl>{self.get_item_from_configuration(configparser, 'other', 'projecturl',current_release_information)}</projectUrl>")
        else:
            nuspec_content = nuspec_content.replace("__.internal.projecturlentry.__", "")

        if "builtin.commitid" in current_release_information and self.configuration_item_is_available(configparser, "other", "repositoryurl"):
            repositoryurl = self.get_item_from_configuration(configparser, 'other', 'repositoryurl', current_release_information)
            branch = self.get_item_from_configuration(configparser, 'prepare', 'targetbranchname', current_release_information)
            commitid = current_release_information["builtin.commitid"]
            nuspec_content = nuspec_content.replace("__.internal.repositoryentry.__", f'<repository type="git" url="{repositoryurl}" branch="{branch}" commit="{commitid}" />')
        else:
            nuspec_content = nuspec_content.replace("__.internal.repositoryentry.__", "")

        if self.configuration_item_is_available(configparser, "dotnet", "iconfile"):
            shutil.copy2(self.get_item_from_configuration(configparser, "dotnet", "iconfile", current_release_information), os.path.join(publishdirectory, "icon.png"))
            nuspec_content = nuspec_content.replace("__.internal.iconentry.__", '<icon>images\\icon.png</icon>')
            nuspec_content = nuspec_content.replace("__.internal.iconfileentry.__", '<file src=".\\icon.png" target="images\\" />')
        else:
            nuspec_content = nuspec_content.replace("__.internal.iconentry.__", "")
            nuspec_content = nuspec_content.replace("__.internal.iconfileentry.__", "")

        nuspecfilename = self.get_item_from_configuration(configparser, 'general', 'productname', current_release_information)+".nuspec"
        nuspecfile = os.path.join(publishdirectory, nuspecfilename)
        with open(nuspecfile, encoding="utf-8", mode="w") as file_object:
            file_object.write(nuspec_content)
        self.execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}", publishdirectory, 3600,
                                                                  self.__get_verbosity_for_exuecutor(configparser))

    def dotnet_nuget_run_tests(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        verbosity = self.__get_verbosity_for_exuecutor(configparser)
        if self.get_boolean_value_from_configuration(configparser, 'other', 'hastestproject', current_release_information):
            self.dotnet_run_tests(configurationfile, current_release_information, verbosity)

    def dotnet_release_nuget(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        repository_version = self.get_version_for_buildscripts(configparser, current_release_information)
        publishdirectory = self.get_item_from_configuration(configparser, 'dotnet', 'publishdirectory', current_release_information)
        latest_nupkg_file = self.get_item_from_configuration(configparser, 'general', 'productname', current_release_information)+"."+repository_version+".nupkg"
        for localnugettarget in self.get_items_from_configuration(configparser, 'dotnet', 'localnugettargets', current_release_information):
            self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}",
                                                                      publishdirectory, 3600,  self.__get_verbosity_for_exuecutor(configparser))
        if (self.get_boolean_value_from_configuration(configparser, 'dotnet', 'publishnugetfile', current_release_information)):
            with open(self.get_item_from_configuration(configparser, 'dotnet', 'nugetapikeyfile', current_release_information), 'r', encoding='utf-8') as apikeyfile:
                api_key = apikeyfile.read()
            nugetsource = self.get_item_from_configuration(configparser, 'dotnet', 'nugetsource', current_release_information)
            self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {nugetsource} --api-key {api_key}",
                                                                      publishdirectory, 3600, self.__get_verbosity_for_exuecutor(configparser))

    def dotnet_reference(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'generatereference', current_release_information):
            self.git_checkout(
                self.get_item_from_configuration(configparser, 'dotnet', 'referencerepository', current_release_information),
                self.get_item_from_configuration(configparser, 'dotnet', 'exportreferencelocalbranchname', current_release_information))
            verbosity = self.__get_verbosity_for_exuecutor(configparser)
            if verbosity == 0:
                verbose_argument_for_reportgenerator = "Off"
                verbose_argument_for_docfx = "Error"
            if verbosity == 1:
                verbose_argument_for_reportgenerator = "Error"
                verbose_argument_for_docfx = "Warning"
            if verbosity == 2:
                verbose_argument_for_reportgenerator = "Info"
                verbose_argument_for_docfx = "Info"
            if verbosity == 3:
                verbose_argument_for_reportgenerator = "Verbose"
                verbose_argument_for_docfx = "verbose"
            docfx_file = self.get_item_from_configuration(configparser, 'dotnet', 'docfxfile', current_release_information)
            docfx_folder = os.path.dirname(docfx_file)
            GeneralUtilities.ensure_directory_does_not_exist(os.path.join(docfx_folder, "obj"))
            self.execute_and_raise_exception_if_exit_code_is_not_zero("docfx",
                                                                      f'"{os.path.basename(docfx_file)}" --loglevel {verbose_argument_for_docfx}', docfx_folder, 3600, verbosity)
            coveragefolder = self.get_item_from_configuration(configparser, 'dotnet', 'coveragefolder', current_release_information)
            GeneralUtilities.ensure_directory_exists(coveragefolder)
            coverage_target_file = coveragefolder+os.path.sep+self.__get_coverage_filename(configparser, current_release_information)
            shutil.copyfile(self.__get_test_csprojfile_folder(configparser, current_release_information)+os.path.sep +
                            self.__get_coverage_filename(configparser, current_release_information), coverage_target_file)
            self.execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator",
                                                                      f'-reports:"{self.__get_coverage_filename(configparser,current_release_information)}"'
                                                                      f' -targetdir:"{coveragefolder}" -verbosity:{verbose_argument_for_reportgenerator}',
                                                                      coveragefolder, 3600, verbosity)
            self.git_commit(self.get_item_from_configuration(configparser, 'dotnet', 'referencerepository', current_release_information), "Updated reference")
            if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'exportreference', current_release_information):
                self.git_push(self.get_item_from_configuration(configparser, 'dotnet', 'referencerepository', current_release_information),
                              self.get_item_from_configuration(configparser, 'dotnet', 'exportreferenceremotename', current_release_information),
                              self.get_item_from_configuration(configparser, 'dotnet', 'exportreferencelocalbranchname', current_release_information),
                              self.get_item_from_configuration(configparser, 'dotnet', 'exportreferenceremotebranchname', current_release_information), False, False)

    def dotnet_build(self, current_release_information: dict, folderOfCsprojFile: str, csprojFilename: str, outputDirectory: str, buildConfiguration: str, runtimeId: str, dotnet_framework: str,
                     clearOutputDirectoryBeforeBuild: bool = True, verbosity: int = 1, filesToSign: list = None, keyToSignForOutputfile: str = None) -> None:
        if os.path.isdir(outputDirectory) and clearOutputDirectoryBeforeBuild:
            GeneralUtilities.ensure_directory_does_not_exist(outputDirectory)
        GeneralUtilities.ensure_directory_exists(outputDirectory)
        GeneralUtilities.write_message_to_stdout("xxxverosity")
        GeneralUtilities.write_message_to_stdout(GeneralUtilities.str_none_safe(verbosity))
        if verbosity == 0:
            verbose_argument_for_dotnet = "quiet"
        elif verbosity == 1:
            verbose_argument_for_dotnet = "minimal"
        elif verbosity == 2:
            verbose_argument_for_dotnet = "normal"
        elif verbosity == 3:
            verbose_argument_for_dotnet = "detailed"
        else:
            raise Exception("Invalid value for verbosity: "+GeneralUtilities.str_none_safe(verbosity))
        argument = csprojFilename
        argument = argument + ' --no-incremental'
        argument = argument + f' --configuration {buildConfiguration}'
        argument = argument + f' --framework {dotnet_framework}'
        argument = argument + f' --runtime {runtimeId}'
        argument = argument + f' --verbosity {verbose_argument_for_dotnet}'
        argument = argument + f' --output "{outputDirectory}"'
        self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'build {argument}', folderOfCsprojFile, 3600, verbosity, False, "Build")
        if(filesToSign is not None):
            for fileToSign in filesToSign:
                self.dotnet_sign(outputDirectory+os.path.sep+fileToSign, keyToSignForOutputfile, verbosity, current_release_information)

    def dotnet_run_tests(self, configurationfile: str, current_release_information: dict[str, str], verbosity: int = 1) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if verbosity == 0:
            verbose_argument_for_dotnet = "quiet"
        if verbosity == 1:
            verbose_argument_for_dotnet = "minimal"
        if verbosity == 2:
            verbose_argument_for_dotnet = "normal"
        if verbosity == 3:
            verbose_argument_for_dotnet = "detailed"
        coveragefilename = self.__get_coverage_filename(configparser, current_release_information)
        csproj = self.__get_test_csprojfile_filename(configparser, current_release_information)
        testbuildconfig = self.get_item_from_configuration(configparser, 'dotnet', 'testbuildconfiguration', current_release_information)
        testargument = f"test {csproj} -c {testbuildconfig}" \
            f" --verbosity {verbose_argument_for_dotnet} /p:CollectCoverage=true /p:CoverletOutput={coveragefilename}" \
            f" /p:CoverletOutputFormat=opencover"
        self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", testargument, self.__get_test_csprojfile_folder(configparser, current_release_information),
                                                                  3600, verbosity, False, "Execute tests")
        root = etree.parse(self.__get_test_csprojfile_folder(configparser, current_release_information)+os.path.sep+coveragefilename)
        coverage_in_percent = math.floor(float(str(root.xpath('//CoverageSession/Summary/@sequenceCoverage')[0])))
        module_count = int(root.xpath('count(//CoverageSession/Modules/*)'))
        if module_count == 0:
            coverage_in_percent = 0
            GeneralUtilities.write_message_to_stdout("Warning: The testcoverage-report does not contain any module, therefore the testcoverage will be set to 0.")
        self.__handle_coverage(configparser, current_release_information, coverage_in_percent, verbosity == 3)

    def __handle_coverage(self, configparser, current_release_information, coverage_in_percent: int, verbose: bool):
        current_release_information['general.testcoverage'] = coverage_in_percent
        minimalrequiredtestcoverageinpercent = self.get_number_value_from_configuration(configparser, "other", "minimalrequiredtestcoverageinpercent")
        if(coverage_in_percent < minimalrequiredtestcoverageinpercent):
            raise ValueError(f"The testcoverage must be {minimalrequiredtestcoverageinpercent}% or more but is {coverage_in_percent}.")
        coverage_regex_begin = "https://img.shields.io/badge/testcoverage-"
        coverage_regex_end = "%25-green"
        for file in self.get_items_from_configuration(configparser, "other", "codecoverageshieldreplacementfiles", current_release_information):
            GeneralUtilities.replace_regex_each_line_of_file(file, re.escape(coverage_regex_begin)+"\\d+"+re.escape(coverage_regex_end),
                                                             coverage_regex_begin+str(coverage_in_percent)+coverage_regex_end, verbose=verbose)

    def dotnet_sign(self, dllOrExefile: str, snkfile: str, verbosity: int, current_release_information: dict[str, str]) -> None:
        dllOrExeFile = GeneralUtilities.resolve_relative_path_from_current_working_directory(dllOrExefile)
        snkfile = GeneralUtilities.resolve_relative_path_from_current_working_directory(snkfile)
        directory = os.path.dirname(dllOrExeFile)
        filename = os.path.basename(dllOrExeFile)
        if filename.lower().endswith(".dll"):
            filename = filename[:-4]
            extension = "dll"
        elif filename.lower().endswith(".exe"):
            filename = filename[:-4]
            extension = "exe"
        else:
            raise Exception("Only .dll-files and .exe-files can be signed")
        self.execute_and_raise_exception_if_exit_code_is_not_zero("ildasm",
                                                                  f'/all /typelist /text /out="{filename}.il" "{filename}.{extension}"',
                                                                  directory, 3600, verbosity, False, "Sign: ildasm")
        self.execute_and_raise_exception_if_exit_code_is_not_zero("ilasm",
                                                                  f'/{extension} /res:"{filename}.res" /optimize /key="{snkfile}" "{filename}.il"',
                                                                  directory, 3600, verbosity, False, "Sign: ilasm")
        os.remove(directory+os.path.sep+filename+".il")
        os.remove(directory+os.path.sep+filename+".res")

    def deb_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        pass

    def deb_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        return False  # TODO implement

    def docker_create_image_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        contextfolder: str = self.get_item_from_configuration(configparser, "docker", "contextfolder", current_release_information)
        imagename: str = self.get_item_from_configuration(configparser, "general", "productname", current_release_information).lower()
        registryaddress: str = self.get_item_from_configuration(configparser, "docker", "registryaddress", current_release_information)
        dockerfile_filename: str = self.get_item_from_configuration(configparser, "docker", "dockerfile", current_release_information)
        repository_version: str = self.get_version_for_buildscripts(configparser, current_release_information)
        environmentconfiguration_for_latest_tag: str = self.get_item_from_configuration(
            configparser, "docker", "environmentconfigurationforlatesttag", current_release_information).lower()
        pushimagetoregistry: bool = self.get_boolean_value_from_configuration(configparser, "docker", "pushimagetoregistry", current_release_information)
        latest_tag: str = f"{imagename}:latest"

        # collect tags
        tags_for_push = []
        tags_by_environment = dict()
        for environmentconfiguration in self.get_items_from_configuration(configparser, "docker", "environmentconfigurations", current_release_information):
            environmentconfiguration_lower: str = environmentconfiguration.lower()
            tags_for_current_environment = []
            version_tag = repository_version  # "1.0.0"
            version_environment_tag = f"{version_tag}-{environmentconfiguration_lower}"  # "1.0.0-environment"
            tags_for_current_environment.append(version_environment_tag)
            if environmentconfiguration_lower == environmentconfiguration_for_latest_tag:
                latest_tag = "latest"  # "latest"
                tags_for_current_environment.append(version_tag)
                tags_for_current_environment.append(latest_tag)
            entire_tags_for_current_environment = []
            for tag in tags_for_current_environment:
                entire_tags_for_current_environment.append(f"{imagename}:{tag}")
                if pushimagetoregistry:
                    tag_for_push = f"{registryaddress}:{tag}"
                    entire_tags_for_current_environment.append(tag_for_push)
                    tags_for_push.append(tag_for_push)
            tags_by_environment[environmentconfiguration] = entire_tags_for_current_environment

        current_release_information["builtin.docker.tags_by_environment"] = tags_by_environment
        current_release_information["builtin.docker.tags_for_push"] = tags_for_push

        # build image
        for environmentconfiguration, tags in tags_by_environment.items():
            argument = f"image build --no-cache --pull --force-rm --progress plain --build-arg EnvironmentStage={environmentconfiguration}"
            for tag in tags:
                argument = f"{argument} --tag {tag}"
            argument = f"{argument} --file {dockerfile_filename} ."
            self.execute_and_raise_exception_if_exit_code_is_not_zero("docker", argument,
                                                                      contextfolder,  print_errors_as_information=True,
                                                                      verbosity=self.__get_verbosity_for_exuecutor(configparser))

    def docker_create_image_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        overwriteexistingfilesinartefactdirectory: bool = self.get_boolean_value_from_configuration(
            configparser, "docker", "overwriteexistingfilesinartefactdirectory", current_release_information)
        verbosity: int = self.__get_verbosity_for_exuecutor(configparser)

        # export to file
        if (self.get_boolean_value_from_configuration(configparser, "docker", "storeimageinartefactdirectory", current_release_information)):
            artefactdirectory = self.get_item_from_configuration(configparser, "docker", "artefactdirectory", current_release_information)
            GeneralUtilities.ensure_directory_exists(artefactdirectory)
            for environment in current_release_information["builtin.docker.tags_by_environment"]:
                for tag in current_release_information["builtin.docker.tags_by_environment"][environment]:
                    if not (tag in current_release_information["builtin.docker.tags_for_push"]):
                        self.__export_tag_to_file(tag, artefactdirectory, overwriteexistingfilesinartefactdirectory, verbosity)

        # push to registry
        for tag in current_release_information["builtin.docker.tags_for_push"]:
            self.execute_and_raise_exception_if_exit_code_is_not_zero("docker", f"push {tag}",
                                                                      print_errors_as_information=True,
                                                                      verbosity=self.__get_verbosity_for_exuecutor(configparser))

        # remove local stored images:
        if self.get_boolean_value_from_configuration(configparser, "docker", "removenewcreatedlocalimagesafterexport", current_release_information):
            for environment in current_release_information["builtin.docker.tags_by_environment"]:
                for tag in current_release_information["builtin.docker.tags_by_environment"][environment]:
                    self.execute_and_raise_exception_if_exit_code_is_not_zero("docker", f"image rm {tag}",
                                                                              print_errors_as_information=True,
                                                                              verbosity=verbosity)

    def __export_tag_to_file(self, tag: str, artefactdirectory: str, overwriteexistingfilesinartefactdirectory: bool, verbosity: int) -> None:
        if tag.endswith(":latest"):
            separator = "_"
        else:
            separator = "_v"
        targetfile_name = tag.replace(":", separator) + ".tar"
        targetfile = os.path.join(artefactdirectory, targetfile_name)
        if os.path.isfile(targetfile):
            if overwriteexistingfilesinartefactdirectory:
                GeneralUtilities.ensure_file_does_not_exist(targetfile)
            else:
                raise Exception(f"File '{targetfile}' does already exist")

        self.execute_and_raise_exception_if_exit_code_is_not_zero("docker", f"save -o {targetfile} {tag}",
                                                                  print_errors_as_information=True,
                                                                  verbosity=verbosity)

    def flutterandroid_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        pass

    def flutterandroid_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        return False  # TODO implement

    def flutterios_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        pass

    def flutterios_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        return False  # TODO implement

    def generic_create_script_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if GeneralUtilities.string_has_content(self.get_item_from_configuration(configparser, 'script', 'premerge_program', current_release_information)):
            self.execute_and_raise_exception_if_exit_code_is_not_zero(self.get_item_from_configuration(configparser, 'script', 'premerge_program', current_release_information),
                                                                      self.get_item_from_configuration(configparser, 'script', 'premerge_argument', current_release_information),
                                                                      self.get_item_from_configuration(configparser, 'script', 'premerge_workingdirectory', current_release_information))

    def generic_create_script_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if GeneralUtilities.string_has_content(self.get_item_from_configuration(configparser, 'script', 'postmerge_program', current_release_information)):
            self.execute_and_raise_exception_if_exit_code_is_not_zero(self.get_item_from_configuration(configparser, 'script', 'postmerge_program', current_release_information),
                                                                      self.get_item_from_configuration(configparser, 'script', 'postmerge_argument', current_release_information),
                                                                      self.get_item_from_configuration(configparser, 'script', 'postmerge_workingdirectory', current_release_information))

    def python_create_wheel_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        repository_version = self.get_version_for_buildscripts(configparser, current_release_information)

        # Update version
        if(self.get_boolean_value_from_configuration(configparser, 'python', 'updateversion', current_release_information)):
            for file in self.get_items_from_configuration(configparser, 'python', 'filesforupdatingversion', current_release_information):
                GeneralUtilities.replace_regex_each_line_of_file(file, '^version = ".+"\n$', f'version = "{repository_version}"\n')

        # lint-checks
        errors_found = False

        repository = self.get_item_from_configuration(configparser, "general", "repository", current_release_information)
        for file in GeneralUtilities.get_all_files_of_folder(repository):
            relative_file_path_in_repository = os.path.relpath(file, repository)
            if file.endswith(".py") and os.path.getsize(file) > 0 and not self.file_is_git_ignored(relative_file_path_in_repository, repository):
                linting_result = self.python_file_has_errors(file)
                if (linting_result[0]):
                    errors_found = True
                    for error in linting_result[1]:
                        GeneralUtilities.write_message_to_stderr(error)
        if errors_found:
            raise Exception("Can not continue due to errors in the python-files")

        # Run testcases
        self.python_run_tests(configurationfile, current_release_information)

    def python_create_wheel_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]):
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        self.python_build_wheel_and_run_tests(configurationfile, current_release_information)
        self.python_release_wheel(configurationfile, current_release_information)

    def __execute_and_return_boolean(self, name: str, method) -> bool:
        try:
            method()
            return True
        except Exception as exception:
            GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback, f"'{name}' resulted in an error")
            return False

    def python_build_wheel_and_run_tests(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        self.python_run_tests(configurationfile, current_release_information)
        self.python_build(configurationfile, current_release_information)

    def python_build(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        setuppyfile = self.get_item_from_configuration(configparser, "python", "pythonsetuppyfile", current_release_information)
        setuppyfilename = os.path.basename(setuppyfile)
        setuppyfilefolder = os.path.dirname(setuppyfile)
        publishdirectoryforwhlfile = self.get_item_from_configuration(configparser, "python", "publishdirectoryforwhlfile", current_release_information)
        GeneralUtilities.ensure_directory_exists(publishdirectoryforwhlfile)
        self.execute_and_raise_exception_if_exit_code_is_not_zero("python",
                                                                  setuppyfilename+' bdist_wheel --dist-dir "'+publishdirectoryforwhlfile+'"',
                                                                  setuppyfilefolder, 3600, self.__get_verbosity_for_exuecutor(configparser))

    def python_run_tests(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        # TODO check minimalrequiredtestcoverageinpercent and generate coverage report
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if self.get_boolean_value_from_configuration(configparser, 'other', 'hastestproject', current_release_information):
            pythontestfilefolder = self.get_item_from_configuration(configparser, 'general', 'repository', current_release_information)
            # TODO set verbosity-level for pytest
            self.execute_and_raise_exception_if_exit_code_is_not_zero("pytest", "", pythontestfilefolder, 3600,
                                                                      self.__get_verbosity_for_exuecutor(configparser), False, "Pytest")

    def python_release_wheel(self, configurationfile: str, current_release_information: dict[str, str]) -> None:
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if self.get_boolean_value_from_configuration(configparser, 'python', 'publishwhlfile', current_release_information):
            with open(self.get_item_from_configuration(configparser, 'python', 'pypiapikeyfile', current_release_information), 'r', encoding='utf-8') as apikeyfile:
                api_key = apikeyfile.read()
            gpgidentity = self.get_item_from_configuration(configparser, 'other', 'gpgidentity', current_release_information)
            repository_version = self.get_version_for_buildscripts(configparser, current_release_information)
            productname = self.get_item_from_configuration(configparser, 'general', 'productname', current_release_information)
            verbosity = self.__get_verbosity_for_exuecutor(configparser)
            if verbosity > 2:
                verbose_argument = "--verbose"
            else:
                verbose_argument = ""
            twine_argument = f"upload --sign --identity {gpgidentity} --non-interactive {productname}-{repository_version}-py3-none-any.whl" \
                f" --disable-progress-bar --username __token__ --password {api_key} {verbose_argument}"
            self.execute_and_raise_exception_if_exit_code_is_not_zero("twine", twine_argument,
                                                                      self.get_item_from_configuration(
                                                                          configparser, "python", "publishdirectoryforwhlfile", current_release_information),
                                                                      3600, verbosity)

    # </Build>

    # <git>

    def commit_is_signed_by_key(self, repository_folder: str, revision_identifier: str, key: str) -> bool:
        result = self.start_program_synchronously("git", f"verify-commit {revision_identifier}", repository_folder)
        if(result[0] != 0):
            return False
        if(not GeneralUtilities.contains_line(result[1].splitlines(), f"gpg\\:\\ using\\ [A-Za-z0-9]+\\ key\\ [A-Za-z0-9]+{key}")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        if(not GeneralUtilities.contains_line(result[1].splitlines(), "gpg\\:\\ Good\\ signature\\ from")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        return True

    def get_parent_commit_ids_of_commit(self, repository_folder: str, commit_id: str) -> str:
        return self.execute_and_raise_exception_if_exit_code_is_not_zero("git",
                                                                         f'log --pretty=%P -n 1 "{commit_id}"',
                                                                         repository_folder)[1].replace("\r", "").replace("\n", "").split(" ")

    def get_commit_ids_between_dates(self, repository_folder: str, since: datetime, until: datetime, ignore_commits_which_are_not_in_history_of_head: bool = True) -> None:
        since_as_string = self.datetime_to_string_for_git(since)
        until_as_string = self.datetime_to_string_for_git(until)
        result = filter(lambda line: not GeneralUtilities.string_is_none_or_whitespace(line),
                        self.execute_and_raise_exception_if_exit_code_is_not_zero("git",
                                                                                  f'log --since "{since_as_string}" --until "{until_as_string}" --pretty=format:"%H" --no-patch',
                                                                                  repository_folder)[1].split("\n").replace("\r", ""))
        if ignore_commits_which_are_not_in_history_of_head:
            result = [commit_id for commit_id in result if self.git_commit_is_ancestor(repository_folder, commit_id)]
        return result

    def datetime_to_string_for_git(self, datetime_object: datetime) -> str:
        return datetime_object.strftime('%Y-%m-%d %H:%M:%S')

    def git_commit_is_ancestor(self, repository_folder: str,  ancestor: str, descendant: str = "HEAD") -> bool:
        return self.start_program_synchronously_argsasarray("git", ["merge-base", "--is-ancestor", ancestor, descendant], repository_folder)[0] == 0

    def git_repository_has_new_untracked_files(self, repository_folder: str) -> bool:
        return self.__run_git_command(repository_folder, ["ls-files", "--exclude-standard", "--others"])

    def git_repository_has_unstaged_changes(self, repository_folder: str) -> bool:
        if(self.__run_git_command(repository_folder, ["diff"])):
            return True
        if(self.git_repository_has_new_untracked_files(repository_folder)):
            return True
        return False

    def git_repository_has_staged_changes(self, repository_folder: str) -> bool:
        return self.__run_git_command(repository_folder, ["diff", "--cached"])

    def git_repository_has_uncommitted_changes(self, repository_folder: str) -> bool:
        if(self.git_repository_has_unstaged_changes(repository_folder)):
            return True
        if(self.git_repository_has_staged_changes(repository_folder)):
            return True
        return False

    def __run_git_command(self, repository_folder: str, argument: list) -> bool:
        return not GeneralUtilities.string_is_none_or_whitespace(
            self.start_program_synchronously_argsasarray("git", argument, repository_folder, timeoutInSeconds=100, verbosity=0, prevent_using_epew=True)[1])

    def git_get_current_commit_id(self, repository_folder: str, commit: str = "HEAD") -> str:
        result = self.start_program_synchronously_argsasarray("git", ["rev-parse", "--verify", commit], repository_folder,
                                                              timeoutInSeconds=100, verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        return result[1].replace('\r', '').replace('\n', '')

    def git_fetch(self, folder: str, remotename: str = "--all", print_errors_as_information: bool = True, verbosity=1) -> None:
        self.start_program_synchronously_argsasarray("git", ["fetch", remotename, "--tags", "--prune"], folder, timeoutInSeconds=100, verbosity=verbosity,
                                                     print_errors_as_information=print_errors_as_information,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_remove_branch(self, folder: str, branchname: str, verbosity=1) -> None:
        self.start_program_synchronously_argsasarray("git", f"branch -D {branchname}", folder, timeoutInSeconds=30, verbosity=verbosity,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_push(self, folder: str, remotename: str, localbranchname: str, remotebranchname: str, forcepush: bool = False, pushalltags: bool = False, verbosity=1) -> None:
        argument = ["push", remotename, f"{localbranchname}:{remotebranchname}"]
        if (forcepush):
            argument.append("--force")
        if (pushalltags):
            argument.append("--tags")
        result = self.start_program_synchronously_argsasarray("git", argument, folder, timeoutInSeconds=7200, verbosity=verbosity,
                                                              prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        return result[1].replace('\r', '').replace('\n', '')

    def git_clone_if_not_already_done(self, clone_target_folder: str, remote_repository_path: str, include_submodules: bool = True, mirror: bool = False) -> None:
        original_cwd = os.getcwd()
        args = ["clone", remote_repository_path]
        try:
            if(not os.path.isdir(clone_target_folder)):
                if include_submodules:
                    args.append("--recurse-submodules")
                    args.append("--remote-submodules")
                if mirror:
                    args.append("--mirror")
                GeneralUtilities.ensure_directory_exists(clone_target_folder)
                self.start_program_synchronously_argsasarray("git", args, clone_target_folder, throw_exception_if_exitcode_is_not_zero=True)
        finally:
            os.chdir(original_cwd)

    def git_get_all_remote_names(self, directory) -> list[str]:
        lines = self.start_program_synchronously_argsasarray("git", ["remote"], directory, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)[1]
        result = []
        for line in lines:
            if(not GeneralUtilities.string_is_none_or_whitespace(line)):
                result.append(line.strip())
        return result

    def repository_has_remote_with_specific_name(self, directory: str, remote_name: str) -> bool:
        return remote_name in self.git_get_all_remote_names(directory)

    def git_add_or_set_remote_address(self, directory: str, remote_name: str, remote_address: str) -> None:
        if (self.repository_has_remote_with_specific_name(directory, remote_name)):
            self.start_program_synchronously_argsasarray("git", ['remote', 'set-url', 'remote_name', remote_address],
                                                         directory, timeoutInSeconds=100, verbosity=0,
                                                         prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        else:
            self.start_program_synchronously_argsasarray("git", ['remote', 'add', remote_name, remote_address], directory,
                                                         timeoutInSeconds=100, verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_stage_all_changes(self, directory: str) -> None:
        self.start_program_synchronously_argsasarray("git", ["add", "-A"], directory, timeoutInSeconds=100, verbosity=0,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_unstage_all_changes(self, directory: str) -> None:
        self.start_program_synchronously_argsasarray("git", ["reset"], directory, timeoutInSeconds=100, verbosity=0,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_stage_file(self, directory: str, file: str) -> None:
        self.start_program_synchronously_argsasarray("git", ['stage', file], directory, timeoutInSeconds=100,
                                                     verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_unstage_file(self, directory: str, file: str) -> None:
        self.start_program_synchronously_argsasarray("git", ['reset', file], directory, timeoutInSeconds=100,
                                                     verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_discard_unstaged_changes_of_file(self, directory: str, file: str) -> None:
        """Caution: This method works really only for 'changed' files yet. So this method does not work properly for new or renamed files."""
        self.start_program_synchronously_argsasarray("git", ['checkout', file], directory, timeoutInSeconds=100, verbosity=0,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_discard_all_unstaged_changes(self, directory: str) -> None:
        """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
        self.start_program_synchronously_argsasarray("git", ['clean', '-df'], directory, timeoutInSeconds=100, verbosity=0,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        self.start_program_synchronously_argsasarray("git", ['checkout', '.'], directory, timeoutInSeconds=100, verbosity=0,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_commit(self, directory: str, message: str, author_name: str = None, author_email: str = None, stage_all_changes: bool = True,
                   no_changes_behavior: int = 0) -> None:
        # no_changes_behavior=0 => No commit
        # no_changes_behavior=1 => Commit anyway
        # no_changes_behavior=2 => Exception
        author_name = GeneralUtilities.str_none_safe(author_name).strip()
        author_email = GeneralUtilities.str_none_safe(author_email).strip()
        argument = ['commit', '--message', message]
        if(GeneralUtilities.string_has_content(author_name)):
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
            if no_changes_behavior == 1:
                GeneralUtilities.write_message_to_stdout(f"There are no changes to commit in repository '{directory}'. Commit '{message}' will be done anyway.")
                do_commit = True
                argument.append('--allow-empty')
            if no_changes_behavior == 2:
                raise RuntimeError(f"There are no changes to commit in repository '{directory}'. Commit '{message}' will not be done.")

        if do_commit:
            GeneralUtilities.write_message_to_stdout(f"Commit changes in '{directory}'...")
            self.start_program_synchronously_argsasarray("git", argument, directory, 0, False, None, 1200,
                                                         prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

        return self.git_get_current_commit_id(directory)

    def git_create_tag(self, directory: str, target_for_tag: str, tag: str, sign: bool = False, message: str = None) -> None:
        argument = ["tag", tag, target_for_tag]
        if sign:
            if message is None:
                message = f"Created {target_for_tag}"
            argument.extend(["-s", "-m", message])
        self.start_program_synchronously_argsasarray("git", argument, directory, timeoutInSeconds=100,
                                                     verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)

    def git_checkout(self, directory: str, branch: str) -> None:
        self.start_program_synchronously_argsasarray("git", ["checkout", branch], directory, timeoutInSeconds=100, verbosity=0, prevent_using_epew=True,
                                                     throw_exception_if_exitcode_is_not_zero=True)

    def git_merge_abort(self, directory: str) -> None:
        self.start_program_synchronously_argsasarray("git", ["merge", "--abort"], directory, timeoutInSeconds=100, verbosity=0, prevent_using_epew=True)

    def git_merge(self, directory: str, sourcebranch: str, targetbranch: str, fastforward: bool = True, commit: bool = True) -> str:
        self.git_checkout(directory, targetbranch)
        args = ["merge"]
        if not commit:
            args.append("--no-commit")
        if not fastforward:
            args.append("--no-ff")
        args.append(sourcebranch)
        self.start_program_synchronously_argsasarray("git", args, directory, timeoutInSeconds=100, verbosity=0,
                                                     prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        return self.git_get_current_commit_id(directory)

    def git_undo_all_changes(self, directory: str) -> None:
        """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
        self.git_unstage_all_changes(directory)
        self.git_discard_all_unstaged_changes(directory)

    def __undo_changes(self, repository: str) -> None:
        if(self.git_repository_has_uncommitted_changes(repository)):
            self.git_undo_all_changes(repository)

    def __repository_has_changes(self, repository: str) -> None:
        if(self.git_repository_has_uncommitted_changes(repository)):
            GeneralUtilities.write_message_to_stderr(f"'{repository}' contains uncommitted changes")
            return True
        else:
            return False

    def file_is_git_ignored(self, file_in_repository: str, repositorybasefolder: str) -> None:
        exit_code = self.start_program_synchronously_argsasarray("git", ['check-ignore', file_in_repository],
                                                                 repositorybasefolder, 0, False, None, 120, False, prevent_using_epew=True)[0]
        if(exit_code == 0):
            return True
        if(exit_code == 1):
            return False
        raise Exception(f"Unable to calculate whether '{file_in_repository}' in repository '{repositorybasefolder}' is ignored due to git-exitcode {exit_code}.")

    def discard_all_changes(self, repository: str) -> None:
        self.start_program_synchronously_argsasarray("git", ["reset", "HEAD", "."], repository, throw_exception_if_exitcode_is_not_zero=True)
        self.start_program_synchronously_argsasarray("git", ["checkout", "."], repository, throw_exception_if_exitcode_is_not_zero=True)

    def git_get_current_branch_name(self, repository: str) -> str:
        result = self.start_program_synchronously_argsasarray("git", ["rev-parse", "--abbrev-ref", "HEAD"], repository,
                                                              timeoutInSeconds=100, verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        return result[1].replace("\r", "").replace("\n", "")

    # </git>

    # <miscellaneous>

    def export_filemetadata(self, folder: str, target_file: str, encoding: str = "utf-8", filter_function=None) -> None:
        folder = GeneralUtilities.resolve_relative_path_from_current_working_directory(folder)
        lines = list()
        path_prefix = len(folder)+1
        items = dict()
        for item in GeneralUtilities.get_all_files_of_folder(folder):
            items[item] = "f"
        for item in GeneralUtilities.get_all_folders_of_folder(folder):
            items[item] = "d"
        for file_or_folder, item_type in items.items():
            truncated_file = file_or_folder[path_prefix:]
            if(filter_function is None or filter_function(folder, truncated_file)):
                owner_and_permisssion = self.get_file_owner_and_file_permission(file_or_folder)
                user = owner_and_permisssion[0]
                permissions = owner_and_permisssion[1]
                lines.append(f"{truncated_file};{item_type};{user};{permissions}")
        lines = sorted(lines, key=str.casefold)
        with open(target_file, "w", encoding=encoding) as file_object:
            file_object.write("\n".join(lines))

    def restore_filemetadata(self, folder: str, source_file: str, strict=False, encoding: str = "utf-8") -> None:
        for line in GeneralUtilities.read_lines_from_file(source_file, encoding):
            splitted: list = line.split(";")
            full_path_of_file_or_folder: str = os.path.join(folder, splitted[0])
            filetype: str = splitted[1]
            user: str = splitted[2]
            permissions: str = splitted[3]
            if (filetype == "f" and os.path.isfile(full_path_of_file_or_folder)) or (filetype == "d" and os.path.isdir(full_path_of_file_or_folder)):
                self.set_owner(full_path_of_file_or_folder, user, os.name != 'nt')
                self.set_permission(full_path_of_file_or_folder, permissions)
            else:
                if strict:
                    if filetype == "f":
                        filetype_full = "File"
                    if filetype == "d":
                        filetype_full = "Directory"
                    raise Exception(f"{filetype_full} '{full_path_of_file_or_folder}' does not exist")

    def __verbose_check_for_not_available_item(self, configparser: ConfigParser, queried_items: list, section: str, propertyname: str) -> None:
        if self.__get_verbosity_for_exuecutor(configparser) > 0:
            for item in queried_items:
                self.private_check_for_not_available_config_item(item, section, propertyname)

    def private_check_for_not_available_config_item(self, item, section: str, propertyname: str):
        if item == "<notavailable>":
            GeneralUtilities.write_message_to_stderr(f"Warning: The property '{section}.{propertyname}' which is not available was queried. "
                                                     + "This may result in errors or involuntary behavior")
            GeneralUtilities.print_stacktrace()

    def __get_verbosity_for_exuecutor(self, configparser: ConfigParser) -> int:
        return self.get_number_value_from_configuration(configparser, 'other', 'verbose')

    def __get_buildoutputdirectory(self, configparser: ConfigParser, runtime: str, current_release_information: dict[str, str]) -> str:
        result = self.get_item_from_configuration(configparser, 'dotnet', 'buildoutputdirectory', current_release_information)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'separatefolderforeachruntime', current_release_information):
            result = result+os.path.sep+runtime
        return result

    def get_boolean_value_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str, current_release_information: dict[str, str]) -> bool:
        try:
            value = configparser.get(section, propertyname)
            self.private_check_for_not_available_config_item(value, section, propertyname)
            return configparser.getboolean(section, propertyname)
        except:
            try:
                return GeneralUtilities.string_to_boolean(self.get_item_from_configuration(configparser, section, propertyname, current_release_information))
            except:
                return False

    def get_number_value_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str) -> int:
        value = configparser.get(section, propertyname)
        self.private_check_for_not_available_config_item(value, section, propertyname)
        return int(value)

    def configuration_item_is_available(self, configparser: ConfigParser, sectioon: str, item: str) -> bool:
        if not configparser.has_option(sectioon, item):
            return False
        plain_value = configparser.get(sectioon, item)
        if GeneralUtilities.string_is_none_or_whitespace(plain_value):
            return False
        if plain_value == "<notavailable>":
            return False
        return True

    def __calculate_version(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> None:
        if "builtin.version" not in current_release_information:
            current_release_information['builtin.version'] = self.get_semver_version_from_gitversion(
                self.get_item_from_configuration(configparser, 'general', 'repository', current_release_information))

    def get_item_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str, current_release_information: dict[str, str]) -> str:

        now = datetime.now()
        current_release_information["builtin.year"] = str(now.year)
        current_release_information["builtin.month"] = str(now.month)
        current_release_information["builtin.day"] = str(now.day)

        result = self.__replace_underscores_for_buildconfiguration(f"__.{section}.{propertyname}.__", configparser, current_release_information)
        result = GeneralUtilities.strip_new_line_character(result)
        self.__verbose_check_for_not_available_item(configparser, [result], section, propertyname)
        return result

    def get_items_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str, current_release_information: dict[str, str]) -> list[str]:
        itemlist_as_string = self.__replace_underscores_for_buildconfiguration(f"__.{section}.{propertyname}.__", configparser, current_release_information)
        if not GeneralUtilities.string_has_content(itemlist_as_string):
            return []
        if ',' in itemlist_as_string:
            result = [item.strip() for item in itemlist_as_string.split(',')]
        else:
            result = [itemlist_as_string.strip()]
        self.__verbose_check_for_not_available_item(configparser, result, section, propertyname)
        return result

    def __get_csprojfile_filename(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "csprojfile", current_release_information)
        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        result = os.path.basename(file)
        return result

    def __get_test_csprojfile_filename(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "testcsprojfile", current_release_information)
        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        result = os.path.basename(file)
        return result

    def __get_csprojfile_folder(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "csprojfile", current_release_information)
        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        result = os.path.dirname(file)
        return result

    def __get_test_csprojfile_folder(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "testcsprojfile", current_release_information)
        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        result = os.path.dirname(file)
        return result

    def __get_coverage_filename(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        return self.get_item_from_configuration(configparser, "general", "productname", current_release_information)+".TestCoverage.opencover.xml"

    def get_version_for_buildscripts(self, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        return self.get_item_from_configuration(configparser, 'builtin', 'version', current_release_information)

    def __replace_underscores_for_buildconfiguration(self, string: str, configparser: ConfigParser, current_release_information: dict[str, str]) -> str:
        # TODO improve performance: the content of this function must mostly be executed once at the begining of a create-release-process, not always again

        available_configuration_items = []

        available_configuration_items.append(["docker", "artefactdirectory"])
        available_configuration_items.append(["docker", "contextfolder"])
        available_configuration_items.append(["docker", "dockerfile"])
        available_configuration_items.append(["docker", "registryaddress"])
        available_configuration_items.append(["dotnet", "csprojfile"])
        available_configuration_items.append(["dotnet", "buildoutputdirectory"])
        available_configuration_items.append(["dotnet", "publishdirectory"])
        available_configuration_items.append(["dotnet", "runtimes"])
        available_configuration_items.append(["dotnet", "dotnetframework"])
        available_configuration_items.append(["dotnet", "buildconfiguration"])
        available_configuration_items.append(["dotnet", "filestosign"])
        available_configuration_items.append(["dotnet", "snkfile"])
        available_configuration_items.append(["dotnet", "testdotnetframework"])
        available_configuration_items.append(["dotnet", "testcsprojfile"])
        available_configuration_items.append(["dotnet", "localnugettargets"])
        available_configuration_items.append(["dotnet", "testbuildconfiguration"])
        available_configuration_items.append(["dotnet", "docfxfile"])
        available_configuration_items.append(["dotnet", "coveragefolder"])
        available_configuration_items.append(["dotnet", "coveragereportfolder"])
        available_configuration_items.append(["dotnet", "referencerepository"])
        available_configuration_items.append(["dotnet", "exportreferenceremotename"])
        available_configuration_items.append(["dotnet", "nugetsource"])
        available_configuration_items.append(["dotnet", "iconfile"])
        available_configuration_items.append(["dotnet", "exportreferencelocalbranchname"])
        available_configuration_items.append(["dotnet", "nugetapikeyfile"])
        available_configuration_items.append(["general", "productname"])
        available_configuration_items.append(["general", "basefolder"])
        available_configuration_items.append(["general", "logfilefolder"])
        available_configuration_items.append(["general", "repository"])
        available_configuration_items.append(["general", "author"])
        available_configuration_items.append(["general", "description"])
        available_configuration_items.append(["prepare", "sourcebranchname"])
        available_configuration_items.append(["prepare", "targetbranchname"])
        available_configuration_items.append(["prepare", "gittagprefix"])
        available_configuration_items.append(["script", "premerge_program"])
        available_configuration_items.append(["script", "premerge_argument"])
        available_configuration_items.append(["script", "premerge_argument"])
        available_configuration_items.append(["script", "postmerge_program"])
        available_configuration_items.append(["script", "postmerge_argument"])
        available_configuration_items.append(["script", "postmerge_workingdirectory"])
        available_configuration_items.append(["other", "codecoverageshieldreplacementfiles"])
        available_configuration_items.append(["other", "releaserepository"])
        available_configuration_items.append(["other", "gpgidentity"])
        available_configuration_items.append(["other", "projecturl"])
        available_configuration_items.append(["other", "repositoryurl"])
        available_configuration_items.append(["other", "exportrepositoryremotename"])
        available_configuration_items.append(["other", "minimalrequiredtestcoverageinpercent"])
        available_configuration_items.append(["python", "readmefile"])
        available_configuration_items.append(["python", "pythonsetuppyfile"])
        available_configuration_items.append(["python", "filesforupdatingversion"])
        available_configuration_items.append(["python", "pypiapikeyfile"])
        available_configuration_items.append(["python", "publishdirectoryforwhlfile"])

        for item in available_configuration_items:
            if configparser.has_option(item[0], item[1]):
                current_release_information[f"{item[0]}.{item[1]}"] = configparser.get(item[0], item[1])

        changed = True
        result = string
        while changed:
            changed = False
            for key, value in current_release_information.items():
                previousValue = result
                result = result.replace(f"__.{key}.__", str(value))
                if(not result == previousValue):
                    changed = True

        return result

    def __create_dotnet_release_premerge(self, configurationfile: str, current_release_information: dict[str, str]):
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'createexe', current_release_information):
            self.dotnet_create_executable_release_premerge(configurationfile, current_release_information)
        else:
            self.dotnet_create_nuget_release_premerge(configurationfile, current_release_information)

    def __create_dotnet_release_postmerge(self, configurationfile: str, current_release_information: dict[str, str]):
        configparser = ConfigParser()
        with(open(configurationfile, mode="r", encoding="utf-8")) as text_io_wrapper:
            configparser.read_file(text_io_wrapper)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'createexe', current_release_information):
            self.dotnet_create_executable_release_postmerge(configurationfile, current_release_information)
        else:
            self.dotnet_create_nuget_release_postmerge(configurationfile, current_release_information)

    def __calculate_lengh_in_seconds(self, filename: str, folder: str) -> float:
        argument = f'-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filename}"'
        return float(self.execute_and_raise_exception_if_exit_code_is_not_zero("ffprobe", argument, folder)[1])

    def __create_thumbnails(self, filename: str, fps: float, folder: str, tempname_for_thumbnails: str) -> None:
        argument = f'-i "{filename}" -r {str(fps)} -vf scale=-1:120 -vcodec png {tempname_for_thumbnails}-%002d.png'
        self.execute_and_raise_exception_if_exit_code_is_not_zero("ffmpeg", argument, folder)

    def __create_thumbnail(self, outputfilename: str, folder: str, length_in_seconds: float, tempname_for_thumbnails: str, amount_of_images: int) -> None:
        duration = timedelta(seconds=length_in_seconds)
        info = GeneralUtilities.timedelta_to_simple_string(duration)
        next_square_number = str(int(math.sqrt(GeneralUtilities.get_next_square_number(amount_of_images))))
        argument = f'-title "{outputfilename} ({info})" -geometry +{next_square_number}+{next_square_number} {tempname_for_thumbnails}*.png "{outputfilename}.png"'
        self.execute_and_raise_exception_if_exit_code_is_not_zero("montage", argument, folder)

    def generate_thumbnail(self, file: str, frames_per_second: str, tempname_for_thumbnails: str = None) -> None:
        if tempname_for_thumbnails is None:
            tempname_for_thumbnails = "t"+str(uuid.uuid4())

        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        filename = os.path.basename(file)
        folder = os.path.dirname(file)
        filename_without_extension = Path(file).stem

        try:
            length_in_seconds = self.__calculate_lengh_in_seconds(filename, folder)
            if(frames_per_second.endswith("fps")):
                # frames per second, example: frames_per_second="20fps" => 20 frames per second
                frames_per_second = round(float(frames_per_second[:-3]), 2)
                amounf_of_previewframes = math.floor(length_in_seconds*frames_per_second)
            else:
                # concrete amount of frame, examples: frames_per_second="16" => 16 frames for entire video
                amounf_of_previewframes = float(frames_per_second)
                frames_per_second = round(amounf_of_previewframes/length_in_seconds, 2)
            self.__create_thumbnails(filename, frames_per_second, folder, tempname_for_thumbnails)
            self.__create_thumbnail(filename_without_extension, folder, length_in_seconds, tempname_for_thumbnails, amounf_of_previewframes)
        finally:
            for thumbnail_to_delete in Path(folder).rglob(tempname_for_thumbnails+"-*"):
                file = str(thumbnail_to_delete)
                os.remove(file)

    def merge_pdf_files(self, files, outputfile: str) -> None:
        # TODO add wildcard-option
        pdfFileMerger = PdfFileMerger()
        for file in files:
            pdfFileMerger.append(file.strip())
        pdfFileMerger.write(outputfile)
        pdfFileMerger.close()
        return 0

    def SCShowMissingFiles(self, folderA: str, folderB: str):
        for file in GeneralUtilities.get_missing_files(folderA, folderB):
            GeneralUtilities.write_message_to_stdout(file)

    def SCCreateEmptyFileWithSpecificSize(self, name: str, size_string: str) -> int:
        if size_string.isdigit():
            size = int(size_string)
        else:
            if len(size_string) >= 3:
                if(size_string.endswith("kb")):
                    size = int(size_string[:-2]) * pow(10, 3)
                elif(size_string.endswith("mb")):
                    size = int(size_string[:-2]) * pow(10, 6)
                elif(size_string.endswith("gb")):
                    size = int(size_string[:-2]) * pow(10, 9)
                elif(size_string.endswith("kib")):
                    size = int(size_string[:-3]) * pow(2, 10)
                elif(size_string.endswith("mib")):
                    size = int(size_string[:-3]) * pow(2, 20)
                elif(size_string.endswith("gib")):
                    size = int(size_string[:-3]) * pow(2, 30)
                else:
                    GeneralUtilities.write_message_to_stderr("Wrong format")
            else:
                GeneralUtilities.write_message_to_stderr("Wrong format")
                return 1
        with open(name, "wb") as f:
            f.seek(size-1)
            f.write(b"\0")
        return 0

    def SCCreateHashOfAllFiles(self, folder: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            with open(file+".sha256", "w+", encoding="utf-8") as f:
                f.write(GeneralUtilities.get_sha256_of_file(file))

    def SCCreateSimpleMergeWithoutRelease(self, repository: str, sourcebranch: str, targetbranch: str, remotename: str, remove_source_branch: bool) -> None:
        commitid = self.git_merge(repository, sourcebranch, targetbranch, False, True)
        self.git_merge(repository, targetbranch, sourcebranch, True, True)
        created_version = self.get_semver_version_from_gitversion(repository)
        self.git_create_tag(repository, commitid, f"v{created_version}", True)
        self.git_push(repository, remotename, targetbranch, targetbranch, False, True)
        if (GeneralUtilities.string_has_nonwhitespace_content(remotename)):
            self.git_push(repository, remotename, sourcebranch, sourcebranch, False, True)
        if(remove_source_branch):
            self.git_remove_branch(repository, sourcebranch)

    def sc_organize_lines_in_file(self, file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False,
                                  remove_empty_lines: bool = True, ignored_start_character: list = list()) -> int:
        if os.path.isfile(file):

            # read file
            lines = GeneralUtilities.read_lines_from_file(file, encoding)
            if(len(lines) == 0):
                return 0

            # store first line if desiredpopd

            if(ignore_first_line):
                first_line = lines.pop(0)

            # remove empty lines if desired
            if remove_empty_lines:
                temp = lines
                lines = []
                for line in temp:
                    if(not (GeneralUtilities.string_is_none_or_whitespace(line))):
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

    def __adapt_line_for_sorting(self, line: str, ignored_start_characters: list):
        result = line.lower()
        while len(result) > 0 and result[0] in ignored_start_characters:
            result = result[1:]
        return result

    def SCGenerateSnkFiles(self, outputfolder, keysize=4096, amountofkeys=10) -> int:
        GeneralUtilities.ensure_directory_exists(outputfolder)
        for _ in range(amountofkeys):
            file = os.path.join(outputfolder, str(uuid.uuid4())+".snk")
            argument = f"-k {keysize} {file}"
            self.execute_and_raise_exception_if_exit_code_is_not_zero("sn", argument, outputfolder)

    def __merge_files(self, sourcefile: str, targetfile: str) -> None:
        with open(sourcefile, "rb") as f:
            source_data = f.read()
        with open(targetfile, "ab") as fout:
            merge_separator = [0x0A]
            fout.write(bytes(merge_separator))
            fout.write(source_data)

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
                        if(os.path.getmtime(file) - os.path.getmtime(new_filename) > 0):
                            send2trash.send2trash(file)
                        else:
                            send2trash.send2trash(new_filename)
                            os.rename(file, new_filename)
                    elif(conflictResolveMode == "merge"):
                        self.__merge_files(file, new_filename)
                        send2trash.send2trash(file)
                    else:
                        raise Exception('Unknown conflict resolve mode')
            else:
                os.rename(file, new_filename)

    def SCReplaceSubstringsInFilenames(self, folder: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            self.__process_file(file, substringInFilename, newSubstringInFilename, conflictResolveMode)

    def __check_file(self, file: str, searchstring: str) -> None:
        bytes_ascii = bytes(searchstring, "ascii")
        bytes_utf16 = bytes(searchstring, "utf-16")  # often called "unicode-encoding"
        bytes_utf8 = bytes(searchstring, "utf-8")
        with open(file, mode='rb') as file_object:
            content = file_object.read()
            if bytes_ascii in content:
                GeneralUtilities.write_message_to_stdout(file)
            elif bytes_utf16 in content:
                GeneralUtilities.write_message_to_stdout(file)
            elif bytes_utf8 in content:
                GeneralUtilities.write_message_to_stdout(file)

    def SCSearchInFiles(self, folder: str, searchstring: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            self.__check_file(file, searchstring)

    def __print_qr_code_by_csv_line(self, displayname, website, emailaddress, key, period) -> None:
        qrcode_content = f"otpauth://totp/{website}:{emailaddress}?secret={key}&issuer={displayname}&period={period}"
        GeneralUtilities.write_message_to_stdout(f"{displayname} ({emailaddress}):")
        GeneralUtilities.write_message_to_stdout(qrcode_content)
        call(["qr", qrcode_content])

    def SCShow2FAAsQRCode(self, csvfile: str) -> None:
        separator_line = "--------------------------------------------------------"
        for line in GeneralUtilities.read_csv_file(csvfile, True):
            GeneralUtilities.write_message_to_stdout(separator_line)
            self.__print_qr_code_by_csv_line(line[0], line[1], line[2], line[3], line[4])
        GeneralUtilities.write_message_to_stdout(separator_line)

    def SCUpdateNugetpackagesInCsharpProject(self, csprojfile: str) -> int:
        outdated_packages = self.get_nuget_packages_of_csproj_file(csprojfile, True)
        GeneralUtilities.write_message_to_stdout("The following packages will be updated:")
        for outdated_package in outdated_packages:
            GeneralUtilities.write_message_to_stdout(outdated_package)
            self.update_nuget_package(csprojfile, outdated_package)
        GeneralUtilities.write_message_to_stdout(f"{len(outdated_packages)} package(s) were updated")
        return len(outdated_packages) > 0

    def SCUploadFileToFileHost(self, file: str, host: str) -> int:
        try:
            GeneralUtilities.write_message_to_stdout(self.upload_file_to_file_host(file, host))
            return 0
        except Exception as exception:
            GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback)
            return 1

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

    def __adjust_folder_name(self, folder: str) -> str:
        result = os.path.dirname(folder).replace("\\", "/")
        if result == "/":
            return ""
        else:
            return result

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
                with(open(full_path, "rb").read()) as text_io_wrapper:
                    content = text_io_wrapper
                    path_in_iso = '/' + files_directory + self.__adjust_folder_name(full_path[len(folder)::1]).upper()
                    if path_in_iso not in created_directories:
                        iso.add_directory(path_in_iso)
                        created_directories.append(path_in_iso)
                    iso.add_fp(BytesIO(content), len(content), path_in_iso + '/' + file.upper() + ';1')
        iso.write(iso_file)
        iso.close()

    def SCCreateISOFileWithObfuscatedFiles(self, inputfolder: str, outputfile: str, printtableheadline, createisofile, extensions) -> None:
        if (os.path.isdir(inputfolder)):
            namemappingfile = "name_map.csv"
            files_directory = inputfolder
            files_directory_obf = files_directory + "_Obfuscated"
            self.SCObfuscateFilesFolder(inputfolder, printtableheadline, namemappingfile, extensions)
            os.rename(namemappingfile, os.path.join(files_directory_obf, namemappingfile))
            if createisofile:
                self.__create_iso(files_directory_obf, outputfile)
                shutil.rmtree(files_directory_obf)
        else:
            raise Exception(f"Directory not found: '{inputfolder}'")

    def SCFilenameObfuscator(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if(not obfuscate_all_files):
            obfuscate_file_extensions = extensions.split(",")

        if (os.path.isdir(inputfolder)):
            printtableheadline = GeneralUtilities.string_to_boolean(printtableheadline)
            files = []
            if not os.path.isfile(namemappingfile):
                with open(namemappingfile, "a", encoding="utf-8"):
                    pass
            if printtableheadline:
                GeneralUtilities.append_line_to_file(namemappingfile, "Original filename;new filename;SHA2-hash of file")
            for file in GeneralUtilities.absolute_file_paths(inputfolder):
                if os.path.isfile(os.path.join(inputfolder, file)):
                    if obfuscate_all_files or self.__extension_matchs(file, obfuscate_file_extensions):
                        files.append(file)
            for file in files:
                hash_value = GeneralUtilities.get_sha256_of_file(file)
                extension = Path(file).suffix
                new_file_name_without_path = str(uuid.uuid4())[0:8] + extension
                new_file_name = os.path.join(os.path.dirname(file), new_file_name_without_path)
                os.rename(file, new_file_name)
                GeneralUtilities.append_line_to_file(namemappingfile, os.path.basename(file) + ";" + new_file_name_without_path + ";" + hash_value)
        else:
            raise Exception(f"Directory not found: '{inputfolder}'")

    def __extension_matchs(self, file: str, obfuscate_file_extensions) -> bool:
        for extension in obfuscate_file_extensions:
            if file.lower().endswith("."+extension.lower()):
                return True
        return False

    def SCObfuscateFilesFolder(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if(not obfuscate_all_files):
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
            raise Exception(f"Directory not found: '{inputfolder}'")

    def upload_file_to_file_host(self, file: str, host: str) -> int:
        if(host is None):
            return self.upload_file_to_random_filesharing_service(file)
        elif host == "anonfiles.com":
            return self.upload_file_to_anonfiles(file)
        elif host == "bayfiles.com":
            return self.upload_file_to_bayfiles(file)
        GeneralUtilities.write_message_to_stderr("Unknown host: "+host)
        return 1

    def upload_file_to_random_filesharing_service(self, file: str) -> int:
        host = randrange(2)
        if host == 0:
            return self.upload_file_to_anonfiles(file)
        if host == 1:
            return self.upload_file_to_bayfiles(file)
        return 1

    def upload_file_to_anonfiles(self, file) -> int:
        return self.upload_file_by_using_simple_curl_request("https://api.anonfiles.com/upload", file)

    def upload_file_to_bayfiles(self, file) -> int:
        return self.upload_file_by_using_simple_curl_request("https://api.bayfiles.com/upload", file)

    def upload_file_by_using_simple_curl_request(self, api_url: str, file: str) -> int:
        # TODO implement
        return 1

    def file_is_available_on_file_host(self, file) -> int:
        # TODO implement
        return 1

    def python_file_has_errors(self, file, treat_warnings_as_errors: bool = True) -> tuple[bool, list[str]]:
        errors = list()
        folder = os.path.dirname(file)
        filename = os.path.basename(file)
        GeneralUtilities.write_message_to_stdout(f"Start checking {file}...")
        if treat_warnings_as_errors:
            errorsonly_argument = ""
        else:
            errorsonly_argument = " --errors-only"
        (exit_code, stdout, stderr, _) = self.start_program_synchronously("pylint", filename+errorsonly_argument, folder)
        if(exit_code != 0):
            errors.append(f"Linting-issues of {file}:")
            errors.append(f"Pylint-exitcode: {exit_code}")
            for line in GeneralUtilities.string_to_lines(stdout):
                errors.append(line)
            for line in GeneralUtilities.string_to_lines(stderr):
                errors.append(line)
            return (True, errors)

        return (False, errors)

    def get_nuget_packages_of_csproj_file(self, csproj_file: str, only_outdated_packages: bool) -> bool:
        self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'restore --disable-parallel --force --force-evaluate "{csproj_file}"')
        if only_outdated_packages:
            only_outdated_packages_argument = " --outdated"
        else:
            only_outdated_packages_argument = ""
        stdout = self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'list "{csproj_file}" package{only_outdated_packages_argument}')[1]
        result = []
        for line in stdout.splitlines():
            trimmed_line = line.replace("\t", "").strip()
            if trimmed_line.startswith(">"):
                result.append(trimmed_line[2:].split(" ")[0])
        return result

    def update_nuget_package(self, csproj_file: str, name: str) -> None:
        self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'add "{csproj_file}" package {name}')

    def get_file_permission(self, file: str) -> str:
        """This function returns an usual octet-triple, for example "0700"."""
        ls_output = self.__ls(file)
        return self.__get_file_permission_helper(ls_output)

    def __get_file_permission_helper(self, ls_output: str) -> str:
        permissions = ' '.join(ls_output.split()).split(' ')[0][1:]
        return str(self.__to_octet(permissions[0:3]))+str(self.__to_octet(permissions[3:6]))+str(self.__to_octet(permissions[6:9]))

    def __to_octet(self, string: str) -> int:
        return int(self.__to_octet_helper(string[0])+self.__to_octet_helper(string[1])+self.__to_octet_helper(string[2]), 2)

    def __to_octet_helper(self, string: str) -> str:
        if(string == "-"):
            return "0"
        else:
            return "1"

    def get_file_owner(self, file: str) -> str:
        """This function returns the user and the group in the format "user:group"."""
        ls_output = self.__ls(file)
        return self.__get_file_owner_helper(ls_output)

    def __get_file_owner_helper(self, ls_output: str) -> str:
        try:
            splitted = ' '.join(ls_output.split()).split(' ')
            return f"{splitted[2]}:{splitted[3]}"
        except Exception as exception:
            raise ValueError(f"ls-output '{ls_output}' not parsable") from exception

    def get_file_owner_and_file_permission(self, file: str) -> str:
        ls_output = self.__ls(file)
        return [self.__get_file_owner_helper(ls_output), self.__get_file_permission_helper(ls_output)]

    def __ls(self, file: str) -> str:
        file = file.replace("\\", "/")
        GeneralUtilities.assert_condition(os.path.isfile(file) or os.path.isdir(file), f"Can not execute 'ls' because '{file}' does not exist")
        result = self.__start_internal_for_helper("ls", ["-ld", file])
        GeneralUtilities.assert_condition(result[0] == 0, f"'ls -ld {file}' resulted in exitcode {str(result[0])}. StdErr: {result[2]}")
        GeneralUtilities.assert_condition(not GeneralUtilities.string_is_none_or_whitespace(result[1]), f"'ls' of '{file}' had an empty output. StdErr: '{result[2]}'")
        return result[1]

    def set_permission(self, file_or_folder: str, permissions: str, recursive: bool = False) -> None:
        """This function expects an usual octet-triple, for example "700"."""
        args = []
        if recursive:
            args.append("--recursive")
        args.append(permissions)
        args.append(file_or_folder)
        self.start_program_synchronously_argsasarray("chmod", args)

    def set_owner(self, file_or_folder: str, owner: str, recursive: bool = False, follow_symlinks: bool = False) -> None:
        """This function expects the user and the group in the format "user:group"."""
        args = []
        if recursive:
            args.append("--recursive")
        if follow_symlinks:
            args.append("--no-dereference")
        args.append(owner)
        args.append(file_or_folder)
        self.start_program_synchronously_argsasarray("chown", args)

    def __adapt_workingdirectory(self, workingdirectory: str) -> str:
        if workingdirectory is None:
            return os.getcwd()
        else:
            return GeneralUtilities.resolve_relative_path_from_current_working_directory(workingdirectory)

    def __log_program_start(self, program: str, arguments: str, workingdirectory: str, verbosity: int = 1) -> None:
        if(verbosity == 2):
            GeneralUtilities.write_message_to_stdout(f"Start '{workingdirectory}>{program} {arguments}'")

    def start_program_asynchronously(self, program: str, arguments: str = "", workingdirectory: str = "", verbosity: int = 1, prevent_using_epew: bool = False,
                                     print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600, addLogOverhead: bool = False,
                                     title: str = None, log_namespace: str = "") -> int:
        workingdirectory = self.__adapt_workingdirectory(workingdirectory)
        if self.mock_program_calls:
            try:
                return self.__get_mock_program_call(program, arguments, workingdirectory)[3]
            except LookupError:
                if not self.execute_programy_really_if_no_mock_call_is_defined:
                    raise
        return self.__start_process(program, arguments, workingdirectory, verbosity, print_errors_as_information,
                                    log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, None, None, None, None)

    def start_program_asynchronously_argsasarray(self, program: str, argument_list: list = [], workingdirectory: str = "", verbosity: int = 1, prevent_using_epew: bool = False,
                                                 print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600, addLogOverhead: bool = False,
                                                 title: str = None, log_namespace: str = "") -> int:
        arguments = ' '.join(argument_list)
        workingdirectory = self.__adapt_workingdirectory(workingdirectory)
        if self.mock_program_calls:
            try:
                return self.__get_mock_program_call(program, arguments, workingdirectory)[3]
            except LookupError:
                if not self.execute_programy_really_if_no_mock_call_is_defined:
                    raise
        return self.__start_process_argsasarray(program, argument_list, workingdirectory, verbosity, print_errors_as_information,
                                                log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, None, None, None, None)

    def execute_and_raise_exception_if_exit_code_is_not_zero(self, program: str, arguments: str = "", workingdirectory: str = "",
                                                             timeoutInSeconds: int = 3600, verbosity: int = 1, addLogOverhead: bool = False, title: str = None,
                                                             print_errors_as_information: bool = False, log_file: str = None, prevent_using_epew: bool = False,
                                                             log_namespace: str = "") -> None:
        # TODO remove this function
        return self.start_program_synchronously(program, arguments, workingdirectory, verbosity,
                                                print_errors_as_information, log_file, timeoutInSeconds,
                                                addLogOverhead, title, True, prevent_using_epew, log_namespace)

    def __start_internal_for_helper(self, program: str, arguments: list, workingdirectory: str = None):
        return self.start_program_synchronously_argsasarray(program, arguments,
                                                            workingdirectory, verbosity=0, throw_exception_if_exitcode_is_not_zero=True, prevent_using_epew=True)

    def start_program_synchronously(self, program: str, arguments: str = "", workingdirectory: str = None, verbosity: int = 1,
                                    print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                                    addLogOverhead: bool = False, title: str = None,
                                    throw_exception_if_exitcode_is_not_zero: bool = False, prevent_using_epew: bool = False,
                                    log_namespace: str = ""):
        return self.start_program_synchronously_argsasarray(program, GeneralUtilities.arguments_to_array(arguments), workingdirectory, verbosity, print_errors_as_information,
                                                            log_file, timeoutInSeconds, addLogOverhead, title,
                                                            throw_exception_if_exitcode_is_not_zero, prevent_using_epew, log_namespace)

    def start_program_synchronously_argsasarray(self, program: str, argument_list: list = [], workingdirectory: str = None, verbosity: int = 1,
                                                print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                                                addLogOverhead: bool = False, title: str = None,
                                                throw_exception_if_exitcode_is_not_zero: bool = False, prevent_using_epew: bool = False,
                                                log_namespace: str = ""):
        arguments = ' '.join(argument_list)
        workingdirectory = self.__adapt_workingdirectory(workingdirectory)
        if self.mock_program_calls:
            try:
                return self.__get_mock_program_call(program, arguments, workingdirectory)
            except LookupError:
                if not self.execute_programy_really_if_no_mock_call_is_defined:
                    raise
        cmd = f'{workingdirectory}>{program} {arguments}'
        if (self.__epew_is_available and not prevent_using_epew):
            tempdir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            output_file_for_stdout = tempdir + ".epew.stdout.txt"
            output_file_for_stderr = tempdir + ".epew.stderr.txt"
            output_file_for_exit_code = tempdir + ".epew.exitcode.txt"
            output_file_for_pid = tempdir + ".epew.pid.txt"
            process = self.__start_process(program, arguments, workingdirectory, verbosity, print_errors_as_information,
                                           log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, output_file_for_stdout, output_file_for_stderr,
                                           output_file_for_pid, output_file_for_exit_code)
            process.wait()
            stdout = self.__load_text(output_file_for_stdout)
            stderr = self.__load_text(output_file_for_stderr)
            exit_code = self.__get_number_from_filecontent(self.__load_text(output_file_for_exit_code))
            pid = self.__get_number_from_filecontent(self.__load_text(output_file_for_pid))
            GeneralUtilities.ensure_directory_does_not_exist(tempdir)
            if GeneralUtilities.string_is_none_or_whitespace(title):
                title_for_message = ""
            else:
                title_for_message = f"for task '{title}' "
            title_local = f"epew {title_for_message}('{cmd}')"
            result = (exit_code, stdout, stderr, pid)
        else:
            if GeneralUtilities.string_is_none_or_whitespace(title):
                title_local = cmd
            else:
                title_local = title
            arguments_for_process = [program]
            arguments_for_process.extend(argument_list)
            with Popen(arguments_for_process, stdout=PIPE, stderr=PIPE, cwd=workingdirectory, shell=False) as process:
                pid = process.pid
                stdout, stderr = process.communicate()
                exit_code = process.wait()
                stdout = GeneralUtilities.bytes_to_string(stdout).replace('\r', '')
                stderr = GeneralUtilities.bytes_to_string(stderr).replace('\r', '')
                result = (exit_code, stdout, stderr, pid)
        if verbosity == 3:
            GeneralUtilities.write_message_to_stdout(f"Finished executing '{title_local}' with exitcode {str(exit_code)}")
        if throw_exception_if_exitcode_is_not_zero and exit_code != 0:
            raise Exception(f"'{title_local}' had exitcode {str(exit_code)}. (StdOut: '{stdout}'; StdErr: '{stderr}')")
        else:
            return result

    def __start_process_argsasarray(self, program: str, argument_list: str, workingdirectory: str = None, verbosity: int = 1,
                                    print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                                    addLogOverhead: bool = False, title: str = None, log_namespace: str = "", stdoutfile: str = None,
                                    stderrfile: str = None, pidfile: str = None, exitcodefile: str = None):
        return self.__start_process(program, ' '.join(argument_list), workingdirectory, verbosity, print_errors_as_information, log_file,
                                    timeoutInSeconds, addLogOverhead, title, log_namespace, stdoutfile, stderrfile, pidfile, exitcodefile)

    def __start_process(self, program: str, arguments: str, workingdirectory: str = None, verbosity: int = 1,
                        print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                        addLogOverhead: bool = False, title: str = None, log_namespace: str = "", stdoutfile: str = None,
                        stderrfile: str = None, pidfile: str = None, exitcodefile: str = None):
        workingdirectory = self.__adapt_workingdirectory(workingdirectory)
        cmd = f'{workingdirectory}>{program} {arguments}'
        if(arguments is None):
            arguments = ""
        if GeneralUtilities.string_is_none_or_whitespace(title):
            title = ""
            title_for_message = ""
            title_argument = cmd
        title_for_message = f"for task '{title}' "
        title_argument = title
        self.__log_program_start(program, arguments, workingdirectory, verbosity)
        title_argument = title_argument.replace("\"", "'").replace("\\", "/")
        cmdcall = f"{workingdirectory}>{program} {arguments}"
        if verbosity >= 1:
            GeneralUtilities.write_message_to_stdout("Run "+cmdcall)
        title_local = f"epew {title_for_message}('{cmdcall}')"
        base64argument = base64.b64encode(arguments.encode('utf-8')).decode('utf-8')
        args = ["epew"]
        args.append(f'-p "{program}"')
        args.append(f'-a {base64argument}')
        args.append('-b')
        args.append(f'-w "{workingdirectory}"')
        if stdoutfile is not None:
            args.append(f'-o {stdoutfile}')
        if stderrfile is not None:
            args.append(f'-e {stderrfile}')
        if exitcodefile is not None:
            args.append(f'-x {exitcodefile}')
        if pidfile is not None:
            args.append(f'-r {pidfile}')
        args.append(f'-d {str(timeoutInSeconds*1000)}')
        args.append(f'-t "{title_argument}"')
        args.append(f'-l "{log_namespace}"')
        if not GeneralUtilities.string_is_none_or_whitespace(log_file):
            args.append(f'-f "{log_file}"')
        if print_errors_as_information:
            args.append("-i")
        if addLogOverhead:
            args.append("-h")
        args.append("-v "+str(verbosity))
        if verbosity == 3:
            args_as_string = " ".join(args)
            GeneralUtilities.write_message_to_stdout(f"Start executing '{title_local}' (epew-call: '{args_as_string}')")
        return Popen(args, shell=False)

    def verify_no_pending_mock_program_calls(self):
        if(len(self.__mocked_program_calls) > 0):
            raise AssertionError(
                "The following mock-calls were not called:\n    "+",\n    ".join([self.__format_mock_program_call(r) for r in self.__mocked_program_calls]))

    def __format_mock_program_call(self, r) -> str:
        return f"'{r.workingdirectory}>{r.program} {r.argument}' (" \
            f"exitcode: {GeneralUtilities.str_none_safe(str(r.exit_code))}, " \
            f"pid: {GeneralUtilities.str_none_safe(str(r.pid))}, "\
            f"stdout: {GeneralUtilities.str_none_safe(str(r.stdout))}, " \
            f"stderr: {GeneralUtilities.str_none_safe(str(r.stderr))})"

    def register_mock_program_call(self, program: str, argument: str, workingdirectory: str, result_exit_code: int, result_stdout: str, result_stderr: str,
                                   result_pid: int, amount_of_expected_calls=1):
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

    def __get_mock_program_call(self, program: str, argument: str, workingdirectory: str):
        result: ScriptCollectionCore.__MockProgramCall = None
        for mock_call in self.__mocked_program_calls:
            if((re.match(mock_call.program, program) is not None)
               and (re.match(mock_call.argument, argument) is not None)
               and (re.match(mock_call.workingdirectory, workingdirectory) is not None)):
                result = mock_call
                break
        if result is None:
            raise LookupError(f"Tried to execute mock-call '{workingdirectory}>{program} {argument}' but no mock-call was defined for that execution")
        else:
            self.__mocked_program_calls.remove(result)
            return (result.exit_code, result.stdout, result.stderr, result.pid)

    class __MockProgramCall:
        program: str
        argument: str
        workingdirectory: str
        exit_code: int
        stdout: str
        stderr: str
        pid: int

    def __get_number_from_filecontent(self, filecontent: str) -> int:
        for line in filecontent.splitlines():
            try:
                striped_line = GeneralUtilities.strip_new_line_character(line)
                result = int(striped_line)
                return result
            except:
                pass
        raise Exception(f"'{filecontent}' does not containe an int-line")

    def __load_text(self, file: str) -> str:
        if os.path.isfile(file):
            content = GeneralUtilities.read_text_from_file(file)
            os.remove(file)
            return content
        else:
            raise Exception(f"File '{file}' does not exist")

    def extract_archive_with_7z(self, unzip_program_file: str, zipfile: str, password: str, output_directory: str) -> None:
        password_set = not password is None
        file_name = Path(zipfile).name
        file_folder = os.path.dirname(zipfile)
        argument = "x"
        if password_set:
            argument = f"{argument} -p\"{password}\""
        argument = f"{argument} -o {output_directory}"
        argument = f"{argument} {file_name}"
        return self.execute_and_raise_exception_if_exit_code_is_not_zero(unzip_program_file, argument, file_folder)

    def get_internet_time(self) -> datetime:
        response = ntplib.NTPClient().request('pool.ntp.org')
        return datetime.fromtimestamp(response.tx_time)

    def system_time_equals_internet_time(self, maximal_tolerance_difference: timedelta) -> bool:
        return abs(datetime.now() - self.get_internet_time()) < maximal_tolerance_difference

    def system_time_equals_internet_time_with_default_tolerance(self) -> bool:
        return self.system_time_equals_internet_time(self.__get_default_tolerance_for_system_time_equals_internet_time())

    def check_system_time(self, maximal_tolerance_difference: timedelta):
        if not self.system_time_equals_internet_time(maximal_tolerance_difference):
            raise ValueError("System time may be wrong")

    def check_system_time_with_default_tolerance(self) -> None:
        self.check_system_time(self.__get_default_tolerance_for_system_time_equals_internet_time())

    def __get_default_tolerance_for_system_time_equals_internet_time(self) -> timedelta:
        return timedelta(hours=0, minutes=0, seconds=3)

    def get_semver_version_from_gitversion(self, folder: str) -> str:
        return self.get_version_from_gitversion(folder, "MajorMinorPatch")

    def get_version_from_gitversion(self, folder: str, variable: str) -> str:
        # called twice as workaround for bug in gitversion ( https://github.com/GitTools/GitVersion/issues/1877 )
        result = self.__start_internal_for_helper("gitversion", ["/showVariable", variable], folder)
        result = self.__start_internal_for_helper("gitversion", ["/showVariable", variable], folder)
        return GeneralUtilities.strip_new_line_character(result[1])

    def export_released_file_and_commit(self, whl_file_with_path: str, target_file: str, targetfolder_repository: str, product_name: str, version_of_release: str):
        copyfile(whl_file_with_path, target_file)
        self.git_commit(targetfolder_repository, f"Added {product_name} v{version_of_release}")

    # </miscellaneous>
