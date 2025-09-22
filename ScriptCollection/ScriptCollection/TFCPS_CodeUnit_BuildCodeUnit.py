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
from .TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python

class TFCPS_CodeUnit_BuildCodeUnit:

    codeunit_folder:str
    sc:ScriptCollectionCore=ScriptCollectionCore()
    verbosity:LogLevel

    def __init__(self,codeunit_folder:str,verbosity:LogLevel):
        self.codeunit_folder=codeunit_folder
        self.verbosity=verbosity
        
    @GeneralUtilities.check_arguments
    def build_codeunit(self) -> None:
        self.sc.log.log("Do common tasks...")
        self.sc.run_program("python","CommonTasks.py",os.path.join(self.codeunit_folder,"Other"))
        self.sc.log.log("Build...")
        self.sc.run_program("python","Build.py",os.path.join(self.codeunit_folder,"Other","Build"))
        self.sc.log.log("Run testcases...")
        self.sc.run_program("python","RunTestcases.py",os.path.join(self.codeunit_folder,"Other","QualityCheck"))
        self.sc.log.log("Check for linting-issues...")
        self.sc.run_program("python","Linting.py",os.path.join(self.codeunit_folder,"Other","QualityCheck"))
        self.sc.log.log("Generate reference...")
        self.sc.run_program("python","GenerateReference.py",os.path.join(self.codeunit_folder,"Other","Reference"))
