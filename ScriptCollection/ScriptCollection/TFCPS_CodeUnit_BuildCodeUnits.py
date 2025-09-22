import os
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore
from .SCLog import  LogLevel
from .TFCPS_CodeUnit_BuildCodeUnit import TFCPS_CodeUnit_BuildCodeUnit
from .TFCPS_Other import TFCPS_Other

class TFCPS_CodeUnit_BuildCodeUnits:
    repository:str=None
    tFCPS_Other:TFCPS_Other=None 
    sc:ScriptCollectionCore=None

    def __init__(self,repository:str,loglevel:LogLevel):
        self.repository=repository
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=loglevel
        self.tFCPS_Other:TFCPS_Other=TFCPS_Other(self.sc)

    @GeneralUtilities.check_arguments
    def build_codeunits(self) -> None:
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel)
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit() 
