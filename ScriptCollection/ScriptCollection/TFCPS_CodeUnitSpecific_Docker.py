import os
from .GeneralUtilities import GeneralUtilities
from .SCLog import  LogLevel
from .TFCPS_CodeUnitSpecific_Base import TFCPS_CodeUnitSpecific_Base,TFCPS_CodeUnitSpecific_Base_CLI

class TFCPS_CodeUnitSpecific_Docker_Functions(TFCPS_CodeUnitSpecific_Base):

    def __init__(self,current_file:str,verbosity:LogLevel,targetenvironmenttype:str,additional_arguments_file:str):
        super().__init__(current_file, verbosity,targetenvironmenttype,additional_arguments_file)


    @GeneralUtilities.check_arguments
    def build_implementation(self,additional_arguments:dict=None) -> None:
        use_cache: bool = False
        
        codeunitname: str =self.get_codeunit_name()
        codeunit_folder =self.get_codeunit_folder()
        codeunitname_lower = codeunitname.lower()
        codeunit_file =self.get_codeunit_file()
        codeunitversion = self._protected_TFCPS_Tools_General.get_version_of_codeunit(codeunit_file)
        args = ["image", "build", "--pull", "--force-rm", "--progress=plain", "--build-arg", f"TargetEnvironmentType={self.get_target_environment_type()}", "--build-arg", f"CodeUnitName={codeunitname}", "--build-arg", f"CodeUnitVersion={codeunitversion}", "--build-arg", f"CodeUnitOwnerName={self._protected_TFCPS_Tools_General.get_codeunit_owner_name(self.get_codeunit_file())}", "--build-arg", f"CodeUnitOwnerEMailAddress={self._protected_TFCPS_Tools_General.get_codeunit_owner_emailaddress(self.get_codeunit_file())}"]
        custom_arguments:dict[str,str]={}#TODO must be setable from outside
        if custom_arguments is not None:
            for custom_argument_key, custom_argument_value in custom_arguments.items():
                args.append("--build-arg")
                args.append(f"{custom_argument_key}={custom_argument_value}")
        args = args+["--tag", f"{codeunitname_lower}:latest", "--tag", f"{codeunitname_lower}:{codeunitversion}", "--file", f"{codeunitname}/Dockerfile"]
        if not use_cache:
            args.append("--no-cache")
        args.append(".")
        codeunit_content_folder = os.path.join(codeunit_folder)
        self._protected_sc.run_program_argsasarray("docker", args, codeunit_content_folder, print_errors_as_information=True)
        artifacts_folder = GeneralUtilities.resolve_relative_path("Other/Artifacts", codeunit_folder)
        app_artifacts_folder = os.path.join(artifacts_folder, "BuildResult_OCIImage")
        GeneralUtilities.ensure_directory_does_not_exist(app_artifacts_folder)
        GeneralUtilities.ensure_directory_exists(app_artifacts_folder)
        self._protected_sc.run_program_argsasarray("docker", ["save", "--output", f"{codeunitname}_v{codeunitversion}.tar", f"{codeunitname_lower}:{codeunitversion}"], app_artifacts_folder, print_errors_as_information=True)
        self.copy_source_files_to_output_directory()
        self.__generate_sbom_for_docker_image()


    @GeneralUtilities.check_arguments
    def __generate_sbom_for_docker_image(self) -> None:
        
        codeunitname=self.get_codeunit_name()
        codeunit_folder =self.get_codeunit_folder()
        artifacts_folder = GeneralUtilities.resolve_relative_path("Other/Artifacts", codeunit_folder)
        codeunitname_lower = codeunitname.lower()
        sbom_folder = os.path.join(artifacts_folder, "BOM")
        codeunitversion = self._protected_TFCPS_Tools_General.get_version_of_codeunit(self.get_codeunit_file())
        GeneralUtilities.ensure_directory_exists(sbom_folder)
        self._protected_sc.run_program_argsasarray("docker", ["sbom", "--format", "cyclonedx", f"{codeunitname_lower}:{codeunitversion}", "--output", f"{codeunitname}.{codeunitversion}.sbom.xml"], sbom_folder, print_errors_as_information=True)
        self._protected_sc.format_xml_file(sbom_folder+f"/{codeunitname}.{codeunitversion}.sbom.xml")
 
    @GeneralUtilities.check_arguments
    def linting_implementation(self,additional_arguments:dict=None) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def do_common_tasks_implementation(self,additional_arguments:dict=None) -> None:
        pass#TODO

    @GeneralUtilities.check_arguments
    def generate_reference_implementation(self,additional_arguments:dict=None) -> None:
        pass#nothing to do

    @GeneralUtilities.check_arguments
    def update_dependencies_implementation(self,additional_arguments:dict=None) -> None:
        pass#TODO
    
    @GeneralUtilities.check_arguments
    def run_testcases_implementation(self,additional_arguments:dict=None) -> None:
        pass#TODO

class TFCPS_CodeUnitSpecific_Python_CLI:

    @staticmethod
    def parse(file:str,args:list[str])->TFCPS_CodeUnitSpecific_Docker_Functions:
        parser=TFCPS_CodeUnitSpecific_Base_CLI.get_base_parser()
        #add custom parameter if desired
        args=parser.parse_args()
        result:TFCPS_CodeUnitSpecific_Docker_Functions=TFCPS_CodeUnitSpecific_Docker_Functions(file,LogLevel(int(args.verbosity)),args.targetenvironmenttype,args.additionalargumentsfile)
        return result
