"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
from Utilities import *
from collections.abc import Iterable
from shutil import copyfile
import json

parser = argparse.ArgumentParser(description='Generates overviews for example for it-system-landscapes.')
parser.add_argument('configuration', help='File which contains the generation-parameter')
args = parser.parse_args()

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
else:
    write_message_to_stderr(configuration_file + " can not be found")
    sys.exit(1)
this_folder=os.path.abspath(os.path.dirname(__file__))
with open(generator.core.datasource, encoding='utf8') as datasource_file_object:
    generator.data = json.load(datasource_file_object)
templates_folder=os.path.join(this_folder,"GenerateOverviewGraphicsHelper","Templates")
global_template_file=os.path.join(templates_folder,"Global.svg.template")
keyvaluepairlist_template_file=os.path.join(templates_folder,"KeyValuePairListTemplate.svg.template")
list_template_file=os.path.join(templates_folder,"List.svg.template")
from pprint import pprint

def calculate_overview():
    with open(global_template_file, encoding='utf8') as global_template_file_object:
        result=global_template_file_object.read()
    result=result.replace("__Title__", f"{generator.metadata.title} ({generator.metadata.version})")
    #todo
    return result
with open(generator.core.output, "r+", encoding='utf8') as result_file_object:
    result_file_object.write(calculate_overview())

