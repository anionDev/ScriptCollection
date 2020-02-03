import pkg_resources
import subprocess
subprocess.call('pip install --upgrade ' + ' '.join([w.project_name for w in pkg_resources.working_set]))