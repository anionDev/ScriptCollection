import os
import shutil
from functools import cmp_to_key
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import  LogLevel
from .TFCPS_Tools_General import TFCPS_Tools_General
from .TFCPS_CodeUnit_BuildCodeUnits import TFCPS_CodeUnit_BuildCodeUnits
 

class CreateReleaseConfigurationOld():
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


class CreateReleaseInformationForProjectInCommonProjectFormatOld:
    projectname: str
    repository: str
    artifacts_folder: str
    reference_repository: str = None
    public_repository_url: str = None
    target_branch_name: str = None
    push_artifacts_scripts_folder: str = None
    target_environmenttype_for_qualitycheck: str = "QualityCheck"
    target_environmenttype_for_productive: str = "Productive"
    additional_arguments_file: str = None
    export_target: str = None
    sc:ScriptCollectionCore=None

    def __init__(self, repository: str, artifacts_folder: str, projectname: str, public_repository_url: str, target_branch_name: str, additional_arguments_file: str, export_target: str, push_artifacts_scripts_folder: str,sc:ScriptCollectionCore):
        self.repository = repository
        self.sc=sc
        self.public_repository_url = public_repository_url
        self.target_branch_name = target_branch_name
        self.artifacts_folder = artifacts_folder
        self.additional_arguments_file = additional_arguments_file
        self.export_target = export_target
        self.push_artifacts_scripts_folder = push_artifacts_scripts_folder
        if projectname is None:
            projectname = os.path.basename(self.repository)
        else:
            self.projectname = projectname
        self.reference_repository = f"{repository}Reference"


class MergeToStableBranchInformationForProjectInCommonProjectFormatOld:
    repository: str
    sourcebranch: str = "main"
    targetbranch: str = "stable"
    sign_git_tags: bool = True
    target_environmenttype_for_qualitycheck: str = "QualityCheck"
    target_environmenttype_for_productive: str = "Productive"
    additional_arguments_file: str = None
    export_target: str = None

    push_source_branch: bool = False
    push_source_branch_remote_name: str = None
    push_target_branch: bool = False
    push_target_branch_remote_name: str = None

    sc:ScriptCollectionCore=None

    def __init__(self, repository: str, additional_arguments_file: str, export_target: str,sc:ScriptCollectionCore):
        self.repository = repository
        self.additional_arguments_file = additional_arguments_file
        self.export_target = export_target
        self.sc=sc



