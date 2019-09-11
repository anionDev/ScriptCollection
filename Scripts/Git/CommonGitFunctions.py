from Utilities import *

def repository_has_uncommitted_changes(repository_folder:str):
    pass#TODO
def get_current_commit_id(repository_folder:str):
    pass#TODO return the output of "git rev-parse --verify HEAD"

def commit(directory:str, message:str):
    execute("git","add -A", directory, 3600)
    execute("git","commit -m \""+message+"\"",directory)
