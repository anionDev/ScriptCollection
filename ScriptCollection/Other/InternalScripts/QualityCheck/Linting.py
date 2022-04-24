import os
from pathlib import Path
from ScriptCollection.GeneralUtilities import GeneralUtilities
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore


def python_file_has_errors(self:ScriptCollectionCore, file:str,working_directory:str, treat_warnings_as_errors: bool = True) -> tuple[bool, list[str]]:
    errors = list()
    filename = os.path.relpath(file,working_directory)
    if treat_warnings_as_errors:
        errorsonly_argument = ""
    else:
        errorsonly_argument = " --errors-only"
    (exit_code, stdout, stderr, _) = self.start_program_synchronously("pylint", filename+errorsonly_argument, working_directory, throw_exception_if_exitcode_is_not_zero=False, prevent_using_epew=True)
    if(exit_code != 0):
        errors.append(f"Linting-issues of {file}:")
        errors.append(f"Pylint-exitcode: {exit_code}")
        for line in GeneralUtilities.string_to_lines(stdout):
            errors.append(line)
        for line in GeneralUtilities.string_to_lines(stderr):
            errors.append(line)
        return (True, errors)

    return (False, errors)

def linting_for_python_project_in_common_project_structure(self:ScriptCollectionCore,repository_folder:str,codeunitname:str):
    errors_found = False
    GeneralUtilities.write_message_to_stdout(f"Check for linting-issues in codeunit {codeunitname}")
    for file in GeneralUtilities.get_all_files_of_folder(os.path.join( repository_folder,codeunitname)):
        relative_file_path_in_repository = os.path.relpath(file, repository_folder)
        if file.endswith(".py") and os.path.getsize(file) > 0 and not self.file_is_git_ignored(relative_file_path_in_repository, repository_folder):
            GeneralUtilities.write_message_to_stdout(f"Check for linting-issues in {os.path.relpath(file,os.path.join(repository_folder,codeunitname))}")
            linting_result = python_file_has_errors(self, file,repository_folder)
            if (linting_result[0]):
                errors_found = True
                for error in linting_result[1]:
                    GeneralUtilities.write_message_to_stderr(error)
    if errors_found:
        raise Exception("Linting-issues occurred")

def linting():
    linting_for_python_project_in_common_project_structure(ScriptCollectionCore(),
        str(Path(os.path.dirname(__file__)).parent.parent.parent.parent.absolute()),"ScriptCollection")

if __name__=="__main__":
    linting()
