import os
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..SCLog import  LogLevel
from .TFCPS_CodeUnit_BuildCodeUnit import TFCPS_CodeUnit_BuildCodeUnit
from .TFCPS_Tools_General import TFCPS_Tools_General

class TFCPS_CodeUnit_BuildCodeUnits:
    repository:str=None
    tFCPS_Other:TFCPS_Tools_General=None 
    sc:ScriptCollectionCore=None
    target_environment_type:str=None
    additionalargumentsfile:str=None
    __use_cache:bool
    __is_pre_merge:bool

    def __init__(self,repository:str,loglevel:LogLevel,target_environment_type:str,additionalargumentsfile:str,use_cache:bool,is_pre_merge:bool):
        self.sc=ScriptCollectionCore()
        self.sc.log.loglevel=loglevel
        self.__use_cache=use_cache
        self.sc.assert_is_git_repository(repository)
        self.repository=repository
        self.tFCPS_Other:TFCPS_Tools_General=TFCPS_Tools_General(self.sc)
        allowed_target_environment_types=["Development","QualityCheck","Productive"]
        GeneralUtilities.assert_condition(target_environment_type in allowed_target_environment_types,"Unknown target-environment-type. Allowed values are: "+", ".join(allowed_target_environment_types))
        self.target_environment_type=target_environment_type
        self.additionalargumentsfile=additionalargumentsfile
        self.__is_pre_merge=is_pre_merge

    @GeneralUtilities.check_arguments
    def build_codeunits(self) -> None:
        self.sc.log.log(GeneralUtilities.get_line())
        self.sc.log.log(f"Start building codeunits. (Target environment-type: {self.target_environment_type})")
        changelog_file=os.path.join(self.repository,"Other","Resources","Changelog",f"v{self.tFCPS_Other.get_version_of_project(self.repository)}.md")
        GeneralUtilities.assert_file_exists(changelog_file,f"Changelogfile \"{changelog_file}\" does not exist. Try to create it for example using \"sccreatechangelogentry -m ...\".") 
        if  os.path.isfile( os.path.join(self.repository,"Other","Scripts","PrepareBuildCodeunits.py")):
            arguments:str=f"--targetenvironmenttype {self.target_environment_type} --additionalargumentsfile {self.additionalargumentsfile} --verbosity {int(self.sc.log.loglevel)}"
            if not self.__use_cache:
                arguments=f"{arguments} --nocache"
                if self.sc.git_repository_has_uncommitted_changes(self.repository):
                    self.sc.log.log("No-cache-option can not be applied because there are uncommited changes in the repository.",LogLevel.Warning)
                else:
                    self.sc.run_program("git","clean -dfx",self.repository)
            self.sc.log.log("Prepare build codeunits...")
            self.sc.run_program("python", f"PrepareBuildCodeunits.py {arguments}", os.path.join(self.repository,"Other","Scripts"),print_live_output=True)
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        self.sc.log.log("Codeunits will be built in the following order:")
        for codeunit_name in codeunits:
            self.sc.log.log("  - "+codeunit_name)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel,self.target_environment_type,self.additionalargumentsfile,self.use_cache())
            self.sc.log.log(GeneralUtilities.get_line())
            tFCPS_CodeUnit_BuildCodeUnit.build_codeunit()
        self.sc.log.log(GeneralUtilities.get_line())
        self.sc.log.log("Finished building codeunits.")
        self.sc.log.log(GeneralUtilities.get_line())


    @GeneralUtilities.check_arguments
    def use_cache(self) -> bool:
        return self.__use_cache


    @GeneralUtilities.check_arguments
    def is_pre_merge(self) -> bool:
        return self.__is_pre_merge

    @GeneralUtilities.check_arguments
    def update_dependencies(self) -> None:
        self.update_year_in_license_file()

        #TODO update project-wide-dependencies here
        codeunits:list[str]=self.tFCPS_Other.get_codeunits(self.repository)
        for codeunit_name in codeunits:
            tFCPS_CodeUnit_BuildCodeUnit:TFCPS_CodeUnit_BuildCodeUnit = TFCPS_CodeUnit_BuildCodeUnit(os.path.join(self.repository,codeunit_name),self.sc.log.loglevel,self.target_environment_type,self.additionalargumentsfile,self.use_cache())
            tFCPS_CodeUnit_BuildCodeUnit.update_dependencies() 

    @GeneralUtilities.check_arguments
    def update_year_in_license_file(self) -> None:
        self.sc.update_year_in_first_line_of_file(os.path.join(self.repository, "License.txt"))
