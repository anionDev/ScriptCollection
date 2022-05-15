from pathlib import Path
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore


def build():
    ScriptCollectionCore().standardized_tasks_build_for_python_project_in_common_project_structure(Path(__file__).absolute())


if __name__ == "__main__":
    build()
