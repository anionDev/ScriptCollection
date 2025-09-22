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
from .TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base

class TFCPS_CodeUnitSpecific_Python(TFCPS_CodeUnitSpecific_Base):

    def __init__(self,current_file:str,verbosity:LogLevel):
            super().__init__(current_file, verbosity)


    @GeneralUtilities.check_arguments
    def build_implementation(self) -> None:
        codeunitname: str = self.get_codeunit_name()
        
        codeunit_folder = self.get_codeunit_folder()
        repository_folder: str = self.get_repository_folder()
        target_directory = GeneralUtilities.resolve_relative_path("../Artifacts/BuildResult_Wheel", os.path.join(self.get_artifacts_folder()))
        GeneralUtilities.ensure_directory_exists(target_directory)
        self._protected_sc.run_program("python", f"-m build --wheel --outdir {target_directory}", codeunit_folder)
        self.generate_bom_for_python_project( )
        self.copy_source_files_to_output_directory()
        #TODO check for updateable dependencies (in a unified way)

    @GeneralUtilities.check_arguments
    def generate_bom_for_python_project(self) -> None:
        codeunit_folder: str=self.get_codeunit_folder()
        codeunitname: str=self.get_codeunit_name()
        repository_folder = os.path.dirname(codeunit_folder) 
        
        codeunitversion = self._protected_TFCPS_Other.get_version_of_codeunit()
        bom_folder = "Other/Artifacts/BOM"
        bom_folder_full = os.path.join(codeunit_folder, bom_folder)
        GeneralUtilities.ensure_directory_exists(bom_folder_full)
        if not os.path.isfile(os.path.join(codeunit_folder, "requirements.txt")):
            raise ValueError(f"Codeunit {codeunitname} does not have a 'requirements.txt'-file.")
        # TODO check that all values from setup.cfg are contained in requirements.txt
        result = self._protected_sc.run_program("cyclonedx-py", "requirements", codeunit_folder)
        bom_file_relative_json = f"{bom_folder}/{codeunitname}.{codeunitversion}.bom.json"
        bom_file_relative_xml = f"{bom_folder}/{codeunitname}.{codeunitversion}.bom.xml"
        bom_file_json = os.path.join(codeunit_folder, bom_file_relative_json)
        bom_file_xml = os.path.join(codeunit_folder, bom_file_relative_xml)

        GeneralUtilities.ensure_file_exists(bom_file_json)
        GeneralUtilities.write_text_to_file(bom_file_json, result[1])
        self._protected_TFCPS_Other.ensure_cyclonedxcli_is_available(repository_folder)
        cyclonedx_exe = os.path.join(repository_folder, "Other/Resources/CycloneDXCLI/cyclonedx-cli")
        if GeneralUtilities.current_system_is_windows():
            cyclonedx_exe = cyclonedx_exe+".exe"
        self._protected_sc.run_program(cyclonedx_exe, f"convert --input-file ./{codeunitname}/{bom_file_relative_json} --input-format json --output-file ./{codeunitname}/{bom_file_relative_xml} --output-format xml", repository_folder)
        self._protected_sc.format_xml_file(bom_file_xml)
        GeneralUtilities.ensure_file_does_not_exist(bom_file_json)

    @GeneralUtilities.check_arguments
    def linting_implementation(self) -> None:
        codeunitname: str = self.get_codeunit_name()
        
        repository_folder: str = self.get_repository_folder()
        errors_found = False
        self._protected_sc.log.log(f"Check for linting-issues in codeunit {codeunitname}.")
        src_folder = os.path.join(repository_folder, codeunitname, codeunitname)
        tests_folder = src_folder+"Tests"
        # TODO check if there are errors in sarif-file
        for file in GeneralUtilities.get_all_files_of_folder(src_folder)+GeneralUtilities.get_all_files_of_folder(tests_folder):
            relative_file_path_in_repository = os.path.relpath(file, repository_folder)
            if file.endswith(".py") and os.path.getsize(file) > 0 and not self._protected_sc.file_is_git_ignored(relative_file_path_in_repository, repository_folder):
                self._protected_sc.log.log(f"Check for linting-issues in {os.path.relpath(file, os.path.join(repository_folder, codeunitname))}.")
                linting_result = self._protected_sc.python_file_has_errors(file, repository_folder)
                if (linting_result[0]):
                    errors_found = True
                    for error in linting_result[1]:
                        self._protected_sc.log.log(error, LogLevel.Warning)
        if errors_found:
            raise ValueError("Linting-issues occurred.")
        else:
            self._protected_sc.log.log("No linting-issues found.")

    @GeneralUtilities.check_arguments
    def do_common_tasks_implementation(self) -> None:
        pass

    @GeneralUtilities.check_arguments
    def generate_reference_implementation(self) -> None:
        pass

    @GeneralUtilities.check_arguments
    def update_dependencies_implementation(self) -> None:
        pass
    
    @GeneralUtilities.check_arguments
    def run_testcases_implementation(self) -> None:
        codeunitname: str =self.get_codeunit_name()
        repository_folder: str = self.get_repository_folder()
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        self._protected_sc.run_program("coverage", f"run -m pytest -s ./{codeunitname}Tests", codeunit_folder)
        self._protected_sc.run_program("coverage", "xml", codeunit_folder)
        coveragefolder = os.path.join(repository_folder, codeunitname, "Other/Artifacts/TestCoverage")
        GeneralUtilities.ensure_directory_exists(coveragefolder)
        coveragefile = os.path.join(coveragefolder, "TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder, codeunitname, "coverage.xml"), coveragefile)
        self.run_testcases_common_post_task(repository_folder, codeunitname, True, self.get_type_environment_type())

class TFCPS_CodeUnitSpecific_Python_CLI:

    @staticmethod
    def parse(file:str,args:list[str])->TFCPS_CodeUnitSpecific_Python:
        #TODO process arguments which can contain loglevel etc.
        result:TFCPS_CodeUnitSpecific_Python=TFCPS_CodeUnitSpecific_Python(file,LogLevel.Debug)
        return result
