

def execute_command_in_vm_and_expect_exitcode_zero(name_of_vm:str, directory:str, command:str):
    exitcode=execute_command_in_vm(name_of_vm,directory,command)
    if(exitcode!=0):
        raise Exception(f"{name_of_vm}: '{directory}>{command}' had exitcode {str(exitcode)}"):
def execute_command_in_vm(name_of_vm:str, directory:str, command:str)
    if(not vm_is_running(name_of_vm):
        raise Exception(f"{name_of_vm}: Can not execute '{directory}>{command}' because the vm is not running"):
        
    pass#todo execute and return exit-code

def vm_is_running(name_of_vm:str):
    pass#todo
def vm_is_shutdown(name_of_vm:str):
    pass#todo
def vm_is_suspended(name_of_vm:str):
    pass#todo
def ensure_vm_is_running(name_of_vm:str):
 if(vm_is_shutdown(name_of_vm)):
     pass#todo
 if(vm_is_suspended(name_of_vm)):
     pass#todo
def ensure_vm_is_shutdown(name_of_vm:str):
 if(vm_is_running(name_of_vm)):
     pass#todo
 if(vm_is_suspended(name_of_vm)):
     pass#todo
def ensure_vm_is_suspended(name_of_vm:str):
 if(vm_is_shutdown(name_of_vm)):
     pass#todo
 if(vm_is_running(name_of_vm)):
     pass#todo


