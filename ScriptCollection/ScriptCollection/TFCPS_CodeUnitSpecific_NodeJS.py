from .GeneralUtilities import GeneralUtilities
from .SCLog import  LogLevel
from .TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base

class TFCPS_CodeUnitSpecific_NodeJS(TFCPS_CodeUnitSpecific_Base):

    def __init__(self,current_file:str,verbosity:LogLevel):
        super().__init__(current_file, verbosity)


    @GeneralUtilities.check_arguments
    def build_implementation(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def linting_implementation(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def do_common_tasks_implementation(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def generate_reference_implementation(self) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def update_dependencies_implementation(self) -> None:
        pass#TODO
    
    @GeneralUtilities.check_arguments
    def run_testcases_implementation(self) -> None:
        pass#TODO

class TFCPS_CodeUnitSpecific_Python_CLI:

    @staticmethod
    def parse(file:str,args:list[str])->TFCPS_CodeUnitSpecific_NodeJS:
        #TODO process arguments which can contain loglevel etc.
        result:TFCPS_CodeUnitSpecific_NodeJS=TFCPS_CodeUnitSpecific_NodeJS(file,LogLevel.Debug)
        return result
