import filecmp
from distutils.dir_util import copy_tree
from functools import lru_cache
import keyboard
import re
import ntplib
import base64
import os
from shutil import copytree
from subprocess import Popen, PIPE, call
import hashlib
import send2trash
import time
import shutil
import ctypes
import io
import tempfile
from PyPDF2 import PdfFileMerger
import uuid
from pathlib import Path
import codecs
from shutil import copyfile
import sys
import xml.dom.minidom
from configparser import ConfigParser
import argparse
from os.path import abspath
import traceback
from os.path import isfile, join, isdir
from os import listdir
import datetime


version = "1.12.14"


# <Build>

# <CreateRelease>


def SCCreateRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    error_occurred = False
    prepare = configparser.getboolean('general', 'prepare')
    repository = get_buildscript_config_item(configparser, "general", "repository")
    if(git_repository_has_uncommitted_changes(repository)):
        write_message_to_stderr(f"'{repository}' contains uncommitted changes")
        return 1
    if prepare:
        devbranch = get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname')
        masterbranch = get_buildscript_config_item(configparser, 'prepare', 'masterbranchname')
        commitid = git_get_current_commit_id(repository, masterbranch)
        if(commitid == git_get_current_commit_id(repository, devbranch)):
            write_message_to_stderr(f"Can not prepare since the master-branch and the development-branch are on the same commit ({commitid})")
            return 1
        git_checkout(repository, devbranch)
        git_merge(repository, devbranch, masterbranch, False, False)

    try:

        if configparser.getboolean('general', 'createdotnetrelease') and not error_occurred:
            error_occurred = private_create_dotnet_release(configurationfile) != 0

        if configparser.getboolean('general', 'createpythonrelease') and not error_occurred:
            error_occurred = SCPythonCreateWheelRelease(configurationfile) != 0

    except Exception as exception:
        error_occurred = True
        write_exception_to_stderr(exception, "Error occurred while creating release")

    if error_occurred:
        if prepare:
            git_merge_abort(repository)
            git_checkout(repository, get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname'))
        write_message_to_stderr("Building wheel and running testcases was not successful")
        return 1
    else:
        if prepare:
            commit_id = git_commit(repository, "Merge branch '" + get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname')+"' into '"+get_buildscript_config_item(configparser, 'prepare', 'masterbranchname')+"'")
            repository_version = get_version_for_buildscripts(configparser)
            git_create_tag(repository, commit_id, get_buildscript_config_item(configparser, 'prepare', 'gittagprefix') + repository_version)
            git_merge(repository, get_buildscript_config_item(configparser, 'prepare', 'masterbranchname'), get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname'), True)
            if configparser.getboolean('other', 'exportrepository'):
                branch = get_buildscript_config_item(configparser, 'prepare', 'masterbranchname')
                git_push(repository, get_buildscript_config_item(configparser, 'other', 'exportrepositoryremotename'), branch, branch, False, True)
            git_commit(get_buildscript_config_item(configparser, 'other', 'releaserepository'), "Added "+get_buildscript_config_item(configparser, 'general', 'productname')+" "+get_buildscript_config_item(configparser, 'prepare', 'gittagprefix')+repository_version)
        write_message_to_stdout("Building wheel and running testcases was successful")
        return 0


def SCCreateRelease_cli():
    parser = argparse.ArgumentParser(description="""SCCreateRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCCreateRelease(args.configurationfile)

# </CreateRelease>

# <SCDotNetBuildExecutableAndRunTests>


def SCDotNetBuildExecutableAndRunTests(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('other', 'hastestproject'):
        SCDotNetRunTests(configurationfile)
    for runtime in get_buildscript_config_items(configparser, 'dotnet', 'runtimes'):
        SCDotNetBuild(_private_get_csprojfile_folder(configparser), _private_get_csprojfile_filename(configparser), _private_get_buildoutputdirectory(configparser, runtime), get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration'), runtime,
                      get_buildscript_config_item(configparser, 'dotnet', 'dotnetframework'), True, "normal",  get_buildscript_config_item(configparser, 'dotnet', 'filestosign'), get_buildscript_config_item(configparser, 'dotnet', 'snkfile'))
    publishdirectory = get_buildscript_config_item(configparser, 'dotnet', 'publishdirectory')
    ensure_directory_does_not_exist(publishdirectory)
    copy_tree(get_buildscript_config_item(configparser, 'dotnet', 'buildoutputdirectory'), publishdirectory)
    return 0


def SCDotNetBuildExecutableAndRunTests_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetBuildExecutableAndRunTests_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetBuildExecutableAndRunTests(args.configurationfile)

# </SCDotNetBuildExecutableAndRunTests>

# <SCDotNetCreateExecutableRelease>


def SCDotNetCreateExecutableRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    if configparser.getboolean('dotnet', 'updateversionsincsprojfile'):
        update_version_in_csproj_file(get_buildscript_config_item(configparser, 'dotnet', 'csprojfile'), repository_version)

    build_and_tests_were_successful = False
    try:
        exitcode = SCDotNetBuildExecutableAndRunTests(configurationfile)
        build_and_tests_were_successful = exitcode == 0
        if not build_and_tests_were_successful:
            write_exception_to_stderr("Building executable and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_and_tests_were_successful = False
        write_exception_to_stderr(exception, "Building executable and running testcases resulted in an error")

    if build_and_tests_were_successful:
        SCDotNetReference(configurationfile)
        return 0
    else:
        return 1


def SCDotNetCreateExecutableRelease_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetCreateExecutableRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetCreateExecutableRelease(args.configurationfile)

# </SCDotNetCreateExecutableRelease>

# <SCDotNetCreateNugetRelease>


def SCDotNetCreateNugetRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    if configparser.getboolean('dotnet', 'updateversionsincsprojfile'):
        update_version_in_csproj_file(get_buildscript_config_item(configparser, 'dotnet', 'csprojfile'), repository_version)

    build_and_tests_were_successful = False
    try:
        exitcode = SCDotNetBuildNugetAndRunTests(configurationfile)
        build_and_tests_were_successful = exitcode == 0
        if not build_and_tests_were_successful:
            write_exception_to_stderr("Building nuget and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_and_tests_were_successful = False
        write_exception_to_stderr(exception, "Building nuget and running testcases resulted in an error")

    if build_and_tests_were_successful:
        SCDotNetReference(configurationfile)
        SCDotNetReleaseNuget(configurationfile)
        return 0
    else:
        return 1


def SCDotNetCreateNugetRelease_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetCreateNugetRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetCreateNugetRelease(args.configurationfile)

# </SCDotNetCreateNugetRelease>

# <SCDotNetBuildNugetAndRunTests>


_private_nuget_template = r"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2011/10/nuspec.xsd">
  <metadata minClientVersion="2.12">
    <id>__productname__</id>
    <version>__version__</version>
    <title>__productname__</title>
    <authors>__author__</authors>
    <owners>__author__</owners>
    <requireLicenseAcceptance>true</requireLicenseAcceptance>
    <copyright>Copyright © __year__ by __author__</copyright>
    <description>__description__</description>
    <summary>__description__</summary>
    <license type="file">lib/__dotnetframework__/__productname__.License.txt</license>
    <dependencies>
      <group targetFramework="__dotnetframework__" />
    </dependencies>
  </metadata>
  <files>
    <file src="Binary/__productname__.dll" target="lib/__dotnetframework__" />
    <file src="Binary/__productname__.License.txt" target="lib/__dotnetframework__" />
  </files>
</package>"""


def SCDotNetBuildNugetAndRunTests(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('other', 'hastestproject'):
        SCDotNetRunTests(configurationfile)
    for runtime in get_buildscript_config_items(configparser, 'dotnet', 'runtimes'):
        SCDotNetBuild(_private_get_csprojfile_folder(configparser), _private_get_csprojfile_filename(configparser), _private_get_buildoutputdirectory(configparser, runtime), get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration'), runtime,
                      get_buildscript_config_item(configparser, 'dotnet', 'dotnetframework'), True, "normal",  get_buildscript_config_item(configparser, 'dotnet', 'filestosign'), get_buildscript_config_item(configparser, 'dotnet', 'snkfile'))
    publishdirectory = get_buildscript_config_item(configparser, 'dotnet', 'publishdirectory')
    publishdirectory_binary = publishdirectory+os.path.sep+"Binary"
    ensure_directory_does_not_exist(publishdirectory)
    ensure_directory_exists(publishdirectory_binary)
    copy_tree(get_buildscript_config_item(configparser, 'dotnet', 'buildoutputdirectory'), publishdirectory_binary)
    nuspec_content = _private_replace_underscores_for_buildconfiguration(_private_nuget_template, configparser)
    nuspecfilename = get_buildscript_config_item(configparser, 'general', 'productname')+".nuspec"
    nuspecfile = os.path.join(publishdirectory, nuspecfilename)
    with open(nuspecfile, encoding="utf-8", mode="w") as f:
        f.write(nuspec_content)
    execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}", publishdirectory)
    return 0


def SCDotNetBuildNugetAndRunTests_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetBuildNugetAndRunTests_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetBuildNugetAndRunTests(args.configurationfile)

# </SCDotNetBuildNugetAndRunTests>

# <SCDotNetReleaseNuget>


def SCDotNetReleaseNuget(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    publishdirectory = get_buildscript_config_item(configparser, 'dotnet', 'publishdirectory')
    latest_nupkg_file = get_buildscript_config_item(configparser, 'general', 'productname')+"."+repository_version+".nupkg"
    for localnugettarget in get_buildscript_config_items(configparser, 'dotnet', 'localnugettargets'):
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}", publishdirectory)
    for localnugettargetrepository in get_buildscript_config_items(configparser, 'dotnet', 'localnugettargetrepositories'):
        git_commit(localnugettargetrepository,  f"Added {get_buildscript_config_item(configparser,'general','productname')} .NET-release {get_buildscript_config_item(configparser,'prepare','gittagprefix')}{repository_version}")
    if (configparser.getboolean('dotnet', 'publishnugetfile')):
        with open(get_buildscript_config_item(configparser, 'dotnet', 'nugetapikeyfile'), 'r', encoding='utf-8') as apikeyfile:
            api_key = apikeyfile.read()
        nugetsource = get_buildscript_config_item(configparser, 'dotnet', 'nugetsource')
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --source {nugetsource} --api-key {api_key}", publishdirectory)
    return 0


def SCDotNetReleaseNuget_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetReleaseNuget_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetReleaseNuget(args.configurationfile)

# </SCDotNetReleaseNuget>

# <SCDotNetReference>


def SCDotNetReference(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('dotnet', 'generatereference'):
        docfx_file = get_buildscript_config_item(configparser, 'dotnet', 'docfxfile')
        docfx_folder=os.path.dirname(docfx_file)
        ensure_directory_does_not_exist(os.path.join(docfx_folder,"obj"))
        execute_and_raise_exception_if_exit_code_is_not_zero("docfx", os.path.basename(docfx_file), docfx_folder)
        coveragefolder = get_buildscript_config_item(configparser, 'dotnet', 'coveragefolder')
        ensure_directory_exists(coveragefolder)
        coverage_target_file = coveragefolder+os.path.sep+_private_get_coverage_filename(configparser)
        shutil.copyfile(_private_get_test_csprojfile_folder(configparser)+os.path.sep+_private_get_coverage_filename(configparser), coverage_target_file)
        execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator", '-reports:"'+_private_get_coverage_filename(configparser)+'" -targetdir:"'+coveragefolder+'"', coveragefolder)
        git_commit(get_buildscript_config_item(configparser, 'dotnet', 'referencerepository'), "Updated reference")
        if configparser.getboolean('dotnet', 'exportreference'):
            git_push(get_buildscript_config_item(configparser, 'dotnet', 'referencerepository'), get_buildscript_config_item(configparser, 'dotnet', 'exportreferenceremotename'), "master", "master", False, False)
    return 0


def SCDotNetReference_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetReference_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetReference(args.configurationfile)

# </SCDotNetReference>

# <SCDotNetBuild>


def SCDotNetBuild(folderOfCsprojFile: str, csprojFilename: str, outputDirectory: str, buildConfiguration: str, runtimeId: str, dotNetFramework: str, clearOutputDirectoryBeforeBuild: bool = True, verbosity="normal", outputFilenameToSign: str = None, keyToSignForOutputfile: str = None):
    if os.path.isdir(outputDirectory) and clearOutputDirectoryBeforeBuild:
        shutil.rmtree(outputDirectory)
    ensure_directory_exists(outputDirectory)

    argument = csprojFilename
    argument = argument + f' --no-incremental'
    argument = argument + f' --configuration {buildConfiguration}'
    argument = argument + f' --framework {dotNetFramework}'
    argument = argument + f' --runtime {runtimeId}'
    argument = argument + f' --verbosity {verbosity}'
    argument = argument + f' --output "{outputDirectory}"'
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'build {argument}', folderOfCsprojFile, 3600, True, False, "Build")
    if(outputFilenameToSign is not None):
        SCDotNetsign(outputDirectory+os.path.sep+outputFilenameToSign, keyToSignForOutputfile)
    return 0


def SCDotNetBuild_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetRunTests_cli:
Description: Builds a DotNet-project by a given .csproj-file.
Required commandline-commands: dotnet
Required configuration-items: TODO
Requires the requirements of: TODO""")
    parser.add_argument("folderOfCsprojFile")
    parser.add_argument("csprojFilename")
    parser.add_argument("outputDirectory")
    parser.add_argument("buildConfiguration")
    parser.add_argument("runtimeId")
    parser.add_argument("dotnetframework")
    parser.add_argument("clearOutputDirectoryBeforeBuild", type=string_to_boolean, nargs='?', const=True, default=False)
    parser.add_argument("verbosity")
    parser.add_argument("outputFilenameToSign")
    parser.add_argument("keyToSignForOutputfile")
    args = parser.parse_args()
    return SCDotNetBuild(args.folderOfCsprojFile, args.csprojFilename, args.outputDirectory, args.buildConfiguration, args.runtimeId, args.dotnetframework, args.clearOutputDirectoryBeforeBuild, args.verbosity, args.outputFilenameToSign, args.keyToSignForOutputfile)

# </SCDotNetBuild>

# <SCDotNetRunTests>


def SCDotNetRunTests(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    runtime = get_buildscript_config_item(configparser, 'dotnet', 'testruntime')
    SCDotNetBuild(_private_get_test_csprojfile_folder(configparser), _private_get_test_csprojfile_filename(configparser), get_buildscript_config_item(configparser, 'dotnet', 'testoutputfolder'), get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration'), runtime, get_buildscript_config_item(configparser, 'dotnet', 'testdotnetframework'), True, "normal", None, None)
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", "test "+_private_get_test_csprojfile_filename(configparser)+" -c " + get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration') + " --verbosity normal /p:CollectCoverage=true /p:CoverletOutput=" +
                                                         _private_get_coverage_filename(configparser)+" /p:CoverletOutputFormat=opencover", _private_get_test_csprojfile_folder(configparser), 3600, True, False, "Execute tests")
    return 0


def SCDotNetRunTests_cli():
    parser = argparse.ArgumentParser(description="""SCDotNetRunTests_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetRunTests(args.configurationfile)

# </SCDotNetRunTests>

# <SCDotNetsign>


def SCDotNetsign(dllOrExefile: str, snkfile: str):
    dllOrExeFile = resolve_relative_path_from_current_working_directory(dllOrExefile)
    snkfile = resolve_relative_path_from_current_working_directory(snkfile)
    directory = os.path.dirname(dllOrExeFile)
    filename = os.path.basename(dllOrExeFile)
    if filename.lower().endswith(".dll"):
        filename = filename[:-4]
        extension = "dll"
    elif filename.lower().endswith(".exe"):
        filename = filename[:-4]
        extension = "exe"
    else:
        raise Exception("Only .dll-files and .exe-files can be signed")
    execute_and_raise_exception_if_exit_code_is_not_zero("ildasm", f'/all /typelist /text /out="{filename}.il" "{filename}.{extension}"', directory, 3600, True, False, "Sign: ildasm")
    execute_and_raise_exception_if_exit_code_is_not_zero("ilasm", f'/{extension} /res:"{filename}.res" /optimize /key="{snkfile}" "{filename}.il"', directory, 3600, True, False, "Sign: ilasm")
    os.remove(directory+os.path.sep+filename+".il")
    os.remove(directory+os.path.sep+filename+".res")
    return 0


def SCDotNetsign_cli():
    parser = argparse.ArgumentParser(description='Signs a dll- or exe-file with a snk-file. Requires ilasm and ildasm as available commandline-commands.')
    parser.add_argument("dllOrExefile")
    parser.add_argument("snkfile")
    args = parser.parse_args()
    return SCDotNetsign(args.dllOrExefile, args.snkfile)

# </SCDotNetsign>

# <SCPythonCreateWheelRelease>


def SCPythonCreateWheelRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    if(configparser.getboolean('python', 'updateversion')):
        for file in get_buildscript_config_items(configparser, 'python', 'filesforupdatingversion'):
            replace_regex_each_line_of_file(file, '^version = ".+"\n$', 'version = "'+repository_version+'"\n')
    try:
        exitcode = SCPythonBuildWheelAndRunTests(configurationfile)
        build_and_tests_were_successful = exitcode == 0
        if not build_and_tests_were_successful:
            write_exception_to_stderr("Building wheel and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_and_tests_were_successful = False
        write_exception_to_stderr(exception, "Building wheel and running testcases resulted in an error")
    if build_and_tests_were_successful:
        SCPythonReleaseWheel(configurationfile)
        return 0
    else:
        return 1


def SCPythonCreateWheelRelease_cli():
    parser = argparse.ArgumentParser(description="""SCPythonCreateWheelRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonCreateWheelRelease(args.configurationfile)

# </SCPythonCreateWheelRelease>

# <SCPythonBuildWheelAndRunTests>


def SCPythonBuildWheelAndRunTests(configurationfile: str):
    SCPythonRunTests(configurationfile)
    SCPythonBuild(configurationfile)
    return 0


def SCPythonBuildWheelAndRunTests_cli():
    parser = argparse.ArgumentParser(description="""SCPythonBuildWheelAndRunTests_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonBuildWheelAndRunTests(args.configurationfile)

# </SCPythonBuildWheelAndRunTests>

# <SCPythonBuild>


def SCPythonBuild(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    for folder in get_buildscript_config_items(configparser, "python", "deletefolderbeforcreatewheel"):
        ensure_directory_does_not_exist(folder)
    setuppyfile = get_buildscript_config_item(configparser, "python", "pythonsetuppyfile")
    setuppyfilename = os.path.basename(setuppyfile)
    setuppyfilefolder = os.path.dirname(setuppyfile)
    execute_and_raise_exception_if_exit_code_is_not_zero("python", setuppyfilename+" bdist_wheel --dist-dir "+get_buildscript_config_item(configparser, "python", "publishdirectoryforwhlfile"), setuppyfilefolder)
    return 0


def SCPythonBuild_cli():
    parser = argparse.ArgumentParser(description="""SCPythonBuild_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonBuild(args.configurationfile)

# </SCPythonBuild>

# <SCPythonRunTests>


def SCPythonRunTests(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('other', 'hastestproject'):
        pythontestfile = get_buildscript_config_item(configparser, 'python', 'pythontestfile')
        pythontestfilename = os.path.basename(pythontestfile)
        pythontestfilefolder = os.path.dirname(pythontestfile)
        execute_and_raise_exception_if_exit_code_is_not_zero("pytest", pythontestfilename, pythontestfilefolder, 3600, True, False, "Pytest")
    return 0


def SCPythonRunTests_cli():
    parser = argparse.ArgumentParser(description="""SCPythonRunTests_cli:
Description: Executes python-unit-tests.
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonRunTests(args.configurationfile)

# </SCPythonRunTests>

# <SCPythonReleaseWheel>


def SCPythonReleaseWheel(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('python', 'publishwhlfile'):
        with open(get_buildscript_config_item(configparser, 'python', 'pypiapikeyfile'), 'r', encoding='utf-8') as apikeyfile:
            api_key = apikeyfile.read()
        gpgidentity = get_buildscript_config_item(configparser, 'other', 'gpgidentity')
        repository_version = get_version_for_buildscripts(configparser)
        productname = get_buildscript_config_item(configparser, 'general', 'productname')
        twine_argument = f"upload --sign --identity {gpgidentity} --non-interactive {productname}-{repository_version}-py3-none-any.whl --disable-progress-bar --verbose --username __token__ --password {api_key}"
        execute_and_raise_exception_if_exit_code_is_not_zero("twine", twine_argument, get_buildscript_config_item(configparser, "python", "publishdirectoryforwhlfile"))
    return 0


def SCPythonReleaseWheel_cli():
    parser = argparse.ArgumentParser(description="""SCPythonReleaseWheel_cli:
Description: Uploads a .whl-file using twine.
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonReleaseWheel(args.configurationfile)

# </SCPythonReleaseWheel>

# <Helper>


def _private_verbose_check_for_not_available_item(configparser: ConfigParser, queried_items: list, section: str, propertyname: str):
    if configparser.getboolean('other', 'verbose'):
        for item in queried_items:
            if "<notavailable>" in item:
                write_message_to_stderr(f"Warning: The property '{section}.{propertyname}' which is not available was queried")
                print_stacktrace()


def _private_get_buildoutputdirectory(configparser: ConfigParser, runtime):
    result = get_buildscript_config_item(configparser, 'dotnet', 'buildoutputdirectory')
    if configparser.getboolean('dotnet', 'separatefolderforeachruntime'):
        result = result+os.path.sep+runtime
    return result


def get_buildscript_config_item(configparser: ConfigParser, section: str, propertyname: str, custom_replacements: dict = {}, include_version=True):
    result = _private_replace_underscores_for_buildconfiguration(configparser.get(section, propertyname), configparser, custom_replacements, include_version)
    _private_verbose_check_for_not_available_item(configparser, [result], section, propertyname)
    return result


def get_buildscript_config_items(configparser: ConfigParser, section: str, propertyname: str, custom_replacements: dict = {}, include_version=True):
    itemlist_as_string = _private_replace_underscores_for_buildconfiguration(configparser.get(section, propertyname), configparser, custom_replacements, include_version)
    if ',' in itemlist_as_string:
        result = [item.strip() for item in itemlist_as_string.split(',')]
    else:
        result = [itemlist_as_string.strip()]
    _private_verbose_check_for_not_available_item(configparser, result, section, propertyname)
    return result


def _private_get_csprojfile_filename(configparser: ConfigParser):
    file = get_buildscript_config_item(configparser, "dotnet", "csprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.basename(file)
    return result


def _private_get_test_csprojfile_filename(configparser: ConfigParser):
    file = get_buildscript_config_item(configparser, "dotnet", "testcsprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.basename(file)
    return result


def _private_get_csprojfile_folder(configparser: ConfigParser):
    file = get_buildscript_config_item(configparser, "dotnet", "csprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.dirname(file)
    return result


def _private_get_test_csprojfile_folder(configparser: ConfigParser):
    file = get_buildscript_config_item(configparser, "dotnet", "testcsprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.dirname(file)
    return result


def _private_get_coverage_filename(configparser: ConfigParser):
    return get_buildscript_config_item(configparser, "general", "productname")+".TestCoverage.opencover.xml"


def get_version_for_buildscripts(configparser: ConfigParser):
    return get_version_for_buildscripts_helper(get_buildscript_config_item(configparser, 'general', 'repository', {}, False))


@lru_cache(maxsize=None)
def get_version_for_buildscripts_helper(folder: str):
    return get_semver_version_from_gitversion(folder)


def _private_replace_underscore_in_file_for_buildconfiguration(file: str, configparser: ConfigParser, replacements: dict = {}, encoding="utf-8"):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text = _private_replace_underscores_for_buildconfiguration(text, configparser, replacements)
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)


def _private_replace_underscores_for_buildconfiguration(string: str, configparser: ConfigParser, replacements: dict = {}, include_version=True):
    replacements["year"] = str(datetime.datetime.now().year)
    if include_version:
        replacements["version"] = get_version_for_buildscripts(configparser)

    available_configuration_items = []

    available_configuration_items.append(["general", "productname"])
    available_configuration_items.append(["general", "basefolder"])
    available_configuration_items.append(["general", "logfilefolder"])
    available_configuration_items.append(["general", "repository"])
    available_configuration_items.append(["general", "author"])
    available_configuration_items.append(["general", "description"])
    available_configuration_items.append(["prepare", "developmentbranchname"])
    available_configuration_items.append(["prepare", "masterbranchname"])
    available_configuration_items.append(["prepare", "gittagprefix"])
    available_configuration_items.append(["python", "readmefile"])
    available_configuration_items.append(["python", "pythontestfile"])
    available_configuration_items.append(["python", "pythonsetuppyfile"])
    available_configuration_items.append(["python", "filesforupdatingversion"])
    available_configuration_items.append(["python", "pypiapikeyfile"])
    available_configuration_items.append(["python", "deletefolderbeforcreatewheel"])
    available_configuration_items.append(["python", "publishdirectoryforwhlfile"])
    available_configuration_items.append(["dotnet", "csprojfile"])
    available_configuration_items.append(["dotnet", "buildoutputdirectory"])
    available_configuration_items.append(["dotnet", "publishdirectory"])
    available_configuration_items.append(["dotnet", "runtimes"])
    available_configuration_items.append(["dotnet", "dotnetframework"])
    available_configuration_items.append(["dotnet", "buildconfiguration"])
    available_configuration_items.append(["dotnet", "filestosign"])
    available_configuration_items.append(["dotnet", "snkfile"])
    available_configuration_items.append(["dotnet", "testruntime"])
    available_configuration_items.append(["dotnet", "testdotnetframework"])
    available_configuration_items.append(["dotnet", "testcsprojfile"])
    available_configuration_items.append(["dotnet", "testoutputfolder"])
    available_configuration_items.append(["dotnet", "localnugettargets"])
    available_configuration_items.append(["dotnet", "localnugettargetrepositories"])
    available_configuration_items.append(["dotnet", "docfxfile"])
    available_configuration_items.append(["dotnet", "coveragefolder"])
    available_configuration_items.append(["dotnet", "coveragereportfolder"])
    available_configuration_items.append(["dotnet", "referencerepository"])
    available_configuration_items.append(["dotnet", "exportreferenceremotename"])
    available_configuration_items.append(["dotnet", "nugetsource"])
    available_configuration_items.append(["other", "releaserepository"])
    available_configuration_items.append(["other", "gpgidentity"])
    available_configuration_items.append(["other", "exportrepositoryremotename"])

    for item in available_configuration_items:
        if configparser.has_option(item[0], item[1]):
            replacements[item[1]] = configparser.get(item[0], item[1])

    changed = True
    result = string
    while changed:
        changed = False
        for key, value in replacements.items():
            previousValue = result
            result = result.replace(f"__{key}__", value)
            if(not result == previousValue):
                changed = True
    return result


def private_create_dotnet_release(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('dotnet', 'createexe'):
        return SCDotNetCreateExecutableRelease(configurationfile)
    else:
        return SCDotNetCreateNugetRelease(configurationfile)


# </Helper>

# </Build>

# <SCGenerateThumbnail>


def _private_calculate_lengh_in_seconds(filename: str, folder: str):
    argument = '-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "'+filename+'"'
    return float(execute_and_raise_exception_if_exit_code_is_not_zero("ffprobe", argument, folder)[1])


def _private_create_thumbnails(filename: str, length_in_seconds: float, amount_of_images: int, folder: str, tempname_for_thumbnails):
    rrp = length_in_seconds/(amount_of_images-2)
    argument = '-i "'+filename+'" -r 1/'+str(rrp)+' -vf scale=-1:120 -vcodec png '+tempname_for_thumbnails+'-%002d.png'
    execute_and_raise_exception_if_exit_code_is_not_zero("ffmpeg", argument, folder)


def _private_create_thumbnail(outputfilename: str, folder: str, length_in_seconds: float, tempname_for_thumbnails):
    duration = datetime.timedelta(seconds=length_in_seconds)
    info = timedelta_to_simple_string(duration)
    argument = '-title "'+outputfilename+" ("+info+')" -geometry +4+4 '+tempname_for_thumbnails+'*.png "'+outputfilename+'.png"'
    execute_and_raise_exception_if_exit_code_is_not_zero("montage", argument, folder)


def SCGenerateThumbnail(file: str):
    tempname_for_thumbnails = "t"+str(uuid.uuid4())

    amount_of_images = 16
    file = resolve_relative_path_from_current_working_directory(file)
    filename = os.path.basename(file)
    folder = os.path.dirname(file)
    filename_without_extension = Path(file).stem

    try:
        length_in_seconds = _private_calculate_lengh_in_seconds(filename, folder)
        _private_create_thumbnails(filename, length_in_seconds, amount_of_images, folder, tempname_for_thumbnails)
        _private_create_thumbnail(filename_without_extension, folder, length_in_seconds, tempname_for_thumbnails)
    finally:
        for thumbnail_to_delete in Path(folder).rglob(tempname_for_thumbnails+"-*"):
            file = str(thumbnail_to_delete)
            os.remove(file)


def SCGenerateThumbnail_cli():
    parser = argparse.ArgumentParser(description='Generate thumpnails for video-files')
    parser.add_argument('file', help='Input-videofile for thumbnail-generation')
    args = parser.parse_args()
    SCGenerateThumbnail(args.file)

# </SCGenerateThumbnail>

# <SCKeyboardDiagnosis>


def _private_keyhook(event):
    print(str(event.name)+" "+event.event_type)


def SCKeyboardDiagnosis_cli():
    keyboard.hook(_private_keyhook)
    while True:
        time.sleep(10)

# </SCKeyboardDiagnosis>

# <SCMergePDFs>


def SCMergePDFs(files, outputfile: str):
    # TODO add wildcard-option
    pdfFileMerger = PdfFileMerger()
    for file in files:
        pdfFileMerger.append(file.strip())
    pdfFileMerger.write(outputfile)
    pdfFileMerger.close()


def SCMergePDFs_cli():
    parser = argparse.ArgumentParser(description='merges pdf-files')
    parser.add_argument('files', help='Comma-separated filenames')
    parser = argparse.ArgumentParser(description='Takes some pdf-files and merge them to one single pdf-file. Usage: "python MergePDFs.py myfile1.pdf,myfile2.pdf,myfile3.pdf result.pdf"')
    parser.add_argument('outputfile', help='File for the resulting pdf-document')
    args = parser.parse_args()
    SCMergePDFs(args.files.split(','), args.outputfile)

# </SCMergePDFs>

# <SCShowMissingFiles>


def SCShowMissingFiles(folderA: str, folderB: str):
    for file in get_missing_files(folderA, folderB):
        write_message_to_stdout(file)


def SCShowMissingFiles_cli():
    parser = argparse.ArgumentParser(description='Shows all files which are in folderA but not in folder B. This program does not do any content-comparisons.')
    parser.add_argument('folderA')
    parser.add_argument('folderB')
    args = parser.parse_args()
    SCShowMissingFiles(args.folderA, args.folderB)

# </SCShowMissingFiles>

# <SCCreateEmptyFileWithSpecificSize>


def SCCreateEmptyFileWithSpecificSize(name: str, size_string: str):
    if size_string.isdigit():
        size = int(size_string)
    else:
        if len(size_string) >= 3:
            if(size_string.endswith("kb")):
                size = int(size_string[:-2]) * pow(10, 3)
            elif(size_string.endswith("mb")):
                size = int(size_string[:-2]) * pow(10, 6)
            elif(size_string.endswith("gb")):
                size = int(size_string[:-2]) * pow(10, 9)
            elif(size_string.endswith("kib")):
                size = int(size_string[:-3]) * pow(2, 10)
            elif(size_string.endswith("mib")):
                size = int(size_string[:-3]) * pow(2, 20)
            elif(size_string.endswith("gib")):
                size = int(size_string[:-3]) * pow(2, 30)
            else:
                write_message_to_stderr("Wrong format")
        else:
            write_message_to_stderr("Wrong format")
            return 1
    with open(name, "wb") as f:
        f.seek(size-1)
        f.write(b"\0")
    return 0


def SCCreateEmptyFileWithSpecificSize_cli():
    parser = argparse.ArgumentParser(description='Creates a file with a specific size')
    parser.add_argument('name', help='Specifies the name of the created file')
    parser.add_argument('size', help='Specifies the size of the created file')
    args = parser.parse_args()
    SCCreateEmptyFileWithSpecificSize(args.name, args.size)

# </SCCreateEmptyFileWithSpecificSize>

# <SCCreateHashOfAllFiles>


def SCCreateHashOfAllFiles(folder: str):
    for file in absolute_file_paths(folder):
        with open(file+".sha256", "w+") as f:
            f.write(get_sha256_of_file(file))


def SCCreateHashOfAllFiles_cli():
    parser = argparse.ArgumentParser(description='Calculates the SHA-256-value of all files in the given folder and stores the hash-value in a file next to the hashed file.')
    parser.add_argument('folder', help='Folder where the files are stored which should be hashed')
    args = parser.parse_args()
    SCCreateHashOfAllFiles(args.folder)

# </SCCreateHashOfAllFiles>

# <SCOrganizeLinesInFile>


def SCOrganizeLinesInFile(file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False, remove_empty_lines: bool = True):
    if os.path.isfile(file):

        # read file
        lines = read_lines_from_file(file, encoding)
        if(len(lines) == 0):
            return 0

        # store first line if desired
        if(ignore_first_line):
            first_line = lines.pop(0)

        # remove empty lines if desired
        if remove_empty_lines:
            temp = lines
            lines = []
            for line in temp:
                if(not (string_is_none_or_whitespace(line))):
                    lines.append(line)

        # remove duplicated lines if desired
        if remove_duplicated_lines:
            lines = remove_duplicates(lines)

        # sort lines if desired
        if sort:
            lines = sorted(lines, key=str.casefold)

        # reinsert first line
        if ignore_first_line:
            lines.insert(0, first_line)

        # write result to file
        write_lines_to_file(file, lines, encoding)

        return 0
    else:
        write_message_to_stdout(f"File '{file}' does not exist")
        return 1


def SCOrganizeLinesInFile_cli():
    parser = argparse.ArgumentParser(description='Processes the lines of a file with the given commands')

    parser.add_argument('file', help='File which should be transformed')
    parser.add_argument('--encoding', default="utf-8", help='Encoding for the file which should be transformed')
    parser.add_argument("--sort", help="Sort lines", action='store_true')
    parser.add_argument("--remove_duplicated_lines", help="Remove duplicate lines", action='store_true')
    parser.add_argument("--ignore_first_line", help="Ignores the first line in the file", action='store_true')
    parser.add_argument("--remove_empty_lines", help="Removes lines which are empty or contains only whitespaces", action='store_true')

    args = parser.parse_args()
    SCOrganizeLinesInFile(args.file, args.encoding, args.sort, args.remove_duplicated_lines, args.ignore_first_line, args.remove_empty_lines)


# </SCOrganizeLinesInFile>

# <SCGenerateSnkFiles>


def SCGenerateSnkFiles(outputfolder, keysize=4096, amountofkeys=10):
    ensure_directory_exists(outputfolder)
    for _ in range(amountofkeys):
        file = os.path.join(outputfolder, str(uuid.uuid4())+".snk")
        argument = f"-k {keysize} {file}"
        execute("sn", argument, outputfolder)


def SCGenerateSnkFiles_cli():
    parser = argparse.ArgumentParser(description='Generate multiple .snk-files')
    parser.add_argument('outputfolder', help='Folder where the files are stored which should be hashed')
    parser.add_argument('--keysize', default='4096')
    parser.add_argument('--amountofkeys', default='10')

    args = parser.parse_args()
    SCGenerateSnkFiles(args.outputfolder, args.keysize, args.amountofkeys)

# </SCGenerateSnkFiles>


# <SCReplaceSubstringsInFilenames>


def absolute_file_paths(directory: str):
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.abspath(os.path.join(dirpath, filename))


def _private_merge_files(sourcefile: str, targetfile: str):
    with open(sourcefile, "rb") as f:
        source_data = f.read()
    fout = open(targetfile, "ab")
    merge_separator = [0x0A]
    fout.write(bytes(merge_separator))
    fout.write(source_data)
    fout.close()


def _private_process_file(file: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str):
    new_filename = os.path.join(os.path.dirname(file), os.path.basename(file).replace(substringInFilename, newSubstringInFilename))
    if file != new_filename:
        if os.path.isfile(new_filename):
            if(filecmp.cmp(file, new_filename)):
                send2trash.send2trash(file)
            else:
                if(conflictResolveMode == "ignore"):
                    pass
                elif(conflictResolveMode == "preservenewest"):
                    if(os.path.getmtime(file) - os.path.getmtime(new_filename) > 0):
                        send2trash.send2trash(file)
                    else:
                        send2trash.send2trash(new_filename)
                        os.rename(file, new_filename)
                elif(conflictResolveMode == "merge"):
                    _private_merge_files(file, new_filename)
                    send2trash.send2trash(file)
                else:
                    raise Exception('Unknown conflict resolve mode')
        else:
            os.rename(file, new_filename)


def SCReplaceSubstringsInFilenames(folder: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str):
    for file in absolute_file_paths(folder):
        _private_process_file(file, substringInFilename, newSubstringInFilename, conflictResolveMode)


def SCReplaceSubstringsInFilenames_cli():
    parser = argparse.ArgumentParser(description='Replaces certain substrings in filenames. This program requires "pip install Send2Trash" in certain cases.')

    parser.add_argument('folder', help='Folder where the files are stored which should be renamed')
    parser.add_argument('substringInFilename', help='String to be replaced')
    parser.add_argument('newSubstringInFilename', help='new string value for filename')
    parser.add_argument('conflictResolveMode', help='Set a method how to handle cases where a file with the new filename already exits and the files have not the same content. Possible values are: ignore, preservenewest, merge')

    args = parser.parse_args()

    SCReplaceSubstringsInFilenames(args.folder, args.substringInFilename, args.newSubstringInFilename, args.conflictResolveMode,)

# </SCReplaceSubstringsInFilenames>


# <SCSearchInFiles>

def _private_check_file(file: str, searchstring: str):
    bytes_ascii = bytes(searchstring, "ascii")
    bytes_utf16 = bytes(searchstring, "utf-16")  # often called "unicode-encoding"
    bytes_utf8 = bytes(searchstring, "utf-8")
    with open(file, mode='rb') as file:
        content = file.read()
        if bytes_ascii in content:
            write_message_to_stdout(file)
        elif bytes_utf16 in content:
            write_message_to_stdout(file)
        elif bytes_utf8 in content:
            write_message_to_stdout(file)


def SCSearchInFiles(folder: str, searchstring: str):
    for file in absolute_file_paths(folder):
        _private_check_file(file, searchstring)


def SCSearchInFiles_cli():
    parser = argparse.ArgumentParser(description='Searchs for the given searchstrings in the content of all files in the given folder. This program prints all files where the given searchstring was found to the console')

    parser.add_argument('folder', help='Folder for search')
    parser.add_argument('searchstring', help='string to look for')

    args = parser.parse_args()
    SCSearchInFiles(args.folder, args.searchstring)

# </SCSearchInFiles>

# <SCShow2FAAsQRCode>


def _private_print_qr_code_by_csv_line(line: str):
    splitted = line.split(";")
    displayname = splitted[0]
    website = splitted[1]
    emailaddress = splitted[2]
    key = splitted[3]
    period = splitted[4]
    qrcode_content = f"otpauth://totp/{website}:{emailaddress}?secret={key}&issuer={displayname}&period={period}"
    print(f"{displayname} ({emailaddress}):")
    print(qrcode_content)
    call(["qr", qrcode_content])


def SCShow2FAAsQRCode(csvfile: str):
    separator_line = "--------------------------------------------------------"
    with open(csvfile) as f:
        lines = f.readlines()
    lines = [line.rstrip('\n') for line in lines]
    itertor = iter(lines)
    next(itertor)
    for line in itertor:
        write_message_to_stdout(separator_line)
        _private_print_qr_code_by_csv_line(line)
    write_message_to_stdout(separator_line)


def SCShow2FAAsQRCode_cli():

    parser = argparse.ArgumentParser(description="""Always when you use 2-factor-authentication you have the problem: Where to backup the secret-key so that it is easy to re-setup them when you have a new phone?
Using this script is a solution. Always when you setup a 2fa you copy and store the secret in a csv-file.
It should be obviously that this csv-file must be stored encrypted!
Now if you want to move your 2fa-codes to a new phone you simply call "SCShow2FAAsQRCode 2FA.csv"
Then the qr-codes will be displayed in the console and you can scan them on your new phone.
This script does not saving the any data anywhere.

The structure of the csv-file can be viewd here:
Displayname;Website;Email-address;Secret;Period;
Amazon;Amazon.de;myemailaddress@example.com;QWERTY;30;
Google;Google.de;myemailaddress@example.com;ASDFGH;30;

Hints:
-Since the first line of the csv-file contains headlines the first line will always be ignored
-30 is the commonly used value for the period""")
    parser.add_argument('csvfile', help='File where the 2fa-codes are stored')
    args = parser.parse_args()
    SCShow2FAAsQRCode(args.csvfile)

# </SCShow2FAAsQRCode>

# <miscellaneous>


def ensure_path_is_not_quoted(path: str):
    if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
        path = path[1:]
        path = path[:-1]
        return path
    else:
        return path


def get_missing_files(folderA: str, folderB: str):
    folderA_length = len(folderA)
    result = []
    for fileA in absolute_file_paths(folderA):
        file = fileA[folderA_length:]
        fileB = folderB+file
        if not os.path.isfile(fileB):
            result.append(fileB)
    return result


def write_lines_to_file(file: str, lines: list, encoding="utf-8"):
    write_text_to_file(file, os.linesep.join(lines), encoding)


def write_text_to_file(file: str, content: str, encoding="utf-8"):
    write_binary_to_file(file, bytearray(content, encoding))


def write_binary_to_file(file: str, content: bytearray):
    with open(file, "wb") as file_object:
        file_object.write(content)


def read_lines_from_file(file: str, encoding="utf-8"):
    return read_text_from_file(file, encoding).split(os.linesep)


def read_text_from_file(file: str, encoding="utf-8"):
    return read_binary_from_file(file).decode(encoding)


def read_binary_from_file(file: str):
    with open(file, "rb") as file_object:
        return file_object.read()


def rename_names_of_all_files_and_folders(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    for file in get_direct_files_of_folder(folder):
        replace_in_filename(file, replace_from, replace_to, replace_only_full_match)
    for sub_folder in get_direct_folders_of_folder(folder):
        rename_names_of_all_files_and_folders(sub_folder, replace_from, replace_to, replace_only_full_match)
    replace_in_foldername(folder, replace_from, replace_to, replace_only_full_match)


def get_direct_files_of_folder(folder: str):
    result = [os.path.join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]
    return result


def get_direct_folders_of_folder(folder: str):
    result = [os.path.join(folder, f) for f in listdir(folder) if isdir(join(folder, f))]
    return result


def replace_in_filename(file: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    filename = Path(file).name
    if(_private_should_get_replaced(filename, replace_from, replace_only_full_match)):
        folder_of_file = os.path.dirname(file)
        os.rename(file, os.path.join(folder_of_file, filename.replace(replace_from, replace_to)))


def replace_in_foldername(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    foldername = Path(folder).name
    if(_private_should_get_replaced(foldername, replace_from, replace_only_full_match)):
        folder_of_folder = os.path.dirname(folder)
        os.rename(folder, os.path.join(folder_of_folder, foldername.replace(replace_from, replace_to)))


def _private_should_get_replaced(input_text, search_text, replace_only_full_match):
    if replace_only_full_match:
        return input_text == search_text
    else:
        return search_text in input_text


def str_none_safe(variable):
    if variable is None:
        return ''
    else:
        return str(variable)


def get_sha256_of_file(file: str):
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def remove_duplicates(input):
    result = []
    for item in input:
        if not item in result:
            result.append(item)
    return result


def print_stacktrace():
    for line in traceback.format_stack():
        write_message_to_stdout(line.strip())


def string_to_boolean(value: str):
    value = value.strip().lower()
    if value in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise Exception(f"Can not convert '{value}' to a boolean value")


def file_is_empty(file: str):
    return os.stat(file).st_size == 0


def get_time_based_logfile_by_folder(folder: str, name: str = "Log"):
    return os.path.join(folder, name+"_"+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+".log")


def execute_and_raise_exception_if_exit_code_is_not_zero(program: str, arguments: str = "", workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity=1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None, write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero: bool = True):
    result = execute_full(program, arguments, workingdirectory, print_errors_as_information, log_file, timeoutInSeconds, verbosity, addLogOverhead, title)
    if result[0] == 0:
        return result
    else:
        if(write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero):
            write_message_to_stderr(result[2])
        raise Exception(f"'{workingdirectory}>{program} {arguments}' had exitcode {str(result[0])}")


def execute(program: str, arguments: str, workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity=1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None):
    result = execute_full(program, arguments, workingdirectory, timeoutInSeconds, verbosity, addLogOverhead, title, print_errors_as_information, log_file)
    return result[0]


def execute_full(program: str, arguments: str, workingdirectory: str = "", print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds=3600, verbosity=1, addLogOverhead: bool = False, title: str = None):
    if string_is_none_or_whitespace(title):
        title_for_message = ""
    else:
        title_for_message = f"for task '{title}' "
    if workingdirectory == "":
        workingdirectory = os.getcwd()
    else:
        workingdirectory = resolve_relative_path_from_current_working_directory(workingdirectory)
    title_local = f"epew {title_for_message}('{workingdirectory}>{program} {arguments}')"
    output_file_for_stdout = tempfile.gettempdir() + os.path.sep+str(uuid.uuid4()) + ".temp.txt"
    output_file_for_stderr = tempfile.gettempdir() + os.path.sep+str(uuid.uuid4()) + ".temp.txt"
    if verbosity == 2:
        write_message_to_stdout(f"Start executing {title_local}")
    argument = " -p "+program
    argument = argument+" -a "+base64.b64encode(arguments.encode('utf-8')).decode('utf-8')
    argument = argument+" -b "
    argument = argument+" -w "+'"'+workingdirectory+'"'
    if print_errors_as_information:
        argument = argument+" -i"
    if addLogOverhead:
        argument = argument+" -h"
    if verbosity == 0:
        argument = argument+" -v Quiet"
    if verbosity == 1:
        argument = argument+" -v Normal"
    if verbosity == 2:
        argument = argument+" -v Verbose"
    argument = argument+" -o "+'"'+output_file_for_stdout+'"'
    argument = argument+" -e "+'"'+output_file_for_stderr+'"'
    if not string_is_none_or_whitespace(log_file):
        argument = argument+" -l "+'"'+log_file+'"'
    argument = argument+" -d "+str(timeoutInSeconds*1000)
    argument = argument+' -t "'+program+'"'
    argument = argument.replace('"', '\\"')
    process = Popen("epew"+argument)
    exit_code = process.wait()
    stdout = _private_load_text(output_file_for_stdout)
    stderr = _private_load_text(output_file_for_stderr)
    if verbosity == 2:
        write_message_to_stdout(f"Finished executing {title_local} with exitcode "+str(exit_code))
    return (exit_code, stdout, stderr)


def _private_load_text(file: str):
    if os.path.isfile(file):
        with io.open(file, mode='r', encoding="utf-8") as f:
            content = f.read()
        os.remove(file)
        return content
    else:
        return ""


def ensure_directory_exists(path: str):
    if(not os.path.isdir(path)):
        os.makedirs(path)


def ensure_file_exists(path: str):
    if(not os.path.isfile(path)):
        with open(path, "a+"):
            pass


def ensure_directory_does_not_exist(path: str):
    if(os.path.isdir(path)):
        shutil.rmtree(path)


def ensure_file_does_not_exist(path: str):
    if(os.path.isfile(path)):
        os.remove(path)


def format_xml_file(file: str, encoding: str):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text = xml.dom.minidom.parseString(text).toprettyxml()
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)


def get_clusters_and_sectors_of_disk(diskpath: str):
    sectorsPerCluster = ctypes.c_ulonglong(0)
    bytesPerSector = ctypes.c_ulonglong(0)
    rootPathName = ctypes.c_wchar_p(diskpath)
    ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName, ctypes.pointer(sectorsPerCluster), ctypes.pointer(bytesPerSector), None, None)
    return (sectorsPerCluster.value, bytesPerSector.value)


def extract_archive_with_7z(unzip_file: str, file: str, password: str, output_directory: str):
    password_set = not password is None
    file_name = Path(file).name
    file_folder = os.path.dirname(file)
    argument = "x"
    if password_set:
        argument = f"{argument} -p\"{password}\""
    argument = f"{argument} -o {output_directory}"
    argument = f"{argument} {file_name}"
    return execute(unzip_file, argument, file_folder)


def get_internet_time():
    response = ntplib.NTPClient().request('pool.ntp.org')
    return datetime.datetime.fromtimestamp(response.tx_time)


def system_time_equals_internet_time(maximal_tolerance_difference: datetime.timedelta):
    return abs(datetime.datetime.now() - get_internet_time()) < maximal_tolerance_difference


def timedelta_to_simple_string(delta):
    return (datetime.datetime(1970, 1, 1, 0, 0, 0)+delta).strftime('%H:%M:%S')


def resolve_relative_path_from_current_working_directory(path: str):
    return resolve_relative_path(path, os.getcwd())


def resolve_relative_path(path: str, base_path: str):
    if(os.path.isabs(path)):
        return path
    else:
        return str(Path(os.path.join(base_path, path)).resolve())


def get_metadata_for_file_for_clone_folder_structure(file: str):
    size = os.path.getsize(file)
    last_modified_timestamp = os.path.getmtime(file)
    hash_value = get_sha256_of_file(file)
    last_access_timestamp = os.path.getatime(file)
    return f'{{"size":"{size}","sha256":"{hash_value}","mtime":"{last_modified_timestamp}","atime":"{last_access_timestamp}"}}'


def clone_folder_structure(source: str, target: str, write_information_to_file):
    source = resolve_relative_path(source, os.getcwd())
    target = resolve_relative_path(target, os.getcwd())
    length_of_source = len(source)
    for source_file in absolute_file_paths(source):
        target_file = target+source_file[length_of_source:]
        ensure_directory_exists(os.path.dirname(target_file))
        with open(target_file, 'w', encoding='utf8') as f:
            f.write(get_metadata_for_file_for_clone_folder_structure(source_file))


def system_time_equals_internet_time_with_default_tolerance():
    return system_time_equals_internet_time(get_default_tolerance_for_system_time_equals_internet_time())


def check_system_time(maximal_tolerance_difference: datetime.timedelta):
    if not system_time_equals_internet_time(maximal_tolerance_difference):
        raise ValueError("System time may be wrong")


def check_system_time_with_default_tolerance():
    return check_system_time(get_default_tolerance_for_system_time_equals_internet_time())


def get_default_tolerance_for_system_time_equals_internet_time():
    return datetime.timedelta(hours=0, minutes=0, seconds=3)


def write_message_to_stdout(message: str):
    message = str(message)
    sys.stdout.write(message+"\n")
    sys.stdout.flush()


def write_message_to_stderr(message: str):
    message = str(message)
    sys.stderr.write(message+"\n")
    sys.stderr.flush()


def write_exception_to_stderr(exception: Exception, extra_message=None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr(")")


def write_exception_to_stderr_with_traceback(exception: Exception, traceback, extra_message=None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr("Traceback: "+traceback.format_exc())
    write_message_to_stderr(")")


def string_is_none_or_empty(string: str):
    if string is None:
        return True
    if type(string) == str:
        return string == ""
    else:
        raise Exception("expected string-variable in argument of string_is_none_or_empty but the type was 'str'")


def string_is_none_or_whitespace(string: str):
    if string_is_none_or_empty(string):
        return True
    else:
        return string.strip() == ""


def strip_new_lines_at_begin_and_end(string: str):
    return string.lstrip('\r').lstrip('\n').rstrip('\r').rstrip('\n')


def get_semver_version_from_gitversion(folder: str):
    return get_version_from_gitversion(folder, "MajorMinorPatch")


def get_version_from_gitversion(folder: str, variable: str):
    strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("gitversion", "/showVariable "+variable, folder, 30, 0)[1])
    return strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("gitversion", "/showVariable "+variable, folder, 30, 0)[1])


def move_content_of_folder(srcDir, dstDir):
    srcDirFull = resolve_relative_path_from_current_working_directory(srcDir)
    dstDirFull = resolve_relative_path_from_current_working_directory(dstDir)
    for file in get_direct_files_of_folder(srcDirFull):
        shutil.move(file, dstDirFull)
    for sub_folder in get_direct_folders_of_folder(srcDirFull):
        shutil.move(sub_folder, dstDirFull)


def replace_regex_each_line_of_file(file: str, replace_from_regex: str, replace_to_regex: str, encoding="utf-8"):
    """This function iterates over each line in the file and replaces it by the line which applied regex.
    Note: The lines will be taken from open(...).readlines(). So the lines may contain '\\n' or '\\r\\n' for example."""
    with open(file, encoding=encoding, mode="r") as f:
        lines = f.readlines()
        replaced_lines = []
        for line in lines:
            replaced_line = re.sub(replace_from_regex, replace_to_regex, line)
            replaced_lines.append(replaced_line)
    with open(file, encoding=encoding, mode="w") as f:
        f.writelines(replaced_lines)


def replace_regex_in_file(file: str, replace_from_regex: str, replace_to_regex: str, encoding="utf-8"):
    with open(file, encoding=encoding, mode="r") as f:
        content = f.read()
        content = re.sub(replace_from_regex, replace_to_regex, content)
    with open(file, encoding=encoding, mode="w") as f:
        f.write(content)


def replace_xmltag_in_file(file: str, tag: str, new_value: str, encoding="utf-8"):
    replace_regex_in_file(file, f"<{tag}>.*</{tag}>", f"<{tag}>{new_value}</{tag}>", encoding)


def update_version_in_csproj_file(file: str, version: str):
    replace_xmltag_in_file(file, "Version", version)
    replace_xmltag_in_file(file, "AssemblyVersion", version + ".0")
    replace_xmltag_in_file(file, "FileVersion", version + ".0")

def replace_underscores_in_text(text: str, replacements: dict):
    changed = True
    while changed:
        changed = False
        for key, value in replacements.items():
            previousValue = text
            text = text.replace(f"__{key}__", value)
            if(not text == previousValue):
                changed = True
    return text

def replace_underscores_in_file(file: str, replacements: dict, encoding:str="utf-8"):
    text=read_text_from_file(file,encoding)
    text=replace_underscores_in_text(text,replacements)
    write_text_to_file(file,text,encoding)


def get_ScriptCollection_version():
    return version


# </miscellaneous>

# <git>


def git_repository_has_new_untracked_files(repository_folder: str):
    return _private_git_repository_has_uncommitted_changes(repository_folder, "ls-files --exclude-standard --others")


def git_repository_has_unstaged_changes(repository_folder: str):
    if(_private_git_repository_has_uncommitted_changes(repository_folder, "diff")):
        return True
    if(git_repository_has_new_untracked_files(repository_folder)):
        return True
    return False


def git_repository_has_staged_changes(repository_folder: str):
    return _private_git_repository_has_uncommitted_changes(repository_folder, "diff --cached")


def git_repository_has_uncommitted_changes(repository_folder: str):
    if(git_repository_has_unstaged_changes(repository_folder)):
        return True
    if(git_repository_has_staged_changes(repository_folder)):
        return True
    return False


def _private_git_repository_has_uncommitted_changes(repository_folder: str, argument: str):
    return not string_is_none_or_whitespace(execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, repository_folder, 3600, 0)[1])


def git_get_current_commit_id(repository_folder: str, commit: str = "HEAD"):
    result = execute_and_raise_exception_if_exit_code_is_not_zero("git", f"rev-parse --verify {commit}", repository_folder, 30, 0)
    return result[1].replace('\r', '').replace('\n', '')


def git_push(folder: str, remotename: str, localbranchname: str, remotebranchname: str, forcepush: bool = False, pushalltags: bool = False):
    argument = f"push {remotename} {localbranchname}:{remotebranchname}"
    if (forcepush):
        argument = argument+" --force"
    if (pushalltags):
        argument = argument+" --tags"
    result = execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, folder, 7200, 1, False, None, True)
    return result[1].replace('\r', '').replace('\n', '')


def git_clone_if_not_already_done(folder: str, link: str):
    original_cwd = os.getcwd()
    try:
        if(not os.path.isdir(folder)):
            argument = f"clone {link} --recurse-submodules --remote-submodules"
            execute_and_raise_exception_if_exit_code_is_not_zero(f"git {argument}", argument, original_cwd)[0]
    finally:
        os.chdir(original_cwd)


def git_commit(directory: str, message: str, author_name: str = None, author_email: str = None):
    if (git_repository_has_uncommitted_changes(directory)):
        write_message_to_stdout(f"Committing all changes in {directory}...")
        execute_and_raise_exception_if_exit_code_is_not_zero("git", "add -A", directory, 3600, 1, False, "Add", False)
        if(author_name is not None and author_email is not None):
            author = f' --author="{author_name} <{author_email}>"'
        else:
            author = ""
        execute_and_raise_exception_if_exit_code_is_not_zero("git", f'commit --message="{message}"{author}', directory, 600, 1, False, "Commit", False)
    else:
        write_message_to_stdout(f"There are no changes to commit in {directory}")
    return git_get_current_commit_id(directory)


def git_create_tag(directory: str, target_for_tag: str, tag: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f"tag {tag} {target_for_tag}", directory, 3600, 1, False, "CreateTag", False)


def git_checkout(directory: str, branch: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "checkout "+branch, directory, 3600, 1, False, "Checkout", True)


def git_merge_abort(directory: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "merge --abort", directory, 3600, 1, False, "AbortMerge", False)


def git_merge(directory: str, sourcebranch: str, targetbranch: str, fastforward: bool = True, commit: bool = True):
    git_checkout(directory, targetbranch)
    if(fastforward):
        fastforward_argument = ""
    else:
        fastforward_argument = "--no-ff "
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "merge --no-commit "+fastforward_argument+sourcebranch, directory, 3600, 1, False, "Merge", True)
    if commit:
        return git_commit(directory, f"Merge branch '{sourcebranch}' into '{targetbranch}'")
    else:
        git_get_current_commit_id(directory)


# </git>
