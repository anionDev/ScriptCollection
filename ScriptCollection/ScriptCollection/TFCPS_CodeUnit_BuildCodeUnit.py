import os
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore
from .SCLog import  LogLevel

class TFCPS_CodeUnit_BuildCodeUnit:

    codeunit_folder:str
    sc:ScriptCollectionCore=ScriptCollectionCore()
    codeunit_name:str

    def __init__(self,codeunit_folder:str,verbosity:LogLevel):
        self.codeunit_folder=codeunit_folder
        self.codeunit_name=os.path.dirname(self.codeunit_folder)
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=verbosity
        
    @GeneralUtilities.check_arguments
    def build_codeunit(self) -> None:
        self.sc.log.log(f"Build codeunit {self.codeunit_name}...")
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
