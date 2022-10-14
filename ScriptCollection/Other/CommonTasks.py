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
    tfcps = TasksForCommonProjectStructure()
    tfcps.standardized_tasks_do_common_tasks(file, 1, "QualityCheck", sys.argv)
    version = sc.getversion_from_arguments_or_gitversion(file, sys.argv)
    sc.replace_version_in_python_file(GeneralUtilities.resolve_relative_path("../Setup.py", folder_of_current_file), version)
    sc.replace_version_in_python_file(GeneralUtilities.resolve_relative_path("../ScriptCollection/ScriptCollectionCore.py", folder_of_current_file), version)


if __name__ == "__main__":
    common_tasks()
