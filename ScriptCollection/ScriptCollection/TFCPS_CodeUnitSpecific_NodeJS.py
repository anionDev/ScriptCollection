from .GeneralUtilities import GeneralUtilities
from .SCLog import  LogLevel
from .TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base,TFCPS_CodeUnitSpecific_Base_CLI

class TFCPS_CodeUnitSpecific_NodeJS_Functions(TFCPS_CodeUnitSpecific_Base):


    def __init__(self,current_file:str,verbosity:LogLevel,targetenvironmenttype:str,additional_arguments_file:str):
        super().__init__(current_file, verbosity,targetenvironmenttype,additional_arguments_file)


    @GeneralUtilities.check_arguments
    def build_implementation(self,additional_arguments:dict) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def linting_implementation(self,additional_arguments:dict) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def do_common_tasks_implementation(self,additional_arguments:dict) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def generate_reference_implementation(self,additional_arguments:dict) -> None:
        pass#nothing to do

    @GeneralUtilities.check_arguments
    def update_dependencies_implementation(self,additional_arguments:dict) -> None:
        pass#TODO
    
    @GeneralUtilities.check_arguments
    def run_testcases_implementation(self,additional_arguments:dict) -> None:
        pass#TODO

class TFCPS_CodeUnitSpecific_Flutter_CLI:
 
    @staticmethod
    def parse(file:str,args:list[str])->TFCPS_CodeUnitSpecific_NodeJS_Functions:
        parser=TFCPS_CodeUnitSpecific_Base_CLI.get_base_parser()
        #add custom parameter if desired
        args=parser.parse_args()
        result:TFCPS_CodeUnitSpecific_NodeJS_Functions=TFCPS_CodeUnitSpecific_NodeJS_Functions(file,LogLevel(int(args.verbosity)),args.targetenvironmenttype,args.additionalargumentsfile)
        return result
