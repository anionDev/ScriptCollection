import os
import argparse
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import  LogLevel
from .TFCPS_Tools_General import TFCPS_Tools_General

class TFCPS_Generic_Functions:
    script_file:str
    repository_folder:str=None
    targetenvironmenttype:str
    additionalargumentsfile:str
    verbosity:LogLevel
    sc:ScriptCollectionCore
    tfcps_Tools_General:TFCPS_Tools_General
    
    def __init__(self,script_file:str,targetenvironmenttype:str,additionalargumentsfile:str,verbosity:LogLevel):
        self.verbosity=verbosity
        self.script_file=script_file
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=self.verbosity
        self.tfcps_Tools_General=TFCPS_Tools_General(self.sc)
        self.repository_folder=self.__search_repository_folder()
        self.targetenvironmenttype=targetenvironmenttype
        self.additionalargumentsfile=additionalargumentsfile

    def __search_repository_folder(self)->str:
        current_path:str=os.path.dirname(self.script_file)
        enabled:bool=True
        while enabled:
            try:
                current_path=GeneralUtilities.resolve_relative_path("..",current_path)
                if self.sc.is_git_repository(current_path):
                    return current_path
            except:
                enabled=False
        raise ValueError(f"Can not find git-repository for folder \"{self.script_file}\".")

class TFCPS_Generic_CLI:

    @staticmethod
    def parse(file:str)->TFCPS_Generic_Functions:
        parser = argparse.ArgumentParser()
        verbosity_values = ", ".join(f"{lvl.value}={lvl.name}" for lvl in LogLevel)
        parser.add_argument('-e', '--targetenvironmenttype', required=False, default="QualityCheck")
        parser.add_argument('-a', '--additionalargumentsfile', required=False, default=None)
        parser.add_argument('-v', '--verbosity', required=False, default=3, help=f"Sets the loglevel. Possible values: {verbosity_values}")
        args=parser.parse_args()
        result:TFCPS_Generic_Functions=TFCPS_Generic_Functions(file,args.targetenvironmenttype,args.additionalargumentsfile,LogLevel(int(args.verbosity)))
        return result 
