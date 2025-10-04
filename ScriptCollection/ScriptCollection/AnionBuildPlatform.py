import argparse
import os
from .SCLog import LogLevel
from .GeneralUtilities import GeneralUtilities
from .ScriptCollectionCore import ScriptCollectionCore

class AnionBuildPlatformConfiguration:
    build_repositories_folder:str
    project_to_build:str
    additional_arguments_file:str
    verbosity:LogLevel
    source_branch:str

    def __init__(self,
                 build_repositories_folder:str,
                 project_to_build:str,
                 additional_arguments_file:str,
                 verbosity:LogLevel,
                 source_branch:str):
        self.build_repositories_folder=build_repositories_folder
        self.project_to_build=project_to_build
        self.additional_arguments_file=additional_arguments_file
        self.verbosity=verbosity
        self.source_branch=source_branch

class AnionBuildPlatform:

    __configuration: AnionBuildPlatformConfiguration
    __sc:ScriptCollectionCore

    def __init__(self, configuration: AnionBuildPlatformConfiguration):
        self.__configuration = configuration
        self.__sc = ScriptCollectionCore()
        self.__sc.log.loglevel=configuration.verbosity

    def run(self) -> None:
        build_repo_folder:str=os.path.join(self.__configuration.build_repositories_folder,self.__configuration.project_to_build+"Build")
        self.__sc.assert_is_git_repository(build_repo_folder)
        scripts_folder:str=os.path.join(build_repo_folder,"Scripts","CreateRelease")
        self.__sc.run_program("python",f"MergeToMain",scripts_folder)
        self.__sc.run_program("python","MergeToStable",scripts_folder)

class TFCPS_AnionBuildPlatform_CLI:

    @staticmethod
    def get_with_overwritable_defaults(default_project_to_build:str=None,default_loglevel:LogLevel=None,default_additionalargumentsfile:str=None,default_build_repositories_folder:str=None,default_source_branch:str=None)->AnionBuildPlatform:
        parser = argparse.ArgumentParser()
        verbosity_values = ", ".join(f"{lvl.value}={lvl.name}" for lvl in LogLevel)
        parser.add_argument('-r', '--buildrepositoriesfolder', required=False,default=None)
        parser.add_argument('-p', '--projecttobuild', required=False, default=None)
        parser.add_argument('-a', '--additionalargumentsfile', required=False, default=None)
        parser.add_argument('-v', '--verbosity', required=False, default=3, help=f"Sets the loglevel. Possible values: {verbosity_values}")
        parser.add_argument('-s', '--sourcebranch', required=False, default="other/next-release")
        args=parser.parse_args()

        if args.projecttobuild is not None: 
            default_project_to_build=args.projecttobuild

        if args.buildrepositoriesfolder is not None:
            default_build_repositories_folder=args.buildrepositoriesfolder

        if default_project_to_build is None and default_build_repositories_folder is None:
            current_folder=os.getcwd()
            if os.path.basename(current_folder).endswith("Build"):
                default_build_repositories_folder=os.path.dirname(current_folder)
                default_project_to_build=os.path.basename(current_folder)[:-len("Build")]
        GeneralUtilities.assert_not_null(default_project_to_build,"projecttobuild is not set")
        GeneralUtilities.assert_not_null(default_build_repositories_folder,"buildrepositoriesfolder is not set")

        if args.verbosity is not None:
            default_loglevel=LogLevel(int( args.verbosity))
        GeneralUtilities.assert_not_null(default_loglevel,"verbosity is not set")

        if args.additionalargumentsfile is not None:
            default_additionalargumentsfile=args.additionalargumentsfile

        if args.sourcebranch is not None:
            default_source_branch=args.sourcebranch
        GeneralUtilities.assert_not_null(default_build_repositories_folder,"sourcebranch is not set")

        config:AnionBuildPlatformConfiguration=AnionBuildPlatformConfiguration(default_build_repositories_folder,default_project_to_build,default_additionalargumentsfile,default_loglevel,default_source_branch)
        tFCPS_MergeToMain:AnionBuildPlatform=AnionBuildPlatform(config)
        return tFCPS_MergeToMain
