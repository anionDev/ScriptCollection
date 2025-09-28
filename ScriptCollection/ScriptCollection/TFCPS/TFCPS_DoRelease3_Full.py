import os
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from .TFCPS_Tools_General import TFCPS_Tools_General
#from .TFCPS_DoRelease1_MergeToMain import CreateReleaseConfiguration

class GenericCreateReleaseArguments():
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

class TFCPS_DoRelease3_Full:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)

    @GeneralUtilities.check_arguments
    def generic_create_release(self, generic_create_release_arguments: GenericCreateReleaseArguments) -> tuple[bool, str]:
        self.sc.log.log(f"Create release for {generic_create_release_arguments.product_name}.")
        folder_of_this_file = os.path.dirname(generic_create_release_arguments.current_file)
        build_repository_folder = GeneralUtilities.resolve_relative_path("../..", folder_of_this_file)
        #repository_folder_name = generic_create_release_arguments.product_name
        repository_folder = GeneralUtilities.resolve_relative_path(f"../../Submodules/{generic_create_release_arguments.product_name}", folder_of_this_file)
        self.sc.assert_is_git_repository(repository_folder)

        merge_source_branch = "main"  # TODO make this configurable
        main_branch = "stable"  # TODO make this configurable

        #additional_arguments_file = os.path.join(folder_of_this_file, "AdditionalArguments.configuration")
        #createReleaseConfiguration: CreateReleaseConfiguration = CreateReleaseConfiguration(generic_create_release_arguments.product_name, generic_create_release_arguments.common_remote_name, generic_create_release_arguments.artifacts_target_folder, folder_of_this_file, repository_folder, additional_arguments_file, repository_folder_name)

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
            new_version =None#TODO call this method in dorelease2: self.merge_to_stable_branch(generic_create_release_arguments.current_file, createReleaseConfiguration)
            self.sc.log.log(f"Finished create release for {generic_create_release_arguments.product_name}.")
            return True, new_version
