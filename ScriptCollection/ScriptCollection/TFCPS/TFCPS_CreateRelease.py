import os
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import LogLevel
from .TFCPS_Tools_General import TFCPS_Tools_General
from .TFCPS_MergeToMain import TFCPS_MergeToMain,MergeToMainConfiguration
from .TFCPS_MergeToStable import TFCPS_MergeToStable,MergeToStableConfiguration
 
class GenericCreateReleaseArgumentsOld():
    current_file: str
    product_name: str
    common_remote_name: str
    artifacts_target_folder: str
    commandline_arguments: list[str]

    def __init__(self, current_file: str, product_name: str, common_remote_name: str, artifacts_target_folder: str,commandline_arguments:list[str]):
        self.current_file = current_file
        self.product_name = product_name
        self.common_remote_name = common_remote_name
        self.artifacts_target_folder = artifacts_target_folder
        self.commandline_arguments = commandline_arguments

class TFCPS_DoRelease3_FullOld:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)

    @GeneralUtilities.check_arguments
    def generic_create_release_old(self, generic_create_release_arguments: GenericCreateReleaseArgumentsOld) -> tuple[bool, str]:
        self.sc.log.log(f"Create release for {generic_create_release_arguments.product_name}.")
        folder_of_this_file = os.path.dirname(generic_create_release_arguments.current_file)
        build_repository_folder = GeneralUtilities.resolve_relative_path("../..", folder_of_this_file)
        #repository_folder_name = generic_create_release_arguments.product_name
        repository_folder = GeneralUtilities.resolve_relative_path(f"../../Submodules/{generic_create_release_arguments.product_name}", folder_of_this_file)
        self.sc.assert_is_git_repository(repository_folder)

        merge_source_branch = "main"  # TODO make this configurable
        main_branch = "stable"  # TODO make this configurable

        #additional_arguments_file = os.path.join(folder_of_this_file, "AdditionalArguments.configuration")
        createReleaseConfiguration=None#CreateReleaseConfigurationOld = CreateReleaseConfigurationOld(generic_create_release_arguments.product_name, generic_create_release_arguments.common_remote_name, generic_create_release_arguments.artifacts_target_folder, folder_of_this_file, repository_folder, additional_arguments_file, repository_folder_name)

        merge_source_branch_commit_id = self.sc.git_get_commit_id(repository_folder, merge_source_branch)
        main_branch_commit_id = self.sc.git_get_commit_id(repository_folder, main_branch)
        if merge_source_branch_commit_id == main_branch_commit_id:
            self.sc.log.log("Release will not be done because there are no changed which can be released.")
            return False, None
        else:
            self.sc.git_checkout(repository_folder, merge_source_branch)
            reference_repo: str = os.path.join(build_repository_folder, "Submodules", f"{generic_create_release_arguments.product_name}Reference")
            self.sc.git_commit(reference_repo, "Updated reference")
            self.sc.git_push_with_retry(reference_repo, generic_create_release_arguments.common_remote_name, "main", "main")
            self.sc.git_commit(build_repository_folder, "Updated submodule")

            # create release
            m2=None#:TFCPS_MainToStable=TFCPS_MainToStable()
            new_version =m2.merge_to_stable_branch(generic_create_release_arguments.current_file, createReleaseConfiguration)
            self.sc.log.log(f"Finished create release for {generic_create_release_arguments.product_name}.")
            return True, new_version


class TFCPS_CreateReleaseConfiguration:
    
    product_name: str
    branch_to_be_released:str
    additional_arguments_file:str
    log_level:LogLevel
    main_branch:str
    stable_branch:str
    build_repository:str
    repository:str
    reference_repository:str
    
    def __init__(self, current_file: str, product_name: str,branch_to_be_released:str,log_level:LogLevel,additional_arguments_file:str,main_branch:str,stable_branch:str):
        self.product_name = product_name
        self.branch_to_be_released=branch_to_be_released
        self.additional_arguments_file=additional_arguments_file
        self.log_level=log_level
        self.main_branch=main_branch
        self.stable_branch=stable_branch
        self.build_repository=ScriptCollectionCore().search_repository_folder(current_file)
        self.repository=os.path.join(self.build_repository,"Submodules",product_name)
        self.reference_repository=os.path.join(self.build_repository,"Submodules",product_name+"Reference")

