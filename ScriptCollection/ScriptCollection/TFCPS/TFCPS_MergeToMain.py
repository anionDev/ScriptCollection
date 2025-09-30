from ..GeneralUtilities import GeneralUtilities
from ..SCLog import LogLevel
from ..ScriptCollectionCore import ScriptCollectionCore
from .TFCPS_Tools_General import TFCPS_Tools_General
from .TFCPS_CodeUnit_BuildCodeUnits import TFCPS_CodeUnit_BuildCodeUnits
from .TFCPS_Generic import TFCPS_Generic_Functions

class MergeToMainConfiguration:
    product_name: str
    merge_source_branch:str
    additional_arguments_file:str
    log_level:LogLevel
    main_branch:str
    repository_folder:str
    tFCPS_Generic_Functions:TFCPS_Generic_Functions
    common_remote_name:str
    sc:ScriptCollectionCore=ScriptCollectionCore()

    def __init__(self, current_file: str, product_name: str,merge_source_branch:str,log_level:LogLevel,additional_arguments_file:str,main_branch:str,common_remote_name:str):
        self.sc.log.loglevel=log_level
        self.repository_folder = self.sc.search_repository_folder(current_file)
        self.product_name = product_name
        self.merge_source_branch=merge_source_branch
        self.additional_arguments_file=additional_arguments_file
        self.log_level=log_level
        self.main_branch=main_branch
        self.common_remote_name=common_remote_name

class TFCPS_MergeToMain:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General


    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)


    @GeneralUtilities.check_arguments
    def merge_to_main_branch(self,  generic_prepare_new_release_arguments:MergeToMainConfiguration) -> None:
        self.sc.log.loglevel=generic_prepare_new_release_arguments.log_level
        fast_forward_source_branch: bool=True
        source_branch: str=generic_prepare_new_release_arguments.merge_source_branch
        target_branch: str=generic_prepare_new_release_arguments.main_branch
        self.sc.log.log(f"Merge to main-branch...")
        self.sc.assert_is_git_repository(generic_prepare_new_release_arguments.repository_folder)

        self.sc.assert_no_uncommitted_changes(generic_prepare_new_release_arguments.repository_folder)
        self.sc.git_checkout(generic_prepare_new_release_arguments.repository_folder, source_branch)
        self.sc.assert_no_uncommitted_changes(generic_prepare_new_release_arguments.repository_folder)

        tfcps_CodeUnit_BuildCodeUnits:TFCPS_CodeUnit_BuildCodeUnits=TFCPS_CodeUnit_BuildCodeUnits(generic_prepare_new_release_arguments.repository_folder,self.sc.log.loglevel,"QualityCheck",generic_prepare_new_release_arguments.additional_arguments_file,False,True)
        try:
            tfcps_CodeUnit_BuildCodeUnits.build_codeunits()
        except Exception:
            self.sc.git_undo_all_changes(generic_prepare_new_release_arguments.repository_folder)
            raise

        self.sc.git_commit(generic_prepare_new_release_arguments.repository_folder, f'Built codeunits', stage_all_changes=True, no_changes_behavior=0)
        
        if fast_forward_source_branch:
            self.sc.git_checkout(generic_prepare_new_release_arguments.repository_folder, target_branch)
            self.sc.git_merge(generic_prepare_new_release_arguments.repository_folder, target_branch, source_branch, True, True)
        self.sc.git_push_with_retry(generic_prepare_new_release_arguments.repository_folder,generic_prepare_new_release_arguments.common_remote_name,source_branch,source_branch)
        self.sc.git_push_with_retry(generic_prepare_new_release_arguments.repository_folder,generic_prepare_new_release_arguments.common_remote_name,target_branch,target_branch)
