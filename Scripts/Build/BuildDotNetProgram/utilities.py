import subprocess
import os

def execute(command:str, arguments:str, workingdirectory:str,timeout=120):
    if not os.path.isabs(workingdirectory):
        workingdirectory=os.path.abspath(workingdirectory)
    print("Start "+workingdirectory +" "+command + " " + arguments)
    exit_code = subprocess.call(command + " " + arguments, cwd=workingdirectory, timeout=timeout)
    print("Finished "+workingdirectory +" "+command + " " + arguments )
    print("Exitcode: "+str(exit_code))
    return exit_code
