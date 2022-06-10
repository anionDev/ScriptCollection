import os
from pathlib import Path
import shutil
import re
from lxml import etree
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore


class CreateReleaseInformationForProjectInCommonProjectFormat:
    projectname: str
    repository: str
    build_artifacts_target_folder: str
    build_py_arguments: str = ""
    verbosity: int = 1
    push_artifact_to_registry_scripts: dict[str, str] = dict[str, str]()  # key: codeunit, value: scriptfile for pushing codeunit's artifact to one or more registries
    reference_repository: str = None
    public_repository_url: str = None
    target_branch_name: str = None

    def __init__(self, repository: str, build_artifacts_target_folder: str, projectname: str, public_repository_url: str, target_branch_name: str):
        self.repository = repository
        self.public_repository_url = public_repository_url
        self.target_branch_name = target_branch_name
        self.build_artifacts_target_folder = build_artifacts_target_folder
        if projectname is None:
            projectname = os.path.basename(self.repository)
        else:
            self.projectname = projectname
        self.reference_repository = GeneralUtilities.resolve_relative_path(f"../{projectname}Reference", repository)


class MergeToStableBranchInformationForProjectInCommonProjectFormat:
    project_has_source_code: bool = True
    repository: str
    sourcebranch: str = "main"
    targetbranch: str = "stable"
    run_build_py: bool = True
    build_py_arguments: str = ""
    sign_git_tags: bool = True

    push_source_branch: bool = False
    push_source_branch_remote_name: str = None  # This value will be ignored if push_source_branch = False

    merge_target_as_fast_forward_into_source_after_merge: bool = True
    push_target_branch: bool = False  # This value will be ignored if merge_target_as_fast_forward_into_source_after_merge = False
    push_target_branch_remote_name: str = None  # This value will be ignored if or merge_target_as_fast_forward_into_source_after_merge push_target_branch = False

    verbosity: int = 1

    def __init__(self, repository: str):
        self.repository = repository