class TFCPS_DoRelease2_MainToStableOld:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)
 
    @GeneralUtilities.check_arguments
    def merge_to_stable_branch(self, create_release_file: str, createRelease_configuration: CreateReleaseConfigurationOld):

        self.sc.log.log(f"Create release for project {createRelease_configuration.projectname}.")
        self.sc.log.log(f"Merge to stable-branch...")
        self.sc.assert_is_git_repository(createRelease_configuration.repository_folder)
        folder_of_create_release_file_file = os.path.abspath(os.path.dirname(create_release_file))

        build_repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}..", folder_of_create_release_file_file)
        #self.assert_no_uncommitted_changes(build_repository_folder)

        repository_folder = GeneralUtilities.resolve_relative_path(f"Submodules{os.path.sep}{createRelease_configuration.repository_folder_name}", build_repository_folder)
        mergeInformation:MergeToStableBranchInformationForProjectInCommonProjectFormatOld=None# = MergeToStableBranchInformationForProjectInCommonProjectFormat(repository_folder, createRelease_configuration.additional_arguments_file, createRelease_configuration.artifacts_folder)
        createReleaseInformation = CreateReleaseInformationForProjectInCommonProjectFormatOld(repository_folder, createRelease_configuration.artifacts_folder, createRelease_configuration.projectname, createRelease_configuration.public_repository_url, mergeInformation.targetbranch, mergeInformation.additional_arguments_file, mergeInformation.export_target, createRelease_configuration.push_artifacts_scripts_folder,self.sc)
        createReleaseInformation.sc = createRelease_configuration.sc

        self.sc.git_checkout(build_repository_folder, createRelease_configuration.build_repository_branch)
        self.sc.git_checkout(createReleaseInformation.reference_repository, createRelease_configuration.reference_repository_branch_name)

        self.sc.assert_is_git_repository(repository_folder)
        self.sc.assert_is_git_repository(createReleaseInformation.reference_repository)

        # TODO check if repository_folder-merge-source-branch and repository_folder-merge-target-branch have different commits
        #self.assert_no_uncommitted_changes(repository_folder)
        mergeInformation.sc = createRelease_configuration.sc
        mergeInformation.push_target_branch = createRelease_configuration.remotename is not None
        mergeInformation.push_target_branch_remote_name = createRelease_configuration.remotename
        mergeInformation.push_source_branch = createRelease_configuration.remotename is not None
        mergeInformation.push_source_branch_remote_name = createRelease_configuration.remotename
        new_project_version = self.__standardized_tasks_merge_to_stable_branch(mergeInformation)

        self.__standardized_tasks_release_artifact(createReleaseInformation)

        GeneralUtilities.assert_condition(createRelease_configuration.reference_repository_remote_name is not None, "Remote for reference-repository not set.")
        self.sc.git_commit(createReleaseInformation.reference_repository, f"Added reference of {createRelease_configuration.projectname} v{new_project_version}")
        self.sc.git_push_with_retry(createReleaseInformation.reference_repository, createRelease_configuration.reference_repository_remote_name, createRelease_configuration.reference_repository_branch_name, createRelease_configuration.reference_repository_branch_name)
        self.sc.git_commit(build_repository_folder, f"Added {createRelease_configuration.projectname} release v{new_project_version}")
        self.sc.log.log(f"Finished release for project {createRelease_configuration.projectname} v{new_project_version} successfully.")
        return new_project_version

    @GeneralUtilities.check_arguments
    def __standardized_tasks_merge_to_stable_branch(self, information: MergeToStableBranchInformationForProjectInCommonProjectFormatOld) -> str:
        src_branch_commit_id = self.sc.git_get_commit_id(information.repository,  information.sourcebranch)
        if (src_branch_commit_id == self.sc.git_get_commit_id(information.repository,  information.targetbranch)):
            raise ValueError(f"Can not merge because the source-branch and the target-branch are on the same commit (commit-id: {src_branch_commit_id})")

        #self.assert_no_uncommitted_changes(information.repository)
        self.sc.git_checkout(information.repository, information.sourcebranch)
        self.sc.run_program("git", "clean -dfx", information.repository,  throw_exception_if_exitcode_is_not_zero=True)
        project_version = self.sc.get_semver_version_from_gitversion(information.repository)

        #TODO self.build_codeunits(information.repository, information. information.target_environmenttype_for_qualitycheck, information.additional_arguments_file, False, information.export_target, [], True, "Productive build")  # verify hat codeunits are buildable with productive-config before merge

        #TODO self.assert_no_uncommitted_changes(information.repository)

        commit_id = self.sc.git_merge(information.repository, information.sourcebranch, information.targetbranch, True, True)
        self.sc.git_create_tag(information.repository, commit_id, f"v{project_version}", information.sign_git_tags)

        if information.push_source_branch:
            self.sc.log.log("Push source-branch...")
            self.sc.git_push_with_retry(information.repository, information.push_source_branch_remote_name, information.sourcebranch, information.sourcebranch, pushalltags=True)

        if information.push_target_branch:
            self.sc.log.log("Push target-branch...")
            self.sc.git_push_with_retry(information.repository, information.push_target_branch_remote_name, information.targetbranch, information.targetbranch, pushalltags=True)

        return project_version


    @GeneralUtilities.check_arguments
    def __standardized_tasks_release_artifact(self, information: CreateReleaseInformationForProjectInCommonProjectFormatOld) -> None:
        self.sc.log.log("Release artifacts...")
        project_version = self.sc.get_semver_version_from_gitversion(information.repository)
        target_folder_base = os.path.join(information.artifacts_folder, information.projectname, project_version)
        GeneralUtilities.ensure_directory_exists(target_folder_base)

        #TODO self.build_codeunits(information.repository, information. information.target_environmenttype_for_productive, information.additional_arguments_file, False, information.export_target, [], True, "Generate artifacts")  # Generate artifacts after merge (because now are constants like commit-id of the new version available)

        reference_folder = os.path.join(information.reference_repository, "ReferenceContent")

        for codeunitname in []:#TODO self.get_codeunits(information.repository):
            # Push artifacts to registry
            self.sc.log.log(f"Push artifacts of {codeunitname}...",LogLevel.Debug)
            scriptfilename = f"PushArtifacts.{codeunitname}.py"
            push_artifact_to_registry_script = os.path.join(information.push_artifacts_scripts_folder, scriptfilename)
            if os.path.isfile(push_artifact_to_registry_script):
                self.sc.log.log(f"Push artifacts of codeunit {codeunitname}...")
                self.sc.run_program("python", push_artifact_to_registry_script, information.push_artifacts_scripts_folder, throw_exception_if_exitcode_is_not_zero=True)

            # Copy reference of codeunit to reference-repository
            codeunit_version = self.tFCPS_Tools_General.get_version_of_codeunit(os.path.join(information.repository, codeunitname,f"{codeunitname}.codeunit.xml"))
            self.__export_codeunit_reference_content_to_reference_repository(f"v{project_version}", False, reference_folder, information.repository, codeunitname, information.projectname, codeunit_version, information.public_repository_url, f"v{project_version}")
            self.__export_codeunit_reference_content_to_reference_repository("Latest", True, reference_folder, information.repository, codeunitname, information.projectname, codeunit_version, information.public_repository_url, information.target_branch_name)

            # Generate reference
            self.__generate_entire_reference(information.projectname, project_version, reference_folder)


        
    @GeneralUtilities.check_arguments
    def __generate_entire_reference(self, projectname: str, project_version: str, reference_folder: str) -> None:
        all_available_version_identifier_folders_of_reference: list[str] = list(folder for folder in GeneralUtilities.get_direct_folders_of_folder(reference_folder))
        all_available_version_identifier_folders_of_reference = sorted(all_available_version_identifier_folders_of_reference, key=cmp_to_key(TFCPS_Tools_General._internal_sort_reference_folder))
        reference_versions_html_lines = []
        reference_versions_html_lines.append('    <hr/>')
        for all_available_version_identifier_folder_of_reference in all_available_version_identifier_folders_of_reference:
            version_identifier_of_project = os.path.basename(all_available_version_identifier_folder_of_reference)
            if version_identifier_of_project == "Latest":
                latest_version_hint = f" (v{project_version})"
            else:
                latest_version_hint = GeneralUtilities.empty_string
            reference_versions_html_lines.append(f'    <h2>{version_identifier_of_project}{latest_version_hint}</h2>')
            reference_versions_html_lines.append("    Contained codeunits:<br/>")
            reference_versions_html_lines.append("    <ul>")
            for codeunit_reference_folder in list(folder for folder in GeneralUtilities.get_direct_folders_of_folder(all_available_version_identifier_folder_of_reference)):
                reference_versions_html_lines.append(f'      <li><a href="./{version_identifier_of_project}/{os.path.basename(codeunit_reference_folder)}/index.html">' +
                                                     f'{os.path.basename(codeunit_reference_folder)} {version_identifier_of_project}</a></li>')
            reference_versions_html_lines.append("    </ul>")
            reference_versions_html_lines.append('    <hr/>')
            if version_identifier_of_project == "Latest":
                latest_version_hint = "    <h2>History</h2>"

        design_file = None
        design = "ModestDark"
        if design == "ModestDark":
            design_file = GeneralUtilities.get_modest_dark_url()
        # TODO make designs from customizable sources be available by a customizable name and outsource this to a class-property because this is duplicated code.
        if design_file is None:
            design_html = GeneralUtilities.empty_string
        else:
            design_html = f'<link type="text/css" rel="stylesheet" href="{design_file}" />'

        reference_versions_links_file_content = "    \n".join(reference_versions_html_lines)
        title = f"{projectname}-reference"
        reference_index_file = os.path.join(reference_folder, "index.html")
        reference_index_file_content = f"""<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {design_html}
  </head>

  <body>
    <h1>{title}</h1>
{reference_versions_links_file_content}
  </body>

</html>
"""  # see https://getbootstrap.com/docs/5.1/getting-started/introduction/
        GeneralUtilities.write_text_to_file(reference_index_file, reference_index_file_content)

    @GeneralUtilities.check_arguments
    def __export_codeunit_reference_content_to_reference_repository(self, project_version_identifier: str, replace_existing_content: bool, target_folder_for_reference_repository: str, repository: str, codeunitname: str, projectname: str, codeunit_version: str, public_repository_url: str, branch: str) -> None:
        codeunit_folder = os.path.join(repository, codeunitname)
        codeunit_file = os.path.join(codeunit_folder, f"{codeunitname}.codeunit.xml")
        codeunit_has_testcases = self.tFCPS_Tools_General.codeunit_has_testable_sourcecode(codeunit_file)
        target_folder = os.path.join(target_folder_for_reference_repository, project_version_identifier, codeunitname)
        if os.path.isdir(target_folder) and not replace_existing_content:
            raise ValueError(f"Folder '{target_folder}' already exists.")
        GeneralUtilities.ensure_directory_does_not_exist(target_folder)
        GeneralUtilities.ensure_directory_exists(target_folder)
        codeunit_version_identifier = "Latest" if project_version_identifier == "Latest" else "v"+codeunit_version
        page_title = f"{codeunitname} {codeunit_version_identifier} codeunit-reference"
        diff_report = f"{repository}/{codeunitname}/Other/Artifacts/DiffReport/DiffReport.html"
        diff_target_folder = os.path.join(target_folder, "DiffReport")
        GeneralUtilities.ensure_directory_exists(diff_target_folder)
        diff_target_file = os.path.join(diff_target_folder, "DiffReport.html")
        title = (f'Reference of codeunit {codeunitname} {codeunit_version_identifier} (contained in project <a href="{public_repository_url}">{projectname}</a> {project_version_identifier})')
        if public_repository_url is None:
            repo_url_html = GeneralUtilities.empty_string
        else:
            repo_url_html = f'<a href="{public_repository_url}/tree/{branch}/{codeunitname}">Source-code</a>'
        if codeunit_has_testcases:
            coverage_report_link = '<a href="./TestCoverageReport/index.html">Test-coverage-report</a><br>'
        else:
            coverage_report_link = GeneralUtilities.empty_string
        index_file_for_reference = os.path.join(target_folder, "index.html")

        design_file = None
        design = "ModestDark"
        if design == "ModestDark":
            design_file = GeneralUtilities.get_modest_dark_url()
        # TODO make designs from customizable sources be available by a customizable name and outsource this to a class-property because this is duplicated code.
        if design_file is None:
            design_html = GeneralUtilities.empty_string
        else:
            design_html = f'<link type="text/css" rel="stylesheet" href="{design_file}" />'

        index_file_content = f"""<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <title>{page_title}</title>
    {design_html}
  </head>

  <body>
    <h1>{title}</h1>
    <hr/>
    Available reference-content for {codeunitname}:<br>
    {repo_url_html}<br>
    <!--TODO add artefacts-link: <a href="./x">Artefacts</a><br>-->
    <a href="./Reference/index.html">Reference</a><br>
    <a href="./DiffReport/DiffReport.html">Diff-report</a><br>
    {coverage_report_link}
  </body>

</html>
"""

        GeneralUtilities.ensure_file_exists(index_file_for_reference)
        GeneralUtilities.write_text_to_file(index_file_for_reference, index_file_content)
        other_folder_in_repository = os.path.join(repository, codeunitname, "Other")
        source_generatedreference = os.path.join(other_folder_in_repository, "Artifacts", "Reference")
        target_generatedreference = os.path.join(target_folder, "Reference")
        shutil.copytree(source_generatedreference, target_generatedreference)

        shutil.copyfile(diff_report, diff_target_file)

        if codeunit_has_testcases:
            source_testcoveragereport = os.path.join(other_folder_in_repository, "Artifacts", "TestCoverageReport")
            if os.path.isdir(source_testcoveragereport):  # check, because it is not a mandatory artifact. if the artifact is not available, the user gets already a warning.
                target_testcoveragereport = os.path.join(target_folder, "TestCoverageReport")
                shutil.copytree(source_testcoveragereport, target_testcoveragereport)