class TFCPS_CreateRelease:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)

    def do_release(self,tfcps_CreateReleaseConfiguration:TFCPS_CreateReleaseConfiguration):
        self.sc.log.loglevel=tfcps_CreateReleaseConfiguration.log_level
        self.sc.do_and_log_task(f"Release {tfcps_CreateReleaseConfiguration.product_name}",lambda : self.__do(tfcps_CreateReleaseConfiguration))

    def __do(self,tfcps_CreateReleaseConfiguration:TFCPS_CreateReleaseConfiguration):
        self.sc.log.log("Do checks...",LogLevel.Information)

        self.sc.assert_is_git_repository(tfcps_CreateReleaseConfiguration.build_repository)
        self.sc.assert_no_uncommitted_changes(tfcps_CreateReleaseConfiguration.build_repository)

        self.sc.assert_is_git_repository(tfcps_CreateReleaseConfiguration.repository)
        self.sc.assert_no_uncommitted_changes(tfcps_CreateReleaseConfiguration.repository)

        self.sc.assert_is_git_repository(tfcps_CreateReleaseConfiguration.reference_repository)
        self.sc.assert_no_uncommitted_changes(tfcps_CreateReleaseConfiguration.reference_repository)
        
        branch_to_be_released_commit_id = self.sc.git_get_commit_id(tfcps_CreateReleaseConfiguration.repository, tfcps_CreateReleaseConfiguration.branch_to_be_released)
        main_branch_commit_id = self.sc.git_get_commit_id(tfcps_CreateReleaseConfiguration.repository, tfcps_CreateReleaseConfiguration.main_branch)
        if branch_to_be_released_commit_id == main_branch_commit_id:
            self.sc.log.log("Merge to main-branch will not be done because there are no changed which can be merged.")
        else:
            self.sc.log.log("Merge to main-branch...",LogLevel.Information)
            mergeToMainConfiguration:MergeToMainConfiguration=MergeToMainConfiguration(tfcps_CreateReleaseConfiguration.current_file,tfcps_CreateReleaseConfiguration.product_name,tfcps_CreateReleaseConfiguration.branch_to_be_released,tfcps_CreateReleaseConfiguration.log_level,tfcps_CreateReleaseConfiguration.additional_arguments_file,tfcps_CreateReleaseConfiguration.main_branch)
            tFCPS_MergeToMain:TFCPS_MergeToMain=TFCPS_MergeToMain()
            tFCPS_MergeToMain.merge_to_main_branch(mergeToMainConfiguration)

        main_branch_commit_id = self.sc.git_get_commit_id(tfcps_CreateReleaseConfiguration.repository, tfcps_CreateReleaseConfiguration.main_branch)
        stable_branch_commit_id = self.sc.git_get_commit_id(tfcps_CreateReleaseConfiguration.repository, tfcps_CreateReleaseConfiguration.stable_branch)
        if main_branch_commit_id == stable_branch_commit_id:
            self.sc.log.log("Merge to stable-branch will not be done because there are no changed which can be released.")
        else:
            self.sc.log.log("Merge to stable-branch...",LogLevel.Information)
            mergeToStableConfiguration:MergeToStableConfiguration=MergeToStableConfiguration(tfcps_CreateReleaseConfiguration.log_level,tfcps_CreateReleaseConfiguration.main_branch,tfcps_CreateReleaseConfiguration.stable_branch,tfcps_CreateReleaseConfiguration.repository,tfcps_CreateReleaseConfiguration.build_repository)
            tFCPS_MergeToStable:TFCPS_MergeToStable=TFCPS_MergeToStable()
            tFCPS_MergeToStable.merge_to_stable_branch(mergeToStableConfiguration)
