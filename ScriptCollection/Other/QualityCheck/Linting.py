from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ScriptCollection.GeneralUtilities import GeneralUtilities
from pathlib import Path
import os

class ScriptCollectionCore2:

    self2:ScriptCollectionCore=ScriptCollectionCore()
    def standardized_tasks_linting_for_python_project_in_common_project_structure(self,linting_script_file):
        repository_folder: str=str(Path(os.path.dirname(linting_script_file)).parent.parent.parent.absolute())
        codeunitname: str=Path(os.path.dirname(linting_script_file)).parent.parent.name
        errors_found = False
        GeneralUtilities.write_message_to_stdout(f"Check for linting-issues in codeunit {codeunitname}")
        for file in GeneralUtilities.get_all_files_of_folder(os.path.join(repository_folder, codeunitname)):
            #TODO ignore files in the "<repository>/<codeunit>/other"-folder
            relative_file_path_in_repository = os.path.relpath(file, repository_folder)
            if file.endswith(".py") and os.path.getsize(file) > 0 and not self.self2.file_is_git_ignored(relative_file_path_in_repository, repository_folder):
                GeneralUtilities.write_message_to_stdout(f"Check for linting-issues in {os.path.relpath(file,os.path.join(repository_folder,codeunitname))}")
                linting_result = self.self2.python_file_has_errors(file, repository_folder)
                if (linting_result[0]):
                    errors_found = True
                    for error in linting_result[1]:
                        GeneralUtilities.write_message_to_stderr(error)
        if errors_found:
            raise Exception("Linting-issues occurred")

def linting():
    ScriptCollectionCore2().standardized_tasks_linting_for_python_project_in_common_project_structure(__file__)


if __name__ == "__main__":
    linting()
