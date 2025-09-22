import sys
from pathlib import Path
from ScriptCollection.TasksForCommonProjectStructure import TasksForCommonProjectStructure


def update_dependencies():
    TasksForCommonProjectStructure(sys.argv).update_dependencies_of_typical_python_codeunit(str(Path(__file__).absolute()) )


if __name__ == "__main__":
    update_dependencies()
