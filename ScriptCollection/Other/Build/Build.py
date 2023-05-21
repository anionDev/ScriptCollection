import sys
from pathlib import Path
from ScriptCollection.TasksForCommonProjectStructure import TasksForCommonProjectStructure


def ensure_development_requirements_for_python_codeunit_are_installed(t: TasksForCommonProjectStructure, script_file: str, verbosity: int, commandline_arguments: list[str]):
    verbosity = t.get_verbosity_from_commandline_arguments(commandline_arguments, verbosity)
    # TODO


def build():
    script_file = str(Path(__file__).absolute())
    t = TasksForCommonProjectStructure()
    verbosity = 1
    commandline_arguments: str = sys.argv
    ensure_development_requirements_for_python_codeunit_are_installed(t, script_file, verbosity, commandline_arguments)
    t.standardized_tasks_build_for_python_codeunit(script_file, verbosity, "QualityCheck", commandline_arguments)


if __name__ == "__main__":
    build()
