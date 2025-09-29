from ...GeneralUtilities import GeneralUtilities
from ...SCLog import  LogLevel
from ..TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base,TFCPS_CodeUnitSpecific_Base_CLI

class TFCPS_CodeUnitSpecific_Flutter_Functions(TFCPS_CodeUnitSpecific_Base):
 
    def __init__(self,current_file:str,verbosity:LogLevel,targetenvironmenttype:str,use_cache:bool):
        super().__init__(current_file, verbosity,targetenvironmenttype,use_cache)


    @GeneralUtilities.check_arguments
    def build(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def linting(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def do_common_tasks(self,current_codeunit_version:str )-> None:
        self.do_common_tasks_base(current_codeunit_version)

    @GeneralUtilities.check_arguments
    def generate_reference(self) -> None:
        self.generate_reference_using_docfx()

    @GeneralUtilities.check_arguments
    def update_dependencies(self) -> None:
        pass#TODO
    
    @GeneralUtilities.check_arguments
    def run_testcases(self) -> None:
        pass#TODO

class TFCPS_CodeUnitSpecific_Flutter_CLI:

    @staticmethod
    def parse(file:str)->TFCPS_CodeUnitSpecific_Flutter_Functions:
        parser=TFCPS_CodeUnitSpecific_Base_CLI.get_base_parser()
        #add custom parameter if desired
        args=parser.parse_args()
        result:TFCPS_CodeUnitSpecific_Flutter_Functions=TFCPS_CodeUnitSpecific_Flutter_Functions(file,LogLevel(int(args.verbosity)),args.targetenvironmenttype,not args.nocache)
        return result