class TasksForCommonProjectStructure:
    __sc: ScriptCollectionCore = ScriptCollectionCore()

    @GeneralUtilities.check_arguments
    def __run_build_py(self, commitid, codeunit_version, build_py_arguments, repository, codeunitname, verbosity):
        self.__sc.run_program("python", f"Build.py --commitid={commitid} --codeunitversion={codeunit_version} {build_py_arguments}", os.path.join(repository, codeunitname, "Other", "Build"),
                              verbosity=verbosity)

    @GeneralUtilities.check_arguments
    def get_build_folder_in_repository_in_common_repository_format(self, repository_folder: str, codeunit_name: str) -> str:
        return os.path.join(repository_folder, codeunit_name, "Other", "Build", "BuildArtifact")

    @GeneralUtilities.check_arguments
    def get_wheel_file_in_repository_in_common_repository_format(self, repository_folder: str, codeunit_name: str) -> str:
        return self.__sc.find_file_by_extension(self.get_build_folder_in_repository_in_common_repository_format(repository_folder, codeunit_name), "whl")

    @GeneralUtilities.check_arguments
    def __export_codeunit_reference_content_to_reference_repository(self, project_version_identifier: str, replace_existing_content: bool, target_folder_for_reference_repository: str,
                                                                    repository: str, codeunitname, projectname: str, codeunit_version: str, public_repository_url: str, branch: str) -> None:

        target_folder = os.path.join(target_folder_for_reference_repository, project_version_identifier, codeunitname)
        if os.path.isdir(target_folder) and not replace_existing_content:
            raise ValueError(f"Folder '{target_folder}' already exists.")

        GeneralUtilities.ensure_directory_does_not_exist(target_folder)
        GeneralUtilities.ensure_directory_exists(target_folder)
        title = f"{codeunitname}-reference (codeunit v{codeunit_version}, conained in project {projectname} ({project_version_identifier}))"

        if public_repository_url is None:
            repo_url_html = ""
        else:
            repo_url_html = f'<a href="{public_repository_url}/tree/{branch}/{codeunitname}">Source-code</a><br>'

        index_file_for_reference = os.path.join(target_folder, "index.html")
        index_file_content = f"""<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <title>{title}</title>
  </head>

  <body>
    <h1>{title}</h1>
    Available reference-content for {codeunitname}:<br>
    {repo_url_html}
    <a href="./GeneratedReference/index.html">Refrerence</a><br>
    <a href="./TestCoverageReport/index.html">TestCoverageReport</a><br>
  </body>

</html>
"""
        GeneralUtilities.ensure_file_exists(index_file_for_reference)
        GeneralUtilities.write_text_to_file(index_file_for_reference, index_file_content)

        other_folder_in_repository = os.path.join(repository, codeunitname, "Other")

        source_generatedreference = os.path.join(other_folder_in_repository, "Reference", "GeneratedReference")
        target_generatedreference = os.path.join(target_folder, "GeneratedReference")
        shutil.copytree(source_generatedreference, target_generatedreference)

        source_testcoveragereport = os.path.join(other_folder_in_repository, "QualityCheck", "TestCoverage", "TestCoverageReport")
        target_testcoveragereport = os.path.join(target_folder, "TestCoverageReport")
        shutil.copytree(source_testcoveragereport, target_testcoveragereport)

    @GeneralUtilities.check_arguments
    def __get_testcoverage_threshold_from_codeunit_file(self, codeunit_file):
        root: etree._ElementTree = etree.parse(codeunit_file)
        return float(str(root.xpath('//codeunit:minimalcodecoverageinpercent/text()', namespaces={'codeunit': 'https://github.com/anionDev/ProjectTemplates'})[0]))

    @GeneralUtilities.check_arguments
    def __get_testcoverage_threshold_from_codeunit_file(self, codeunit_file):
        root: etree._ElementTree = etree.parse(codeunit_file)
        return float(str(root.xpath('//codeunit:minimalcodecoverageinpercent/text()', namespaces={'codeunit': 'https://github.com/anionDev/ProjectTemplates'})[0]))

    @GeneralUtilities.check_arguments
    def check_testcoverage(self, testcoverage_file_in_cobertura_format: str, threshold_in_percent: float):
        root: etree._ElementTree = etree.parse(testcoverage_file_in_cobertura_format)
        coverage_in_percent = round(float(str(root.xpath('//coverage/@line-rate')[0]))*100, 2)
        minimalrequiredtestcoverageinpercent = threshold_in_percent
        if(coverage_in_percent < minimalrequiredtestcoverageinpercent):
            raise ValueError(f"The testcoverage must be {minimalrequiredtestcoverageinpercent}% or more but is {coverage_in_percent}%.")

    @GeneralUtilities.check_arguments
    def __run_build_py(self, commitid, codeunit_version, build_py_arguments, repository, codeunitname, verbosity):
        self.__sc.run_program("python", f"Build.py --commitid={commitid} --codeunitversion={codeunit_version} {build_py_arguments}", os.path.join(repository, codeunitname, "Other", "Build"),
                              verbosity=verbosity)

    @GeneralUtilities.check_arguments
    def replace_version_in_python_file(self, file: str, new_version_value: str):
        GeneralUtilities.write_text_to_file(file, re.sub("version = \"\\d+\\.\\d+\\.\\d+\"", f"version = \"{new_version_value}\"",
                                                         GeneralUtilities.read_text_from_file(file)))

    @GeneralUtilities.check_arguments
    def __standardized_tasks_run_testcases_for_python_codeunit(self, repository_folder: str, codeunitname: str):
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        self.__sc.run_program("coverage", "run -m pytest", codeunit_folder)
        self.__sc.run_program("coverage", "xml", codeunit_folder)
        coveragefile = os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder, codeunitname, "coverage.xml"), coveragefile)

    @GeneralUtilities.check_arguments
    def standardized_tasks_generate_refefrence_for_project_in_common_project_structure(self, generate_reference_file: str, commandline_arguments: list[str] = []):
        reference_folder = os.path.dirname(generate_reference_file)
        reference_result_folder = os.path.join(reference_folder, "GeneratedReference")
        GeneralUtilities.ensure_directory_does_not_exist(reference_result_folder)
        self.__sc.run_program("docfx", "docfx.json", reference_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_run_testcases_for_python_codeunit_in_common_project_structure(self, run_testcases_file: str, generate_badges: bool = True):
        repository_folder: str = str(Path(os.path.dirname(run_testcases_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(run_testcases_file)).parent.parent.name
        self.__standardized_tasks_run_testcases_for_python_codeunit(repository_folder, codeunitname)
        self.__standardized_tasks_generate_coverage_report(repository_folder, codeunitname, generate_badges)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_python_project_in_common_project_structure(self, build_file: str):
        setuppy_file_folder = str(Path(os.path.dirname(build_file)).parent.parent.absolute())
        setuppy_file_filename = "Setup.py"
        repository_folder: str = str(Path(os.path.dirname(build_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(build_file)).parent.parent.name
        target_directory = os.path.join(repository_folder, codeunitname, "Other", "Build", "BuildArtifact")
        GeneralUtilities.ensure_directory_does_not_exist(target_directory)
        self.__sc.run_program("git", f"clean -dfx --exclude={codeunitname}/Other {codeunitname}", repository_folder)
        GeneralUtilities.ensure_directory_exists(target_directory)
        self.__sc.run_program("python", f"{setuppy_file_filename} bdist_wheel --dist-dir {target_directory}", setuppy_file_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_push_wheel_file_to_registry(self, wheel_file: str, api_key: str, repository="pypi", gpg_identity: str = None, verbosity: int = 1) -> None:
        folder = os.path.dirname(wheel_file)
        filename = os.path.basename(wheel_file)

        if gpg_identity is None:
            gpg_identity_argument = ""
        else:
            gpg_identity_argument = f" --sign --identity {gpg_identity}"

        if verbosity > 2:
            verbose_argument = " --verbose"
        else:
            verbose_argument = ""

        twine_argument = f"upload{gpg_identity_argument} --repository {repository} --non-interactive {filename} --disable-progress-bar"
        twine_argument = f"{twine_argument} --username __token__ --password {api_key}{verbose_argument}"
        self.__sc.run_program("twine", twine_argument, folder, verbosity, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def push_wheel_build_artifact_of_repository_in_common_file_structure(self, push_build_artifacts_file, product_name, codeunitname, apikey, gpg_identity: str = None) -> None:
        folder_of_this_file = os.path.dirname(push_build_artifacts_file)
        repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}../Submodules{os.path.sep}{product_name}", folder_of_this_file)
        wheel_file = self.get_wheel_file_in_repository_in_common_repository_format(repository_folder, codeunitname)
        self.standardized_tasks_push_wheel_file_to_registry(wheel_file, apikey, gpg_identity=gpg_identity)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_build_for_dotnet_build(self, csproj_file: str, buildconfiguration: str, outputfolder: str, files_to_sign: dict):
        csproj_file_folder = os.path.dirname(csproj_file)
        csproj_file_name = os.path.basename(csproj_file)
        self.__sc.run_program("dotnet", "clean", csproj_file_folder)
        GeneralUtilities.ensure_directory_does_not_exist(outputfolder)
        GeneralUtilities.ensure_directory_exists(outputfolder)
        self.__sc.run_program("dotnet", f"build {csproj_file_name} -c {buildconfiguration} -o {outputfolder}", csproj_file_folder)
        for file, keyfile in files_to_sign.items():
            self.__sc.dotnet_sign_file(os.path.join(outputfolder, file), keyfile)

    @GeneralUtilities.check_arguments
    def get_version_of_codeunit(self, codeunit_file: str) -> None:
        root: etree._ElementTree = etree.parse(codeunit_file)
        result = str(root.xpath('//codeunit:version/text()', namespaces={'codeunit': 'https://github.com/anionDev/ProjectTemplates'})[0])
        return result

    @GeneralUtilities.check_arguments
    def update_version_of_codeunit_to_project_version(self, common_tasks_file: str, current_version: str) -> None:
        codeunit_name: str = os.path.basename(GeneralUtilities.resolve_relative_path("..", os.path.dirname(common_tasks_file)))
        codeunit_file: str = os.path.join(GeneralUtilities.resolve_relative_path("..", os.path.dirname(common_tasks_file)), f"{codeunit_name}.codeunit")
        self.write_version_to_codeunit_file(codeunit_file, current_version)

    @GeneralUtilities.check_arguments
    def standardized_tasks_generate_reference_by_docfx(self, generate_reference_script_file: str) -> None:
        folder_of_current_file = os.path.dirname(generate_reference_script_file)
        generated_reference_folder = os.path.join(folder_of_current_file, "GeneratedReference")
        GeneralUtilities.ensure_directory_does_not_exist(generated_reference_folder)
        GeneralUtilities.ensure_directory_exists(generated_reference_folder)
        obj_folder = os.path.join(folder_of_current_file, "obj")
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)
        GeneralUtilities.ensure_directory_exists(obj_folder)
        self.__sc.run_program("docfx", "docfx.json", folder_of_current_file)
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_dotnet_build(self, csproj_file: str, buildconfiguration: str, outputfolder: str, files_to_sign: dict):
        csproj_file_folder = os.path.dirname(csproj_file)
        csproj_file_name = os.path.basename(csproj_file)
        self.__sc.run_program("dotnet", "clean", csproj_file_folder)
        GeneralUtilities.ensure_directory_does_not_exist(outputfolder)
        GeneralUtilities.ensure_directory_exists(outputfolder)
        self.__sc.run_program("dotnet", f"build {csproj_file_name} -c {buildconfiguration} -o {outputfolder}", csproj_file_folder)
        for file, keyfile in files_to_sign.items():
            self.__sc.dotnet_sign_file(os.path.join(outputfolder, file), keyfile)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_dotnet_project_in_common_project_structure(self, buildscript_file: str, buildconfiguration: str, commandline_arguments: list[str] = []):
        # this function builds an exe or dll
        self.__standardized_tasks_build_for_dotnet_project_in_common_project_structure(buildscript_file, buildconfiguration, True, commandline_arguments)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_dotnet_library_project_in_common_project_structure(self, buildscript_file: str, buildconfiguration: str = "Release", commandline_arguments: list[str] = []):
        # this function builds an exe or dll and converts it immediately to an nupkg-file
        self.__standardized_tasks_build_for_dotnet_project_in_common_project_structure(buildscript_file, buildconfiguration, True, commandline_arguments)
        self.__standardized_tasks_build_nupkg_for_dotnet_create_package(buildscript_file)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_build_for_dotnet_project_in_common_project_structure(self, buildscript_file: str, buildconfiguration: str,
                                                                                  build_test_project_too: bool = True, commandline_arguments: list[str] = []):
        repository_folder: str = str(Path(os.path.dirname(buildscript_file)).parent.parent.parent.absolute())
        codeunitname: str = os.path.basename(str(Path(os.path.dirname(buildscript_file)).parent.parent.absolute()))
        outputfolder = os.path.join(os.path.dirname(buildscript_file), "BuildArtifact")
        GeneralUtilities.ensure_directory_does_not_exist(outputfolder)
        GeneralUtilities.ensure_directory_exists(outputfolder)

        codeunit_folder = os.path.join(repository_folder, codeunitname)
        csproj_file = os.path.join(codeunit_folder, codeunitname, codeunitname+".csproj")
        csproj_test_file = os.path.join(codeunit_folder, codeunitname+"Tests", codeunitname+"Tests.csproj")
        commandline_arguments = commandline_arguments[1:]
        files_to_sign: dict() = dict()
        for commandline_argument in commandline_arguments:
            if commandline_argument.startswith("-buildconfiguration:"):
                buildconfiguration = commandline_argument[len("-buildconfiguration:"):]
            if commandline_argument.startswith("-sign:"):
                commandline_argument_splitted: list[str] = commandline_argument.split(":")
                files_to_sign[commandline_argument_splitted[1]] = commandline_argument[len("-sign:"+commandline_argument_splitted[1])+1:]

        self.__sc.run_program("dotnet", "restore", codeunit_folder)
        self.__standardized_tasks_build_for_dotnet_build(csproj_file, buildconfiguration, os.path.join(outputfolder, codeunitname), files_to_sign)
        if build_test_project_too:
            self.__standardized_tasks_build_for_dotnet_build(csproj_test_file, buildconfiguration, os.path.join(outputfolder, codeunitname+"Tests"), files_to_sign)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_build_nupkg_for_dotnet_create_package(self, buildscript_file: str):
        repository_folder: str = str(Path(os.path.dirname(buildscript_file)).parent.parent.parent.absolute())
        codeunitname: str = os.path.basename(str(Path(os.path.dirname(buildscript_file)).parent.parent.absolute()))
        outputfolder = os.path.join(os.path.dirname(buildscript_file), "BuildArtifact")

        build_folder = os.path.join(repository_folder, codeunitname, "Other", "Build")
        root: etree._ElementTree = etree.parse(os.path.join(build_folder, f"{codeunitname}.nuspec"))
        current_version = root.xpath("//*[name() = 'package']/*[name() = 'metadata']/*[name() = 'version']/text()")[0]
        nupkg_filename = f"{codeunitname}.{current_version}.nupkg"
        nupkg_file = f"{build_folder}/{nupkg_filename}"
        GeneralUtilities.ensure_file_does_not_exist(nupkg_file)
        self.__sc.run_program("nuget", f"pack {codeunitname}.nuspec", build_folder)
        GeneralUtilities.ensure_directory_does_not_exist(outputfolder)
        GeneralUtilities.ensure_directory_exists(outputfolder)
        os.rename(nupkg_file, f"{build_folder}/BuildArtifact/{nupkg_filename}")

    @GeneralUtilities.check_arguments
    def standardized_tasks_linting_for_python_codeunit_in_common_project_structure(self, linting_script_file):
        repository_folder: str = str(Path(os.path.dirname(linting_script_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(linting_script_file)).parent.parent.name
        errors_found = False
        GeneralUtilities.write_message_to_stdout(f"Check for linting-issues in codeunit {codeunitname}")
        src_folder = os.path.join(repository_folder, codeunitname, codeunitname)
        tests_folder = src_folder+"Tests"
        for file in GeneralUtilities.get_all_files_of_folder(src_folder)+GeneralUtilities.get_all_files_of_folder(tests_folder):
            relative_file_path_in_repository = os.path.relpath(file, repository_folder)
            if file.endswith(".py") and os.path.getsize(file) > 0 and not self.__sc.file_is_git_ignored(relative_file_path_in_repository, repository_folder):
                GeneralUtilities.write_message_to_stdout(f"Check for linting-issues in {os.path.relpath(file,os.path.join(repository_folder,codeunitname))}")
                linting_result = self.__sc.python_file_has_errors(file, repository_folder)
                if (linting_result[0]):
                    errors_found = True
                    for error in linting_result[1]:
                        GeneralUtilities.write_message_to_stderr(error)
        if errors_found:
            raise Exception("Linting-issues occurred")
        else:
            GeneralUtilities.write_message_to_stdout("No linting-issues found.")

    @GeneralUtilities.check_arguments
    def __standardized_tasks_generate_coverage_report(self, repository_folder: str, codeunitname: str, verbosity: int = 1, generate_badges: bool = True, args: list[str] = []):
        """This script expects that the file '<repositorybasefolder>/<codeunitname>/Other/QualityCheck/TestCoverage/TestCoverage.xml'
        which contains a test-coverage-report in the cobertura-format exists.
        This script expectes that the testcoverage-reportfolder is '<repositorybasefolder>/<codeunitname>/Other/QualityCheck/TestCoverage/TestCoverageReport'.
        This script expectes that a test-coverage-badges should be added to '<repositorybasefolder>/<codeunitname>/Other/QualityCheck/TestCoverage/Badges'."""
        if verbosity == 0:
            verbose_argument_for_reportgenerator = "Off"
        if verbosity == 1:
            verbose_argument_for_reportgenerator = "Error"
        if verbosity == 2:
            verbose_argument_for_reportgenerator = "Info"
        if verbosity == 3:
            verbose_argument_for_reportgenerator = "Verbose"

        # Generating report
        GeneralUtilities.ensure_directory_does_not_exist(os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/TestCoverageReport"))
        GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/TestCoverageReport"))
        self.__sc.run_program("reportgenerator", "-reports:Other/QualityCheck/TestCoverage/TestCoverage.xml -targetdir:Other/QualityCheck/TestCoverage/TestCoverageReport " +
                              f"-verbosity:{verbose_argument_for_reportgenerator}", os.path.join(repository_folder, codeunitname))

        if generate_badges:
            # Generating badges
            GeneralUtilities.ensure_directory_does_not_exist(os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/Badges"))
            GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder, codeunitname, "Other/QualityCheck/TestCoverage/Badges"))
            self.__sc.run_program("reportgenerator", "-reports:Other/QualityCheck/TestCoverage/TestCoverage.xml -targetdir:Other/QualityCheck/TestCoverage/Badges -reporttypes:Badges " +
                                  f"-verbosity:{verbose_argument_for_reportgenerator}",  os.path.join(repository_folder, codeunitname))

    @GeneralUtilities.check_arguments
    def standardized_tasks_generate_refefrence_for_dotnet_project_in_common_project_structure(self, generate_reference_file: str, commandline_arguments: list[str] = []):
        reference_folder = os.path.dirname(generate_reference_file)
        reference_result_folder = os.path.join(reference_folder, "GeneratedReference")
        GeneralUtilities.ensure_directory_does_not_exist(reference_result_folder)
        self.__sc.run_program("docfx", "docfx.json", reference_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_run_testcases_for_dotnet_project_in_common_project_structure(self, runtestcases_file: str, buildconfiguration: str = "Release", commandline_arguments: list[str] = []):
        repository_folder: str = str(Path(os.path.dirname(runtestcases_file)).parent.parent.parent.absolute())
        codeunit_name: str = os.path.basename(str(Path(os.path.dirname(runtestcases_file)).parent.parent.absolute()))
        for commandline_argument in commandline_arguments:
            if commandline_argument.startswith("-buildconfiguration:"):
                buildconfiguration = commandline_argument[len("-buildconfiguration:"):]
        testprojectname = codeunit_name+"Tests"
        coveragefilesource = os.path.join(repository_folder, codeunit_name, testprojectname, "TestCoverage.xml")
        coverage_file_folder = os.path.join(repository_folder, codeunit_name, "Other/QualityCheck/TestCoverage")
        coveragefiletarget = os.path.join(coverage_file_folder,  "TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefilesource)
        self.__sc.run_program("dotnet", f"test {testprojectname}/{testprojectname}.csproj -c {buildconfiguration}"
                              f" --verbosity normal /p:CollectCoverage=true /p:CoverletOutput=TestCoverage.xml"
                              f" /p:CoverletOutputFormat=cobertura", os.path.join(repository_folder, codeunit_name))
        GeneralUtilities.ensure_file_does_not_exist(coveragefiletarget)
        GeneralUtilities.ensure_directory_exists(coverage_file_folder)
        os.rename(coveragefilesource, coveragefiletarget)
        self.__standardized_tasks_generate_coverage_report(repository_folder, codeunit_name, 1)

    @GeneralUtilities.check_arguments
    def get_code_units_of_repository_in_common_project_format(self, repository_folder: str) -> list[str]:
        result = []
        for direct_subfolder in GeneralUtilities.get_direct_folders_of_folder(repository_folder):
            subfolder_name = os.path.basename(direct_subfolder)
            if os.path.isfile(os.path.join(direct_subfolder, subfolder_name+".codeunit")):
                # TODO validate .codeunit file against appropriate xsd-file
                result.append(subfolder_name)
        return result

    @GeneralUtilities.check_arguments
    def write_version_to_codeunit_file(self, codeunit_file: str, current_version: str) -> None:
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(current_version):
            GeneralUtilities.write_text_to_file(codeunit_file, re.sub(f"<codeunit:version>{versionregex}<\\/codeunit:version>",
                                                                      f"<codeunit:version>{current_version}</codeunit:version>", GeneralUtilities.read_text_from_file(codeunit_file)))
        else:
            raise ValueError(f"Version '{current_version}' does not match version-regex '{versiononlyregex}'")

    @GeneralUtilities.check_arguments
    def standardized_tasks_linting_for_dotnet_project_in_common_project_structure(self, linting_script_file: str, args: list[str]):
        pass  # TODO

    @GeneralUtilities.check_arguments
    def standardized_tasks_release_buildartifact_for_project_in_common_project_format(self, information: CreateReleaseInformationForProjectInCommonProjectFormat) -> None:
        # This function is intended to be called directly after standardized_tasks_merge_to_stable_branch_for_project_in_common_project_format

        project_version = self.__sc.get_semver_version_from_gitversion(information.repository)
        target_folder_base = os.path.join(information.build_artifacts_target_folder, information.projectname, project_version)
        if os.path.isdir(target_folder_base):
            raise ValueError(f"The folder '{target_folder_base}' already exists.")
        GeneralUtilities.ensure_directory_exists(target_folder_base)
        commitid = self.__sc.git_get_current_commit_id(information.repository)
        codeunits = self.get_code_units_of_repository_in_common_project_format(information.repository)

        for codeunitname in codeunits:
            codeunit_folder = os.path.join(information.repository, codeunitname)
            codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))
            GeneralUtilities.write_message_to_stdout(f"Build codeunit {codeunitname}")
            self.__run_build_py(commitid, codeunit_version, information.build_py_arguments, information.repository, codeunitname, information.verbosity)

        reference_repository_target_for_project = os.path.join(information.reference_repository, "ReferenceContent")

        for codeunitname in codeunits:
            codeunit_folder = os.path.join(information.repository, codeunitname)
            codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))

            target_folder_for_codeunit = os.path.join(target_folder_base, codeunitname)
            GeneralUtilities.ensure_directory_exists(target_folder_for_codeunit)
            shutil.copyfile(os.path.join(information.repository, codeunitname, f"{codeunitname}.codeunit"), os.path.join(target_folder_for_codeunit, f"{codeunitname}.codeunit"))

            target_folder_for_codeunit_buildartifact = os.path.join(target_folder_for_codeunit, "BuildArtifact")
            shutil.copytree(os.path.join(codeunit_folder, "Other", "Build", "BuildArtifact"), target_folder_for_codeunit_buildartifact)

            target_folder_for_codeunit_testcoveragereport = os.path.join(target_folder_for_codeunit, "TestCoverageReport")
            shutil.copytree(os.path.join(codeunit_folder, "Other", "QualityCheck", "TestCoverage", "TestCoverageReport"), target_folder_for_codeunit_testcoveragereport)

            target_folder_for_codeunit_generatedreference = os.path.join(target_folder_for_codeunit, "GeneratedReference")
            shutil.copytree(os.path.join(codeunit_folder, "Other", "Reference", "GeneratedReference"), target_folder_for_codeunit_generatedreference)

            if codeunitname in information.push_artifact_to_registry_scripts:
                push_artifact_to_registry_script = information.push_artifact_to_registry_scripts[codeunitname]
                folder = os.path.dirname(push_artifact_to_registry_script)
                file = os.path.basename(push_artifact_to_registry_script)
                GeneralUtilities.write_message_to_stdout(f"Push buildartifact of codeunit {codeunitname}")
                self.__sc.run_program("python", file, folder, verbosity=information.verbosity, throw_exception_if_exitcode_is_not_zero=True)

            # Copy reference of codeunit to reference-repository
            self.__export_codeunit_reference_content_to_reference_repository(f"v{project_version}", False, reference_repository_target_for_project, information.repository,
                                                                             codeunitname, information.projectname, codeunit_version, information.public_repository_url,
                                                                             information.target_branch_name)
            self.__export_codeunit_reference_content_to_reference_repository("Latest", True, reference_repository_target_for_project, information.repository,
                                                                             codeunitname, information.projectname,  codeunit_version, information.public_repository_url,
                                                                             information.target_branch_name)

        GeneralUtilities.write_message_to_stdout("Create entire reference")
        all_available_version_identifier_folders_of_reference = list(folder for folder in GeneralUtilities.get_direct_folders_of_folder(reference_repository_target_for_project))
        all_available_version_identifier_folders_of_reference.reverse()  # move newer versions above
        all_available_version_identifier_folders_of_reference.insert(0, all_available_version_identifier_folders_of_reference.pop())  # move latest version to the top
        reference_versions_html_lines = []
        for all_available_version_identifier_folder_of_reference in all_available_version_identifier_folders_of_reference:
            version_identifier_of_project = os.path.basename(all_available_version_identifier_folder_of_reference)
            if version_identifier_of_project == "Latest":
                latest_version_hint = f" (v {project_version})"
            else:
                latest_version_hint = ""
            reference_versions_html_lines.append(f"<h2>{version_identifier_of_project}{latest_version_hint}</h2>")
            reference_versions_html_lines.append("Contained codeunits:<br>")
            reference_versions_html_lines.append("<ul>")
            for codeunit_reference_folder in list(folder for folder in GeneralUtilities.get_direct_folders_of_folder(all_available_version_identifier_folder_of_reference)):
                codeunit_folder = os.path.join(information.repository, codeunitname)
                codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))
                reference_versions_html_lines.append(f'<li><a href="./{version_identifier_of_project}/{os.path.basename(codeunit_reference_folder)}/index.html">'
                                                     f'{os.path.basename(codeunit_reference_folder)} v{version_identifier_of_project}</a></li>')
            reference_versions_html_lines.append("</ul>")

        reference_versions_links_file_content = "    \n".join(reference_versions_html_lines)
        title = f"{information.projectname}-reference"
        reference_index_file = os.path.join(reference_repository_target_for_project, "index.html")
        reference_index_file_content = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>

<body>
    <h1>{title}</h1>
    {reference_versions_links_file_content}
</body>

</html>
"""
        GeneralUtilities.write_text_to_file(reference_index_file, reference_index_file_content)

    @GeneralUtilities.check_arguments
    def push_nuget_build_artifact_for_project_in_standardized_project_structure(self, push_script_file: str, codeunitname: str,
                                                                                registry_address: str = "nuget.org", api_key: str = None):
        build_artifact_folder = GeneralUtilities.resolve_relative_path(
            f"../../Submodules/{codeunitname}/{codeunitname}/Other/Build/BuildArtifact", os.path.dirname(push_script_file))
        self.__sc.push_nuget_build_artifact_of_repository_in_common_file_structure(self.__sc.find_file_by_extension(build_artifact_folder, "nupkg"),
                                                                                   registry_address, api_key)

    @GeneralUtilities.check_arguments
    def create_release_for_project_in_standardized_release_repository_format(self, projectname: str, create_release_file: str,
                                                                             project_has_source_code: bool, remotename: str, build_artifacts_target_folder: str, push_to_registry_scripts:
                                                                             dict[str, str], verbosity: int = 1, reference_repository_remote_name: str = None,
                                                                             reference_repository_branch_name: str = "main", build_repository_branch="main",
                                                                             public_repository_url: str = None, build_py_arguments: str = ""):

        GeneralUtilities.write_message_to_stdout(f"Create release for project {projectname}")
        folder_of_create_release_file_file = os.path.abspath(os.path.dirname(create_release_file))

        build_repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}..", folder_of_create_release_file_file)
        if self.__sc.git_repository_has_uncommitted_changes(build_repository_folder):
            raise ValueError(f"Repository '{build_repository_folder}' has uncommitted changes.")

        self.__sc.git_checkout(build_repository_folder, build_repository_branch)

        repository_folder = GeneralUtilities.resolve_relative_path(f"Submodules{os.path.sep}{projectname}", build_repository_folder)
        mergeToStableBranchInformation = MergeToStableBranchInformationForProjectInCommonProjectFormat(repository_folder)
        mergeToStableBranchInformation.verbosity = verbosity
        mergeToStableBranchInformation.project_has_source_code = project_has_source_code
        mergeToStableBranchInformation.push_source_branch = True
        mergeToStableBranchInformation.push_source_branch_remote_name = remotename
        mergeToStableBranchInformation.push_target_branch = True
        mergeToStableBranchInformation.push_target_branch_remote_name = remotename
        mergeToStableBranchInformation.merge_target_as_fast_forward_into_source_after_merge = True
        mergeToStableBranchInformation.build_py_arguments = build_py_arguments
        new_project_version = self.standardized_tasks_merge_to_stable_branch_for_project_in_common_project_format(mergeToStableBranchInformation)

        createReleaseInformation = CreateReleaseInformationForProjectInCommonProjectFormat(repository_folder, build_artifacts_target_folder,
                                                                                           projectname, public_repository_url,
                                                                                           mergeToStableBranchInformation.targetbranch)
        createReleaseInformation.verbosity = verbosity
        createReleaseInformation.build_py_arguments = build_py_arguments
        if project_has_source_code:
            createReleaseInformation.push_artifact_to_registry_scripts = push_to_registry_scripts
            self.standardized_tasks_release_buildartifact_for_project_in_common_project_format(createReleaseInformation)

            self.__sc.git_commit(createReleaseInformation.reference_repository, f"Added reference of {projectname} v{new_project_version}")
            if reference_repository_remote_name is not None:
                self.__sc.git_push(createReleaseInformation.reference_repository, reference_repository_remote_name, reference_repository_branch_name,
                                   reference_repository_branch_name,  verbosity=verbosity)
        self.__sc.git_commit(build_repository_folder, f"Added {projectname} release v{new_project_version}")
        GeneralUtilities.write_message_to_stdout(f"Finished release for project {projectname} successfully")
        return new_project_version

    @GeneralUtilities.check_arguments
    def create_release_starter_for_repository_in_standardized_format(self, create_release_file: str, logfile=None, verbosity: int = 1):
        folder_of_this_file = os.path.dirname(create_release_file)
        self.__sc.run_program("python.py", "CreateRelease.py", folder_of_this_file, verbosity, log_file=logfile)

    @GeneralUtilities.check_arguments
    def standardized_tasks_merge_to_stable_branch_for_project_in_common_project_format(self, information: MergeToStableBranchInformationForProjectInCommonProjectFormat) -> str:

        src_branch_commit_id = self.__sc.git_get_current_commit_id(information.repository,  information.sourcebranch)
        if(src_branch_commit_id == self.__sc.git_get_current_commit_id(information.repository,  information.targetbranch)):
            GeneralUtilities.write_message_to_stderr(
                f"Can not merge because the source-branch and the target-branch are on the same commit (commit-id: {src_branch_commit_id})")

        self.__sc.git_checkout(information.repository, information.sourcebranch)
        self.__sc.run_program("git", "clean -dfx", information.repository, throw_exception_if_exitcode_is_not_zero=True)
        project_version = self.__sc.get_semver_version_from_gitversion(information.repository)
        self.__sc.git_merge(information.repository, information.sourcebranch, information.targetbranch, False, False)
        success = False
        try:
            for codeunitname in self.get_code_units_of_repository_in_common_project_format(information.repository):
                GeneralUtilities.write_message_to_stdout(f"Start processing codeunit {codeunitname}")

                common_tasks_file: str = "CommonTasks.py"
                common_tasks_folder: str = os.path.join(information.repository, codeunitname, "Other")
                if os.path.isfile(os.path.join(common_tasks_folder, common_tasks_file)):
                    GeneralUtilities.write_message_to_stdout("Do common tasks")
                    self.__sc.run_program("python", f"{common_tasks_file} --projectversion={project_version}", common_tasks_folder, verbosity=information.verbosity)

                if information.project_has_source_code:
                    GeneralUtilities.write_message_to_stdout("Run testcases")
                    qualityfolder = os.path.join(information.repository, codeunitname, "Other", "QualityCheck")
                    self.__sc.run_program("python", "RunTestcases.py", qualityfolder, verbosity=information.verbosity)
                    self.check_testcoverage(os.path.join(information.repository, codeunitname, "Other", "QualityCheck", "TestCoverage", "TestCoverage.xml"),
                                            self.__get_testcoverage_threshold_from_codeunit_file(os.path.join(information.repository, codeunitname, f"{codeunitname}.codeunit")))

                    GeneralUtilities.write_message_to_stdout("Check linting")
                    self.__sc.run_program("python", "Linting.py", os.path.join(information.repository, codeunitname, "Other", "QualityCheck"), verbosity=information.verbosity)

                    GeneralUtilities.write_message_to_stdout("Generate reference")
                    self.__sc.run_program("python", "GenerateReference.py", os.path.join(information.repository,
                                          codeunitname, "Other", "Reference"), verbosity=information.verbosity)

                    if information.run_build_py:
                        codeunit_folder = os.path.join(information.repository, codeunitname)
                        codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))
                        GeneralUtilities.write_message_to_stdout("Test if codeunit is buildable")
                        commitid = self.__sc.git_get_current_commit_id(information.repository)
                        self.__run_build_py(commitid, codeunit_version, information.build_py_arguments, information.repository, codeunitname, information.verbosity)
                GeneralUtilities.write_message_to_stdout(f"Finished processing codeunit {codeunitname}")

            commit_id = self.__sc.git_commit(information.repository,  f"Created release v{project_version}")
            success = True
        except Exception as exception:
            GeneralUtilities.write_exception_to_stderr(exception, "Error while doing merge-tasks. Merge will be aborted.")
            self.__sc.git_merge_abort(information.repository)
            self.__sc.git_checkout(information.repository, information.sourcebranch)

        if not success:
            raise Exception("Release was not successful.")

        self.__sc.git_create_tag(information.repository, commit_id, f"v{project_version}", information.sign_git_tags)

        if information.push_target_branch:
            GeneralUtilities.write_message_to_stdout("Push target-branch")
            self.__sc.git_push(information.repository, information.push_target_branch_remote_name,
                               information.targetbranch, information.targetbranch, pushalltags=True, verbosity=False)

        if information.merge_target_as_fast_forward_into_source_after_merge:
            self.__sc.git_merge(information.repository, information.targetbranch, information.sourcebranch, True, True)
            if information.push_source_branch:
                GeneralUtilities.write_message_to_stdout("Push source-branch")
                self.__sc.git_push(information.repository, information.push_source_branch_remote_name, information.sourcebranch,
                                   information.sourcebranch, pushalltags=False, verbosity=information.verbosity)
        return project_version

    @GeneralUtilities.check_arguments
    def __export_codeunit_reference_content_to_reference_repository(self, project_version_identifier: str, replace_existing_content: bool, target_folder_for_reference_repository: str,
                                                                    repository: str, codeunitname, projectname: str, codeunit_version: str, public_repository_url: str, branch: str) -> None:

        target_folder = os.path.join(target_folder_for_reference_repository, project_version_identifier, codeunitname)
        if os.path.isdir(target_folder) and not replace_existing_content:
            raise ValueError(f"Folder '{target_folder}' already exists.")

        GeneralUtilities.ensure_directory_does_not_exist(target_folder)
        GeneralUtilities.ensure_directory_exists(target_folder)
        title = f"{codeunitname}-reference (codeunit v{codeunit_version}, conained in project {projectname} ({project_version_identifier}))"

        if public_repository_url is None:
            repo_url_html = ""
        else:
            repo_url_html = f'<a href="{public_repository_url}/tree/{branch}/{codeunitname}">Source-code</a><br>'

        index_file_for_reference = os.path.join(target_folder, "index.html")
        index_file_content = f"""<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <title>{title}</title>
  </head>

  <body>
    <h1>{title}</h1>
    Available reference-content for {codeunitname}:<br>
    {repo_url_html}
    <a href="./GeneratedReference/index.html">Refrerence</a><br>
    <a href="./TestCoverageReport/index.html">TestCoverageReport</a><br>
  </body>

</html>
"""
        GeneralUtilities.ensure_file_exists(index_file_for_reference)
        GeneralUtilities.write_text_to_file(index_file_for_reference, index_file_content)

        other_folder_in_repository = os.path.join(repository, codeunitname, "Other")

        source_generatedreference = os.path.join(other_folder_in_repository, "Reference", "GeneratedReference")
        target_generatedreference = os.path.join(target_folder, "GeneratedReference")
        shutil.copytree(source_generatedreference, target_generatedreference)

        source_testcoveragereport = os.path.join(other_folder_in_repository, "QualityCheck", "TestCoverage", "TestCoverageReport")
        target_testcoveragereport = os.path.join(target_folder, "TestCoverageReport")
        shutil.copytree(source_testcoveragereport, target_testcoveragereport)
