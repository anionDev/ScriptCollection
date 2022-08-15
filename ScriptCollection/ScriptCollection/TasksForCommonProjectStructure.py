import os
from pathlib import Path
import shutil
import re
from lxml import etree
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore


class CodeUnitConfiguration():
    name: str
    push_to_registry_script: str
    build_script_arguments: str
    generate_reference_script_arguments: str
    linting_script_arguments: str
    run_testcases_script_arguments: str

    def __init__(self, name: str, push_to_registry_script: str, build_script_arguments: str, generate_reference_script_arguments: str,
                 linting_script_arguments: str, run_testcases_script_arguments: str):

        self.name = name
        self.push_to_registry_script = push_to_registry_script
        self.build_script_arguments = build_script_arguments
        self.generate_reference_script_arguments = generate_reference_script_arguments
        self.linting_script_arguments = linting_script_arguments
        self.run_testcases_script_arguments = run_testcases_script_arguments


class CreateReleaseConfiguration():
    projectname: str
    remotename: str
    artifacts_folder: str
    codeunits: dict[str, CodeUnitConfiguration]
    verbosity: int
    reference_repository_remote_name: str
    reference_repository_branch_name: str
    build_repository_branch: str
    public_repository_url: str

    def __init__(self, projectname: str, remotename: str, build_artifacts_target_folder: str, codeunits: dict[str, CodeUnitConfiguration],
                 verbosity: int, reference_repository_remote_name: str, reference_repository_branch_name: str, build_repository_branch: str,
                 public_repository_url: str):

        self.projectname = projectname
        self.remotename = remotename
        self.artifacts_folder = build_artifacts_target_folder
        self.codeunits = codeunits
        self.verbosity = verbosity
        self.reference_repository_remote_name = reference_repository_remote_name
        self.reference_repository_branch_name = reference_repository_branch_name
        self.build_repository_branch = build_repository_branch
        self.public_repository_url = public_repository_url


class CreateReleaseInformationForProjectInCommonProjectFormat:
    projectname: str
    repository: str
    artifacts_folder: str
    build_py_arguments: str = ""
    verbosity: int = 1
    reference_repository: str = None
    public_repository_url: str = None
    target_branch_name: str = None
    codeunits: dict[str, CodeUnitConfiguration]

    def __init__(self, repository: str, artifacts_folder: str, projectname: str, public_repository_url: str, target_branch_name: str):
        self.repository = repository
        self.public_repository_url = public_repository_url
        self.target_branch_name = target_branch_name
        self.artifacts_folder = artifacts_folder
        if projectname is None:
            projectname = os.path.basename(self.repository)
        else:
            self.projectname = projectname
        self.reference_repository = GeneralUtilities.resolve_relative_path(f"../{projectname}Reference", repository)


