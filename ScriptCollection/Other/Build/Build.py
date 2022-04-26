from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from pathlib import Path
import os


def build():
    ScriptCollectionCore().standardized_tasks_build_for_python_project_in_common_project_structure(
        __file__, os.path.join(str(Path(os.path.dirname(__file__)).parent.parent.parent.absolute()), "Setup.py"))


if __name__ == "__main__":
    build()
