import argparse
import base64
import binascii
import codecs
import ctypes
import itertools
import filecmp
import hashlib
import math
import pathlib
import re
import os
import shutil
import stat
import sys
import tempfile
import time
import traceback
import uuid
from datetime import datetime, timedelta
from configparser import ConfigParser
from distutils.dir_util import copy_tree
from distutils.spawn import find_executable
from functools import lru_cache
from io import BytesIO
from os import listdir
from os.path import isfile, join, isdir
from pathlib import Path
from random import randrange
from shutil import copy2, copyfile
from subprocess import Popen, call, PIPE
from lxml import etree
from defusedxml.minidom import parse
from PyPDF2 import PdfFileMerger
import keyboard
import ntplib
import pycdlib
import send2trash

version = "2.5.25"
__version__ = version


class ScriptCollection:

    # <Properties>

    mock_program_calls: bool = False  # This property is for test-purposes only
    execute_programy_really_if_no_mock_call_is_defined: bool = False  # This property is for test-purposes only
    _private_mocked_program_calls: list = list()
    _private_constants_build_template_dockerfile_dotnet = "template://dockerfile_dotnet"
    _private_epew_is_available: bool = False
    # </Properties>

    def __init__(self):
        self._private_epew_is_available = epew_is_available()

    # <Build>

    # TODO use typechecks everywhere like disucced here https://stackoverflow.com/questions/19684434/best-way-to-check-function-arguments/37961120
    def create_release(self, configurationfile: str) -> int:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        error_occurred = False
        prepare = self.get_boolean_value_from_configuration(configparser, 'general', 'prepare')
        repository_version = self.get_version_for_buildscripts(configparser)
        repository = self.get_item_from_configuration(configparser, "general", "repository")
        write_message_to_stdout(f"Create release v{repository_version} for repository {repository}")
        releaserepository = self.get_item_from_configuration(configparser, "other", "releaserepository")

        if (self._private_repository_has_changes(repository) or self._private_repository_has_changes(releaserepository)):
            return 1

        if prepare:
            devbranch = self.get_item_from_configuration(configparser, 'prepare', 'developmentbranchname')
            masterbranch = self.get_item_from_configuration(configparser, 'prepare', 'masterbranchname')
            commitid = self.git_get_current_commit_id(repository, masterbranch)
            if(commitid == self.git_get_current_commit_id(repository, devbranch)):
                write_message_to_stderr(f"Can not prepare since the master-branch and the development-branch are on the same commit (commit-id: {commitid})")
                return 1
            self.git_checkout(repository, devbranch)
            self.git_merge(repository, devbranch, masterbranch, False, False)

        try:
            current_release_information = {}

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createdotnetrelease') and not error_occurred:
                write_message_to_stdout("Start to create .NET-release")
                error_occurred = not self._private_execute_and_return_boolean("create_dotnet_release",
                                                                              lambda: self._private_create_dotnet_release_premerge(configurationfile, current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createpythonrelease') and not error_occurred:
                write_message_to_stdout("Start to create Python-release")
                error_occurred = not self._private_execute_and_return_boolean("python_create_wheel_release",
                                                                              lambda: self.python_create_wheel_release_premerge(configurationfile, current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createdebrelease') and not error_occurred:
                write_message_to_stdout("Start to create Deb-release")
                error_occurred = not self._private_execute_and_return_boolean("deb_create_installer_release",
                                                                              lambda: self.deb_create_installer_release_premerge(configurationfile, current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createdockerrelease') and not error_occurred:
                write_message_to_stdout("Start to create docker-release")
                error_occurred = not self._private_execute_and_return_boolean("docker_create_installer_release",
                                                                              lambda: self.docker_create_installer_release_premerge(configurationfile,
                                                                                                                                    current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutterandroidrelease') and not error_occurred:
                write_message_to_stdout("Start to create FlutterAndroid-release")
                error_occurred = not self._private_execute_and_return_boolean("flutterandroid_create_installer_release",
                                                                              lambda: self.flutterandroid_create_installer_release_premerge(configurationfile,
                                                                                                                                            current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutteriosrelease') and not error_occurred:
                write_message_to_stdout("Start to create FlutterIOS-release")
                error_occurred = not self._private_execute_and_return_boolean("flutterios_create_installer_release",
                                                                              lambda: self.flutterios_create_installer_release_premerge(configurationfile,
                                                                                                                                        current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createscriptrelease') and not error_occurred:
                write_message_to_stdout("Start to create Script-release")
                error_occurred = not self._private_execute_and_return_boolean("generic_create_installer_release",
                                                                              lambda: self.generic_create_script_release_premerge(configurationfile, current_release_information))

            commit_id = self.git_commit(repository, f"Merge branch '{self.get_item_from_configuration(configparser, 'prepare', 'developmentbranchname')}' "
                                        f"into '{self.get_item_from_configuration(configparser, 'prepare', 'masterbranchname')}'")
            current_release_information["builtin.mergecommitid"] = commit_id

            # TODO allow multiple custom pre- (and post)-build-regex-replacements for files specified by glob-pattern
            # (like "!\[Generic\ badge\]\(https://img\.shields\.io/badge/coverage\-\d(\d)?%25\-green\)"
            # -> "![Generic badge](https://img.shields.io/badge/coverage-__testcoverage__%25-green)" in all "**/*.md"-files)

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createdotnetrelease') and not error_occurred:
                write_message_to_stdout("Start to create .NET-release")
                error_occurred = not self._private_execute_and_return_boolean("create_dotnet_release",
                                                                              lambda: self._private_create_dotnet_release_postmerge(configurationfile, current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createpythonrelease') and not error_occurred:
                write_message_to_stdout("Start to create Python-release")
                error_occurred = not self._private_execute_and_return_boolean("python_create_wheel_release",
                                                                              lambda: self.python_create_wheel_release_postmerge(configurationfile, current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createdebrelease') and not error_occurred:
                write_message_to_stdout("Start to create Deb-release")
                error_occurred = not self._private_execute_and_return_boolean("deb_create_installer_release",
                                                                              lambda: self.deb_create_installer_release_postmerge(configurationfile, current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createdockerrelease') and not error_occurred:
                write_message_to_stdout("Start to create docker-release")
                error_occurred = not self._private_execute_and_return_boolean("docker_create_installer_release",
                                                                              lambda: self.docker_create_installer_release_postmerge(configurationfile,
                                                                                                                                     current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutterandroidrelease') and not error_occurred:
                write_message_to_stdout("Start to create FlutterAndroid-release")
                error_occurred = not self._private_execute_and_return_boolean("flutterandroid_create_installer_release",
                                                                              lambda: self.flutterandroid_create_installer_release_postmerge(configurationfile,
                                                                                                                                             current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createflutteriosrelease') and not error_occurred:
                write_message_to_stdout("Start to create FlutterIOS-release")
                error_occurred = not self._private_execute_and_return_boolean("flutterios_create_installer_release",
                                                                              lambda: self.flutterios_create_installer_release_postmerge(configurationfile,
                                                                                                                                         current_release_information))

            if self.get_boolean_value_from_configuration(configparser, 'general', 'createscriptrelease') and not error_occurred:
                write_message_to_stdout("Start to create Script-release")
                error_occurred = not self._private_execute_and_return_boolean("generic_create_installer_release",
                                                                              lambda: self.generic_create_script_release_postmerge(configurationfile, current_release_information))

        except Exception as exception:
            error_occurred = True
            write_exception_to_stderr_with_traceback(exception, traceback, "Error occurred while creating release")

        finally:
            write_message_to_stdout("Finished to create releases")

        if error_occurred:
            write_message_to_stderr("Creating release was not successful")
            if prepare:
                self.git_merge_abort(repository)
                self._private_undo_changes(repository)
                self._private_undo_changes(releaserepository)
                self.git_checkout(repository, self.get_item_from_configuration(configparser, 'prepare', 'developmentbranchname'))
            return 1
        else:
            if prepare:
                self.git_merge(repository, self.get_item_from_configuration(configparser, 'prepare', 'masterbranchname'),
                               self.get_item_from_configuration(configparser, 'prepare', 'developmentbranchname'), True)
                tag = self.get_item_from_configuration(configparser, 'prepare', 'gittagprefix') + repository_version
                tag_message = f"Created {tag}"
                self.git_create_tag(repository, commit_id,
                                    tag, self.get_boolean_value_from_configuration(configparser, 'other', 'signtags'), tag_message)
                if self.get_boolean_value_from_configuration(configparser, 'other', 'exportrepository'):
                    branch = self.get_item_from_configuration(configparser, 'prepare', 'masterbranchname')
                    self.git_push(repository, self.get_item_from_configuration(configparser, 'other', 'exportrepositoryremotename'), branch, branch, False, True)
            write_message_to_stdout("Creating release was successful")
            return 0

    def dotnet_executable_build(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        verbosity = self._private_get_verbosity_for_exuecutor(configparser)
        sign_things = self._private_get_sign_things(configparser)
        config = self.get_item_from_configuration(configparser, 'dotnet', 'buildconfiguration')
        for runtime in self.get_items_from_configuration(configparser, 'dotnet', 'runtimes'):
            self.dotnet_build(self._private_get_csprojfile_folder(configparser), self._private_get_csprojfile_filename(configparser),
                              self._private_get_buildoutputdirectory(configparser, runtime), config,
                              runtime, self.get_item_from_configuration(configparser, 'dotnet', 'dotnetframework'), True,
                              verbosity, sign_things[0], sign_things[1], current_release_information)
        publishdirectory = self.get_item_from_configuration(configparser, 'dotnet', 'publishdirectory')
        ensure_directory_does_not_exist(publishdirectory)
        copy_tree(self.get_item_from_configuration(configparser, 'dotnet', 'buildoutputdirectory'), publishdirectory)

    def dotnet_executable_run_tests(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        verbosity = self._private_get_verbosity_for_exuecutor(configparser)
        if self.get_boolean_value_from_configuration(configparser, 'other', 'hastestproject'):
            self.dotnet_run_tests(configurationfile, current_release_information, verbosity)

    def _private_get_sign_things(self, configparser: ConfigParser) -> tuple:
        files_to_sign_raw_value = self.get_item_from_configuration(configparser, 'dotnet', 'filestosign')
        if(string_is_none_or_whitespace(files_to_sign_raw_value)):
            return [None, None]
        else:
            return [to_list(files_to_sign_raw_value, ";"), self.get_item_from_configuration(configparser, 'dotnet', 'snkfile')]

    def dotnet_create_executable_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        repository_version = self.get_version_for_buildscripts(configparser)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'updateversionsincsprojfile'):
            update_version_in_csproj_file(self.get_item_from_configuration(configparser, 'dotnet', 'csprojfile'), repository_version)
        self.dotnet_executable_run_tests(configurationfile, current_release_information)

    def dotnet_create_executable_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        self.dotnet_executable_build(configurationfile, current_release_information)
        self.dotnet_reference(configurationfile, current_release_information)

    def dotnet_create_nuget_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        repository_version = self.get_version_for_buildscripts(configparser)
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'updateversionsincsprojfile'):
            update_version_in_csproj_file(self.get_item_from_configuration(configparser, 'dotnet', 'csprojfile'), repository_version)
        self.dotnet_nuget_run_tests(configurationfile, current_release_information)

    def dotnet_create_nuget_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        self.dotnet_nuget_build(configurationfile, current_release_information)
        self.dotnet_reference(configurationfile, current_release_information)
        self.dotnet_release_nuget(configurationfile, current_release_information)

    _private_nuget_template = r"""<?xml version="1.0" encoding="utf-8"?>
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

    def dotnet_nuget_build(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        sign_things = self._private_get_sign_things(configparser)
        config = self.get_item_from_configuration(configparser, 'dotnet', 'buildconfiguration')
        for runtime in self.get_items_from_configuration(configparser, 'dotnet', 'runtimes'):
            self.dotnet_build(self._private_get_csprojfile_folder(configparser), self._private_get_csprojfile_filename(configparser),
                              self._private_get_buildoutputdirectory(configparser, runtime), config,
                              runtime, self.get_item_from_configuration(configparser, 'dotnet', 'dotnetframework'), True,
                              self._private_get_verbosity_for_exuecutor(configparser),
                              sign_things[0], sign_things[1], current_release_information)
        publishdirectory = self.get_item_from_configuration(configparser, 'dotnet', 'publishdirectory')
        publishdirectory_binary = publishdirectory+os.path.sep+"Binary"
        ensure_directory_does_not_exist(publishdirectory)
        ensure_directory_exists(publishdirectory_binary)
        copy_tree(self.get_item_from_configuration(configparser, 'dotnet', 'buildoutputdirectory'), publishdirectory_binary)
        replacements = {}

        nuspec_content = self._private_replace_underscores_for_buildconfiguration(self._private_nuget_template, configparser, replacements)

        if(self.configuration_item_is_available(configparser, "other", "projecturl")):
            nuspec_content = nuspec_content.replace("__.internal.projecturlentry.__",
                                                    f"<projectUrl>{self.get_item_from_configuration(configparser, 'other', 'projecturl')}</projectUrl>")
        else:
            nuspec_content = nuspec_content.replace("__.internal.projecturlentry.__", "")

        if "builtin.commitid" in current_release_information and self.configuration_item_is_available(configparser, "other", "repositoryurl"):
            repositoryurl = self.get_item_from_configuration(configparser, 'other', 'repositoryurl')
            branch = self.get_item_from_configuration(configparser, 'prepare', 'masterbranchname')
            commitid = current_release_information["builtin.commitid"]
            nuspec_content = nuspec_content.replace("__.internal.repositoryentry.__", f'<repository type="git" url="{repositoryurl}" branch="{branch}" commit="{commitid}" />')
        else:
            nuspec_content = nuspec_content.replace("__.internal.repositoryentry.__", "")

        if self.configuration_item_is_available(configparser, "dotnet", "iconfile"):
            shutil.copy2(self.get_item_from_configuration(configparser, "dotnet", "iconfile"), os.path.join(publishdirectory, "icon.png"))
            nuspec_content = nuspec_content.replace("__.internal.iconentry.__", '<icon>images\\icon.png</icon>')
            nuspec_content = nuspec_content.replace("__.internal.iconfileentry.__", '<file src=".\\icon.png" target="images\\" />')
        else:
            nuspec_content = nuspec_content.replace("__.internal.iconentry.__", "")
            nuspec_content = nuspec_content.replace("__.internal.iconfileentry.__", "")

        nuspecfilename = self.get_item_from_configuration(configparser, 'general', 'productname')+".nuspec"
        nuspecfile = os.path.join(publishdirectory, nuspecfilename)
        with open(nuspecfile, encoding="utf-8", mode="w") as file_object:
            file_object.write(nuspec_content)
        self.execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}", publishdirectory, 3600,
                                                                  self._private_get_verbosity_for_exuecutor(configparser))

    def dotnet_nuget_run_tests(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        verbosity = self._private_get_verbosity_for_exuecutor(configparser)
        if self.get_boolean_value_from_configuration(configparser, 'other', 'hastestproject'):
            self.dotnet_run_tests(configurationfile, current_release_information, verbosity)

    def dotnet_release_nuget(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        repository_version = self.get_version_for_buildscripts(configparser)
        publishdirectory = self.get_item_from_configuration(configparser, 'dotnet', 'publishdirectory')
        latest_nupkg_file = self.get_item_from_configuration(configparser, 'general', 'productname')+"."+repository_version+".nupkg"
        for localnugettarget in self.get_items_from_configuration(configparser, 'dotnet', 'localnugettargets'):
            self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}",
                                                                      publishdirectory, 3600,  self._private_get_verbosity_for_exuecutor(configparser))
        if (self.get_boolean_value_from_configuration(configparser, 'dotnet', 'publishnugetfile')):
            with open(self.get_item_from_configuration(configparser, 'dotnet', 'nugetapikeyfile'), 'r', encoding='utf-8') as apikeyfile:
                api_key = apikeyfile.read()
            nugetsource = self.get_item_from_configuration(configparser, 'dotnet', 'nugetsource')
            self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --source {nugetsource} --api-key {api_key}",
                                                                      publishdirectory, 3600, self._private_get_verbosity_for_exuecutor(configparser))

    def dotnet_reference(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'generatereference'):
            verbosity = self._private_get_verbosity_for_exuecutor(configparser)
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
            docfx_file = self.get_item_from_configuration(configparser, 'dotnet', 'docfxfile')
            docfx_folder = os.path.dirname(docfx_file)
            ensure_directory_does_not_exist(os.path.join(docfx_folder, "obj"))
            self.execute_and_raise_exception_if_exit_code_is_not_zero("docfx",
                                                                      f'"{os.path.basename(docfx_file)}" --loglevel {verbose_argument_for_docfx}', docfx_folder, 3600, verbosity)
            coveragefolder = self.get_item_from_configuration(configparser, 'dotnet', 'coveragefolder')
            ensure_directory_exists(coveragefolder)
            coverage_target_file = coveragefolder+os.path.sep+self._private_get_coverage_filename(configparser)
            shutil.copyfile(self._private_get_test_csprojfile_folder(configparser)+os.path.sep+self._private_get_coverage_filename(configparser), coverage_target_file)
            self.execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator",
                                                                      f'-reports:"{self._private_get_coverage_filename(configparser)}"'
                                                                      f' -targetdir:"{coveragefolder}" -verbosity:{verbose_argument_for_reportgenerator}',
                                                                      coveragefolder, 3600, verbosity)
            self.git_commit(self.get_item_from_configuration(configparser, 'dotnet', 'referencerepository'), "Updated reference")
            if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'exportreference'):
                self.git_push(self.get_item_from_configuration(configparser, 'dotnet', 'referencerepository'),
                              self.get_item_from_configuration(configparser, 'dotnet', 'exportreferenceremotename'),
                              "master", "master", False, False)

    def dotnet_build(self, folderOfCsprojFile: str, csprojFilename: str, outputDirectory: str, buildConfiguration: str, runtimeId: str, dotnet_framework: str,
                     clearOutputDirectoryBeforeBuild: bool = True, verbosity: int = 1, filesToSign: list = None, keyToSignForOutputfile: str = None,
                     current_release_information: dict = {}) -> None:
        if os.path.isdir(outputDirectory) and clearOutputDirectoryBeforeBuild:
            ensure_directory_does_not_exist(outputDirectory)
        ensure_directory_exists(outputDirectory)
        if verbosity == 0:
            verbose_argument_for_dotnet = "quiet"
        if verbosity == 1:
            verbose_argument_for_dotnet = "minimal"
        if verbosity == 2:
            verbose_argument_for_dotnet = "normal"
        if verbosity == 3:
            verbose_argument_for_dotnet = "detailed"
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

    def dotnet_run_tests(self, configurationfile: str, current_release_information: dict, verbosity: int = 1) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if verbosity == 0:
            verbose_argument_for_dotnet = "quiet"
        if verbosity == 1:
            verbose_argument_for_dotnet = "minimal"
        if verbosity == 2:
            verbose_argument_for_dotnet = "normal"
        if verbosity == 3:
            verbose_argument_for_dotnet = "detailed"
        coveragefilename = self._private_get_coverage_filename(configparser)
        testargument = f"test {self._private_get_test_csprojfile_filename(configparser)} -c {self.get_item_from_configuration(configparser, 'dotnet', 'testbuildconfiguration')}" \
            f" --verbosity {verbose_argument_for_dotnet} /p:CollectCoverage=true /p:CoverletOutput={coveragefilename}" \
            f" /p:CoverletOutputFormat=opencover"
        self.execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", testargument, self._private_get_test_csprojfile_folder(configparser),
                                                                  3600, verbosity, False, "Execute tests")
        root = etree.parse(self._private_get_test_csprojfile_folder(configparser)+os.path.sep+coveragefilename)
        coverage_in_percent = math.floor(float(str(root.xpath('//CoverageSession/Summary/@sequenceCoverage')[0])))
        module_count = int(root.xpath('count(//CoverageSession/Modules/*)'))
        if module_count == 0:
            coverage_in_percent = 0
            write_message_to_stdout("Warning: The testcoverage-report does not contain any module, therefore the testcoverage will be set to 0.")
        self._private_handle_coverage(configparser, current_release_information, coverage_in_percent, verbosity == 3)

    def _private_handle_coverage(self, configparser, current_release_information, coverage_in_percent: int, verbose: bool):
        current_release_information['general.testcoverage'] = coverage_in_percent
        minimalrequiredtestcoverageinpercent = self.get_number_value_from_configuration(configparser, "other", "minimalrequiredtestcoverageinpercent")
        if(coverage_in_percent < minimalrequiredtestcoverageinpercent):
            raise ValueError(f"The testcoverage must be {minimalrequiredtestcoverageinpercent}% or more but is {coverage_in_percent}.")
        coverage_regex_begin = "https://img.shields.io/badge/testcoverage-"
        coverage_regex_end = "%25-green"
        for file in self.get_items_from_configuration(configparser, "other", "codecoverageshieldreplacementfiles"):
            replace_regex_each_line_of_file(file, re.escape(coverage_regex_begin)+"\\d+"+re.escape(coverage_regex_end),
                                            coverage_regex_begin+str(coverage_in_percent)+coverage_regex_end, verbose=verbose)

    def dotnet_sign(self, dllOrExefile: str, snkfile: str, verbosity: int, current_release_information: dict = {}) -> None:
        dllOrExeFile = resolve_relative_path_from_current_working_directory(dllOrExefile)
        snkfile = resolve_relative_path_from_current_working_directory(snkfile)
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

    def deb_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        pass

    def deb_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        return False  # TODO implement

    def docker_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        pass

    _prvate_template_dockerfile_dotnet = """FROM debian:stable-slim
RUN apt-get update
RUN apt-get -y install wget
RUN apt-get -y install dpkg
RUN wget https://packages.microsoft.com/config/debian/10/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt-get update
RUN apt-get -y install dotnet-runtime-5.0
COPY __.internal.artefactdirectory.__/ App/
WORKDIR /App
# TODO do hardening
ENTRYPOINT ["dotnet", "__.general.productname.__.dll"]
"""

    def docker_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        contextfolder = self.get_item_from_configuration(configparser, "docker", "contextfolder")
        imagename = self.get_item_from_configuration(configparser, "general", "productname").lower()
        dockerfile_filename = self.get_item_from_configuration(configparser, "docker", "dockerfile")
        repository_version = self.get_version_for_buildscripts(configparser)
        use_anytemplate_dockerfile = False
        use_dotnet_dockerfile = False
        dockerfile_with_path = "<notavailable>"
        if dockerfile_filename == self._private_constants_build_template_dockerfile_dotnet:
            use_anytemplate_dockerfile = True
            use_dotnet_dockerfile = True
        if use_dotnet_dockerfile:
            dockerfile_content = self._private_replace_underscores_for_buildconfiguration(self._prvate_template_dockerfile_dotnet, configparser, {})
            dockerfile_content = dockerfile_content.replace("__.internal.artefactdirectory.__",
                                                            self.get_item_from_configuration(configparser, 'docker', 'artefactdirectory').replace("\\", "/"))
            dockerfile_filename = "Dockerfile"
            dockerfile_with_path = os.path.join(contextfolder, dockerfile_filename)
            ensure_file_exists(dockerfile_with_path)
            write_text_to_file(dockerfile_with_path, dockerfile_content)
        self.execute_and_raise_exception_if_exit_code_is_not_zero("docker",
                                                                  f"image build --tag {imagename}:{repository_version} --tag {imagename}:latest "
                                                                  + f"--no-cache --file {dockerfile_filename} .",
                                                                  contextfolder, verbosity=self._private_get_verbosity_for_exuecutor(configparser),
                                                                  print_errors_as_information=True)
        if use_anytemplate_dockerfile:
            ensure_file_does_not_exist(dockerfile_with_path)

    def flutterandroid_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        pass

    def flutterandroid_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        return False  # TODO implement

    def flutterios_create_installer_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        pass

    def flutterios_create_installer_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        return False  # TODO implement

    def generic_create_script_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if string_has_content(self.get_item_from_configuration(configparser, 'script', 'premerge_program')):
            self.execute_and_raise_exception_if_exit_code_is_not_zero(self.get_item_from_configuration(configparser, 'script', 'premerge_program'),
                                                                      self.get_item_from_configuration(configparser, 'script', 'premerge_argument'),
                                                                      self.get_item_from_configuration(configparser, 'script', 'premerge_workingdirectory'))

    def generic_create_script_release_postmerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if string_has_content(self.get_item_from_configuration(configparser, 'script', 'postmerge_program')):
            self.execute_and_raise_exception_if_exit_code_is_not_zero(self.get_item_from_configuration(configparser, 'script', 'postmerge_program'),
                                                                      self.get_item_from_configuration(configparser, 'script', 'postmerge_argument'),
                                                                      self.get_item_from_configuration(configparser, 'script', 'postmerge_workingdirectory'))

    def python_create_wheel_release_premerge(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        repository_version = self.get_version_for_buildscripts(configparser)

        # Update version
        if(self.get_boolean_value_from_configuration(configparser, 'python', 'updateversion')):
            for file in self.get_items_from_configuration(configparser, 'python', 'filesforupdatingversion'):
                replace_regex_each_line_of_file(file, '^version = ".+"\n$', 'version = "'+repository_version+'"\n')

        # lint-checks
        errors_found = False
        for file in self.get_items_from_configuration(configparser, "python", "lintcheckfiles"):
            linting_result = self.python_file_has_errors(file)
            if (linting_result[0]):
                errors_found = True
                for error in linting_result[1]:
                    write_message_to_stderr(error)
        if (errors_found):
            raise Exception("Can not continue due to linting-issues")

        # Run testcases
        self.python_run_tests(configurationfile, current_release_information)

    def python_create_wheel_release_postmerge(self, configurationfile: str, current_release_information: dict):
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        self.python_build_wheel_and_run_tests(configurationfile, current_release_information)
        self.python_release_wheel(configurationfile, current_release_information)

    def _private_execute_and_return_boolean(self, name: str, method) -> bool:
        try:
            method()
            return True
        except Exception as exception:
            write_exception_to_stderr_with_traceback(exception, traceback, f"'{name}' resulted in an error")
            return False

    def python_build_wheel_and_run_tests(self, configurationfile: str, current_release_information: dict) -> None:
        self.python_run_tests(configurationfile, current_release_information)
        self.python_build(configurationfile, current_release_information)

    def python_build(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        for folder in self.get_items_from_configuration(configparser, "python", "deletefolderbeforcreatewheel"):
            ensure_directory_does_not_exist(folder)
        setuppyfile = self.get_item_from_configuration(configparser, "python", "pythonsetuppyfile")
        setuppyfilename = os.path.basename(setuppyfile)
        setuppyfilefolder = os.path.dirname(setuppyfile)
        publishdirectoryforwhlfile = self.get_item_from_configuration(configparser, "python", "publishdirectoryforwhlfile")
        ensure_directory_exists(publishdirectoryforwhlfile)
        self.execute_and_raise_exception_if_exit_code_is_not_zero("python",
                                                                  setuppyfilename+' bdist_wheel --dist-dir "'+publishdirectoryforwhlfile+'"',
                                                                  setuppyfilefolder, 3600, self._private_get_verbosity_for_exuecutor(configparser))

    def python_run_tests(self, configurationfile: str, current_release_information: dict) -> None:
        # TODO check minimalrequiredtestcoverageinpercent
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if self.get_boolean_value_from_configuration(configparser, 'other', 'hastestproject'):
            pythontestfile = self.get_item_from_configuration(configparser, 'python', 'pythontestfile')
            pythontestfilename = os.path.basename(pythontestfile)
            pythontestfilefolder = os.path.dirname(pythontestfile)
            # TODO set verbosity-level for pytest
            self.execute_and_raise_exception_if_exit_code_is_not_zero("pytest", pythontestfilename, pythontestfilefolder, 3600,
                                                                      self._private_get_verbosity_for_exuecutor(configparser), False, "Pytest")

    def python_release_wheel(self, configurationfile: str, current_release_information: dict) -> None:
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if self.get_boolean_value_from_configuration(configparser, 'python', 'publishwhlfile'):
            with open(self.get_item_from_configuration(configparser, 'python', 'pypiapikeyfile'), 'r', encoding='utf-8') as apikeyfile:
                api_key = apikeyfile.read()
            gpgidentity = self.get_item_from_configuration(configparser, 'other', 'gpgidentity')
            repository_version = self.get_version_for_buildscripts(configparser)
            productname = self.get_item_from_configuration(configparser, 'general', 'productname')
            verbosity = self._private_get_verbosity_for_exuecutor(configparser)
            if verbosity > 2:
                verbose_argument = "--verbose"
            else:
                verbose_argument = ""
            twine_argument = f"upload --sign --identity {gpgidentity} --non-interactive {productname}-{repository_version}-py3-none-any.whl" \
                f" --disable-progress-bar --username __token__ --password {api_key} {verbose_argument}"
            self.execute_and_raise_exception_if_exit_code_is_not_zero("twine", twine_argument,
                                                                      self.get_item_from_configuration(configparser, "python", "publishdirectoryforwhlfile"),
                                                                      3600, verbosity)

    # </Build>

    # <git>

    def commit_is_signed_by_key(self, repository_folder: str, revision_identifier: str, key: str) -> bool:
        result = self.start_program_synchronously("git", f"verify-commit {revision_identifier}", repository_folder)
        if(result[0] != 0):
            return False
        if(not contains_line(result[1].splitlines(), f"gpg\\:\\ using\\ [A-Za-z0-9]+\\ key\\ [A-Za-z0-9]+{key}")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        if(not contains_line(result[1].splitlines(), "gpg\\:\\ Good\\ signature\\ from")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        return True

    def get_parent_commit_ids_of_commit(self, repository_folder: str, commit_id: str) -> str:
        return self.execute_and_raise_exception_if_exit_code_is_not_zero("git",
                                                                         f'log --pretty=%P -n 1 "{commit_id}"',
                                                                         repository_folder)[1].replace("\r", "").replace("\n", "").split(" ")

    def get_commit_ids_between_dates(self, repository_folder: str, since: datetime, until: datetime, ignore_commits_which_are_not_in_history_of_head: bool = True) -> None:
        since_as_string = datetime_to_string_for_git(since)
        until_as_string = datetime_to_string_for_git(until)
        result = filter(lambda line: not string_is_none_or_whitespace(line),
                        self.execute_and_raise_exception_if_exit_code_is_not_zero("git",
                                                                                  f'log --since "{since_as_string}" --until "{until_as_string}" --pretty=format:"%H" --no-patch',
                                                                                  repository_folder)[1].split("\n").replace("\r", ""))
        if ignore_commits_which_are_not_in_history_of_head:
            result = [commit_id for commit_id in result if self.git_commit_is_ancestor(repository_folder, commit_id)]
        return result

    def git_commit_is_ancestor(self, repository_folder: str,  ancestor: str, descendant: str = "HEAD") -> bool:
        return self.start_program_synchronously_argsasarray("git", ["merge-base", "--is-ancestor", ancestor, descendant], repository_folder)[0] == 0

    def git_repository_has_new_untracked_files(self, repository_folder: str) -> bool:
        return self._private_run_git_command(repository_folder, ["ls-files", "--exclude-standard", "--others"])

    def git_repository_has_unstaged_changes(self, repository_folder: str) -> bool:
        if(self._private_run_git_command(repository_folder, ["diff"])):
            return True
        if(self.git_repository_has_new_untracked_files(repository_folder)):
            return True
        return False

    def git_repository_has_staged_changes(self, repository_folder: str) -> bool:
        return self._private_run_git_command(repository_folder, ["diff", "--cached"])

    def git_repository_has_uncommitted_changes(self, repository_folder: str) -> bool:
        if(self.git_repository_has_unstaged_changes(repository_folder)):
            return True
        if(self.git_repository_has_staged_changes(repository_folder)):
            return True
        return False

    def _private_run_git_command(self, repository_folder: str, argument: list) -> bool:
        return not string_is_none_or_whitespace(
            self.start_program_synchronously_argsasarray("git", argument, repository_folder, timeoutInSeconds=100, verbosity=0, prevent_using_epew=True)[1])

    def git_get_current_commit_id(self, repository_folder: str, commit: str = "HEAD") -> str:
        result = self.start_program_synchronously_argsasarray("git", ["rev-parse", "--verify", commit], repository_folder,
                                                              timeoutInSeconds=100, verbosity=0, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)
        return result[1].replace('\r', '').replace('\n', '')

    def git_fetch(self, folder: str, remotename: str = "--all", print_errors_as_information: bool = True, verbosity=1) -> None:
        self.start_program_synchronously_argsasarray("git", ["fetch", remotename, "--tags", "--prune", folder], timeoutInSeconds=100, verbosity=verbosity,
                                                     print_errors_as_information=print_errors_as_information,
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
                ensure_directory_exists(clone_target_folder)
                self.start_program_synchronously_argsasarray("git", args, clone_target_folder, throw_exception_if_exitcode_is_not_zero=True)
        finally:
            os.chdir(original_cwd)

    def git_get_all_remote_names(self, directory) -> list:
        lines = self.start_program_synchronously_argsasarray("git", ["remote"], directory, prevent_using_epew=True, throw_exception_if_exitcode_is_not_zero=True)[1]
        result = []
        for line in lines:
            if(not string_is_none_or_whitespace(line)):
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
        author_name = str_none_safe(author_name).strip()
        author_email = str_none_safe(author_email).strip()
        argument = ['commit', '--message', f'"{message}"']
        if(string_has_content(author_name)):
            argument.append(f'--author="{author_name} <{author_email}>"')
        git_repository_has_uncommitted_changes = self.git_repository_has_uncommitted_changes(directory)

        if git_repository_has_uncommitted_changes:
            do_commit = True
            if stage_all_changes:
                self.git_stage_all_changes(directory)
        else:
            if no_changes_behavior == 0:
                write_message_to_stdout(f"Commit '{message}' will not be done because there are no changes to commit in repository '{directory}'")
                do_commit = False
            if no_changes_behavior == 1:
                write_message_to_stdout(f"There are no changes to commit in repository '{directory}'. Commit will be done anyway.")
                do_commit = True
                argument.append('--allow-empty')
            if no_changes_behavior == 2:
                raise RuntimeError(f"There are no changes to commit in repository '{directory}'")

        if do_commit:
            write_message_to_stdout(f"Commit changes in '{directory}'...")
            self.start_program_synchronously_argsasarray("git", argument, directory, 0, False, None, 1200,
                                                         throw_exception_if_exitcode_is_not_zero=True)

        return self.git_get_current_commit_id(directory)

    def git_create_tag(self, directory: str, target_for_tag: str, tag: str, sign: bool = False, message: str = None) -> None:
        argument = ["tag", tag, target_for_tag]
        if sign:
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

    def _private_undo_changes(self, repository: str) -> None:
        if(self.git_repository_has_uncommitted_changes(repository)):
            self.git_undo_all_changes(repository)

    def _private_repository_has_changes(self, repository: str) -> None:
        if(self.git_repository_has_uncommitted_changes(repository)):
            write_message_to_stderr(f"'{repository}' contains uncommitted changes")
            return True
        else:
            return False

    def file_is_git_ignored(self, file: str) -> None:
        filename = os.path.basename(file)
        folder = os.path.dirname(file)
        exit_code = self.start_program_synchronously_argsasarray("git", ['check-ignore', filename], folder, 0, False, None, 120, False, prevent_using_epew=True)[0]
        if(exit_code == 0):
            return True
        if(exit_code == 1):
            return False
        raise Exception(f"Unable to calculate if '{file}' is ignored due to exitcode {exit_code}.")

    def discard_all_changes(self, repository: str) -> None:
        self.start_program_synchronously_argsasarray("git", ["reset", "HEAD", "."], repository, throw_exception_if_exitcode_is_not_zero=True)
        self.start_program_synchronously_argsasarray("git", ["checkout", "."], repository, throw_exception_if_exitcode_is_not_zero=True)

    # </git>

    # <miscellaneous>

    def export_filemetadata(self, folder: str, target_file: str, encoding: str = "utf-8", filter_function=None) -> None:
        folder = resolve_relative_path_from_current_working_directory(folder)
        lines = list()
        path_prefix = len(folder)+1
        items = dict()
        for item in get_all_files_of_folder(folder):
            items[item] = "f"
        for item in get_all_folders_of_folder(folder):
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
        for line in read_lines_from_file(source_file, encoding):
            splitted = line.split(";")
            full_path_of_file_or_folder = os.path.join(folder, splitted[0])
            filetype = splitted[1]
            user = splitted[2]
            permissions = splitted[3]
            if (filetype == "f" and os.path.isfile(full_path_of_file_or_folder)) or (filetype == "d" and os.path.isdir(full_path_of_file_or_folder)):
                self.set_file_owner(full_path_of_file_or_folder, user, os.name != 'nt')
                self.set_file_permission(full_path_of_file_or_folder, permissions)
            else:
                if strict:
                    if filetype == "f":
                        filetype_full = "File"
                    if filetype == "d":
                        filetype_full = "Directory"
                    raise Exception(f"{filetype_full} '{full_path_of_file_or_folder}' does not exist")

    def _private_verbose_check_for_not_available_item(self, configparser: ConfigParser, queried_items: list, section: str, propertyname: str) -> None:
        if self._private_get_verbosity_for_exuecutor(configparser) > 0:
            for item in queried_items:
                if item == "<notavailable>":
                    write_message_to_stderr(f"Warning: The property '{section}.{propertyname}' which is not available was queried. "
                                            + "This may result in errors or involuntary behavior")
                    print_stacktrace()

    def _private_get_verbosity_for_exuecutor(self, configparser: ConfigParser) -> int:
        return self.get_number_value_from_configuration(configparser, 'other', 'verbose')

    def _private_get_buildoutputdirectory(self, configparser: ConfigParser, runtime: str) -> str:
        result = self.get_item_from_configuration(configparser, 'dotnet', 'buildoutputdirectory')
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'separatefolderforeachruntime'):
            result = result+os.path.sep+runtime
        return result

    def get_boolean_value_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str) -> bool:
        try:
            return configparser.getboolean(section, propertyname)
        except:
            try:
                return string_to_boolean(self.get_item_from_configuration(configparser, section, propertyname, {}, False))
            except:
                return False

    def get_number_value_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str) -> int:
        return int(configparser.get(section, propertyname))

    def configuration_item_is_available(self, configparser: ConfigParser, sectioon: str, item: str) -> bool:
        if not configparser.has_option(sectioon, item):
            return False
        plain_value = configparser.get(sectioon, item)
        if string_is_none_or_whitespace(plain_value):
            return False
        if plain_value == "<notavailable>":
            return False
        return True

    def get_item_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str, custom_replacements: dict = {}, include_version=True) -> str:
        result = self._private_replace_underscores_for_buildconfiguration(configparser.get(section, propertyname), configparser, custom_replacements, include_version)
        result = strip_new_line_character(result)
        self._private_verbose_check_for_not_available_item(configparser, [result], section, propertyname)
        return result

    def get_items_from_configuration(self, configparser: ConfigParser, section: str, propertyname: str, custom_replacements: dict = {}, include_version=True) -> list:
        itemlist_as_string = self._private_replace_underscores_for_buildconfiguration(configparser.get(section, propertyname), configparser, custom_replacements, include_version)
        if not string_has_content(itemlist_as_string):
            return []
        if ',' in itemlist_as_string:
            result = [item.strip() for item in itemlist_as_string.split(',')]
        else:
            result = [itemlist_as_string.strip()]
        self._private_verbose_check_for_not_available_item(configparser, result, section, propertyname)
        return result

    def _private_get_csprojfile_filename(self, configparser: ConfigParser) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "csprojfile")
        file = resolve_relative_path_from_current_working_directory(file)
        result = os.path.basename(file)
        return result

    def _private_get_test_csprojfile_filename(self, configparser: ConfigParser) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "testcsprojfile")
        file = resolve_relative_path_from_current_working_directory(file)
        result = os.path.basename(file)
        return result

    def _private_get_csprojfile_folder(self, configparser: ConfigParser) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "csprojfile")
        file = resolve_relative_path_from_current_working_directory(file)
        result = os.path.dirname(file)
        return result

    def _private_get_test_csprojfile_folder(self, configparser: ConfigParser) -> str:
        file = self.get_item_from_configuration(configparser, "dotnet", "testcsprojfile")
        file = resolve_relative_path_from_current_working_directory(file)
        result = os.path.dirname(file)
        return result

    def _private_get_coverage_filename(self, configparser: ConfigParser) -> str:
        return self.get_item_from_configuration(configparser, "general", "productname")+".TestCoverage.opencover.xml"

    def get_version_for_buildscripts(self, configparser: ConfigParser) -> str:
        return self.get_version_for_buildscripts_helper(self.get_item_from_configuration(configparser, 'general', 'repository', {}, False))

    @lru_cache(maxsize=None)
    def get_version_for_buildscripts_helper(self, folder: str) -> str:
        return self.get_semver_version_from_gitversion(folder)

    def _private_replace_underscore_in_file_for_buildconfiguration(self, file: str, configparser: ConfigParser, replacements: dict = {}, encoding="utf-8") -> None:
        with codecs.open(file, 'r', encoding=encoding) as file_object:
            text = file_object.read()
        text = self._private_replace_underscores_for_buildconfiguration(text, configparser, replacements)
        with codecs.open(file, 'w', encoding=encoding) as file_object:
            file_object.write(text)

    def _private_replace_underscores_for_buildconfiguration(self, string: str, configparser: ConfigParser, replacements: dict = {}, include_version=True) -> str:
        replacements["builtin.year"] = str(datetime.now().year)
        replacements["builtin.template_dockerfile_dotnet"] = self._private_constants_build_template_dockerfile_dotnet
        if include_version:
            replacements["builtin.version"] = self.get_version_for_buildscripts(configparser)

        available_configuration_items = []

        available_configuration_items.append(["docker", "artefactdirectory"])
        available_configuration_items.append(["docker", "contextfolder"])
        available_configuration_items.append(["docker", "dockerfile"])
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
        available_configuration_items.append(["general", "productname"])
        available_configuration_items.append(["general", "basefolder"])
        available_configuration_items.append(["general", "logfilefolder"])
        available_configuration_items.append(["general", "repository"])
        available_configuration_items.append(["general", "author"])
        available_configuration_items.append(["general", "description"])
        available_configuration_items.append(["prepare", "developmentbranchname"])
        available_configuration_items.append(["prepare", "masterbranchname"])
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
        available_configuration_items.append(["python", "lintcheckfiles"])
        available_configuration_items.append(["python", "pythontestfile"])
        available_configuration_items.append(["python", "pythonsetuppyfile"])
        available_configuration_items.append(["python", "filesforupdatingversion"])
        available_configuration_items.append(["python", "pypiapikeyfile"])
        available_configuration_items.append(["python", "deletefolderbeforcreatewheel"])
        available_configuration_items.append(["python", "publishdirectoryforwhlfile"])

        for item in available_configuration_items:
            if configparser.has_option(item[0], item[1]):
                replacements[f"{item[0]}.{item[1]}"] = configparser.get(item[0], item[1])

        changed = True
        result = string
        while changed:
            changed = False
            for key, value in replacements.items():
                previousValue = result
                result = result.replace(f"__.{key}.__", value)
                if(not result == previousValue):
                    changed = True
        return result

    def _private_create_dotnet_release_premerge(self, configurationfile: str, current_release_information: dict):
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'createexe'):
            self.dotnet_create_executable_release_premerge(configurationfile, current_release_information)
        else:
            self.dotnet_create_nuget_release_premerge(configurationfile, current_release_information)

    def _private_create_dotnet_release_postmerge(self, configurationfile: str, current_release_information: dict):
        configparser = ConfigParser()
        configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
        if self.get_boolean_value_from_configuration(configparser, 'dotnet', 'createexe'):
            self.dotnet_create_executable_release_postmerge(configurationfile, current_release_information)
        else:
            self.dotnet_create_nuget_release_postmerge(configurationfile, current_release_information)

    def _private_calculate_lengh_in_seconds(self, filename: str, folder: str) -> float:
        argument = f'-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filename}"'
        return float(self.execute_and_raise_exception_if_exit_code_is_not_zero("ffprobe", argument, folder)[1])

    def _private_create_thumbnails(self, filename: str, fps: float, folder: str, tempname_for_thumbnails: str) -> None:
        argument = f'-i "{filename}" -r {str(fps)} -vf scale=-1:120 -vcodec png {tempname_for_thumbnails}-%002d.png'
        self.execute_and_raise_exception_if_exit_code_is_not_zero("ffmpeg", argument, folder)

    def _private_create_thumbnail(self, outputfilename: str, folder: str, length_in_seconds: float, tempname_for_thumbnails: str, amount_of_images: int) -> None:
        duration = timedelta(seconds=length_in_seconds)
        info = timedelta_to_simple_string(duration)
        next_square_number = str(int(math.sqrt(get_next_square_number(amount_of_images))))
        argument = f'-title "{outputfilename} ({info})" -geometry +{next_square_number}+{next_square_number} {tempname_for_thumbnails}*.png "{outputfilename}.png"'
        self.execute_and_raise_exception_if_exit_code_is_not_zero("montage", argument, folder)

    def generate_thumbnail(self, file: str, frames_per_second: str, tempname_for_thumbnails: str = None) -> None:
        if tempname_for_thumbnails is None:
            tempname_for_thumbnails = "t"+str(uuid.uuid4())

        file = resolve_relative_path_from_current_working_directory(file)
        filename = os.path.basename(file)
        folder = os.path.dirname(file)
        filename_without_extension = Path(file).stem

        try:
            length_in_seconds = self._private_calculate_lengh_in_seconds(filename, folder)
            if(frames_per_second.endswith("fps")):
                # frames per second: "20fps" => 20fps
                frames_per_second = round(float(frames_per_second[:-3]), 2)
                amounf_of_previewframes = math.floor(length_in_seconds*frames_per_second)
            else:
                # concrete amount of frames: "20" => 20 frames
                amounf_of_previewframes = float(frames_per_second)
                frames_per_second = round(length_in_seconds/amounf_of_previewframes, 2)
            self._private_create_thumbnails(filename, frames_per_second, folder, tempname_for_thumbnails)
            self._private_create_thumbnail(filename_without_extension, folder, length_in_seconds, tempname_for_thumbnails, amounf_of_previewframes)
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
        for file in get_missing_files(folderA, folderB):
            write_message_to_stdout(file)

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
                    write_message_to_stderr("Wrong format")
            else:
                write_message_to_stderr("Wrong format")
                return 1
        with open(name, "wb") as f:
            f.seek(size-1)
            f.write(b"\0")
        return 0

    def SCCreateHashOfAllFiles(self, folder: str) -> None:
        for file in absolute_file_paths(folder):
            with open(file+".sha256", "w+") as f:
                f.write(get_sha256_of_file(file))

    def sc_organize_lines_in_file(self, file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False,
                                  remove_empty_lines: bool = True, ignored_start_character: list = list()) -> int:
        if os.path.isfile(file):

            # read file
            lines = read_lines_from_file(file, encoding)
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
                    if(not (string_is_none_or_whitespace(line))):
                        lines.append(line)

            # remove duplicated lines if desired
            if remove_duplicated_lines:
                lines = remove_duplicates(lines)

            # sort lines if desired
            if sort:
                lines = sorted(lines, key=lambda singleline: self._private_adapt_line_for_sorting(singleline, ignored_start_character))

            # reinsert first line
            if ignore_first_line:
                lines.insert(0, first_line)

            # write result to file
            write_lines_to_file(file, lines, encoding)

            return 0
        else:
            write_message_to_stdout(f"File '{file}' does not exist")
            return 1

    def _private_adapt_line_for_sorting(self, line: str, ignored_start_characters: list):
        result = line.lower()
        while len(result) > 0 and result[0] in ignored_start_characters:
            result = result[1:]
        return result

    def SCGenerateSnkFiles(self, outputfolder, keysize=4096, amountofkeys=10) -> int:
        ensure_directory_exists(outputfolder)
        for _ in range(amountofkeys):
            file = os.path.join(outputfolder, str(uuid.uuid4())+".snk")
            argument = f"-k {keysize} {file}"
            self.execute_and_raise_exception_if_exit_code_is_not_zero("sn", argument, outputfolder)

    def _private_merge_files(self, sourcefile: str, targetfile: str) -> None:
        with open(sourcefile, "rb") as f:
            source_data = f.read()
        with open(targetfile, "ab") as fout:
            merge_separator = [0x0A]
            fout.write(bytes(merge_separator))
            fout.write(source_data)

    def _private_process_file(self, file: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
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
                        self._private_merge_files(file, new_filename)
                        send2trash.send2trash(file)
                    else:
                        raise Exception('Unknown conflict resolve mode')
            else:
                os.rename(file, new_filename)

    def SCReplaceSubstringsInFilenames(self, folder: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
        for file in absolute_file_paths(folder):
            self._private_process_file(file, substringInFilename, newSubstringInFilename, conflictResolveMode)

    def _private_check_file(self, file: str, searchstring: str) -> None:
        bytes_ascii = bytes(searchstring, "ascii")
        bytes_utf16 = bytes(searchstring, "utf-16")  # often called "unicode-encoding"
        bytes_utf8 = bytes(searchstring, "utf-8")
        with open(file, mode='rb') as file_object:
            content = file_object.read()
            if bytes_ascii in content:
                write_message_to_stdout(file)
            elif bytes_utf16 in content:
                write_message_to_stdout(file)
            elif bytes_utf8 in content:
                write_message_to_stdout(file)

    def SCSearchInFiles(self, folder: str, searchstring: str) -> None:
        for file in absolute_file_paths(folder):
            self._private_check_file(file, searchstring)

    def _private_print_qr_code_by_csv_line(self, line: str) -> None:
        splitted = line.split(";")
        displayname = splitted[0]
        website = splitted[1]
        emailaddress = splitted[2]
        key = splitted[3]
        period = splitted[4]
        qrcode_content = f"otpauth://totp/{website}:{emailaddress}?secret={key}&issuer={displayname}&period={period}"
        write_message_to_stdout(f"{displayname} ({emailaddress}):")
        write_message_to_stdout(qrcode_content)
        call(["qr", qrcode_content])

    def SCShow2FAAsQRCode(self, csvfile: str) -> None:
        separator_line = "--------------------------------------------------------"
        with open(csvfile) as f:
            lines = f.readlines()
        lines = [line.rstrip('\n') for line in lines]
        itertor = iter(lines)
        next(itertor)
        for line in itertor:
            write_message_to_stdout(separator_line)
            self._private_print_qr_code_by_csv_line(line)
        write_message_to_stdout(separator_line)

    def SCUpdateNugetpackagesInCsharpProject(self, csprojfile: str) -> int:
        outdated_packages = self.get_nuget_packages_of_csproj_file(csprojfile, True)
        write_message_to_stdout("The following packages will be updated:")
        for outdated_package in outdated_packages:
            write_message_to_stdout(outdated_package)
            self.update_nuget_package(csprojfile, outdated_package)
        write_message_to_stdout(f"{len(outdated_packages)} package(s) were updated")
        return len(outdated_packages) > 0

    def SCUploadFileToFileHost(self, file: str, host: str) -> int:
        try:
            write_message_to_stdout(self.upload_file_to_file_host(file, host))
            return 0
        except Exception as exception:
            write_exception_to_stderr_with_traceback(exception, traceback)
            return 1

    def SCFileIsAvailableOnFileHost(self, file: str) -> int:
        try:
            if self.file_is_available_on_file_host(file):
                write_message_to_stdout(f"'{file}' is available")
                return 0
            else:
                write_message_to_stdout(f"'{file}' is not available")
                return 1
        except Exception as exception:
            write_exception_to_stderr_with_traceback(exception, traceback)
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

        copy2(inputfile, outputfile)
        with open(outputfile, 'a') as file:
            # TODO use rcedit for .exe-files instead of appending valuetoappend ( https://github.com/electron/rcedit/ )
            # background: you can retrieve the "original-filename" from the .exe-file like discussed here:
            # https://security.stackexchange.com/questions/210843/ is-it-possible-to-change-original-filename-of-an-exe
            # so removing the original filename with rcedit is probably a better way to make it more difficult to detect the programname.
            # this would obviously also change the hashvalue of the program so appending a whitespace is not required anymore.
            file.write(valuetoappend)

    def _private_adjust_folder_name(self, folder: str) -> str:
        result = os.path.dirname(folder).replace("\\", "/")
        if result == "/":
            return ""
        else:
            return result

    def _private_create_iso(self, folder, iso_file) -> None:
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
                content = open(full_path, "rb").read()
                path_in_iso = '/' + files_directory + self._private_adjust_folder_name(full_path[len(folder)::1]).upper()
                if not (path_in_iso in created_directories):
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
                self._private_create_iso(files_directory_obf, outputfile)
                shutil.rmtree(files_directory_obf)
        else:
            raise Exception(f"Directory not found: '{inputfolder}'")

    def SCFilenameObfuscator(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if(not obfuscate_all_files):
            obfuscate_file_extensions = extensions.split(",")

        if (os.path.isdir(inputfolder)):
            printtableheadline = string_to_boolean(printtableheadline)
            files = []
            if not os.path.isfile(namemappingfile):
                with open(namemappingfile, "a"):
                    pass
            if printtableheadline:
                append_line_to_file(namemappingfile, "Original filename;new filename;SHA2-hash of file")
            for file in absolute_file_paths(inputfolder):
                if os.path.isfile(os.path.join(inputfolder, file)):
                    if obfuscate_all_files or _private_extension_matchs(file, obfuscate_file_extensions):
                        files.append(file)
            for file in files:
                hash_value = get_sha256_of_file(file)
                extension = pathlib.Path(file).suffix
                new_file_name_without_path = str(uuid.uuid4())[0:8] + extension
                new_file_name = os.path.join(os.path.dirname(file), new_file_name_without_path)
                os.rename(file, new_file_name)
                append_line_to_file(namemappingfile, os.path.basename(file) + ";" + new_file_name_without_path + ";" + hash_value)
        else:
            raise Exception(f"Directory not found: '{inputfolder}'")

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
            for file in absolute_file_paths(inputfolder):
                if obfuscate_all_files or _private_extension_matchs(file, obfuscate_file_extensions):
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
        write_message_to_stderr("Unknown host: "+host)
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

    def python_file_has_errors(self, file, treat_warnings_as_errors: bool = True):
        errors = list()
        folder = os.path.dirname(file)
        filename = os.path.basename(file)
        write_message_to_stdout(f"Start error-check in {file}")
        if treat_warnings_as_errors:
            errorsonly_argument = ""
        else:
            errorsonly_argument = " --errors-only"
        (exit_code, stdout, stderr, _) = self.start_program_synchronously("pylint", filename+errorsonly_argument, folder)
        if(exit_code != 0):
            errors.append("Linting-issues:")
            errors.append(f"Pylint-exitcode: {exit_code}")
            for line in string_to_lines(stdout):
                errors.append(line)
            for line in string_to_lines(stderr):
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
        ls_output = self._private_ls(file)
        return self._private_get_file_permission_helper(ls_output)

    def _private_get_file_permission_helper(self, ls_output: str) -> str:
        permissions = ' '.join(ls_output.split()).split(' ')[0][1:]
        return str(self._private_to_octet(permissions[0:3]))+str(self._private_to_octet(permissions[3:6]))+str(self._private_to_octet(permissions[6:9]))

    def _private_to_octet(self, string: str) -> int:
        return int(self._private_to_octet_helper(string[0])+self._private_to_octet_helper(string[1])+self._private_to_octet_helper(string[2]), 2)

    def _private_to_octet_helper(self, string: str) -> str:
        if(string == "-"):
            return "0"
        else:
            return "1"

    def get_file_owner(self, file: str) -> str:
        """This function returns the user and the group in the format "user:group"."""
        ls_output = self._private_ls(file)
        return self._private_get_file_owner_helper(ls_output)

    def _private_get_file_owner_helper(self, ls_output: str) -> str:
        try:
            splitted = ' '.join(ls_output.split()).split(' ')
            return f"{splitted[2]}:{splitted[3]}"
        except Exception as exception:
            raise ValueError(f"ls-output '{ls_output}' not parsable") from exception

    def get_file_owner_and_file_permission(self, file: str) -> str:
        ls_output = self._private_ls(file)
        return [self._private_get_file_owner_helper(ls_output), self._private_get_file_permission_helper(ls_output)]

    def _private_ls(self, file: str) -> str:
        file = file.replace("\\", "/")
        assert_condition(os.path.isfile(file) or os.path.isdir(file), f"Can not execute 'ls' because '{file}' does not exist")
        result = self._private_start_internal_for_helper("ls", ["-ld", file])
        assert_condition(result[0] == 0, f"'ls -ld {file}' resulted in exitcode {str(result[0])}. StdErr: {result[2]}")
        assert_condition(not string_is_none_or_whitespace(result[1]), f"'ls' of '{file}' had an empty output. StdErr: '{result[2]}'")
        return result[1]

    def set_file_permission(self, file: str, permissions: str, recursive: bool = False) -> None:
        """This function expects an usual octet-triple, for example "0700"."""
        argument = f'{permissions} "{file}"'
        if recursive:
            argument = f" --recursive {argument}"
        self.execute_and_raise_exception_if_exit_code_is_not_zero("chmod", argument)

    def set_file_owner(self, file: str, owner: str, recursive: bool = False, follow_symlinks: bool = False) -> None:
        """This function expects the user and the group in the format "user:group"."""
        argument = f'{owner} "{file}"'
        if recursive:
            argument = f" --recursive {argument}"
        if follow_symlinks:
            argument = f" --no-dereference {argument}"
        self.execute_and_raise_exception_if_exit_code_is_not_zero("chown", argument)

    def _private_adapt_workingdirectory(self, workingdirectory: str) -> str:
        if workingdirectory is None:
            return os.getcwd()
        else:
            return resolve_relative_path_from_current_working_directory(workingdirectory)

    def _private_log_program_start(self, program: str, arguments: str, workingdirectory: str, verbosity: int = 1) -> None:
        if(verbosity == 2):
            write_message_to_stdout(f"Start '{workingdirectory}>{program} {arguments}'")

    def start_program_asynchronously(self, program: str, arguments: str = "", workingdirectory: str = "", verbosity: int = 1, prevent_using_epew: bool = False,
                                     print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600, addLogOverhead: bool = False,
                                     title: str = None, log_namespace: str = "") -> int:
        workingdirectory = self._private_adapt_workingdirectory(workingdirectory)
        if self.mock_program_calls:
            try:
                return self._private_get_mock_program_call(program, arguments, workingdirectory)[3]
            except LookupError:
                if not self.execute_programy_really_if_no_mock_call_is_defined:
                    raise
        return self._private_start_process(program, arguments, workingdirectory, verbosity, print_errors_as_information,
                                           log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, None, None, None, None)

    def start_program_asynchronously_argsasarray(self, program: str, argument_list: list = [], workingdirectory: str = "", verbosity: int = 1, prevent_using_epew: bool = False,
                                                 print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600, addLogOverhead: bool = False,
                                                 title: str = None, log_namespace: str = "") -> int:
        arguments = ' '.join(argument_list)
        workingdirectory = self._private_adapt_workingdirectory(workingdirectory)
        if self.mock_program_calls:
            try:
                return self._private_get_mock_program_call(program, arguments, workingdirectory)[3]
            except LookupError:
                if not self.execute_programy_really_if_no_mock_call_is_defined:
                    raise
        return self._private_start_process_argsasarray(program, argument_list, workingdirectory, verbosity, print_errors_as_information,
                                                       log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, None, None, None, None)

    def execute_and_raise_exception_if_exit_code_is_not_zero(self, program: str, arguments: str = "", workingdirectory: str = "",
                                                             timeoutInSeconds: int = 3600, verbosity: int = 1, addLogOverhead: bool = False, title: str = None,
                                                             print_errors_as_information: bool = False, log_file: str = None, prevent_using_epew: bool = False,
                                                             log_namespace: str = "") -> None:
        # TODO remove this function
        return self.start_program_synchronously(program, arguments, workingdirectory, verbosity,
                                                print_errors_as_information, log_file, timeoutInSeconds,
                                                addLogOverhead, title, True, prevent_using_epew, log_namespace)

    def _private_start_internal_for_helper(self, program: str, arguments: list, workingdirectory: str = None):
        return self.start_program_synchronously_argsasarray(program, arguments,
                                                            workingdirectory, verbosity=0, throw_exception_if_exitcode_is_not_zero=True, prevent_using_epew=True)

    def start_program_synchronously(self, program: str, arguments: str = "", workingdirectory: str = None, verbosity: int = 1,
                                    print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                                    addLogOverhead: bool = False, title: str = None,
                                    throw_exception_if_exitcode_is_not_zero: bool = False, prevent_using_epew: bool = False,
                                    log_namespace: str = ""):
        return self.start_program_synchronously_argsasarray(program, arguments_to_array(arguments), workingdirectory, verbosity, print_errors_as_information,
                                                            log_file, timeoutInSeconds, addLogOverhead, title,
                                                            throw_exception_if_exitcode_is_not_zero, prevent_using_epew, log_namespace)

    def start_program_synchronously_argsasarray(self, program: str, argument_list: list = [], workingdirectory: str = None, verbosity: int = 1,
                                                print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                                                addLogOverhead: bool = False, title: str = None,
                                                throw_exception_if_exitcode_is_not_zero: bool = False, prevent_using_epew: bool = False,
                                                log_namespace: str = ""):
        arguments = ' '.join(argument_list)
        workingdirectory = self._private_adapt_workingdirectory(workingdirectory)
        if self.mock_program_calls:
            try:
                return self._private_get_mock_program_call(program, arguments, workingdirectory)
            except LookupError:
                if not self.execute_programy_really_if_no_mock_call_is_defined:
                    raise
        cmd = f'{workingdirectory}>{program} {arguments}'
        if (self._private_epew_is_available and not prevent_using_epew):
            tempdir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            output_file_for_stdout = tempdir + ".epew.stdout.txt"
            output_file_for_stderr = tempdir + ".epew.stderr.txt"
            output_file_for_exit_code = tempdir + ".epew.exitcode.txt"
            output_file_for_pid = tempdir + ".epew.pid.txt"
            process = self._private_start_process(program, arguments, workingdirectory, verbosity, print_errors_as_information,
                                                  log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, output_file_for_stdout, output_file_for_stderr,
                                                  output_file_for_pid, output_file_for_exit_code)
            process.wait()
            stdout = self._private_load_text(output_file_for_stdout)
            stderr = self._private_load_text(output_file_for_stderr)
            exit_code = self._private_get_number_from_filecontent(self._private_load_text(output_file_for_exit_code))
            pid = self._private_get_number_from_filecontent(self._private_load_text(output_file_for_pid))
            ensure_directory_does_not_exist(tempdir)
            if string_is_none_or_whitespace(title):
                title_for_message = ""
            else:
                title_for_message = f"for task '{title}' "
            title_local = f"epew {title_for_message}('{cmd}')"
            result = (exit_code, stdout, stderr, pid)
        else:
            if string_is_none_or_whitespace(title):
                title_local = cmd
            else:
                title_local = title
            arguments_for_process = [program]
            arguments_for_process.extend(argument_list)
            with Popen(arguments_for_process, stdout=PIPE, stderr=PIPE, cwd=workingdirectory, shell=False) as process:
                pid = process.pid
                stdout, stderr = process.communicate()
                exit_code = process.wait()
                stdout = bytes_to_string(stdout).replace('\r', '')
                stderr = bytes_to_string(stderr).replace('\r', '')
                result = (exit_code, stdout, stderr, pid)
        if verbosity == 3:
            write_message_to_stdout(f"Finished executing '{title_local}' with exitcode {str(exit_code)}")
        if throw_exception_if_exitcode_is_not_zero and exit_code != 0:
            raise Exception(f"'{title_local}' had exitcode {str(exit_code)}. (StdOut: '{stdout}'; StdErr: '{stderr}')")
        else:
            return result

    def _private_start_process_argsasarray(self, program: str, argument_list: str, workingdirectory: str = None, verbosity: int = 1,
                                           print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                                           addLogOverhead: bool = False, title: str = None, log_namespace: str = "", stdoutfile: str = None,
                                           stderrfile: str = None, pidfile: str = None, exitcodefile: str = None):
        return self._private_start_process(program, ' '.join(argument_list), workingdirectory, verbosity, print_errors_as_information, log_file,
                                           timeoutInSeconds, addLogOverhead, title, log_namespace, stdoutfile, stderrfile, pidfile, exitcodefile)

    def _private_start_process(self, program: str, arguments: str, workingdirectory: str = None, verbosity: int = 1,
                               print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600,
                               addLogOverhead: bool = False, title: str = None, log_namespace: str = "", stdoutfile: str = None,
                               stderrfile: str = None, pidfile: str = None, exitcodefile: str = None):
        workingdirectory = self._private_adapt_workingdirectory(workingdirectory)
        cmd = f'{workingdirectory}>{program} {arguments}'
        if(arguments is None):
            arguments = ""
        if string_is_none_or_whitespace(title):
            title = ""
            title_for_message = ""
            title_argument = cmd
        title_for_message = f"for task '{title}' "
        title_argument = title
        self._private_log_program_start(program, arguments, workingdirectory, verbosity)
        title_argument = title_argument.replace("\"", "'").replace("\\", "/")
        cmdcall = f"{workingdirectory}>{program} {arguments}"
        if verbosity >= 1:
            write_message_to_stdout("Run "+cmdcall)
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
        if not string_is_none_or_whitespace(log_file):
            args.append(f'-f "{log_file}"')
        if print_errors_as_information:
            args.append("-i")
        if addLogOverhead:
            args.append("-h")
        args.append("-v "+str(verbosity))
        if verbosity == 3:
            args_as_string = " ".join(args)
            write_message_to_stdout(f"Start executing '{title_local}' (epew-call: '{args_as_string}')")
        process = Popen(args, shell=False)  # pylint: disable=bad-option-value, R1732
        return process

    def verify_no_pending_mock_program_calls(self):
        if(len(self._private_mocked_program_calls) > 0):
            raise AssertionError(
                "The following mock-calls were not called:\n    "+",\n    ".join([self._private_format_mock_program_call(r) for r in self._private_mocked_program_calls]))

    def _private_format_mock_program_call(self, r) -> str:
        return f"'{r.workingdirectory}>{r.program} {r.argument}' (" \
            f"exitcode: {str_none_safe(str(r.exit_code))}, " \
            f"pid: {str_none_safe(str(r.pid))}, "\
            f"stdout: {str_none_safe(str(r.stdout))}, " \
            f"stderr: {str_none_safe(str(r.stderr))})"

    def register_mock_program_call(self, program: str, argument: str, workingdirectory: str, result_exit_code: int, result_stdout: str, result_stderr: str,
                                   result_pid: int, amount_of_expected_calls=1):
        "This function is for test-purposes only"
        for _ in itertools.repeat(None, amount_of_expected_calls):
            mock_call = ScriptCollection._private_mock_program_call()
            mock_call.program = program
            mock_call.argument = argument
            mock_call.workingdirectory = workingdirectory
            mock_call.exit_code = result_exit_code
            mock_call.stdout = result_stdout
            mock_call.stderr = result_stderr
            mock_call.pid = result_pid
            self._private_mocked_program_calls.append(mock_call)

    def _private_get_mock_program_call(self, program: str, argument: str, workingdirectory: str):
        result: ScriptCollection._private_mock_program_call = None
        for mock_call in self._private_mocked_program_calls:
            if((re.match(mock_call.program, program) is not None)
               and (re.match(mock_call.argument, argument) is not None)
               and (re.match(mock_call.workingdirectory, workingdirectory) is not None)):
                result = mock_call
                break
        if result is None:
            raise LookupError(f"Tried to execute mock-call '{workingdirectory}>{program} {argument}' but no mock-call was defined for that execution")
        else:
            self._private_mocked_program_calls.remove(result)
            return (result.exit_code, result.stdout, result.stderr, result.pid)

    class _private_mock_program_call:
        program: str
        argument: str
        workingdirectory: str
        exit_code: int
        stdout: str
        stderr: str
        pid: int

    def _private_get_number_from_filecontent(self, filecontent: str) -> int:
        for line in filecontent.splitlines():
            try:
                striped_line = strip_new_line_character(line)
                result = int(striped_line)
                return result
            except:
                pass
        raise Exception(f"'{filecontent}' does not containe an int-line")

    def _private_load_text(self, file: str) -> str:
        if os.path.isfile(file):
            content = read_text_from_file(file)
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
        return self.system_time_equals_internet_time(self._private_get_default_tolerance_for_system_time_equals_internet_time())

    def check_system_time(self, maximal_tolerance_difference: timedelta):
        if not self.system_time_equals_internet_time(maximal_tolerance_difference):
            raise ValueError("System time may be wrong")

    def check_system_time_with_default_tolerance(self) -> None:
        self.check_system_time(self._private_get_default_tolerance_for_system_time_equals_internet_time())

    def _private_get_default_tolerance_for_system_time_equals_internet_time(self) -> timedelta:
        return timedelta(hours=0, minutes=0, seconds=3)

    def get_semver_version_from_gitversion(self, folder: str) -> str:
        return self.get_version_from_gitversion(folder, "MajorMinorPatch")

    def get_version_from_gitversion(self, folder: str, variable: str) -> str:
        # called twice as workaround for bug in gitversion ( https://github.com/GitTools/GitVersion/issues/1877 )
        result = self._private_start_internal_for_helper("gitversion", ["/showVariable", variable], folder)
        result = self._private_start_internal_for_helper("gitversion", ["/showVariable", variable], folder)
        return strip_new_line_character(result[1])

    # </miscellaneous>

# <static>


# <CLI-scripts>

def SCCreateRelease_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCCreateRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().create_release(args.configurationfile)


def SCDotNetCreateExecutableRelease_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDotNetCreateExecutableRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    sc = ScriptCollection()
    sc.dotnet_create_executable_release_premerge(args.configurationfile, {})
    sc.dotnet_create_executable_release_postmerge(args.configurationfile, {})
    return 0


def SCDotNetCreateNugetRelease_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDotNetCreateNugetRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    sc = ScriptCollection()
    sc.dotnet_create_nuget_release_premerge(args.configurationfile, {})
    sc.dotnet_create_nuget_release_postmerge(args.configurationfile, {})
    return 0


def SCDotNetReleaseNuget_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDotNetReleaseNuget_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().dotnet_release_nuget(args.configurationfile, {})


def SCDotNetReference_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDotNetReference_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().dotnet_reference(args.configurationfile, {})


def SCDotNetBuild_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDotNetRunTests_cli:
Description: Builds a DotNet-project by a given .csproj-file.
Required commandline-commands: dotnet
Required configuration-items: TODO
Requires the requirements of: TODO""")
    parser.add_argument("folderOfCsprojFile")
    parser.add_argument("csprojFilename")
    parser.add_argument("outputDirectory")
    parser.add_argument("buildConfiguration")
    parser.add_argument("runtimeId")
    parser.add_argument("dotnetframework")
    parser.add_argument("clearOutputDirectoryBeforeBuild", type=string_to_boolean, nargs='?', const=True, default=False)
    parser.add_argument("verbosity")
    parser.add_argument("outputFilenameToSign")
    parser.add_argument("keyToSignForOutputfile")
    args = parser.parse_args()
    return ScriptCollection().dotnet_build(args.folderOfCsprojFile, args.csprojFilename, args.outputDirectory, args.buildConfiguration, args.runtimeId, args.dotnetframework,
                                           args.clearOutputDirectoryBeforeBuild, args.verbosity, args.outputFilenameToSign, args.keyToSignForOutputfile, {})


def SCDotNetRunTests_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDotNetRunTests_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().dotnet_run_tests(args.configurationfile, {}, 1)


def SCDotNetsign_cli() -> int:
    parser = argparse.ArgumentParser(description='Signs a dll- or exe-file with a snk-file. Requires ilasm and ildasm as available commandline-commands.')
    parser.add_argument("dllOrExefile")
    parser.add_argument("snkfile")
    parser.add_argument("verbose", action='store_true')
    args = parser.parse_args()
    return ScriptCollection().dotnet_sign(args.dllOrExefile, args.snkfile, args.verbose, {})


def SCDebCreateInstallerRelease_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDebCreateInstallerRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().deb_create_installer_release_postmerge(args.configurationfile, {})


def SCPythonCreateWheelRelease_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCPythonCreateWheelRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().python_create_wheel_release_postmerge(args.configurationfile, {})


def SCPythonBuild_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCPythonBuild_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().python_build(args.configurationfile, {})


def SCPythonRunTests_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCPythonRunTests_cli:
Description: Executes python-unit-tests.
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().python_run_tests(args.configurationfile, {})


def SCPythonReleaseWheel_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCPythonReleaseWheel_cli:
Description: Uploads a .whl-file using twine.
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().python_release_wheel(args.configurationfile, {})


def SCPythonBuildWheelAndRunTests_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCPythonBuildWheelAndRunTests_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return ScriptCollection().python_build_wheel_and_run_tests(args.configurationfile, {})


def SCFilenameObfuscator_cli() -> int:
    parser = argparse.ArgumentParser(description=''''Obfuscates the names of all files in the given folder.
Caution: This script can cause harm if you pass a wrong inputfolder-argument.''')

    parser.add_argument('--printtableheadline', type=string_to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
    parser.add_argument('--namemappingfile', default="NameMapping.csv", help='Specifies the file where the name-mapping will be written to')
    parser.add_argument('--extensions', default="exe,py,sh", help='Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
    parser.add_argument('--inputfolder', help='Specifies the foldere where the files are stored whose names should be obfuscated', required=True)

    args = parser.parse_args()
    ScriptCollection().SCFilenameObfuscator(args.inputfolder, args.printtableheadline, args.namemappingfile, args.extensions)
    return 0


def SCCreateISOFileWithObfuscatedFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='''Creates an iso file with the files in the given folder and changes their names and hash-values.
This script does not process subfolders transitively.''')

    parser.add_argument('--inputfolder', help='Specifies the foldere where the files are stored which should be added to the iso-file', required=True)
    parser.add_argument('--outputfile', default="files.iso", help='Specifies the output-iso-file and its location')
    parser.add_argument('--printtableheadline', default=False, action='store_true', help='Prints column-titles in the name-mapping-csv-file')
    parser.add_argument('--createnoisofile', default=False, action='store_true', help="Create no iso file")
    parser.add_argument('--extensions', default="exe,py,sh", help='Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
    args = parser.parse_args()

    ScriptCollection().SCCreateISOFileWithObfuscatedFiles(args.inputfolder, args.outputfile, args.printtableheadline, not args.createnoisofile, args.extensions)
    return 0


def SCChangeHashOfProgram_cli() -> int:
    parser = argparse.ArgumentParser(description='Changes the hash-value of arbitrary files by appending data at the end of the file.')
    parser.add_argument('--inputfile', help='Specifies the script/executable-file whose hash-value should be changed', required=True)
    args = parser.parse_args()
    ScriptCollection().SCChangeHashOfProgram(args.inputfile)
    return 0


def SCCalculateBitcoinBlockHash_cli() -> int:
    parser = argparse.ArgumentParser(description='Calculates the Hash of the header of a bitcoin-block.')
    parser.add_argument('--version', help='Block-version', required=True)
    parser.add_argument('--previousblockhash', help='Hash-value of the previous block', required=True)
    parser.add_argument('--transactionsmerkleroot', help='Hashvalue of the merkle-root of the transactions which are contained in the block', required=True)
    parser.add_argument('--timestamp', help='Timestamp of the block', required=True)
    parser.add_argument('--target', help='difficulty', required=True)
    parser.add_argument('--nonce', help='Arbitrary 32-bit-integer-value', required=True)
    args = parser.parse_args()

    args = parser.parse_args()
    write_message_to_stdout(ScriptCollection().SCCalculateBitcoinBlockHash(args.version, args.previousblockhash,
                                                                           args.transactionsmerkleroot, args.timestamp, args.target, args.nonce))
    return 0


def SCFileIsAvailableOnFileHost_cli() -> int:

    parser = argparse.ArgumentParser(description="Determines whether a file on a filesharing-service supported by the UploadFile-function is still available.")
    parser.add_argument('link')
    args = parser.parse_args()
    return ScriptCollection().SCFileIsAvailableOnFileHost(args.link)


def SCUploadFileToFileHost_cli() -> int:

    parser = argparse.ArgumentParser(description="""Uploads a file to a filesharing-service.
Caution:
You are responsible, accountable and liable for this upload. This trivial script only automates a process which you would otherwise do manually.
Be aware of the issues regarding
- copyright/licenses
- legal issues
of the file content. Furthermore consider the terms of use of the filehoster.
Currently the following filesharing-services will be supported:
- anonfiles.com
- bayfiles.com
""")
    parser.add_argument('file', required=True)
    parser.add_argument('host', required=False)
    args = parser.parse_args()
    return ScriptCollection().SCUploadFileToFileHost(args.file, args.host)


def SCUpdateNugetpackagesInCsharpProject_cli() -> int:

    parser = argparse.ArgumentParser(description="""TODO""")
    parser.add_argument('csprojfile')
    args = parser.parse_args()
    if ScriptCollection().SCUpdateNugetpackagesInCsharpProject(args.csprojfile):
        return 1
    else:
        return 0
    return 2


def SCShow2FAAsQRCode_cli():

    parser = argparse.ArgumentParser(description="""Always when you use 2-factor-authentication you have the problem:
Where to backup the secret-key so that it is easy to re-setup them when you have a new phone?
Using this script is a solution. Always when you setup a 2fa you copy and store the secret in a csv-file.
It should be obviously that this csv-file must be stored encrypted!
Now if you want to move your 2fa-codes to a new phone you simply call "SCShow2FAAsQRCode 2FA.csv"
Then the qr-codes will be displayed in the console and you can scan them on your new phone.
This script does not saving the any data anywhere.

The structure of the csv-file can be viewd here:
Displayname;Website;Email-address;Secret;Period;
Amazon;Amazon.de;myemailaddress@example.com;QWERTY;30;
Google;Google.de;myemailaddress@example.com;ASDFGH;30;

Hints:
-Since the first line of the csv-file contains headlines the first line will always be ignored
-30 is the commonly used value for the period""")
    parser.add_argument('csvfile', help='File where the 2fa-codes are stored')
    args = parser.parse_args()
    ScriptCollection().SCShow2FAAsQRCode(args.csvfile)
    return 0


def SCSearchInFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='''Searchs for the given searchstrings in the content of all files in the given folder.
This program prints all files where the given searchstring was found to the console''')

    parser.add_argument('folder', help='Folder for search')
    parser.add_argument('searchstring', help='string to look for')

    args = parser.parse_args()
    ScriptCollection().SCSearchInFiles(args.folder, args.searchstring)
    return 0


def SCReplaceSubstringsInFilenames_cli() -> int:
    parser = argparse.ArgumentParser(description='Replaces certain substrings in filenames. This program requires "pip install Send2Trash" in certain cases.')

    parser.add_argument('folder', help='Folder where the files are stored which should be renamed')
    parser.add_argument('substringInFilename', help='String to be replaced')
    parser.add_argument('newSubstringInFilename', help='new string value for filename')
    parser.add_argument('conflictResolveMode', help='''Set a method how to handle cases where a file with the new filename already exits and
    the files have not the same content. Possible values are: ignore, preservenewest, merge''')

    args = parser.parse_args()

    ScriptCollection().SCReplaceSubstringsInFilenames(args.folder, args.substringInFilename, args.newSubstringInFilename, args.conflictResolveMode)
    return 0


def SCGenerateSnkFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Generate multiple .snk-files')
    parser.add_argument('outputfolder', help='Folder where the files are stored which should be hashed')
    parser.add_argument('--keysize', default='4096')
    parser.add_argument('--amountofkeys', default='10')

    args = parser.parse_args()
    ScriptCollection().SCGenerateSnkFiles(args.outputfolder, args.keysize, args.amountofkeys)
    return 0


def SCOrganizeLinesInFile_cli() -> int:
    parser = argparse.ArgumentParser(description='Processes the lines of a file with the given commands')

    parser.add_argument('file', help='File which should be transformed')
    parser.add_argument('--encoding', default="utf-8", help='Encoding for the file which should be transformed')
    parser.add_argument("--sort", help="Sort lines", action='store_true')
    parser.add_argument("--remove_duplicated_lines", help="Remove duplicate lines", action='store_true')
    parser.add_argument("--ignore_first_line", help="Ignores the first line in the file", action='store_true')
    parser.add_argument("--remove_empty_lines", help="Removes lines which are empty or contains only whitespaces", action='store_true')
    parser.add_argument('--ignored_start_character', default="", help='Characters which should not be considered at the begin of a line')

    args = parser.parse_args()
    return ScriptCollection().sc_organize_lines_in_file(args.file, args.encoding,
                                                        args.sort, args.remove_duplicated_lines, args.ignore_first_line,
                                                        args.remove_empty_lines, args.ignored_start_character)


def SCCreateHashOfAllFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Calculates the SHA-256-value of all files in the given folder and stores the hash-value in a file next to the hashed file.')
    parser.add_argument('folder', help='Folder where the files are stored which should be hashed')
    args = parser.parse_args()
    ScriptCollection().SCCreateHashOfAllFiles(args.folder)
    return 0


def SCCreateEmptyFileWithSpecificSize_cli() -> int:
    parser = argparse.ArgumentParser(description='Creates a file with a specific size')
    parser.add_argument('name', help='Specifies the name of the created file')
    parser.add_argument('size', help='Specifies the size of the created file')
    args = parser.parse_args()
    return ScriptCollection().SCCreateEmptyFileWithSpecificSize(args.name, args.size)


def SCShowMissingFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Shows all files which are in folderA but not in folder B. This program does not do any content-comparisons.')
    parser.add_argument('folderA')
    parser.add_argument('folderB')
    args = parser.parse_args()
    ScriptCollection().SCShowMissingFiles(args.folderA, args.folderB)
    return 0


def SCMergePDFs_cli() -> int:
    parser = argparse.ArgumentParser(description='merges pdf-files')
    parser.add_argument('files', help='Comma-separated filenames')
    parser = argparse.ArgumentParser(description='''Takes some pdf-files and merge them to one single pdf-file.
Usage: "python MergePDFs.py myfile1.pdf,myfile2.pdf,myfile3.pdf result.pdf"''')
    parser.add_argument('outputfile', help='File for the resulting pdf-document')
    args = parser.parse_args()
    ScriptCollection().merge_pdf_files(args.files.split(','), args.outputfile)
    return 0


def SCKeyboardDiagnosis_cli():
    """Caution: This function does usually never terminate"""
    keyboard.hook(_private_keyhook)
    while True:
        time.sleep(10)


def SCGenerateThumbnail_cli() -> int:
    parser = argparse.ArgumentParser(description='Generate thumpnails for video-files')
    parser.add_argument('file', help='Input-videofile for thumbnail-generation')
    parser.add_argument('framerate', help='', default="16")
    args = parser.parse_args()
    try:
        ScriptCollection().generate_thumbnail(args.file, args.framerate)
        return 0
    except Exception as exception:
        write_exception_to_stderr_with_traceback(exception, traceback)
        return 1


def SCObfuscateFilesFolder_cli() -> int:
    parser = argparse.ArgumentParser(description='''Changes the hash-value of the files in the given folder and renames them to obfuscated names.
This script does not process subfolders transitively.
Caution: This script can cause harm if you pass a wrong inputfolder-argument.''')

    parser.add_argument('--printtableheadline', type=string_to_boolean, const=True,
                        default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
    parser.add_argument('--namemappingfile', default="NameMapping.csv", help='Specifies the file where the name-mapping will be written to')
    parser.add_argument('--extensions', default="exe,py,sh",
                        help='Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
    parser.add_argument('--inputfolder', help='Specifies the folder where the files are stored whose names should be obfuscated', required=True)

    args = parser.parse_args()
    ScriptCollection().SCObfuscateFilesFolder(args.inputfolder, args.printtableheadline, args.namemappingfile, args.extensions)
    return 0

# </CLI-scripts>

# <miscellaneous>


def string_to_lines(string: str, add_empty_lines: bool = True, adapt_lines: bool = True) -> list:
    result = list()
    if(string is not None):
        lines = list()
        if("\n" in string):
            lines = string.splitlines()
        else:
            lines.append(string)
    for rawline in lines:
        if adapt_lines:
            line = rawline.replace("\r", "\n").strip()
        else:
            line = rawline
        if string_is_none_or_whitespace(line):
            if add_empty_lines:
                result.append(line)
        else:
            result.append(line)
    return result


def move_content_of_folder(srcDir, dstDir, overwrite_existing_files=False) -> None:
    srcDirFull = resolve_relative_path_from_current_working_directory(srcDir)
    dstDirFull = resolve_relative_path_from_current_working_directory(dstDir)
    if(os.path.isdir(srcDir)):
        ensure_directory_exists(dstDir)
        for file in get_direct_files_of_folder(srcDirFull):
            shutil.move(file, dstDirFull)
        for sub_folder in get_direct_folders_of_folder(srcDirFull):
            foldername = os.path.basename(sub_folder)
            sub_target = os.path.join(dstDirFull, foldername)
            move_content_of_folder(sub_folder, sub_target)
            ensure_directory_does_not_exist(sub_target)
    else:
        raise ValueError(f"Folder '{srcDir}' does not exist")


def replace_regex_each_line_of_file(file: str, replace_from_regex: str, replace_to_regex: str, encoding="utf-8", verbose: bool = False) -> None:
    """This function iterates over each line in the file and replaces it by the line which applied regex.
    Note: The lines will be taken from open(...).readlines(). So the lines may contain '\\n' or '\\r\\n' for example."""
    if verbose:
        write_message_to_stdout(f"Replace '{replace_from_regex}' to '{replace_to_regex}' in '{file}'")
    with open(file, encoding=encoding, mode="r") as f:
        lines = f.readlines()
        replaced_lines = []
        for line in lines:
            replaced_line = re.sub(replace_from_regex, replace_to_regex, line)
            replaced_lines.append(replaced_line)
    with open(file, encoding=encoding, mode="w") as f:
        f.writelines(replaced_lines)


def replace_regex_in_file(file: str, replace_from_regex: str, replace_to_regex: str, encoding="utf-8") -> None:
    with open(file, encoding=encoding, mode="r") as f:
        content = f.read()
        content = re.sub(replace_from_regex, replace_to_regex, content)
    with open(file, encoding=encoding, mode="w") as f:
        f.write(content)


def replace_xmltag_in_file(file: str, tag: str, new_value: str, encoding="utf-8") -> None:
    replace_regex_in_file(file, f"<{tag}>.*</{tag}>", f"<{tag}>{new_value}</{tag}>", encoding)


def update_version_in_csproj_file(file: str, target_version: str) -> None:
    replace_xmltag_in_file(file, "Version", target_version)
    replace_xmltag_in_file(file, "AssemblyVersion", target_version + ".0")
    replace_xmltag_in_file(file, "FileVersion", target_version + ".0")


def replace_underscores_in_text(text: str, replacements: dict) -> str:
    changed = True
    while changed:
        changed = False
        for key, value in replacements.items():
            previousValue = text
            text = text.replace(f"__{key}__", value)
            if(not text == previousValue):
                changed = True
    return text


def replace_underscores_in_file(file: str, replacements: dict, encoding: str = "utf-8"):
    text = read_text_from_file(file, encoding)
    text = replace_underscores_in_text(text, replacements)
    write_text_to_file(file, text, encoding)


def _private_extension_matchs(file: str, obfuscate_file_extensions) -> bool:
    for extension in obfuscate_file_extensions:
        if file.lower().endswith("."+extension.lower()):
            return True
    return False


def get_ScriptCollection_version() -> str:
    return version


def write_message_to_stdout(message: str):
    sys.stdout.write(str_none_safe(message)+"\n")
    sys.stdout.flush()


def write_message_to_stderr(message: str):
    sys.stderr.write(str_none_safe(message)+"\n")
    sys.stderr.flush()


def write_exception_to_stderr(exception: Exception, extra_message: str = None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr(")")


def write_exception_to_stderr_with_traceback(exception: Exception, current_traceback, extra_message: str = None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    if isinstance(exception, OSError):
        write_message_to_stderr(get_advanced_errormessage_for_os_error(exception))
    write_message_to_stderr("Traceback: "+current_traceback.format_exc())
    write_message_to_stderr(")")


def get_advanced_errormessage_for_os_error(os_error: OSError) -> str:
    if string_has_content(os_error.filename2):
        secondpath = f" {os_error.filename2}"
    else:
        secondpath = ""
    return f"Related path(s): {os_error.filename}{secondpath}"


def string_has_content(string: str) -> bool:
    if string is None:
        return False
    else:
        return len(string) > 0


def datetime_to_string_for_git(datetime_object: datetime) -> str:
    return datetime_object.strftime('%Y-%m-%d %H:%M:%S')


def datetime_to_string_for_logfile_name(datetime_object: datetime) -> str:
    return datetime_object.strftime('%Y-%m-%d_%H-%M-%S')


def datetime_to_string_for_logfile_entry(datetime_object: datetime) -> str:
    return datetime_object.strftime('%Y-%m-%d %H:%M:%S')


def string_has_nonwhitespace_content(string: str) -> bool:
    if string is None:
        return False
    else:
        return len(string.strip()) > 0


def string_is_none_or_empty(argument: str) -> bool:
    if argument is None:
        return True
    type_of_argument = type(argument)
    if type_of_argument == str:
        return argument == ""
    else:
        raise Exception(f"expected string-variable in argument of string_is_none_or_empty but the type was '{str(type_of_argument)}'")


def string_is_none_or_whitespace(string: str) -> bool:
    if string_is_none_or_empty(string):
        return True
    else:
        return string.strip() == ""


def strip_new_line_character(value: str) -> str:
    return value.strip().strip('\n').strip('\r').strip()


def append_line_to_file(file: str, line: str, encoding: str = "utf-8") -> None:
    if not file_is_empty(file):
        line = os.linesep+line
    append_to_file(file, line, encoding)


def append_to_file(file: str, content: str, encoding: str = "utf-8") -> None:
    with open(file, "a", encoding=encoding) as fileObject:
        fileObject.write(content)


def ensure_directory_exists(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def ensure_file_exists(path: str) -> None:
    if(not os.path.isfile(path)):
        with open(path, "a+"):
            pass


def ensure_directory_does_not_exist(path: str) -> None:
    if(os.path.isdir(path)):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)


def ensure_file_does_not_exist(path: str) -> None:
    if(os.path.isfile(path)):
        os.remove(path)


def format_xml_file(filepath: str) -> None:
    format_xml_file_with_encoding(filepath, "utf-8")


def format_xml_file_with_encoding(filepath: str, encoding: str) -> None:
    with codecs.open(filepath, 'r', encoding=encoding) as file:
        text = file.read()
    text = parse(text).toprettyxml()
    with codecs.open(filepath, 'w', encoding=encoding) as file:
        file.write(text)


def get_clusters_and_sectors_of_disk(diskpath: str) -> None:
    sectorsPerCluster = ctypes.c_ulonglong(0)
    bytesPerSector = ctypes.c_ulonglong(0)
    rootPathName = ctypes.c_wchar_p(diskpath)
    ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName, ctypes.pointer(sectorsPerCluster), ctypes.pointer(bytesPerSector), None, None)
    return (sectorsPerCluster.value, bytesPerSector.value)


def ensure_path_is_not_quoted(path: str) -> str:
    if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
        path = path[1:]
        path = path[:-1]
        return path
    else:
        return path


def get_missing_files(folderA: str, folderB: str) -> list:
    folderA_length = len(folderA)
    result = []
    for fileA in absolute_file_paths(folderA):
        file = fileA[folderA_length:]
        fileB = folderB+file
        if not os.path.isfile(fileB):
            result.append(fileB)
    return result


def write_lines_to_file(file: str, lines: list, encoding="utf-8") -> None:
    write_text_to_file(file, os.linesep.join(lines), encoding)


def write_text_to_file(file: str, content: str, encoding="utf-8") -> None:
    write_binary_to_file(file, bytearray(content, encoding))


def write_binary_to_file(file: str, content: bytearray) -> None:
    with open(file, "wb") as file_object:
        file_object.write(content)


def read_lines_from_file(file: str, encoding="utf-8") -> list:
    return read_text_from_file(file, encoding).split(os.linesep)


def read_text_from_file(file: str, encoding="utf-8") -> str:
    return bytes_to_string(read_binary_from_file(file), encoding)


def read_binary_from_file(file: str) -> bytes:
    with open(file, "rb") as file_object:
        return file_object.read()


def timedelta_to_simple_string(delta) -> str:
    return (datetime(1970, 1, 1, 0, 0, 0) + delta).strftime('%H:%M:%S')


def resolve_relative_path_from_current_working_directory(path: str) -> str:
    return resolve_relative_path(path, os.getcwd())


def resolve_relative_path(path: str, base_path: str):
    if(os.path.isabs(path)):
        return path
    else:
        return str(Path(os.path.join(base_path, path)).resolve())


def get_metadata_for_file_for_clone_folder_structure(file: str) -> str:
    size = os.path.getsize(file)
    last_modified_timestamp = os.path.getmtime(file)
    hash_value = get_sha256_of_file(file)
    last_access_timestamp = os.path.getatime(file)
    return f'{{"size":"{size}","sha256":"{hash_value}","mtime":"{last_modified_timestamp}","atime":"{last_access_timestamp}"}}'


def clone_folder_structure(source: str, target: str, copy_only_metadata: bool):
    source = resolve_relative_path(source, os.getcwd())
    target = resolve_relative_path(target, os.getcwd())
    length_of_source = len(source)
    for source_file in absolute_file_paths(source):
        target_file = target+source_file[length_of_source:]
        ensure_directory_exists(os.path.dirname(target_file))
        if copy_only_metadata:
            with open(target_file, 'w', encoding='utf8') as f:
                f.write(get_metadata_for_file_for_clone_folder_structure(source_file))
        else:
            copyfile(source_file, target_file)


def current_user_has_elevated_privileges() -> bool:
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1


def rename_names_of_all_files_and_folders(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    for file in get_direct_files_of_folder(folder):
        replace_in_filename(file, replace_from, replace_to, replace_only_full_match)
    for sub_folder in get_direct_folders_of_folder(folder):
        rename_names_of_all_files_and_folders(sub_folder, replace_from, replace_to, replace_only_full_match)
    replace_in_foldername(folder, replace_from, replace_to, replace_only_full_match)


def get_direct_files_of_folder(folder: str) -> list:
    result = [os.path.join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]
    return result


def get_direct_folders_of_folder(folder: str) -> list:
    result = [os.path.join(folder, f) for f in listdir(folder) if isdir(join(folder, f))]
    return result


def get_all_files_of_folder(folder: str) -> list:
    result = list()
    result.extend(get_direct_files_of_folder(folder))
    for subfolder in get_direct_folders_of_folder(folder):
        result.extend(get_all_files_of_folder(subfolder))
    return result


def get_all_folders_of_folder(folder: str) -> list:
    result = list()
    subfolders = get_direct_folders_of_folder(folder)
    result.extend(subfolders)
    for subfolder in subfolders:
        result.extend(get_all_folders_of_folder(subfolder))
    return result


def get_all_objects_of_folder(folder: str) -> list:
    return get_all_files_of_folder(folder) + get_all_folders_of_folder(folder)


def replace_in_filename(file: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    filename = Path(file).name
    if(_private_should_get_replaced(filename, replace_from, replace_only_full_match)):
        folder_of_file = os.path.dirname(file)
        os.rename(file, os.path.join(folder_of_file, filename.replace(replace_from, replace_to)))


def replace_in_foldername(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    foldername = Path(folder).name
    if(_private_should_get_replaced(foldername, replace_from, replace_only_full_match)):
        folder_of_folder = os.path.dirname(folder)
        os.rename(folder, os.path.join(folder_of_folder, foldername.replace(replace_from, replace_to)))


def _private_should_get_replaced(input_text, search_text, replace_only_full_match) -> bool:
    if replace_only_full_match:
        return input_text == search_text
    else:
        return search_text in input_text


def str_none_safe(variable) -> str:
    if variable is None:
        return ''
    else:
        return str(variable)


def arguments_to_array(arguments_as_string: str) -> list:
    return arguments_as_string.split(" ")  # TODO this function should get heavily improved


def get_sha256_of_file(file: str) -> str:
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def remove_duplicates(input_list) -> list:
    result = []
    for item in input_list:
        if not item in result:
            result.append(item)
    return result


def print_stacktrace() -> None:
    for line in traceback.format_stack():
        write_message_to_stdout(line.strip())


def string_to_boolean(value: str) -> bool:
    value = value.strip().lower()
    if value in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise Exception(f"Can not convert '{value}' to a boolean value")


def file_is_empty(file: str) -> bool:
    return os.stat(file).st_size == 0


def folder_is_empty(folder: str) -> bool:
    return len(get_direct_files_of_folder(folder)) == 0 and len(get_direct_folders_of_folder(folder)) == 0


def get_time_based_logfile_by_folder(folder: str, name: str = "Log", in_utc: bool = False) -> str:
    return os.path.join(resolve_relative_path_from_current_working_directory(folder), f"{get_time_based_logfilename(name, in_utc)}.log")


def get_time_based_logfilename(name: str = "Log", in_utc: bool = False) -> str:
    if(in_utc):
        d = datetime.utcnow()
    else:
        d = datetime.now()
    return f"{name}_{datetime_to_string_for_logfile_name(d)}"


def bytes_to_string(payload: bytes, encoding: str = 'utf-8') -> str:
    return payload.decode(encoding, errors="ignore")


def string_to_bytes(payload: str, encoding: str = 'utf-8') -> bytes:
    return payload.encode(encoding, errors="ignore")


def contains_line(lines, regex: str) -> bool:
    for line in lines:
        if(re.match(regex, line)):
            return True
    return False


def epew_is_available() -> bool:
    try:
        return find_executable("epew") is not None
    except:
        return False


def absolute_file_paths(directory: str) -> list:
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.abspath(os.path.join(dirpath, filename))


def _private_keyhook(event) -> None:
    write_message_to_stdout(str(event.name)+" "+event.event_type)


def os_is_linux():
    return sys.platform == "linux" or sys.platform == "linux2"


def to_list(list_as_string: str, separator: str = ",") -> list:
    result = list()
    if list_as_string is not None:
        list_as_string = list_as_string.strip()
        if list_as_string == "":
            pass
        elif separator in list_as_string:
            for item in list_as_string.split(separator):
                result.append(item.strip())
        else:
            result.append(list_as_string)
    return result


def get_next_square_number(number: int):
    assert_condition(number >= 0, "get_next_square_number is only applicable for nonnegative numbers")
    if number == 0:
        return 1
    root = 0
    square = 0
    while square < number:
        root = root+1
        square = root*root
    return root*root


def assert_condition(condition: bool, information: str):
    if(not condition):
        raise ValueError("Condition failed. "+information)

# <miscellaneous>

# </static>
