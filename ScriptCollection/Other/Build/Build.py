import sys
from pathlib import Path
from ScriptCollection.TasksForCommonProjectStructure import TasksForCommonProjectStructure

def build():
    script_file = str(Path(__file__).absolute())
    t = TasksForCommonProjectStructure( sys.argv)
    t.standardized_tasks_build_for_python_codeunit(script_file)


if __name__ == "__main__":
    build()
