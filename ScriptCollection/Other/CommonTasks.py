import sys
import os
from pathlib import Path
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.TFCPS_CodeUnitSpecific_Python import TFCPS_CodeUnitSpecific_Python


def common_tasks():
    file = str(Path(__file__).absolute())
    folder_of_current_file = os.path.dirname(file)
    sc = ScriptCollectionCore()
    codeunitname = os.path.basename(GeneralUtilities.resolve_relative_path("..", os.path.dirname(file)))
    codeunit_version = sc.get_semver_version_from_gitversion(GeneralUtilities.resolve_relative_path("../..", os.path.dirname(file)))  # Should always be the same as the project-version
    sc.replace_version_in_ini_file(GeneralUtilities.resolve_relative_path("../setup.cfg", folder_of_current_file), codeunit_version)
    sc.replace_version_in_python_file(GeneralUtilities.resolve_relative_path(f"../{codeunitname}/{codeunitname}Core.py", folder_of_current_file), codeunit_version)
    tf:TFCPS_CodeUnitSpecific_Python=TFCPS_CodeUnitSpecific_Python(__file__)
    tf.standardized_tasks_do_common_tasks(sys.argv)


if __name__ == "__main__":
    common_tasks()
