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
from .TFCPS_CodeUnitSpecific import TFCPS_CodeUnitSpecific

class TFCPS_CodeUnitSpecific_Python(TFCPS_CodeUnitSpecific):

    def __init__(self,current_file,cmd_arguments:list[str]):
            super().__init__(current_file, cmd_arguments)

    @GeneralUtilities.check_arguments
    def build_implementation(self) -> None:
        codeunitname: str = Path(os.path.dirname(buildscript_file)).parent.parent.name
        
        codeunit_folder = str(Path(os.path.dirname(buildscript_file)).parent.parent.absolute())
        repository_folder: str = str(Path(os.path.dirname(buildscript_file)).parent.parent.parent.absolute())
        target_directory = GeneralUtilities.resolve_relative_path("../Artifacts/BuildResult_Wheel", os.path.join(self.get_artifacts_folder(repository_folder, codeunitname)))
        GeneralUtilities.ensure_directory_exists(target_directory)
        self.__sc.run_program("python", f"-m build --wheel --outdir {target_directory}", codeunit_folder)
        self.generate_bom_for_python_project( codeunit_folder, codeunitname)
        self.copy_source_files_to_output_directory(buildscript_file)
        #TODO check for updateable dependencies (in a unified way)

    @GeneralUtilities.check_arguments
    def linting_implementation(self) -> None:
        codeunitname: str = Path(os.path.dirname(linting_script_file)).parent.parent.name
        
        repository_folder: str = str(Path(os.path.dirname(linting_script_file)).parent.parent.parent.absolute())
        errors_found = False
        self.__log.log(f"Check for linting-issues in codeunit {codeunitname}.")
        src_folder = os.path.join(repository_folder, codeunitname, codeunitname)
        tests_folder = src_folder+"Tests"
        # TODO check if there are errors in sarif-file
        for file in GeneralUtilities.get_all_files_of_folder(src_folder)+GeneralUtilities.get_all_files_of_folder(tests_folder):
            relative_file_path_in_repository = os.path.relpath(file, repository_folder)
            if file.endswith(".py") and os.path.getsize(file) > 0 and not self.__sc.file_is_git_ignored(relative_file_path_in_repository, repository_folder):
                self.__log.log(f"Check for linting-issues in {os.path.relpath(file, os.path.join(repository_folder, codeunitname))}.")
                linting_result = self.__sc.python_file_has_errors(file, repository_folder)
                if (linting_result[0]):
                    errors_found = True
                    for error in linting_result[1]:
                        self.__log.log(error, LogLevel.Warning)
        if errors_found:
            raise ValueError("Linting-issues occurred.")
        else:
            self.__log.log("No linting-issues found.")

    @GeneralUtilities.check_arguments
    def run_testcases_implementation(self) -> None:
        codeunitname: str = Path(os.path.dirname(run_testcases_file)).parent.parent.name
        repository_folder: str = str(Path(os.path.dirname(run_testcases_file)).parent.parent.parent.absolute())
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        self.__sc.run_program("coverage", f"run -m pytest -s ./{codeunitname}Tests", codeunit_folder)
        self.__sc.run_program("coverage", "xml", codeunit_folder)
        coveragefolder = os.path.join(repository_folder, codeunitname, "Other/Artifacts/TestCoverage")
        GeneralUtilities.ensure_directory_exists(coveragefolder)
        coveragefile = os.path.join(coveragefolder, "TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder, codeunitname, "coverage.xml"), coveragefile)
        self.run_testcases_common_post_task(repository_folder, codeunitname, generate_badges, targetenvironmenttype)
