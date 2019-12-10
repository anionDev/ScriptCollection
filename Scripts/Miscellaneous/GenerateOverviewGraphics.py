"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
from Utilities import *
from collections.abc import Iterable
from shutil import copyfile
import json
import traceback

exit_code=0
parser = argparse.ArgumentParser(description='Generates overviews for example for it-system-landscapes.')
parser.add_argument('configuration', help='File which contains the generation-parameter')
args = parser.parse_args()

def process_str(value):
    return "convertedstr-"+value

def process_list(value):
    result="convertedlist-["
    for item in value:
        result=result+process_object(item)+","
    return result+"]"

def process_bool(value):
    return "convertedbool-"+str(value)

def process_int(value):
    return "convertedint-"+str(value)

def process_null():
    return "null"

def process_dict(value):
    result="converteddiict-{"
    for item in value:
        result=result+"\n"+item+":"+process_object(value[item])+","
    return result+"}"

def process_object(obj):
    try:
        if(obj is None):
            return process_null()
        elif(type(obj) is str):
            return process_str(obj)
        elif(isinstance(obj, list)):
            return process_list(obj)
        elif(isinstance(obj, bool)):
            return process_bool(obj)
        elif(isinstance(obj, int)):
            return process_int(obj)
        elif(isinstance(obj, dict)):
            return process_dict(obj)
        else:
            raise Exception("Not processable type: "+str(type(obj)))
    except Exception:
        write_message_to_stderr(f"Can not process {obj}")
        traceback.print_exc()
        exit_code=2

def get_data_as_svg(data):
    result="\n"
    for obj in data:
        print("---------------------------------------")
        print("start editing "+obj)
        try:
            cur=data[obj]
            result=result+"\n"+obj+"->"+process_object(cur)
        except Exception:
            write_message_to_stderr(f"Can not process {obj}")
            traceback.print_exc()
            exit_code=2
        print("finished editing "+obj)
        print("---------------------------------------")
    return result+"\n"

def calculate_overview():
    with open(global_template_file, encoding='utf8') as global_template_file_object:
        result=global_template_file_object.read()
    result=result.replace("__Title__", f"{generator.metadata.title} ({generator.metadata.version})")
    result=result.replace("__Content__", process_object(generator.data))
    return result

generator=type('', (), {})()
generator.core=type('', (), {})()
generator.metadata=type('', (), {})()
generator.gui=type('', (), {})()
generator.gui.icons=[]
generator.gui.formatting=[]

configuration_file=resolve_relative_path_from_current_working_directory(args.configuration)
print(configuration_file)
if(os.path.isfile(configuration_file)):
    exec(open(configuration_file).read())
    this_folder=os.path.abspath(os.path.dirname(__file__))
    with open(generator.core.datasource, encoding='utf8') as datasource_file_object:
        generator.data = json.load(datasource_file_object)
    templates_folder=os.path.join(this_folder,"GenerateOverviewGraphicsHelper","Templates")
    global_template_file=os.path.join(templates_folder,"Global.svg.template")
    keyvaluepairlist_template_file=os.path.join(templates_folder,"KeyValuePairListTemplate.svg.template")
    list_template_file=os.path.join(templates_folder,"List.svg.template")
    with open(generator.core.output, "r+", encoding='utf8') as result_file_object:
        result=calculate_overview()
        print(result)
        result_file_object.write(result)
else:
    write_message_to_stderr(configuration_file + " can not be found")
    exit_code=1
sys.exit(exit_code)