class MergeToStableConfiguration:
    log_level:LogLevel
    source_branch:str#main
    target_branch:str#stable
    repository:str
    build_repo:str
    def __init__(self,loglevel:LogLevel,source_branch:str,target_branch:str,repository:str,build_repo:str):
        self.log_level=loglevel
        self.source_branch=source_branch
        self.target_branch=target_branch
        self.repository=repository
        self.build_repo=build_repo

class TFCPS_MergeToStable:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)
 
    @GeneralUtilities.check_arguments
    def merge_to_stable_branch(self, createRelease_configuration: MergeToStableConfiguration):
        self.sc.log.loglevel=createRelease_configuration.log_level
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.repository)
        #TODO assert no changes in reference-repo
        #TODO assert no changes in build-repo
        self.sc.git_checkout(createRelease_configuration.repository, createRelease_configuration.source_branch, True,True)
        self.sc.git_merge(createRelease_configuration.repository, createRelease_configuration.source_branch,createRelease_configuration.target_branch, True,True,None,True,True)

        tfcps_CodeUnit_BuildCodeUnits:TFCPS_CodeUnit_BuildCodeUnits=TFCPS_CodeUnit_BuildCodeUnits(createRelease_configuration.repository_folder,self.sc.log.loglevel,"Productive",createRelease_configuration.additional_arguments_file,False,False)
        try:
            tfcps_CodeUnit_BuildCodeUnits.build_codeunits()
        except Exception:
            self.sc.git_undo_all_changes(createRelease_configuration.repository_folder)
            raise

        for codeunit in self.tFCPS_Tools_General.get_codeunits(createRelease_configuration.repository):
            push_script:str=os.path.join( createRelease_configuration.build_repo,"Script","CreateRelease",f"PushArtifacts.{codeunit}.py")
            if os.path.isfile(push_script):
                self.sc.run_program("python3",os.path.basename(push_script),os.path.dirname(push_script))
                
        self.__export_reference(createRelease_configuration)

    def __export_reference(self,createRelease_configuration:MergeToStableConfiguration):
        pass
