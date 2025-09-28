import os
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import LogLevel
from .TFCPS_Tools_General import TFCPS_Tools_General

class GenericPrepareNewReleaseArguments:
    current_file: str
    product_name: str
    commandline_arguments: list[str]
 
    def __init__(self, current_file: str, product_name: str,commandline_arguments:list[str]):
        self.current_file = current_file
        self.product_name = product_name
        self.commandline_arguments = commandline_arguments

class CreateReleaseConfiguration():
    projectname: str
    remotename: str
    artifacts_folder: str
    push_artifacts_scripts_folder: str
    reference_repository_remote_name: str = None
    reference_repository_branch_name: str = "main"
    build_repository_branch: str = "main"
    public_repository_url: str
    additional_arguments_file: str = None
    repository_folder_name: str = None
    repository_folder: str = None
    sc: ScriptCollectionCore = None

    def __init__(self, projectname: str, remotename: str, build_artifacts_target_folder: str, push_artifacts_scripts_folder: str, repository_folder: str, additional_arguments_file: str, repository_folder_name: str):
        self.sc = ScriptCollectionCore()
        self.projectname = projectname
        self.remotename = remotename
        self.artifacts_folder = build_artifacts_target_folder
        self.push_artifacts_scripts_folder = push_artifacts_scripts_folder
        if self.remotename is None:
            self.public_repository_url = None
        else:
            self.public_repository_url = self.sc.git_get_remote_url(repository_folder, remotename)
        self.reference_repository_remote_name = self.remotename
        self.additional_arguments_file = additional_arguments_file
        self.repository_folder = repository_folder
        self.repository_folder_name = repository_folder_name


class TFCPS_DoRelease1_MergeToMain:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)

    @GeneralUtilities.check_arguments
    def generic_prepare_new_release(self, generic_prepare_new_release_arguments: GenericPrepareNewReleaseArguments):
        self.sc.log.log(f"Prepare release for {generic_prepare_new_release_arguments.product_name}.")

        # constants
        folder_of_this_file = os.path.dirname(generic_prepare_new_release_arguments.current_file)
        build_repository_folder = GeneralUtilities.resolve_relative_path("../..", folder_of_this_file)
        self.sc.assert_is_git_repository(build_repository_folder)

        repository_folder = GeneralUtilities.resolve_relative_path(f"../../Submodules/{generic_prepare_new_release_arguments.product_name}", folder_of_this_file)
        self.sc.assert_is_git_repository(repository_folder)
        reference_folder = repository_folder+"Reference"
        self.sc.assert_is_git_repository(reference_folder)

        merge_source_branch = "other/next-release"  # maybe this should be configurable
        main_branch = "main"  # maybe this should be configurable

        # prepare
        #TODO self.assert_no_uncommitted_changes(repository_folder)
        #TODO self.assert_no_uncommitted_changes(reference_folder)
        #TODO self.assert_no_uncommitted_changes(build_repository_folder)
        self.sc.git_checkout(build_repository_folder, "main", True)
        self.sc.git_checkout(repository_folder, merge_source_branch, True)
        self.sc.git_checkout(reference_folder, "main", True)
        #TODO self.assert_no_uncommitted_changes(repository_folder)
        #TODO self.assert_no_uncommitted_changes(reference_folder)
        self.sc.git_commit(build_repository_folder, "Updated submodules")

        if "--dependencyupdate" in generic_prepare_new_release_arguments.commandline_arguments:
            self.sc.log.log("Debug: Update dependencies...")
            #TODO self.generic_update_dependencies(repository_folder)
            #TODO self.assert_no_uncommitted_changes(repository_folder)
        else:
            self.sc.log.log("Dependency-update skipped.",LogLevel.Debug)

        self.sc.log.log(f"Check reference-repository...")
        now = GeneralUtilities.get_now()
        for unsupported_version in self.tFCPS_Tools_General.get_unsupported_versions(repository_folder, now):
            reference_folder = f"{reference_folder}/ReferenceContent/v{unsupported_version[0]}"
            GeneralUtilities.ensure_directory_does_not_exist(reference_folder)
        self.sc.git_commit(reference_folder, "Removed reference of outdated versions.")

        merge_source_branch_commit_id = self.sc.git_get_commit_id(repository_folder, merge_source_branch)
        main_branch_commit_id = self.sc.git_get_commit_id(repository_folder, main_branch)
        if merge_source_branch_commit_id == main_branch_commit_id:
            self.sc.log.log("Release will not be prepared because there are no changed which can be released.")
        else:
            self.merge_to_main_branch(repository_folder, merge_source_branch,  fast_forward_source_branch=True)
            self.sc.git_commit(build_repository_folder, "Updated submodule due to merge to main-branch.")
        self.sc.log.log(f"Finished prepare release for {generic_prepare_new_release_arguments.product_name}.")

    @GeneralUtilities.check_arguments
    def merge_to_main_branch(self, repository_folder: str, source_branch: str = "other/next-release", target_branch: str = "main" , additional_arguments_file: str = None, fast_forward_source_branch: bool = False) -> None:
        # This is an automatization for automatic merges. Usual this merge would be done by a pull request in a sourcecode-version-control-platform
        # (like GitHub, GitLab or Azure DevOps)
        self.sc.log.log(f"Merge to main-branch...")
        self.sc.assert_is_git_repository(repository_folder)
        #TODO self.assert_no_uncommitted_changes(repository_folder)

        src_branch_commit_id = self.sc.git_get_commit_id(repository_folder,  source_branch)
        if (src_branch_commit_id == self.sc.git_get_commit_id(repository_folder,  target_branch)):
            raise ValueError(f"Can not merge because the source-branch and the target-branch are on the same commit (commit-id: {src_branch_commit_id})")

        self.sc.git_checkout(repository_folder, source_branch)
        #TODO self.build_codeunits(repository_folder, TasksForCommonProjectStructure.get_qualitycheck_environment_name(), additional_arguments_file, True, None, [], True, "Check if product is buildable")
        self.sc.git_merge(repository_folder, source_branch, target_branch, False, False, None, False, False)
        self.sc.git_commit(repository_folder, f'Merge branch {source_branch} into {target_branch}', stage_all_changes=True, no_changes_behavior=1)
        self.sc.git_checkout(repository_folder, target_branch)
        if fast_forward_source_branch:
            self.sc.git_merge(repository_folder, target_branch, source_branch, True, True)
