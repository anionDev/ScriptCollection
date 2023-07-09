import sys
from pathlib import Path
from ScriptCollection.TasksForCommonProjectStructure import TasksForCommonProjectStructure

def build():
    script_file = str(Path(__file__).absolute())
    t = TasksForCommonProjectStructure()
    verbosity = 1
    commandline_arguments: str = sys.argv
    t.standardized_tasks_build_for_python_codeunit(script_file, verbosity, "QualityCheck", commandline_arguments)


if __name__ == "__main__":
    build()
