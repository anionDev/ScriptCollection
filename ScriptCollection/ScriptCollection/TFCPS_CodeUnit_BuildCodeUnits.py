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
from .TFCPS_CodeUnit_BuildCodeUnit import TFCPS_CodeUnit_BuildCodeUnit
from .TFCPS_Other import TFCPS_Other

class TFCPS_CodeUnit_BuildCodeUnits:
    repository:str=None
    tFCPS_Other:TFCPS_Other=None 
    verbosity:LogLevel=None
    sc:ScriptCollectionCore=None

    def __init__(self,repository:str,loglevel:LogLevel):
        self.repository=repository
        self.verbosity=loglevel
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=loglevel
        self.tFCPS_Other:TFCPS_Other=TFCPS_Other(self.sc)

    @GeneralUtilities.check_arguments
    def build_codeunits(self) -> None:
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.verbosity)
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit() 
 