import os
import shutil
from functools import cmp_to_key
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import  LogLevel
from .TFCPS_Tools_General import TFCPS_Tools_General
from .TFCPS_CodeUnit_BuildCodeUnits import TFCPS_CodeUnit_BuildCodeUnits




class MergeToStableConfiguration:
    log_level:LogLevel
    source_branch:str#main
    target_branch:str#stable
    repository:str
    build_repo:str
    reference_repo:str
    common_remote_name:str
    build_repo_main_branch_name:str
    reference_repo_main_branch_name:str
    reference_remote_name:str
    build_repo_remote_name:str
    artifacts_target_folder:str
    product_name:str
    common_remote_url:str

    def __init__(self,loglevel:LogLevel,source_branch:str,target_branch:str,repository:str,build_repo:str,reference_repo:str,common_remote_name:str,build_repo_main_branch_name:str,reference_repo_main_branch_name:str,reference_remote_name:str,build_repo_remote_name:str,artifacts_target_folder:str,product_name:str,common_remote_url:str):
        self.log_level=loglevel
        self.source_branch=source_branch
        self.target_branch=target_branch
        self.repository=repository
        self.build_repo=build_repo
        self.reference_repo=reference_repo
        self.common_remote_name=common_remote_name
        self.build_repo_main_branch_name=build_repo_main_branch_name
        self.reference_repo_main_branch_name=reference_repo_main_branch_name
        self.reference_remote_name=reference_remote_name
        self.build_repo_remote_name=build_repo_remote_name
        self.artifacts_target_folder=artifacts_target_folder
        self.product_name=product_name
        self.common_remote_url=common_remote_url

class TFCPS_MergeToStable:

    sc:ScriptCollectionCore
    tFCPS_Tools_General:TFCPS_Tools_General

    def __init__(self):
        self.sc=ScriptCollectionCore()
        self.tFCPS_Tools_General=TFCPS_Tools_General(self.sc)
 
    @GeneralUtilities.check_arguments
    def merge_to_stable_branch(self, createRelease_configuration: MergeToStableConfiguration):
        self.sc.log.loglevel=createRelease_configuration.log_level
        product_name:str=createRelease_configuration.product_name
        product_version:str=self.tFCPS_Tools_General.get_version_of_project(createRelease_configuration.repository)

        self.sc.assert_is_git_repository(createRelease_configuration.build_repo)
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.build_repo)

        self.sc.assert_is_git_repository(createRelease_configuration.repository)
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.repository)

        self.sc.assert_is_git_repository(createRelease_configuration.reference_repo)
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.reference_repo)

        self.sc.git_checkout(createRelease_configuration.repository, createRelease_configuration.source_branch, True,True)
        self.sc.git_merge(createRelease_configuration.repository, createRelease_configuration.source_branch,createRelease_configuration.target_branch, True,True,None,True,True)

        tfcps_CodeUnit_BuildCodeUnits:TFCPS_CodeUnit_BuildCodeUnits=TFCPS_CodeUnit_BuildCodeUnits(createRelease_configuration.repository_folder,self.sc.log.loglevel,"Productive",createRelease_configuration.additional_arguments_file,False,False)
        try:
            tfcps_CodeUnit_BuildCodeUnits.build_codeunits()
        except Exception:
            self.sc.git_undo_all_changes(createRelease_configuration.repository_folder)
            raise
                
        self.__remove_outdated_version(createRelease_configuration)

        for codeunit in self.tFCPS_Tools_General.get_codeunits(createRelease_configuration.repository):
            #export artifacts to local target folder
            if createRelease_configuration.artifacts_target_folder is not None:
                source_folder:str=GeneralUtilities.resolve_relative_path(f"./{codeunit}/Other/Artifacts",createRelease_configuration.repository)
                target_folder:str=GeneralUtilities.resolve_relative_path(f"./{product_name}/{product_version}/{codeunit}",createRelease_configuration.artifacts_target_folder)
                GeneralUtilities.ensure_directory_exists(target_folder)
                codeunit_version:str=self.tFCPS_Tools_General.get_version_of_codeunit(os.path.join(createRelease_configuration.repository,codeunit,f"{codeunit}.codeunit.xml"))
                target_file:str=os.path.join(target_folder,f"{codeunit}.v{codeunit_version}.Artifacts.zip")
                self.sc.run_program("tar",f"-cf {target_file} -C {source_folder} .")

            #push artifacts
            push_script:str=os.path.join( createRelease_configuration.build_repo,"Script","CreateRelease",f"PushArtifacts.{codeunit}.py")
            if os.path.isfile(push_script):
                self.sc.log.log(f"Push artifacts of codeunit {codeunit}...")
                self.sc.run_program("python3",os.path.basename(push_script),os.path.dirname(push_script))

            # Generate reference
            reference_folder:str=os.path.join(createRelease_configuration.reference_repo,"ReferenceContent")
            repository:str=createRelease_configuration.repository
            project_version:str=self.tFCPS_Tools_General.get_version_of_project(repository)
            projectname:str=createRelease_configuration.n
            public_repository_url:str=createRelease_configuration.common_remote_url
            main_branch_name:str=createRelease_configuration.source_branch
            self.__export_codeunit_reference_content_to_reference_repository(f"v{project_version}", False, reference_folder, repository, codeunit, projectname, codeunit_version, public_repository_url, f"v{project_version}")
            self.__export_codeunit_reference_content_to_reference_repository("Latest", True, reference_folder, repository, codeunit, projectname, codeunit_version, public_repository_url, main_branch_name)
            self.__generate_entire_reference(projectname, project_version, reference_folder)
        
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.repository)
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.reference_repo)
        self.sc.assert_no_uncommitted_changes(createRelease_configuration.build_repo)

        self.sc.git_push_with_retry(createRelease_configuration.repository,createRelease_configuration.common_remote_name,createRelease_configuration.target_branch,createRelease_configuration.target_branch)
        self.sc.git_push_with_retry(createRelease_configuration.build_repo,createRelease_configuration.build_repo_remote_name,createRelease_configuration.build_repo_main_branch_name,createRelease_configuration.build_repo_main_branch_name)
        self.sc.git_push_with_retry(createRelease_configuration.reference_repo,createRelease_configuration.reference_remote_name,createRelease_configuration.reference_repo_main_branch_name,createRelease_configuration.reference_repo_main_branch_name)

    def __remove_outdated_version(self,createRelease_configuration:MergeToStableConfiguration):
        now = GeneralUtilities.get_now()
        for unsupported_version in self.tFCPS_Tools_General.get_unsupported_versions(createRelease_configuration.repository, now):
            unsupported_reference_folder = f"{createRelease_configuration.reference_repo}/ReferenceContent/v{unsupported_version[0]}"
            GeneralUtilities.ensure_directory_does_not_exist(unsupported_reference_folder)

        
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
