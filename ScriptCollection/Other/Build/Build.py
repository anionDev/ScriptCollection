from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.GeneralUtilities import GeneralUtilities
from pathlib import Path
import os


class ScriptCollectionCore2:

    self2: ScriptCollectionCore = ScriptCollectionCore()

    def standardized_tasks_build_for_python_project_in_common_project_structure(self, build_file: str, setuppy_file: str):
        setuppy_file_folder = os.path.dirname(setuppy_file)
        setuppy_file_filename = os.path.basename(setuppy_file)
        repository_folder: str = str(Path(os.path.dirname(build_file)).parent.parent.parent.absolute())
        codeunitname: str = Path(os.path.dirname(build_file)).parent.parent.name
        self.self2.run_program("git", "clean -dfx", repository_folder)
        target_directory = os.path.join(repository_folder, codeunitname, "Other", "Build", "BuildArtifact")
        GeneralUtilities.ensure_directory_does_not_exist(target_directory)
        GeneralUtilities.ensure_directory_exists(target_directory)
        self.self2.run_program("python", f"{setuppy_file_filename} bdist_wheel --dist-dir {target_directory}", setuppy_file_folder)


def build():
    ScriptCollectionCore2().standardized_tasks_build_for_python_project_in_common_project_structure(
        __file__,        os.path.join(str(Path(os.path.dirname(__file__)).parent.parent.parent.absolute()), "Setup.py"))


if __name__ == "__main__":
    build()
