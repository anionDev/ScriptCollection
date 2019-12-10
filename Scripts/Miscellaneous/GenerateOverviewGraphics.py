"""
Tested on: Windows
This program comes with absolutely no warranty.
"""
import argparse
from Utilities import *
from collections.abc import Iterable

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
def isArray(obj):
    return isinstance(obj, list) and not isinstance(s, obj)
import json
from pprint import pprint
with open(generator.core.datasource) as f:
    generator.data = json.load(f)
