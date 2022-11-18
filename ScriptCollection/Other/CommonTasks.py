import sys
import os
from pathlib import Path
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.TasksForCommonProjectStructure import TasksForCommonProjectStructure


def common_tasks():
    file = str(Path(__file__).absolute())
    folder_of_current_file = os.path.dirname(file)
    sc = ScriptCollectionCore()
    cmd_args = sys.argv
    tfcps = TasksForCommonProjectStructure()
    verbosity = tfcps.get_verbosity_from_commandline_arguments(cmd_args, 1)
    buildenvironment = tfcps.get_targetenvironmenttype_from_commandline_arguments(cmd_args, "QualityCheck")
    additional_arguments_file = tfcps.get_additionalargumentsfile_from_commandline_arguments(cmd_args, None)
    version = sc.get_semver_version_from_gitversion(GeneralUtilities.resolve_relative_path("../..", os.path.dirname(file)))
    sc.replace_version_in_pyproject_file(GeneralUtilities.resolve_relative_path("../pyproject.toml", folder_of_current_file), version)
    sc.replace_version_in_python_file(GeneralUtilities.resolve_relative_path("../ScriptCollection/ScriptCollectionCore.py", folder_of_current_file), version)
    tfcps.standardized_tasks_do_common_tasks(file, verbosity, buildenvironment, True, additional_arguments_file, sys.argv)


if __name__ == "__main__":
    common_tasks()
