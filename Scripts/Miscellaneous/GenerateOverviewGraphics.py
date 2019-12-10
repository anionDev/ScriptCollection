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

templatescache=dict()

def load_template(template_name):
    with open(os.path.join(objecttemplates_folder,template_name+".svg"), encoding='utf8') as template_file_object:
        templatescache[template_name]=template_file_object.read()

def get_template(template_name):
    if not template_name in templatescache:
        load_template(template_name)
    return templatescache[template_name]

def replace_variable(string:str, variable:str, value):
    if (string is None) or (variable is None) or (value is None):
        return string
    key=f"__{variable}__"
    if(key in string):
        return string.replace(key, str(value))
    else:
        return string
def str_to_svg(value, path_to_value:str):
    result=get_template("String")
    result=replace_variable(result,"Value",value)    
    return result

def list_to_svg(value, path_to_value:str):
    result=get_template("List")
    result=replace_variable(result,"Items",value)    
    return result

def bool_to_svg(value, path_to_value:str):
    result=get_template("Bool")
    result=replace_variable(result,"Value",value)    
    return result

def int_to_svg(value, path_to_value:str):
    result=get_template("Int")
    result=replace_variable(result,"Value",value)    
    return result

def get_null_value_svg(path_to_value:str):
    result=get_template("Null")
    return result
import pprint 
def dictionary_to_svg(value, path_to_value:str):
    result=get_template("Dictionary")
    result=replace_variable(result,"Items",value)    
    return result

def process_str(value, path_to_value:str):
    return str_to_svg(value, path_to_value)

def process_list(value, path_to_value:str):
    items=[]
    for item in value:
        items.append(process_object(item, path_to_value))
    return list_to_svg(items, path_to_value)

def process_bool(value, path_to_value:str):
    return bool_to_svg(value, path_to_value)

def process_int(value, path_to_value:str):
    return int_to_svg(value, path_to_value)

def process_null(path_to_value:str):
    return get_null_value_svg(path_to_value)

def process_dict(value, path_to_value:str):
    items=[]
    for item in value:
        items.append([item,process_object(value[item], item)])
    return dictionary_to_svg(items, path_to_value)

def process_object(obj, path_to_value):
    result=""
    print(path_to_value)
    try:
        if(obj is None):
            return process_null(path_to_value)
        elif(type(obj) is str):
            return process_str(obj, path_to_value)
        elif(isinstance(obj, list)):
            return process_list(obj, path_to_value)
        elif(isinstance(obj, bool)):
            return process_bool(obj, path_to_value)
        elif(isinstance(obj, int)):
            return process_int(obj, path_to_value)
        elif(isinstance(obj, dict)):
            return process_dict(obj, path_to_value)
        else:
            raise Exception("Not processable type: " + str(type(obj)))
        result=replace_variable(result,"Name","todoGetName")    
        return result
    except Exception:
        write_message_to_stderr(f"Can not process {path_to_value}")
        traceback.print_exc()
        exit_code=2

def calculate_overview():
    with open(global_template_file, encoding='utf8') as global_template_file_object:
        result=global_template_file_object.read()
    result=replace_variable(result,"__Title__", f"{generator.metadata.title} ({generator.metadata.version})")
    result=replace_variable(result,"__Content__", process_object(generator.data,""))
    return result

generator=type('', (), {})()
generator.core=type('', (), {})()
generator.metadata=type('', (), {})()
generator.gui=type('', (), {})()
generator.gui.icons=[]
generator.gui.formatting=[]
configuration_file=resolve_relative_path_from_current_working_directory(args.configuration)
if(os.path.isfile(configuration_file)):
    exec(open(configuration_file).read())
    this_folder=os.path.abspath(os.path.dirname(__file__))
    templates_folder=os.path.join(this_folder,"GenerateOverviewGraphicsHelper","Templates")
    objecttemplates_folder=os.path.join(templates_folder,"ObjectTemplates")
    with open(generator.core.datasource, encoding='utf8') as datasource_file_object:
        generator.data = json.load(datasource_file_object)
    global_template_file=os.path.join(templates_folder,"Global.svg")
    with open(generator.core.output, "r+", encoding='utf8') as result_file_object:
        result=calculate_overview()
        print(result)
        result_file_object.write(result)
else:
    write_message_to_stderr(configuration_file + " can not be found")
    exit_code=1
sys.exit(exit_code)

