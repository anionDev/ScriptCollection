import argparse
from ..SCLog import  LogLevel
from ..ScriptCollectionCore import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore

class TFCPS_PreBuildCodeunitsScriptConfiguration:
    targetenvironmenttype:str
    additionalargumentsfile:str
    verbosity:LogLevel
    use_cache:str
    repository_folder:str=None

    def __init__(self,script_file:str,targetenvironmenttype:str,additionalargumentsfile:str,verbosity:LogLevel,use_cache:bool):
        self.targetenvironmenttype=targetenvironmenttype
        self.additionalargumentsfile=additionalargumentsfile
        self.verbosity=verbosity
        self.use_cache=use_cache
        self.repository_folder=ScriptCollectionCore().search_repository_folder(script_file)

class TFCPS_PreBuildCodeunitsScript:
    configuration:TFCPS_PreBuildCodeunitsScriptConfiguration

    def __init__(self,configuration:TFCPS_PreBuildCodeunitsScriptConfiguration):
        self.configuration=configuration

    def pre_merge(self):
        pass#TODO

class TFCPS_PreBuildCodeunitsScript_CLI():

    @staticmethod
    @GeneralUtilities.check_arguments
    def parse(script_file:str)->argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        verbosity_values = ", ".join(f"{lvl.value}={lvl.name}" for lvl in LogLevel)
        parser.add_argument('-e', '--targetenvironmenttype', required=False, default="QualityCheck")
        parser.add_argument('-a', '--additionalargumentsfile', required=False, default=None)
        parser.add_argument('-v', '--verbosity', required=False, default=3, help=f"Sets the loglevel. Possible values: {verbosity_values}")
        parser.add_argument('-c', '--nocache',  action='store_true', required=False, default=False)
        args=parser.parse_args()
        return TFCPS_PreBuildCodeunitsScript(TFCPS_PreBuildCodeunitsScriptConfiguration(script_file,args.targetenvironmenttype,args.additionalargumentsfile,LogLevel(int(args.verbosity)),not args.nocache))
