import os
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore
from .SCLog import  LogLevel
from .TFCPS_CodeUnit_BuildCodeUnit import TFCPS_CodeUnit_BuildCodeUnit
from .TFCPS_Tools_General import TFCPS_Tools_General

class TFCPS_CodeUnit_BuildCodeUnits:
    repository:str=None
    tFCPS_Other:TFCPS_Tools_General=None 
    sc:ScriptCollectionCore=None
    target_environment_type:str=None

    def __init__(self,repository:str,loglevel:LogLevel,target_environment_type):
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=loglevel
        self.sc.assert_is_git_repository(repository)
        self.repository=repository
        self.tFCPS_Other:TFCPS_Tools_General=TFCPS_Tools_General(self.sc)
        self.target_environment_type=target_environment_type

    @GeneralUtilities.check_arguments
    def build_codeunits(self) -> None:
        if  os.path.isfile( os.path.join(self.repository,"Other","Scripts","PrepareBuildCodeunits.py")):
            self.sc.run_program("python", "PrepareBuildCodeunits.py", os.path.join(self.repository,"Other","Scripts"))
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel,self.target_environment_type)
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit()


    @GeneralUtilities.check_arguments
    def update_dependencies(self) -> None:
        self.update_year_in_license_file()
        #TODO update project-wide-dependencies here
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel,self.target_environment_type)
            tFCPS_CodeUnit_BuildCodeUnit.update_dependencies() 

    @GeneralUtilities.check_arguments
    def update_year_in_license_file(self) -> None:
        self.sc.update_year_in_first_line_of_file(os.path.join(self.repository, "License.txt"))
