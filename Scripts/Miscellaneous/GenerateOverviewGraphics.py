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
copyfile(global_template_file,generator.core.output)

