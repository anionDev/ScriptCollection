import os
from ..GeneralUtilities import GeneralUtilities
from ..SCLog import LogLevel
from ..ScriptCollectionCore import ScriptCollectionCore
from .TFCPS_Tools_General import TFCPS_Tools_General
from .TFCPS_CodeUnit_BuildCodeUnits import TFCPS_CodeUnit_BuildCodeUnits

class GenericPrepareNewReleaseArguments:
    current_file: str
    product_name: str
    merge_source_branch:str
    additional_arguments_file:str
    log_level:LogLevel
    main_branch:str
    
    def __init__(self, current_file: str, product_name: str,merge_source_branch:str,log_level:LogLevel,additional_arguments_file:str,main_branch:str):
        self.current_file = current_file
        self.product_name = product_name
        self.merge_source_branch=merge_source_branch
        self.additional_arguments_file=additional_arguments_file
        self.log_level=log_level
        self.main_branch=main_branch

class TFCPS_DoRelease1_MergeToMain:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General


    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)

    @GeneralUtilities.check_arguments
    def generic_prepare_new_release(self, generic_prepare_new_release_arguments: GenericPrepareNewReleaseArguments):
        self.sc.log.loglevel=generic_prepare_new_release_arguments.log_level
        self.sc.log.log(f"Merge {generic_prepare_new_release_arguments.product_name} to main...")

        # constants
        folder_of_this_file = os.path.dirname(generic_prepare_new_release_arguments.current_file)
        build_repository_folder = GeneralUtilities.resolve_relative_path("../..", folder_of_this_file)
        self.sc.assert_is_git_repository(build_repository_folder)

        repository_folder = GeneralUtilities.resolve_relative_path(f"../../Submodules/{generic_prepare_new_release_arguments.product_name}", folder_of_this_file)
        self.sc.assert_is_git_repository(repository_folder)

        merge_source_branch = generic_prepare_new_release_arguments.merge_source_branch
        main_branch = generic_prepare_new_release_arguments.main_branch
        self.sc.assert_no_uncommitted_changes(repository_folder)
 
        # prepare
        keep:bool=False
        if keep:
            reference_folder = repository_folder+"Reference"
            self.sc.assert_is_git_repository(reference_folder)
            #TODO move the following encommented lines to DORelease2 or DoRelease3 
            #TODO self.assert_no_uncommitted_changes(reference_folder)
            #TODO self.assert_no_uncommitted_changes(build_repository_folder)
            self.sc.git_checkout(build_repository_folder, main_branch, True)
            self.sc.git_checkout(repository_folder, merge_source_branch, True)
            self.sc.git_checkout(reference_folder, main_branch, True)
            #TODO self.assert_no_uncommitted_changes(repository_folder)
            #TODO self.assert_no_uncommitted_changes(reference_folder)
            self.sc.git_commit(build_repository_folder, "Updated submodules")

            self.sc.log.log(f"Check reference-repository...")

            #TODO move the following encommented lines to common tasks
            now = GeneralUtilities.get_now()
            for unsupported_version in self.tFCPS_Tools_General.get_unsupported_versions(repository_folder, now):
                reference_folder = f"{reference_folder}/ReferenceContent/v{unsupported_version[0]}"
                GeneralUtilities.ensure_directory_does_not_exist(reference_folder)
            self.sc.git_commit(reference_folder, "Removed reference of outdated versions.")

            #TODO check for updateable dependencies

        merge_source_branch_commit_id = self.sc.git_get_commit_id(repository_folder, merge_source_branch)
        main_branch_commit_id = self.sc.git_get_commit_id(repository_folder, main_branch)
        if merge_source_branch_commit_id == main_branch_commit_id:
            self.sc.log.log("Release will not be prepared because there are no changed which can be released.")
        else:
            self.merge_to_main_branch(repository_folder, merge_source_branch,main_branch,generic_prepare_new_release_arguments.additional_arguments_file,True,generic_prepare_new_release_arguments)
            if keep:
                self.sc.git_commit(build_repository_folder, "Updated submodule due to merge to main-branch.")
        self.sc.log.log(f"Finished merge {generic_prepare_new_release_arguments.product_name} to main branch.")

    @GeneralUtilities.check_arguments
    def merge_to_main_branch(self, repository_folder: str, source_branch: str , target_branch: str, additional_arguments_file: str , fast_forward_source_branch: bool,generic_prepare_new_release_arguments:GenericPrepareNewReleaseArguments) -> None:
        # This is an automatization for automatic merges. Usual this merge would be done by a pull request in a sourcecode-version-control-platform
        # (like GitHub, GitLab or Azure DevOps)
        self.sc.log.log(f"Merge to main-branch...")
        self.sc.assert_is_git_repository(repository_folder)

        src_branch_commit_id = self.sc.git_get_commit_id(repository_folder,  source_branch)
        if (src_branch_commit_id == self.sc.git_get_commit_id(repository_folder,  target_branch)):
            raise ValueError(f"Can not merge because the source-branch and the target-branch are on the same commit (commit-id: {src_branch_commit_id})")

        self.sc.assert_no_uncommitted_changes(repository_folder)
        self.sc.git_checkout(repository_folder, source_branch)
        self.sc.assert_no_uncommitted_changes(repository_folder)

        tfcps_CodeUnit_BuildCodeUnits:TFCPS_CodeUnit_BuildCodeUnits=TFCPS_CodeUnit_BuildCodeUnits(repository_folder,self.sc.log.loglevel,"QualityCheck",generic_prepare_new_release_arguments.additional_arguments_file,False,True)
        try:
            tfcps_CodeUnit_BuildCodeUnits.build_codeunits()
        except Exception:
            self.sc.git_undo_all_changes(repository_folder)
            raise

        self.sc.git_commit(repository_folder, f'Built codeunits', stage_all_changes=True, no_changes_behavior=0)
        
        keep:bool=False
        if keep:
            self.sc.git_merge(repository_folder, source_branch, target_branch, False, False, None, False, False)
            self.sc.git_commit(repository_folder, f'Merge branch {source_branch} into {target_branch}', stage_all_changes=True, no_changes_behavior=1)
        if fast_forward_source_branch:
            self.sc.git_checkout(repository_folder, target_branch)
            self.sc.git_merge(repository_folder, target_branch, source_branch, True, True)
