"""
Tested on: Windows
This script requires that the command 'qemu-img' is available on your system.
This program comes with absolutely no warranty.
"""
import argparse
import shutil
import os
import sys
import io
from Utilities import *

parser = argparse.ArgumentParser(description='Creates a new virtual-machine as vmdk-file')
parser.add_argument('name', type=str,help='Name of virtual machine')
parser.add_argument('outputfolder',type=str,help='Folder where the virtual machine should be saved')
parser.add_argument('--memsize', help='RAM-size in MB', default="4096")
parser.add_argument('--disksize', help='disk-size in GB', default="20")
parser.add_argument('--guestOS', help='Type of guest-vm. Example: debian10-64', default="debian10-64")
parser.add_argument('--coresPerSocket', default="2")
args = parser.parse_args()

this_file=os.path.realpath(__file__)
this_folder=os.path.dirname(this_file)
helper_folder=os.path.join(this_folder,"CreateVirtualMachineHelper")
template_vmx=os.path.join(helper_folder,"Template.vmx")
outputfolder=resolve_relative_path_from_current_working_directory(args.outputfolder)
vmx_file=args.name+".vmx"
vmx_file_with_path=os.path.join(outputfolder,vmx_file)

def replace_underscore_in_string(s:str,replace_from:str, replace_to:str):
    return s.replace("__"+replace_from+"__",replace_to)

ensure_directory_exists(outputfolder)
ensure_file_exists(vmx_file_with_path)
diskname=args.name+"Disk"

with io.open(template_vmx, 'r', encoding="utf-8") as template_file:
    vmx_content=template_file.read()
    vmx_content=replace_underscore_in_string(vmx_content,"name", args.name)
    vmx_content=replace_underscore_in_string(vmx_content,"coresPerSocket", args.coresPerSocket)
    vmx_content=replace_underscore_in_string(vmx_content,"memsize", args.memsize)
    vmx_content=replace_underscore_in_string(vmx_content,"guestOS", args.guestOS)
    vmx_content=replace_underscore_in_string(vmx_content,"diskname", diskname)
    with io.open(vmx_file_with_path, 'w+', encoding="utf-8") as target_file:
        target_file.write(vmx_content)

execute("qemu-img", f"create -f vmdk {diskname}.vmdk {args.disksize}G", outputfolder)