class MergeToStableBranchInformationForProjectInCommonProjectFormat:
    repository: str
    sourcebranch: str = "main"
    targetbranch: str = "stable"
    run_build_script: bool = True
    sign_git_tags: bool = True
    codeunits: dict[str, CodeUnitConfiguration]

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
    def __run_build_py(self, commitid, codeunit_version: str, build_py_arguments: str, repository: str, codeunitname: str, verbosity: int):
        target_folder = self.get_build_folder_in_repository_in_common_repository_format(repository, codeunitname)
        GeneralUtilities.ensure_directory_exists(target_folder)
        self.__sc.run_program("python", f"Build.py --commitid={commitid} --codeunitversion={codeunit_version} --verbosity={str(verbosity)} {build_py_arguments}",
                              target_folder, verbosity=verbosity)

    @GeneralUtilities.check_arguments
    def get_build_folder_in_repository_in_common_repository_format(self, repository_folder: str, codeunit_name: str) -> str:
        return os.path.join(repository_folder, codeunit_name, "Other", "Build")

    @GeneralUtilities.check_arguments
    def get_artifacts_folder_in_repository_in_common_repository_format(self, repository_folder: str, codeunit_name: str) -> str:
        return os.path.join(repository_folder, codeunit_name, "Other", "Artifacts")

    @GeneralUtilities.check_arguments
    def get_wheel_file_in_repository_in_common_repository_format(self, repository_folder: str, codeunit_name: str) -> str:
        return self.__sc.find_file_by_extension(os.path.join(self.get_artifacts_folder_in_repository_in_common_repository_format(repository_folder, codeunit_name), "Wheel"), "whl")

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
    def replace_version_in_python_file(self, file: str, new_version_value: str):
        GeneralUtilities.write_text_to_file(file, re.sub("version = \"\\d+\\.\\d+\\.\\d+\"", f"version = \"{new_version_value}\"",
                                                         GeneralUtilities.read_text_from_file(file)))

    @GeneralUtilities.check_arguments
    def __standardized_tasks_run_testcases_for_python_codeunit(self, repository_folder: str, codeunitname: str, verbosity: int):
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        if verbosity == 1:
            verbosity_for_pytest = 2
        else:
            verbosity_for_pytest = verbosity
        self.__sc.run_program("coverage", "run -m pytest", codeunit_folder, verbosity_for_pytest)
        self.__sc.run_program("coverage", "xml", codeunit_folder)
        coveragefolder = os.path.join(repository_folder, codeunitname, "Other/Artifacts/TestCoverage")
        GeneralUtilities.ensure_directory_exists(coveragefolder)
        coveragefile = os.path.join(coveragefolder, "TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder, codeunitname, "coverage.xml"), coveragefile)

    @GeneralUtilities.check_arguments
    def standardized_tasks_generate_refefrence_for_codeunit_in_common_project_structure(self, generate_reference_file: str, commandline_arguments: list[str]):
        reference_folder = os.path.dirname(generate_reference_file)
        reference_result_folder = os.path.join(reference_folder, "Reference")
        GeneralUtilities.ensure_directory_does_not_exist(reference_result_folder)
        self.__sc.run_program("docfx", "docfx.json", reference_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_run_testcases_for_python_codeunit_in_common_project_structure(self, run_testcases_file: str, generate_badges: bool, verbosity: int,
                                                                                         commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        repository_folder: str = str(Path(os.path.dirname(run_testcases_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(run_testcases_file)).parent.parent.name
        self.__standardized_tasks_run_testcases_for_python_codeunit(repository_folder, codeunitname, verbosity)
        self.__standardized_tasks_generate_coverage_report(repository_folder, codeunitname, verbosity, generate_badges, commandline_arguments)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_node_project_in_common_project_structure(self, build_file: str, verbosity: int, commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        repository_folder: str = str(Path(os.path.dirname(build_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(build_file)).parent.parent.name
        codeunit_folder = os.path.join(repository_folder, codeunitname)
        # target_directory = GeneralUtilities.resolve_relative_path(
        #    "../Artifacts/npm", os.path.join(self.get_artifacts_folder_in_repository_in_common_repository_format(repository_folder, codeunitname)))
        # TODO use this variable and move file accordingly
        self.__sc.run_program("npm", "run build", codeunit_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_python_codeunit_in_common_project_structure(self, build_file: str, verbosity: int, commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        setuppy_file_folder = str(Path(os.path.dirname(build_file)).parent.parent.absolute())
        setuppy_file_filename = "Setup.py"
        repository_folder: str = str(Path(os.path.dirname(build_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(build_file)).parent.parent.name
        target_directory = GeneralUtilities.resolve_relative_path(
            "../Artifacts/Wheel", os.path.join(self.get_artifacts_folder_in_repository_in_common_repository_format(repository_folder, codeunitname)))
        GeneralUtilities.ensure_directory_does_not_exist(target_directory)
        self.__sc.run_program("git", f"clean -dfx --exclude={codeunitname}/Other {codeunitname}", repository_folder)
        GeneralUtilities.ensure_directory_exists(target_directory)
        self.__sc.run_program("python", f"{setuppy_file_filename} bdist_wheel --dist-dir {target_directory}", setuppy_file_folder, verbosity)

    @GeneralUtilities.check_arguments
    def standardized_tasks_push_wheel_file_to_registry(self, wheel_file: str, api_key: str, repository: str, gpg_identity: str, verbosity: int) -> None:
        # repository-value when PyPi should be used: "pypi"
        # gpg_identity-value when wheel-file should not be signed: None
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
    def push_wheel_build_artifact_of_repository_in_common_file_structure(self, push_build_artifacts_file, product_name, codeunitname, repository: str,
                                                                         apikey: str, gpg_identity: str, verbosity: int, commandline_arguments: list[str]) -> None:
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        folder_of_this_file = os.path.dirname(push_build_artifacts_file)
        repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}../Submodules{os.path.sep}{product_name}", folder_of_this_file)
        wheel_file = self.get_wheel_file_in_repository_in_common_repository_format(repository_folder, codeunitname)
        self.standardized_tasks_push_wheel_file_to_registry(wheel_file, apikey, repository, gpg_identity, verbosity)

    @GeneralUtilities.check_arguments
    def get_version_of_codeunit(self, codeunit_file: str) -> None:
        root: etree._ElementTree = etree.parse(codeunit_file)
        result = str(root.xpath('//codeunit:version/text()', namespaces={'codeunit': 'https://github.com/anionDev/ProjectTemplates'})[0])
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_verbosity_from_commandline_arguments(commandline_arguments: list[str], default_value: int) -> None:
        verbosity = None
        for commandline_argument in commandline_arguments[1:]:
            if commandline_argument.startswith("--verbosity="):
                verbosity = int(commandline_argument[len("--verbosity="):])
        if verbosity is None:
            return default_value
        else:
            return verbosity

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_buildconfiguration_from_commandline_arguments(commandline_arguments: list[str], default_value: str) -> None:
        build_configuration = None
        for commandline_argument in commandline_arguments[1:]:
            if commandline_argument.startswith("--buildconfiguration="):
                build_configuration = int(commandline_argument[len("--buildconfiguration="):])
        if build_configuration is None:
            return default_value
        else:
            return build_configuration

    @GeneralUtilities.check_arguments
    def update_version_of_codeunit_to_project_version(self, common_tasks_file: str, current_version: str) -> None:
        codeunit_name: str = os.path.basename(GeneralUtilities.resolve_relative_path("..", os.path.dirname(common_tasks_file)))
        codeunit_file: str = os.path.join(GeneralUtilities.resolve_relative_path("..", os.path.dirname(common_tasks_file)), f"{codeunit_name}.codeunit")
        self.write_version_to_codeunit_file(codeunit_file, current_version)

    @GeneralUtilities.check_arguments
    def standardized_tasks_generate_reference_by_docfx(self, generate_reference_script_file: str, verbosity: int, commandline_arguments: list[str]) -> None:
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        folder_of_current_file = os.path.dirname(generate_reference_script_file)
        generated_reference_folder = GeneralUtilities.resolve_relative_path("../Artifacts/Reference", folder_of_current_file)
        GeneralUtilities.ensure_directory_does_not_exist(generated_reference_folder)
        GeneralUtilities.ensure_directory_exists(generated_reference_folder)
        obj_folder = os.path.join(folder_of_current_file, "obj")
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)
        GeneralUtilities.ensure_directory_exists(obj_folder)
        self.__sc.run_program("docfx", "docfx.json", folder_of_current_file, verbosity)
        GeneralUtilities.ensure_directory_does_not_exist(obj_folder)

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
    def standardized_tasks_build_for_dotnet_project_in_common_project_structure(self, buildscript_file: str, buildconfiguration: str, verbosity: int, commandline_arguments: list[str]):
        # hint: arguments can be overwritten by commandline_arguments
        # this function builds an exe or dll
        self.__standardized_tasks_build_for_dotnet_project_in_common_project_structure(buildscript_file, buildconfiguration, True, verbosity, commandline_arguments)

    @GeneralUtilities.check_arguments
    def standardized_tasks_build_for_dotnet_library_project_in_common_project_structure(self, buildscript_file: str, buildconfiguration: str, verbosity: int, commandline_arguments: list[str]):
        # hint: arguments can be overwritten by commandline_arguments
        # this function builds an exe or dll and converts it to a nupkg-file
        self.__standardized_tasks_build_for_dotnet_project_in_common_project_structure(buildscript_file, buildconfiguration, True, verbosity, commandline_arguments)
        self.__standardized_tasks_build_nupkg_for_dotnet_create_package(buildscript_file, verbosity, commandline_arguments)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_build_for_dotnet_project_in_common_project_structure(self, buildscript_file: str, buildconfiguration: str,
                                                                                  build_test_project_too: bool, verbosity: int, commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        buildconfiguration = TasksForCommonProjectStructure.get_buildconfiguration_from_commandline_arguments(commandline_arguments, buildconfiguration)
        repository_folder: str = str(Path(os.path.dirname(buildscript_file)).parent.parent.parent.absolute())
        codeunitname: str = os.path.basename(str(Path(os.path.dirname(buildscript_file)).parent.parent.absolute()))
        outputfolder = GeneralUtilities.resolve_relative_path("../Artifacts/BuildResult", os.path.dirname(buildscript_file))

        codeunit_folder = os.path.join(repository_folder, codeunitname)
        csproj_file = os.path.join(codeunit_folder, codeunitname, codeunitname+".csproj")
        csproj_test_file = os.path.join(codeunit_folder, codeunitname+"Tests", codeunitname+"Tests.csproj")
        commandline_arguments2 = commandline_arguments[1:]
        files_to_sign: dict() = dict()
        for commandline_argument in commandline_arguments2:
            if commandline_argument.startswith("-sign="):
                commandline_argument = commandline_argument[len("-sign="):]
                commandline_argument_splitted: list[str] = commandline_argument.split(":")
                files_to_sign[commandline_argument_splitted[0]] = commandline_argument[len(commandline_argument_splitted[0])+1:]

        self.__sc.run_program("dotnet", "restore", codeunit_folder)
        self.__standardized_tasks_build_for_dotnet_build(csproj_file, buildconfiguration, os.path.join(outputfolder, codeunitname), files_to_sign)
        if build_test_project_too:
            self.__standardized_tasks_build_for_dotnet_build(csproj_test_file, buildconfiguration, os.path.join(outputfolder, codeunitname+"Tests"), files_to_sign)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_build_nupkg_for_dotnet_create_package(self, buildscript_file: str, verbosity: int, commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        repository_folder: str = str(Path(os.path.dirname(buildscript_file)).parent.parent.parent.absolute())
        codeunitname: str = os.path.basename(str(Path(os.path.dirname(buildscript_file)).parent.parent.absolute()))
        build_folder = os.path.join(repository_folder, codeunitname, "Other", "Build")
        outputfolder = GeneralUtilities.resolve_relative_path("../Artifacts/Nuget", os.path.dirname(buildscript_file))
        root: etree._ElementTree = etree.parse(os.path.join(build_folder, f"{codeunitname}.nuspec"))
        current_version = root.xpath("//*[name() = 'package']/*[name() = 'metadata']/*[name() = 'version']/text()")[0]
        nupkg_filename = f"{codeunitname}.{current_version}.nupkg"
        nupkg_file = f"{build_folder}/{nupkg_filename}"
        GeneralUtilities.ensure_file_does_not_exist(nupkg_file)
        self.__sc.run_program("nuget", f"pack {codeunitname}.nuspec", build_folder, verbosity)
        GeneralUtilities.ensure_directory_does_not_exist(outputfolder)
        GeneralUtilities.ensure_directory_exists(outputfolder)
        os.rename(nupkg_file, f"{outputfolder}/{nupkg_filename}")

    @GeneralUtilities.check_arguments
    def standardized_tasks_linting_for_python_codeunit_in_common_project_structure(self, linting_script_file: str, verbosity: int, commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
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
    def __standardized_tasks_generate_coverage_report(self, repository_folder: str, codeunitname: str, verbosity: int, generate_badges: bool, commandline_arguments: list[str]):
        """This script expects that the file '<repositorybasefolder>/<codeunitname>/Other/Artifacts/TestCoverage/TestCoverage.xml'
        which contains a test-coverage-report in the cobertura-format exists.
        This script expectes that the testcoverage-reportfolder is '<repositorybasefolder>/<codeunitname>/Other/Artifacts/TestCoverageReport'.
        This script expectes that a test-coverage-badges should be added to '<repositorybasefolder>/<codeunitname>/Other/Resources/Badges'."""
        if verbosity == 0:
            verbose_argument_for_reportgenerator = "Off"
        if verbosity == 1:
            verbose_argument_for_reportgenerator = "Error"
        if verbosity == 2:
            verbose_argument_for_reportgenerator = "Info"
        if verbosity == 3:
            verbose_argument_for_reportgenerator = "Verbose"

        # Generating report
        GeneralUtilities.ensure_directory_does_not_exist(os.path.join(repository_folder, codeunitname, "Other/Artifacts/TestCoverageReport"))
        GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder, codeunitname, "Other/Artifacts/TestCoverageReport"))
        self.__sc.run_program("reportgenerator", "-reports:Other/Artifacts/TestCoverage/TestCoverage.xml " +
                              f"-targetdir:Other/Artifacts/TestCoverageReport --verbosity={verbose_argument_for_reportgenerator}", os.path.join(repository_folder, codeunitname))

        if generate_badges:
            # Generating badges
            testcoverageubfolger = "Other/Resources/TestCoverageBadges"
            fulltestcoverageubfolger = os.path.join(repository_folder, codeunitname, testcoverageubfolger)
            GeneralUtilities.ensure_directory_does_not_exist(fulltestcoverageubfolger)
            GeneralUtilities.ensure_directory_exists(fulltestcoverageubfolger)
            self.__sc.run_program("reportgenerator", f"-reports:Other/Artifacts/TestCoverage/TestCoverage.xml -targetdir:{testcoverageubfolger} " +
                                  f"-reporttypes:Badges --verbosity={verbose_argument_for_reportgenerator}",  os.path.join(repository_folder, codeunitname))

    @GeneralUtilities.check_arguments
    def standardized_tasks_generate_refefrence_for_dotnet_project_in_common_project_structure(self, generate_reference_file: str, commandline_arguments: list[str]):
        reference_folder = os.path.dirname(generate_reference_file)
        reference_result_folder = os.path.join(reference_folder, "Reference")
        GeneralUtilities.ensure_directory_does_not_exist(reference_result_folder)
        self.__sc.run_program("docfx", "docfx.json", reference_folder)

    @GeneralUtilities.check_arguments
    def standardized_tasks_run_testcases_for_dotnet_project_in_common_project_structure(self, runtestcases_file: str, buildconfiguration: str, verbosity: int, generate_badges: bool,
                                                                                        commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        buildconfiguration = TasksForCommonProjectStructure.get_buildconfiguration_from_commandline_arguments(commandline_arguments, buildconfiguration)
        repository_folder: str = str(Path(os.path.dirname(runtestcases_file)).parent.parent.parent.absolute())
        codeunit_name: str = os.path.basename(str(Path(os.path.dirname(runtestcases_file)).parent.parent.absolute()))
        testprojectname = codeunit_name+"Tests"
        coveragefilesource = os.path.join(repository_folder, codeunit_name, testprojectname, "TestCoverage.xml")
        coverage_file_folder = os.path.join(repository_folder, codeunit_name, "Other/Artifacts/TestCoverage")
        coveragefiletarget = os.path.join(coverage_file_folder,  "TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefilesource)
        self.__sc.run_program("dotnet", f"test {testprojectname}/{testprojectname}.csproj -c {buildconfiguration}"
                              f" --verbosity normal /p:CollectCoverage=true /p:CoverletOutput=TestCoverage.xml"
                              f" /p:CoverletOutputFormat=cobertura", os.path.join(repository_folder, codeunit_name))
        GeneralUtilities.ensure_file_does_not_exist(coveragefiletarget)
        GeneralUtilities.ensure_directory_exists(coverage_file_folder)
        os.rename(coveragefilesource, coveragefiletarget)
        self.__standardized_tasks_generate_coverage_report(repository_folder, codeunit_name, verbosity, generate_badges, commandline_arguments)

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
    def standardized_tasks_linting_for_dotnet_project_in_common_project_structure(self, linting_script_file: str, verbosity: int, commandline_arguments: list[str]):
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        # TODO implement function

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
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
  </head>
  <body>
    <h1 class="display-1">{title}</h1>
    <hr/>
    Available reference-content for {codeunitname}:<br>
    {repo_url_html}
    <a href="./Reference/index.html">Refrerence</a><br>
    <a href="./TestCoverageReport/index.html">TestCoverageReport</a><br>
  </body>
</html>
"""  # see https://getbootstrap.com/docs/5.1/getting-started/introduction/
        GeneralUtilities.ensure_file_exists(index_file_for_reference)
        GeneralUtilities.write_text_to_file(index_file_for_reference, index_file_content)
        other_folder_in_repository = os.path.join(repository, codeunitname, "Other")
        source_generatedreference = os.path.join(other_folder_in_repository, "Artifacts", "Reference")
        target_generatedreference = os.path.join(target_folder, "Reference")
        shutil.copytree(source_generatedreference, target_generatedreference)
        source_testcoveragereport = os.path.join(other_folder_in_repository, "Artifacts", "TestCoverageReport")
        target_testcoveragereport = os.path.join(target_folder, "TestCoverageReport")
        shutil.copytree(source_testcoveragereport, target_testcoveragereport)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_release_buildartifact_for_project_in_common_project_format(self, information: CreateReleaseInformationForProjectInCommonProjectFormat) -> None:
        # This function is intended to be called directly after standardized_tasks_merge_to_stable_branch_for_project_in_common_project_format
        project_version = self.__sc.get_semver_version_from_gitversion(information.repository)
        target_folder_base = os.path.join(information.artifacts_folder, information.projectname, project_version)
        if os.path.isdir(target_folder_base):
            raise ValueError(f"The folder '{target_folder_base}' already exists.")
        GeneralUtilities.ensure_directory_exists(target_folder_base)
        commitid = self.__sc.git_get_current_commit_id(information.repository)

        for codeunitname in information.codeunits:
            codeunit_folder = os.path.join(information.repository, codeunitname)
            codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))
            GeneralUtilities.write_message_to_stdout("Build codeunit")
            self.__run_build_py(commitid, codeunit_version, information.build_py_arguments, information.repository, codeunitname, information.verbosity)

        reference_repository_target_for_project = os.path.join(information.reference_repository, "ReferenceContent")

        for codeunitname in information.codeunits:
            codeunit_folder = os.path.join(information.repository, codeunitname)
            codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))

            target_folder_for_codeunit = os.path.join(target_folder_base, codeunitname)
            GeneralUtilities.ensure_directory_exists(target_folder_for_codeunit)
            shutil.copyfile(os.path.join(information.repository, codeunitname, f"{codeunitname}.codeunit"), os.path.join(target_folder_for_codeunit, f"{codeunitname}.codeunit"))
            shutil.copytree(os.path.join(codeunit_folder, "Other", "Artifacts"), os.path.join(target_folder_for_codeunit, "Artifacts"))

        for _, codeunit in information.codeunits.items():
            push_artifact_to_registry_script = codeunit.push_to_registry_script
            folder = os.path.dirname(push_artifact_to_registry_script)
            file = os.path.basename(push_artifact_to_registry_script)
            GeneralUtilities.write_message_to_stdout(f"Push buildartifact of codeunit {codeunitname}")
            self.__sc.run_program("python", file, folder, verbosity=information.verbosity, throw_exception_if_exitcode_is_not_zero=True)

            # Copy reference of codeunit to reference-repository
            self.__export_codeunit_reference_content_to_reference_repository(f"v{project_version}", False, reference_repository_target_for_project, information.repository,
                                                                             codeunitname, information.projectname, codeunit_version, information.public_repository_url,
                                                                             f"v{project_version}")
            self.__export_codeunit_reference_content_to_reference_repository("Latest", True, reference_repository_target_for_project, information.repository,
                                                                             codeunitname, information.projectname, codeunit_version, information.public_repository_url,
                                                                             information.target_branch_name)

            GeneralUtilities.write_message_to_stdout("Create entire reference")
            all_available_version_identifier_folders_of_reference = list(
                folder for folder in GeneralUtilities.get_direct_folders_of_folder(reference_repository_target_for_project))
            all_available_version_identifier_folders_of_reference.reverse()  # move newer versions above
            all_available_version_identifier_folders_of_reference.insert(0, all_available_version_identifier_folders_of_reference.pop())  # move latest version to the top
            reference_versions_html_lines = []
            for all_available_version_identifier_folder_of_reference in all_available_version_identifier_folders_of_reference:
                version_identifier_of_project = os.path.basename(all_available_version_identifier_folder_of_reference)
                if version_identifier_of_project == "Latest":
                    latest_version_hint = f" (v {project_version})"
                else:
                    latest_version_hint = ""
                reference_versions_html_lines.append('<hr>')
                reference_versions_html_lines.append(f'<h2 class="display-2">{version_identifier_of_project}{latest_version_hint}</h2>')
                reference_versions_html_lines.append("Contained codeunits:<br>")
                reference_versions_html_lines.append("<ul>")
                for codeunit_reference_folder in list(folder for folder in GeneralUtilities.get_direct_folders_of_folder(all_available_version_identifier_folder_of_reference)):
                    codeunit_folder = os.path.join(information.repository, codeunitname)
                    codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunitname}.codeunit"))
                    reference_versions_html_lines.append(f'<li><a href="./{version_identifier_of_project}/{os.path.basename(codeunit_reference_folder)}/index.html">' +
                                                         f'{os.path.basename(codeunit_reference_folder)} {version_identifier_of_project}</a></li>')
                reference_versions_html_lines.append("</ul>")

            reference_versions_links_file_content = "    \n".join(reference_versions_html_lines)
            title = f"{information.projectname}-reference"
            reference_index_file = os.path.join(reference_repository_target_for_project, "index.html")
            reference_index_file_content = f"""<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
  </head>

  <body>
    <h1 class="display-1">{title}</h1>
    <hr/>
    {reference_versions_links_file_content}
  </body>

</html>
"""  # see https://getbootstrap.com/docs/5.1/getting-started/introduction/
            GeneralUtilities.write_text_to_file(reference_index_file, reference_index_file_content)

    @GeneralUtilities.check_arguments
    def push_nuget_build_artifact_for_project_in_standardized_project_structure(self, push_script_file: str, codeunitname: str,
                                                                                registry_address: str, api_key: str):
        # when pusing to "default public" nuget-server then use registry_address: "nuget.org"
        build_artifact_folder = GeneralUtilities.resolve_relative_path(
            f"../../Submodules/{codeunitname}/{codeunitname}/Other/Artifacts/Nuget", os.path.dirname(push_script_file))
        self.__sc.push_nuget_build_artifact_of_repository_in_common_file_structure(self.__sc.find_file_by_extension(build_artifact_folder, "nupkg"),
                                                                                   registry_address, api_key)

    @GeneralUtilities.check_arguments
    def create_release_for_project_in_standardized_release_repository_format(self, create_release_file: str, createReleaseConfiguration: CreateReleaseConfiguration):

        GeneralUtilities.write_message_to_stdout(f"Create release for project {createReleaseConfiguration.projectname}")
        folder_of_create_release_file_file = os.path.abspath(os.path.dirname(create_release_file))

        build_repository_folder = GeneralUtilities.resolve_relative_path(f"..{os.path.sep}..", folder_of_create_release_file_file)
        if self.__sc.git_repository_has_uncommitted_changes(build_repository_folder):
            raise ValueError(f"Repository '{build_repository_folder}' has uncommitted changes.")

        self.__sc.git_checkout(build_repository_folder, createReleaseConfiguration.build_repository_branch)

        repository_folder = GeneralUtilities.resolve_relative_path(f"Submodules{os.path.sep}{createReleaseConfiguration.projectname}", build_repository_folder)
        mergeToStableBranchInformation = MergeToStableBranchInformationForProjectInCommonProjectFormat(repository_folder)
        mergeToStableBranchInformation.verbosity = createReleaseConfiguration.verbosity
        mergeToStableBranchInformation.push_source_branch = True
        mergeToStableBranchInformation.push_source_branch_remote_name = createReleaseConfiguration.remotename
        mergeToStableBranchInformation.push_target_branch = True
        mergeToStableBranchInformation.push_target_branch_remote_name = createReleaseConfiguration.remotename
        mergeToStableBranchInformation.merge_target_as_fast_forward_into_source_after_merge = True
        mergeToStableBranchInformation.codeunits = createReleaseConfiguration.codeunits
        new_project_version = self.__standardized_tasks_merge_to_stable_branch_for_project_in_common_project_format(mergeToStableBranchInformation)

        createReleaseInformation = CreateReleaseInformationForProjectInCommonProjectFormat(repository_folder, createReleaseConfiguration.artifacts_folder,
                                                                                           createReleaseConfiguration.projectname, createReleaseConfiguration.public_repository_url,
                                                                                           mergeToStableBranchInformation.targetbranch)
        createReleaseInformation.verbosity = createReleaseConfiguration.verbosity
        createReleaseInformation.codeunits = createReleaseConfiguration.codeunits
        self.__standardized_tasks_release_buildartifact_for_project_in_common_project_format(createReleaseInformation)

        self.__sc.git_commit(createReleaseInformation.reference_repository, f"Added reference of {createReleaseConfiguration.projectname} v{new_project_version}")
        if createReleaseConfiguration.reference_repository_remote_name is not None:
            self.__sc.git_push(createReleaseInformation.reference_repository, createReleaseConfiguration.reference_repository_remote_name, createReleaseConfiguration.reference_repository_branch_name,
                               createReleaseConfiguration.reference_repository_branch_name,  verbosity=createReleaseConfiguration.verbosity)
        self.__sc.git_commit(build_repository_folder, f"Added {createReleaseConfiguration.projectname} release v{new_project_version}")
        GeneralUtilities.write_message_to_stdout(f"Finished release for project {createReleaseConfiguration.projectname} successfully")
        return new_project_version

    @GeneralUtilities.check_arguments
    def create_release_starter_for_repository_in_standardized_format(self, create_release_file: str, logfile: str, verbosity: int, commandline_arguments: list[str]):
        # hint: arguments can be overwritten by commandline_arguments
        folder_of_this_file = os.path.dirname(create_release_file)
        verbosity = TasksForCommonProjectStructure.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
        self.__sc.run_program("python", f"CreateRelease.py --verbosity={str(verbosity)}", folder_of_this_file, verbosity, log_file=logfile)

    @GeneralUtilities.check_arguments
    def __standardized_tasks_merge_to_stable_branch_for_project_in_common_project_format(self, information: MergeToStableBranchInformationForProjectInCommonProjectFormat) -> str:

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
            for _, codeunit in information.codeunits.items():
                GeneralUtilities.write_message_to_stdout(f"Start processing codeunit {codeunit.name}")

                common_tasks_file: str = "CommonTasks.py"
                common_tasks_folder: str = os.path.join(information.repository, codeunit.name, "Other")
                if os.path.isfile(os.path.join(common_tasks_folder, common_tasks_file)):
                    GeneralUtilities.write_message_to_stdout("Do common tasks")
                    self.__sc.run_program("python", f"{common_tasks_file} --projectversion={project_version}", common_tasks_folder, verbosity=information.verbosity)

                if information.run_build_script:
                    codeunit_folder = os.path.join(information.repository, codeunit.name)
                    codeunit_version = self.get_version_of_codeunit(os.path.join(codeunit_folder, f"{codeunit.name}.codeunit"))
                    GeneralUtilities.write_message_to_stdout("Build codeunit")
                    commitid = self.__sc.git_get_current_commit_id(information.repository)
                    self.__run_build_py(commitid, codeunit_version, codeunit.build_script_arguments, information.repository, codeunit.name, information.verbosity)

                verbosity_argument = f"--verbosity={str(information.verbosity)}"

                GeneralUtilities.write_message_to_stdout("Run testcases")
                qualityfolder = os.path.join(information.repository, codeunit.name, "Other", "QualityCheck")
                self.__sc.run_program("python", f"RunTestcases.py {verbosity_argument} {codeunit.run_testcases_script_arguments}", qualityfolder, verbosity=information.verbosity)
                self.check_testcoverage(os.path.join(information.repository, codeunit.name, "Other", "Artifacts", "TestCoverage", "TestCoverage.xml"),
                                        self.__get_testcoverage_threshold_from_codeunit_file(os.path.join(information.repository, codeunit.name, f"{codeunit.name}.codeunit")))

                GeneralUtilities.write_message_to_stdout("Check linting")
                self.__sc.run_program("python", f"Linting.py {verbosity_argument} {codeunit.linting_script_arguments}", os.path.join(
                    information.repository, codeunit.name, "Other", "QualityCheck"), verbosity=information.verbosity)

                GeneralUtilities.write_message_to_stdout("Generate reference")
                self.__sc.run_program("python", f"GenerateReference.py {verbosity_argument} {codeunit.generate_reference_script_arguments}",
                                      os.path.join(information.repository, codeunit.name, "Other", "Reference"), verbosity=information.verbosity)

                GeneralUtilities.write_message_to_stdout(f"Finished processing codeunit {codeunit.name}")

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
    def standardized_tasks_build_for_container_application_in_common_project_structure(self, buildscript_file: str, build_configuration: str,
                                                                                       commandline_arguments: list[str]):
        # hint: arguments can be overwritten by commandline_arguments
        sc = ScriptCollectionCore()
        build_configuration = TasksForCommonProjectStructure.get_buildconfiguration_from_commandline_arguments(commandline_arguments, build_configuration)
        codeunitname: str = os.path.basename(str(Path(os.path.dirname(buildscript_file)).parent.parent.absolute()))
        codeunitname_lower = codeunitname.lower()
        buildscript_folder = os.path.dirname(buildscript_file)
        sc.run_program("docker", f"build --build-arg EnvironmentStage={build_configuration} --tag {codeunitname_lower}:latest .", buildscript_folder)
        targetfolder = GeneralUtilities.resolve_relative_path("../Artifacts/ApplicationImage", buildscript_folder)
        GeneralUtilities.ensure_directory_exists(targetfolder)
        sc.run_program("docker", f"save -o {targetfolder}/{codeunitname}.latest.tar {codeunitname_lower}:latest", buildscript_folder)
