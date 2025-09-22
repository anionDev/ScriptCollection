from datetime import datetime, timedelta, timezone
from graphlib import TopologicalSorter
import os
import argparse
from pathlib import Path
from functools import cmp_to_key
import shutil
import math
import tarfile
import re
import sys
import urllib.request
import zipfile
import json
import configparser
import tempfile
import uuid
import yaml
import requests
from packaging import version
import xmlschema
from OpenSSL import crypto
from lxml import etree
from abc import ABC, abstractmethod
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore
from .SCLog import SCLog, LogLevel
from .ProgramRunnerEpew import ProgramRunnerEpew
from .ImageUpdater import ImageUpdater, VersionEcholon


class TFCPS_CodeUnitSpecific(ABC):
    
    __current_file:str=None
    __repository_folder:str=None
    __codeunit_folder:str=None

    def __init__(self,current_file,cmd_arguments:list[str]):
        self.__current_file = str(Path(__file__).absolute())
        self.__codeunit_folder=self.__get_codeunit_folder()
        #TODO assert that codeunitfolder is really a codeunit-folder
        self.__repository_folder=GeneralUtiliites.resolve_relative_path("..",self.__codeunit_folder)
        #TODO assert repository folder is really a git-repository

    @abstractmethod
    def do_common_tasks_implementation(self):
        raise ValueError("This method is abstract.")

    @abstractmethod
    def build_implementation(self):
        raise ValueError("This method is abstract.")

    @abstractmethod
    def run_testcases_implementation(self):
        raise ValueError("This method is abstract.")

    @abstractmethod
    def linting_implementation(self):
        raise ValueError("This method is abstract.")

    @abstractmethod
    def generate_reference_implementation(self):
        raise ValueError("This method is abstract.")

    @abstractmethod
    def update_dependencies_implementation(self):
        raise ValueError("This method is abstract.")

    

    def do_common_tasks(self):
        self.do_common_tasks_implementation()

    def build(self):
        self.build_implementation()

    def run_testcases(self):
        self.run_testcases_implementation()

    def linting(self):
        self.linting_implementation()

    def generate_reference(self):
        self.generate_reference_implementation()

    def update_dependencies(self):
        self.update_dependencies_implementation()

    @GeneralUtilities.check_arguments
    def __standardized_tasks_do_common_tasks(self) -> None:
        #TODO set variables:
        common_tasks_scripts_file: str
        codeunit_version: str
        targetenvironmenttype: str
        clear_artifacts_folder: bool
        additional_arguments_file: str
        assume_dependent_codeunits_are_already_built: bool

        repository_folder: str = str(Path(os.path.dirname(common_tasks_scripts_file)).parent.parent.absolute())
        self.__sc.assert_is_git_repository(repository_folder)
        codeunit_name: str = str(os.path.basename(Path(os.path.dirname(common_tasks_scripts_file)).parent.absolute()))
        project_version = self.get_version_of_project(repository_folder)
        codeunit_folder = os.path.join(repository_folder, codeunit_name)

        # check codeunit-conformity
        # TODO check if foldername=="<codeunitname>[.codeunit.xml]" == <codeunitname> in file
        supported_codeunitspecificationversion = "2.9.4"  # should always be the latest version of the ProjectTemplates-repository
        codeunit_file = os.path.join(codeunit_folder, f"{codeunit_name}.codeunit.xml")
        if not os.path.isfile(codeunit_file):
            raise ValueError(f'Codeunitfile "{codeunit_file}" does not exist.')
        # TODO implement usage of self.reference_latest_version_of_xsd_when_generating_xml
        namespaces = {'cps': 'https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/tree/main/Conventions/RepositoryStructure/CommonProjectStructure',  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        root: etree._ElementTree = etree.parse(codeunit_file)

        # check codeunit-spcecification-version
        try:
            codeunit_file_version = root.xpath('//cps:codeunit/@codeunitspecificationversion', namespaces=namespaces)[0]
            if codeunit_file_version != supported_codeunitspecificationversion:
                raise ValueError(f"ScriptCollection only supports processing codeunits with codeunit-specification-version={supported_codeunitspecificationversion}.")
            schemaLocation = root.xpath('//cps:codeunit/@xsi:schemaLocation', namespaces=namespaces)[0]
            xmlschema.validate(codeunit_file, schemaLocation)
            # TODO check if the properties codeunithastestablesourcecode, codeunithasupdatabledependencies, throwexceptionifcodeunitfilecannotbevalidated, developmentState and description exist and the values are valid
        except Exception as exception:
            if self.codeunit_throws_exception_if_codeunitfile_is_not_validatable(codeunit_file):
                raise exception
            else:
                self.__log.log(f'Codeunitfile "{codeunit_file}" can not be validated due to the following exception:', LogLevel.Warning)
                GeneralUtilities.write_exception_to_stderr(exception)

        # check codeunit-name
        codeunit_name_in_codeunit_file = root.xpath('//cps:codeunit/cps:name/text()', namespaces=namespaces)[0]
        if codeunit_name != codeunit_name_in_codeunit_file:
            raise ValueError(f"The folder-name ('{codeunit_name}') is not equal to the codeunit-name ('{codeunit_name_in_codeunit_file}').")

        # check owner-name
        codeunit_ownername_in_codeunit_file = self. get_codeunit_owner_name(codeunit_file)
        GeneralUtilities.assert_condition(GeneralUtilities.string_has_content(codeunit_ownername_in_codeunit_file), "No valid name for codeunitowner given.")

        # check owner-emailaddress
        codeunit_owneremailaddress_in_codeunit_file = self.get_codeunit_owner_emailaddress(codeunit_file)
        GeneralUtilities.assert_condition(GeneralUtilities.string_has_content(codeunit_owneremailaddress_in_codeunit_file), "No valid email-address for codeunitowner given.")

        # check development-state
        developmentstate = root.xpath('//cps:properties/@developmentstate', namespaces=namespaces)[0]
        developmentstate_active = "Active development"
        developmentstate_maintenance = "Maintenance-updates only"
        developmentstate_inactive = "Inactive"
        GeneralUtilities.assert_condition(developmentstate in (developmentstate_active, developmentstate_maintenance, developmentstate_inactive), f"Invalid development-state. Must be '{developmentstate_active}' or '{developmentstate_maintenance}' or '{developmentstate_inactive}' but was '{developmentstate}'.")

        # check for mandatory files
        files = ["Other/Build/Build.py", "Other/QualityCheck/Linting.py", "Other/Reference/GenerateReference.py"]
        if self.codeunit_has_testable_sourcecode(codeunit_file):
            # TODO check if the testsettings-section appears in the codeunit-file
            files.append("Other/QualityCheck/RunTestcases.py")
        if self.codeunit_has_updatable_dependencies(codeunit_file):
            # TODO check if the updatesettings-section appears in the codeunit-file
            files.append("Other/UpdateDependencies.py")
        for file in files:
            combined_file = os.path.join(codeunit_folder, file)
            if not os.path.isfile(combined_file):
                raise ValueError(f'The mandatory file "{file}" does not exist in the codeunit-folder.')

        if os.path.isfile(os.path.join(codeunit_folder, "Other", "requirements.txt")):
            self.install_requirementstxt_for_codeunit(codeunit_folder)

        # check developer
        if self.validate_developers_of_repository:
            expected_authors: list[tuple[str, str]] = []
            expected_authors_in_xml = root.xpath('//cps:codeunit/cps:developerteam/cps:developer', namespaces=namespaces)
            for expected_author in expected_authors_in_xml:
                author_name = expected_author.xpath('./cps:developername/text()', namespaces=namespaces)[0]
                author_emailaddress = expected_author.xpath('./cps:developeremailaddress/text()', namespaces=namespaces)[0]
                expected_authors.append((author_name, author_emailaddress))
            actual_authors: list[tuple[str, str]] = self.__sc.get_all_authors_and_committers_of_repository(repository_folder, codeunit_name)
            # TODO refactor this check to only check commits which are behind this but which are not already on main
            # TODO verify also if the commit is signed by a valid key of the author
            for actual_author in actual_authors:
                if not (actual_author) in expected_authors:
                    actual_author_formatted = f"{actual_author[0]} <{actual_author[1]}>"
                    raise ValueError(f'Author/Comitter "{actual_author_formatted}" is not in the codeunit-developer-team. If {actual_author} is a authorized developer for this codeunit you should consider defining this in the codeunit-file or adapting the name using a .mailmap-file (see https://git-scm.com/docs/gitmailmap). The developer-team-check can also be disabled using the property validate_developers_of_repository.')

        dependent_codeunits = self.get_dependent_code_units(codeunit_file)
        for dependent_codeunit in dependent_codeunits:
            if not self.dependent_codeunit_exists(repository_folder, dependent_codeunit):
                raise ValueError(f"Codeunit {codeunit_name} does have dependent codeunit {dependent_codeunit} which does not exist.")

        # TODO implement cycle-check for dependent codeunits

        # clear previously builded artifacts if desired:
        if clear_artifacts_folder:
            artifacts_folder = os.path.join(codeunit_folder, "Other", "Artifacts")
            GeneralUtilities.ensure_directory_does_not_exist(artifacts_folder)

        # get artifacts from dependent codeunits
        # if assume_dependent_codeunits_are_already_built:
        #    self.build_dependent_code_units(repository_folder, codeunit_name, target_environmenttype, additional_arguments_file)
        self.copy_artifacts_from_dependent_code_units(repository_folder, codeunit_name)

        # update codeunit-version
        self.update_version_of_codeunit(common_tasks_scripts_file, codeunit_version)

        # set project version
        package_json_file = os.path.join(repository_folder, "package.json")  # TDOO move this to a general project-specific (and codeunit-independent-script)
        if os.path.isfile(package_json_file):
            package_json_data: str = None
            with open(package_json_file, "r", encoding="utf-8") as f1:
                package_json_data = json.load(f1)
                package_json_data["version"] = project_version
            with open(package_json_file, "w", encoding="utf-8") as f2:
                json.dump(package_json_data, f2, indent=2)
            GeneralUtilities.write_text_to_file(package_json_file, GeneralUtilities.read_text_from_file(package_json_file).replace("\r", ""))

        # set default constants
        self.set_default_constants(os.path.join(codeunit_folder))

        # Copy changelog-file
        changelog_folder = os.path.join(repository_folder, "Other", "Resources", "Changelog")
        changelog_file = os.path.join(changelog_folder, f"v{project_version}.md")
        target_folder = os.path.join(codeunit_folder, "Other", "Artifacts", "Changelog")
        GeneralUtilities.ensure_directory_exists(target_folder)
        shutil.copy(changelog_file, target_folder)

        # Hints-file
        hints_file = os.path.join(codeunit_folder, "Other", "Reference", "ReferenceContent", "Hints.md")
        if not os.path.isfile(hints_file):
            raise ValueError(f"Hints-file '{hints_file}' does not exist.")

        # Copy license-file
        self.copy_licence_file(common_tasks_scripts_file)

        # Generate diff-report
        self.generate_diff_report(repository_folder, codeunit_name, codeunit_version)

        # TODO check for secrets using TruffleHog
    @GeneralUtilities.check_arguments
    def __standardized_tasks_generate_reference_by_docfx(self) -> None:
        folder_of_current_file = os.path.dirname(generate_reference_script_file)
        generated_reference_folder = GeneralUtilities.resolve_relative_path("../Artifacts/Reference", folder_of_current_file)
        GeneralUtilities.ensure_directory_does_not_exist(generated_reference_folder)
        GeneralUtilities.ensure_directory_exists(generated_reference_folder)
        obj_folder = os.path.join(folder_of_current_file, "obj")
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)
        GeneralUtilities.ensure_directory_exists(obj_folder)
        self.__sc.run_program("docfx", "-t default,templates/darkfx docfx.json", folder_of_current_file)
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)
