from configparser import ConfigParser
from distutils.dir_util import copy_tree
from distutils.spawn import find_executable
from functools import lru_cache
from io import BytesIO
from os import listdir
from os.path import isfile, join, isdir, abspath
from pathlib import Path
from PyPDF2 import PdfFileMerger
from random import randrange
from shutil import copytree, copy2, copyfile
from subprocess import Popen, PIPE, call
import argparse
import base64
import binascii
import codecs
import ctypes
import datetime
import errno
import filecmp
import hashlib
import io
import keyboard
import ntplib
import os
import pathlib
import pycdlib
import re
import send2trash
import shutil
import stat
import sys
import tempfile
import time
import traceback
import uuid
import xml.dom.minidom


version = "1.12.57"
__version__ = version

# <Build>

# <CreateRelease>


def SCCreateRelease(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    error_occurred = False
    prepare = get_buildscript_config_boolean_value(configparser, 'general', 'prepare')
    repository_version = get_version_for_buildscripts(configparser)
    repository = get_buildscript_config_item(configparser, "general", "repository")
    write_message_to_stdout(f"Create release v{repository_version} for repository {repository}")
    releaserepository = get_buildscript_config_item(configparser, "other", "releaserepository")

    if (_private_repository_has_changes(repository) or _private_repository_has_changes(releaserepository)):
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

        if get_buildscript_config_boolean_value(configparser, 'general', 'createdotnetrelease') and not error_occurred:
            write_message_to_stdout(f"Start to create .NET-release")
            error_occurred = private_create_dotnet_release(configurationfile) != 0

        if get_buildscript_config_boolean_value(configparser, 'general', 'createpythonrelease') and not error_occurred:
            write_message_to_stdout(f"Start to create Python-release")
            error_occurred = SCPythonCreateWheelRelease(configurationfile) != 0

        if get_buildscript_config_boolean_value(configparser, 'general', 'createdebrelease') and not error_occurred:
            write_message_to_stdout(f"Start to create Deb-release")
            # error_occurred = SCDebCreateInstallerRelease(configurationfile) != 0

    except Exception as exception:
        error_occurred = True
        write_exception_to_stderr_with_traceback(exception, traceback, "Error occurred while creating release")

    finally:
        write_message_to_stdout(f"Finished to create releases")

    if error_occurred:
        if prepare:
            git_merge_abort(repository)
            _private_undo_changes(repository)
            _private_undo_changes(releaserepository)
            git_checkout(repository, get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname'))
        write_message_to_stderr("Building wheel and running testcases was not successful")
        return 1
    else:
        if prepare:
            commit_id = git_commit(repository, "Merge branch '" + get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname')+"' into '"+get_buildscript_config_item(configparser, 'prepare', 'masterbranchname')+"'")
            git_create_tag(repository, commit_id, get_buildscript_config_item(configparser, 'prepare', 'gittagprefix') + repository_version)
            git_merge(repository, get_buildscript_config_item(configparser, 'prepare', 'masterbranchname'), get_buildscript_config_item(configparser, 'prepare', 'developmentbranchname'), True)
            if get_buildscript_config_boolean_value(configparser, 'other', 'exportrepository'):
                branch = get_buildscript_config_item(configparser, 'prepare', 'masterbranchname')
                git_push(repository, get_buildscript_config_item(configparser, 'other', 'exportrepositoryremotename'), branch, branch, False, True)
            git_commit(get_buildscript_config_item(configparser, 'other', 'releaserepository'), "Added "+get_buildscript_config_item(configparser, 'general', 'productname')+" "+get_buildscript_config_item(configparser, 'prepare', 'gittagprefix')+repository_version)
        write_message_to_stdout("Building wheel and running testcases was successful")
        return 0


def SCCreateRelease_cli() -> int:
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


def SCDotNetBuildExecutableAndRunTests(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'other', 'hastestproject'):
        SCDotNetRunTests(configurationfile)
    for runtime in get_buildscript_config_items(configparser, 'dotnet', 'runtimes'):
        SCDotNetBuild(_private_get_csprojfile_folder(configparser), _private_get_csprojfile_filename(configparser), _private_get_buildoutputdirectory(configparser, runtime), get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration'), runtime,
                      get_buildscript_config_item(configparser, 'dotnet', 'dotnetframework'), True, "normal",  get_buildscript_config_item(configparser, 'dotnet', 'filestosign'), get_buildscript_config_item(configparser, 'dotnet', 'snkfile'))
    publishdirectory = get_buildscript_config_item(configparser, 'dotnet', 'publishdirectory')
    ensure_directory_does_not_exist(publishdirectory)
    copy_tree(get_buildscript_config_item(configparser, 'dotnet', 'buildoutputdirectory'), publishdirectory)
    return 0


def SCDotNetBuildExecutableAndRunTests_cli() -> int:
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


def SCDotNetCreateExecutableRelease(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    if get_buildscript_config_boolean_value(configparser, 'dotnet', 'updateversionsincsprojfile'):
        update_version_in_csproj_file(get_buildscript_config_item(configparser, 'dotnet', 'csprojfile'), repository_version)

    build_and_tests_were_successful = False
    try:
        exitcode = SCDotNetBuildExecutableAndRunTests(configurationfile)
        build_and_tests_were_successful = exitcode == 0
        if not build_and_tests_were_successful:
            write_exception_to_stderr("Building executable and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_and_tests_were_successful = False
        write_exception_to_stderr_with_traceback(exception, traceback, "Building executable and running testcases resulted in an error")

    if build_and_tests_were_successful:
        SCDotNetReference(configurationfile)
        return 0
    else:
        return 1


def SCDotNetCreateExecutableRelease_cli() -> int:
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


def SCDotNetCreateNugetRelease(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    if get_buildscript_config_boolean_value(configparser, 'dotnet', 'updateversionsincsprojfile'):
        update_version_in_csproj_file(get_buildscript_config_item(configparser, 'dotnet', 'csprojfile'), repository_version)

    build_and_tests_were_successful = False
    try:
        exitcode = SCDotNetBuildNugetAndRunTests(configurationfile)
        build_and_tests_were_successful = exitcode == 0
        if not build_and_tests_were_successful:
            write_exception_to_stderr("Building nuget and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_and_tests_were_successful = False
        write_exception_to_stderr_with_traceback(exception, traceback, "Building nuget and running testcases resulted in an error")

    if build_and_tests_were_successful:
        SCDotNetReference(configurationfile)
        SCDotNetReleaseNuget(configurationfile)
        return 0
    else:
        return 1


def SCDotNetCreateNugetRelease_cli() -> int:
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


def SCDotNetBuildNugetAndRunTests(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'other', 'hastestproject'):
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
    execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}", publishdirectory, 3600, _private_get_verbosity_for_exuecutor(configparser))
    return 0


def SCDotNetBuildNugetAndRunTests_cli() -> int:
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


def SCDotNetReleaseNuget(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'other', 'verbose'):
        verbose_argument = 2
    else:
        verbose_argument = 1
    repository_version = get_version_for_buildscripts(configparser)
    publishdirectory = get_buildscript_config_item(configparser, 'dotnet', 'publishdirectory')
    latest_nupkg_file = get_buildscript_config_item(configparser, 'general', 'productname')+"."+repository_version+".nupkg"
    for localnugettarget in get_buildscript_config_items(configparser, 'dotnet', 'localnugettargets'):
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}", publishdirectory, 3600, verbose_argument)
    for localnugettargetrepository in get_buildscript_config_items(configparser, 'dotnet', 'localnugettargetrepositories'):
        git_commit(localnugettargetrepository,  f"Added {get_buildscript_config_item(configparser,'general','productname')} .NET-release {get_buildscript_config_item(configparser,'prepare','gittagprefix')}{repository_version}")
    if (get_buildscript_config_boolean_value(configparser, 'dotnet', 'publishnugetfile')):
        with open(get_buildscript_config_item(configparser, 'dotnet', 'nugetapikeyfile'), 'r', encoding='utf-8') as apikeyfile:
            api_key = apikeyfile.read()
        nugetsource = get_buildscript_config_item(configparser, 'dotnet', 'nugetsource')
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --source {nugetsource} --api-key {api_key}", publishdirectory, 3600, verbose_argument)
    return 0


def SCDotNetReleaseNuget_cli() -> int:
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


def SCDotNetReference(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'dotnet', 'generatereference'):
        if get_buildscript_config_boolean_value(configparser, 'other', 'verbose'):
            verbose_argument_for_reportgenerator = "-verbosity:Verbose"
            verbose_argument = 2
        else:
            verbose_argument_for_reportgenerator = "-verbosity:Info"
            verbose_argument = 1
        docfx_file = get_buildscript_config_item(configparser, 'dotnet', 'docfxfile')
        docfx_folder = os.path.dirname(docfx_file)
        ensure_directory_does_not_exist(os.path.join(docfx_folder, "obj"))
        execute_and_raise_exception_if_exit_code_is_not_zero("docfx", os.path.basename(docfx_file), docfx_folder, 3600, verbose_argument)
        coveragefolder = get_buildscript_config_item(configparser, 'dotnet', 'coveragefolder')
        ensure_directory_exists(coveragefolder)
        coverage_target_file = coveragefolder+os.path.sep+_private_get_coverage_filename(configparser)
        shutil.copyfile(_private_get_test_csprojfile_folder(configparser)+os.path.sep+_private_get_coverage_filename(configparser), coverage_target_file)
        execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator", f'-reports:"{_private_get_coverage_filename(configparser)}" -targetdir:"{coveragefolder}" {verbose_argument_for_reportgenerator}', coveragefolder, 3600, verbose_argument)
        git_commit(get_buildscript_config_item(configparser, 'dotnet', 'referencerepository'), "Updated reference")
        if get_buildscript_config_boolean_value(configparser, 'dotnet', 'exportreference'):
            git_push(get_buildscript_config_item(configparser, 'dotnet', 'referencerepository'), get_buildscript_config_item(configparser, 'dotnet', 'exportreferenceremotename'), "master", "master", False, False)
    return 0


def SCDotNetReference_cli() -> int:
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


def SCDotNetBuild(folderOfCsprojFile: str, csprojFilename: str, outputDirectory: str, buildConfiguration: str, runtimeId: str, dotNetFramework: str, clearOutputDirectoryBeforeBuild: bool = True, verbose: bool = True, outputFilenameToSign: str = None, keyToSignForOutputfile: str = None) -> int:
    # TODO find a good way to include the merge-commit-id into the build
    if os.path.isdir(outputDirectory) and clearOutputDirectoryBeforeBuild:
        shutil.rmtree(outputDirectory)
    ensure_directory_exists(outputDirectory)
    if verbose:
        verbose_argument = 2
        verbose_argument_for_dotnet = "detailed"
    else:
        verbose_argument = 1
        verbose_argument_for_dotnet = "normal"
    argument = csprojFilename
    argument = argument + f' --no-incremental'
    argument = argument + f' --configuration {buildConfiguration}'
    argument = argument + f' --framework {dotNetFramework}'
    argument = argument + f' --runtime {runtimeId}'
    argument = argument + f' --verbosity {verbose_argument_for_dotnet}'
    argument = argument + f' --output "{outputDirectory}"'
    # TODO remove /bin- and /obj-folder of project and of referenced projects
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'build {argument}', folderOfCsprojFile, 3600, verbose_argument, False, "Build")
    if(outputFilenameToSign is not None):
        SCDotNetsign(outputDirectory+os.path.sep+outputFilenameToSign, keyToSignForOutputfile, verbose)
    return 0


def SCDotNetBuild_cli() -> int:
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

# TODO add possibility to set another buildconfiguration than for the real result-build
# TODO remove the call to SCDotNetBuild


def SCDotNetRunTests(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    runtime = get_buildscript_config_item(configparser, 'dotnet', 'testruntime')
    if get_buildscript_config_boolean_value(configparser, 'other', 'verbose'):
        verbose_argument_for_dotnet = "detailed"
        verbose_argument = 2
    else:
        verbose_argument_for_dotnet = "normal"
        verbose_argument = 1
    SCDotNetBuild(_private_get_test_csprojfile_folder(configparser), _private_get_test_csprojfile_filename(configparser), get_buildscript_config_item(configparser, 'dotnet', 'testoutputfolder'), get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration'), runtime, get_buildscript_config_item(configparser, 'dotnet', 'testdotnetframework'), True, verbose_argument, None, None)
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", "test "+_private_get_test_csprojfile_filename(configparser)+" -c " + get_buildscript_config_item(configparser, 'dotnet', 'buildconfiguration') +
                                                         f" --verbosity {verbose_argument_for_dotnet} /p:CollectCoverage=true /p:CoverletOutput=" + _private_get_coverage_filename(configparser)+" /p:CoverletOutputFormat=opencover", _private_get_test_csprojfile_folder(configparser), 3600, verbose_argument, False, "Execute tests")
    return 0


def SCDotNetRunTests_cli() -> int:
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


def SCDotNetsign(dllOrExefile: str, snkfile: str, verbose: bool) -> int:
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
    execute_and_raise_exception_if_exit_code_is_not_zero("ildasm", f'/all /typelist /text /out="{filename}.il" "{filename}.{extension}"', directory, 3600, verbose, False, "Sign: ildasm")
    execute_and_raise_exception_if_exit_code_is_not_zero("ilasm", f'/{extension} /res:"{filename}.res" /optimize /key="{snkfile}" "{filename}.il"', directory, 3600, verbose, False, "Sign: ilasm")
    os.remove(directory+os.path.sep+filename+".il")
    os.remove(directory+os.path.sep+filename+".res")
    return 0


def SCDotNetsign_cli() -> int:
    parser = argparse.ArgumentParser(description='Signs a dll- or exe-file with a snk-file. Requires ilasm and ildasm as available commandline-commands.')
    parser.add_argument("dllOrExefile")
    parser.add_argument("snkfile")
    parser.add_argument("verbose", action='store_true')
    args = parser.parse_args()
    return SCDotNetsign(args.dllOrExefile, args.snkfile, args.verbose)

# </SCDotNetsign>

# <SCDebCreateInstallerRelease>


def SCDebCreateInstallerRelease(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    write_message_to_stderr("Not implemented yet")
    return 1


def SCDebCreateInstallerRelease_cli() -> int:
    parser = argparse.ArgumentParser(description="""SCDebCreateInstallerRelease_cli:
Description: TODO
Required commandline-commands: TODO
Required configuration-items: TODO
Requires the requirements of: TODO
""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDebCreateInstallerRelease(args.configurationfile)

# </SCDebCreateInstallerRelease>

# <SCPythonCreateWheelRelease>


def SCPythonCreateWheelRelease(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_version = get_version_for_buildscripts(configparser)
    if(get_buildscript_config_boolean_value(configparser, 'python', 'updateversion')):
        for file in get_buildscript_config_items(configparser, 'python', 'filesforupdatingversion'):
            replace_regex_each_line_of_file(file, '^version = ".+"\n$', 'version = "'+repository_version+'"\n')
    try:
        exitcode = SCPythonBuildWheelAndRunTests(configurationfile)
        build_and_tests_were_successful = exitcode == 0
        if not build_and_tests_were_successful:
            write_exception_to_stderr("Building wheel and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_and_tests_were_successful = False
        write_exception_to_stderr_with_traceback(exception, traceback, "Building wheel and running testcases resulted in an error")
    if build_and_tests_were_successful:
        SCPythonReleaseWheel(configurationfile)
        return 0
    else:
        return 1


def SCPythonCreateWheelRelease_cli() -> int:
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


def SCPythonBuildWheelAndRunTests(configurationfile: str) -> int:
    SCPythonRunTests(configurationfile)
    SCPythonBuild(configurationfile)
    return 0


def SCPythonBuildWheelAndRunTests_cli() -> int:
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


def SCPythonBuild(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    for folder in get_buildscript_config_items(configparser, "python", "deletefolderbeforcreatewheel"):
        ensure_directory_does_not_exist(folder)
    setuppyfile = get_buildscript_config_item(configparser, "python", "pythonsetuppyfile")
    setuppyfilename = os.path.basename(setuppyfile)
    setuppyfilefolder = os.path.dirname(setuppyfile)
    publishdirectoryforwhlfile = get_buildscript_config_item(configparser, "python", "publishdirectoryforwhlfile")
    ensure_directory_exists(publishdirectoryforwhlfile)
    execute_and_raise_exception_if_exit_code_is_not_zero("python", setuppyfilename+' bdist_wheel --dist-dir "'+publishdirectoryforwhlfile+'"', setuppyfilefolder, 3600, _private_get_verbosity_for_exuecutor(configparser))
    return 0


def SCPythonBuild_cli() -> int:
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


def SCPythonRunTests(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'other', 'hastestproject'):
        pythontestfile = get_buildscript_config_item(configparser, 'python', 'pythontestfile')
        pythontestfilename = os.path.basename(pythontestfile)
        pythontestfilefolder = os.path.dirname(pythontestfile)
        execute_and_raise_exception_if_exit_code_is_not_zero("pytest", pythontestfilename, pythontestfilefolder, 3600, _private_get_verbosity_for_exuecutor(configparser), False, "Pytest")
    return 0


def SCPythonRunTests_cli() -> int:
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


def SCPythonReleaseWheel(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'python', 'publishwhlfile'):
        with open(get_buildscript_config_item(configparser, 'python', 'pypiapikeyfile'), 'r', encoding='utf-8') as apikeyfile:
            api_key = apikeyfile.read()
        gpgidentity = get_buildscript_config_item(configparser, 'other', 'gpgidentity')
        repository_version = get_version_for_buildscripts(configparser)
        productname = get_buildscript_config_item(configparser, 'general', 'productname')
        if get_buildscript_config_boolean_value(configparser, 'other', 'verbose'):
            verbose_argument = "--verbose"
        else:
            verbose_argument = ""
        twine_argument = f"upload --sign --identity {gpgidentity} --non-interactive {productname}-{repository_version}-py3-none-any.whl --disable-progress-bar --username __token__ --password {api_key} {verbose_argument}"
        execute_and_raise_exception_if_exit_code_is_not_zero("twine", twine_argument, get_buildscript_config_item(configparser, "python", "publishdirectoryforwhlfile"), 3600, _private_get_verbosity_for_exuecutor(configparser))
    return 0


def SCPythonReleaseWheel_cli() -> int:
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


def _private_get_verbosity_for_exuecutor(configparser: ConfigParser) -> int:
    if get_buildscript_config_boolean_value(configparser, 'other', 'verbose'):
        return 2
    else:
        return 1


def _private_verbose_check_for_not_available_item(configparser: ConfigParser, queried_items: list, section: str, propertyname: str):
    if get_buildscript_config_boolean_value(configparser, 'other', 'verbose'):
        for item in queried_items:
            if "<notavailable>" in item:
                write_message_to_stderr(f"Warning: The property '{section}.{propertyname}' which is not available was queried")
                print_stacktrace()


def _private_get_buildoutputdirectory(configparser: ConfigParser, runtime: str) -> str:
    result = get_buildscript_config_item(configparser, 'dotnet', 'buildoutputdirectory')
    if get_buildscript_config_boolean_value(configparser, 'dotnet', 'separatefolderforeachruntime'):
        result = result+os.path.sep+runtime
    return result


def get_buildscript_config_boolean_value(configparser: ConfigParser, section: str, propertyname: str) -> bool:
    try:
        return configparser.getboolean(section, propertyname)
    except:
        return False


def get_buildscript_config_item(configparser: ConfigParser, section: str, propertyname: str, custom_replacements: dict = {}, include_version=True) -> str:
    result = _private_replace_underscores_for_buildconfiguration(configparser.get(section, propertyname), configparser, custom_replacements, include_version)
    _private_verbose_check_for_not_available_item(configparser, [result], section, propertyname)
    return result


def get_buildscript_config_items(configparser: ConfigParser, section: str, propertyname: str, custom_replacements: dict = {}, include_version=True) -> list:
    itemlist_as_string = _private_replace_underscores_for_buildconfiguration(configparser.get(section, propertyname), configparser, custom_replacements, include_version)
    if not string_has_content(itemlist_as_string):
        return []
    if ',' in itemlist_as_string:
        result = [item.strip() for item in itemlist_as_string.split(',')]
    else:
        result = [itemlist_as_string.strip()]
    _private_verbose_check_for_not_available_item(configparser, result, section, propertyname)
    return result


def _private_get_csprojfile_filename(configparser: ConfigParser) -> str:
    file = get_buildscript_config_item(configparser, "dotnet", "csprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.basename(file)
    return result


def _private_get_test_csprojfile_filename(configparser: ConfigParser) -> str:
    file = get_buildscript_config_item(configparser, "dotnet", "testcsprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.basename(file)
    return result


def _private_get_csprojfile_folder(configparser: ConfigParser) -> str:
    file = get_buildscript_config_item(configparser, "dotnet", "csprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.dirname(file)
    return result


def _private_get_test_csprojfile_folder(configparser: ConfigParser) -> str:
    file = get_buildscript_config_item(configparser, "dotnet", "testcsprojfile")
    file = resolve_relative_path_from_current_working_directory(file)
    result = os.path.dirname(file)
    return result


def _private_get_coverage_filename(configparser: ConfigParser) -> str:
    return get_buildscript_config_item(configparser, "general", "productname")+".TestCoverage.opencover.xml"


def get_version_for_buildscripts(configparser: ConfigParser) -> str:
    return get_version_for_buildscripts_helper(get_buildscript_config_item(configparser, 'general', 'repository', {}, False))


@lru_cache(maxsize=None)
def get_version_for_buildscripts_helper(folder: str) -> str:
    return get_semver_version_from_gitversion(folder)


def _private_replace_underscore_in_file_for_buildconfiguration(file: str, configparser: ConfigParser, replacements: dict = {}, encoding="utf-8"):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text = _private_replace_underscores_for_buildconfiguration(text, configparser, replacements)
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)


def _private_replace_underscores_for_buildconfiguration(string: str, configparser: ConfigParser, replacements: dict = {}, include_version=True) -> str:
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
    available_configuration_items.append(["other", "minimalrequiredtestcoverageinpercent"])  # TODO use this value

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


def private_create_dotnet_release(configurationfile: str) -> int:
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if get_buildscript_config_boolean_value(configparser, 'dotnet', 'createexe'):
        return SCDotNetCreateExecutableRelease(configurationfile)
    else:
        return SCDotNetCreateNugetRelease(configurationfile)


# </Helper>

# </Build>

# <SCGenerateThumbnail>


def _private_calculate_lengh_in_seconds(filename: str, folder: str) -> float:
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


def SCGenerateThumbnail(file: str) -> int:
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
        return 0
    except Exception as exception:
        write_exception_to_stderr_with_traceback(exception, traceback)
        return 1
    finally:
        for thumbnail_to_delete in Path(folder).rglob(tempname_for_thumbnails+"-*"):
            file = str(thumbnail_to_delete)
            os.remove(file)


def SCGenerateThumbnail_cli() -> int:
    parser = argparse.ArgumentParser(description='Generate thumpnails for video-files')
    parser.add_argument('file', help='Input-videofile for thumbnail-generation')
    args = parser.parse_args()
    return SCGenerateThumbnail(args.file)

# </SCGenerateThumbnail>

# <SCKeyboardDiagnosis>


def _private_keyhook(event):
    write_message_to_stdout(str(event.name)+" "+event.event_type)


def SCKeyboardDiagnosis_cli():
    keyboard.hook(_private_keyhook)
    while True:
        time.sleep(10)


# </SCKeyboardDiagnosis>

# <SCMergePDFs>


def SCMergePDFs(files, outputfile: str) -> int:
    # TODO add wildcard-option
    pdfFileMerger = PdfFileMerger()
    for file in files:
        pdfFileMerger.append(file.strip())
    pdfFileMerger.write(outputfile)
    pdfFileMerger.close()
    return 0


def SCMergePDFs_cli() -> int:
    parser = argparse.ArgumentParser(description='merges pdf-files')
    parser.add_argument('files', help='Comma-separated filenames')
    parser = argparse.ArgumentParser(description='Takes some pdf-files and merge them to one single pdf-file. Usage: "python MergePDFs.py myfile1.pdf,myfile2.pdf,myfile3.pdf result.pdf"')
    parser.add_argument('outputfile', help='File for the resulting pdf-document')
    args = parser.parse_args()
    SCMergePDFs(args.files.split(','), args.outputfile)
    return 0

# </SCMergePDFs>

# <SCShowMissingFiles>


def SCShowMissingFiles(folderA: str, folderB: str):
    for file in get_missing_files(folderA, folderB):
        write_message_to_stdout(file)


def SCShowMissingFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Shows all files which are in folderA but not in folder B. This program does not do any content-comparisons.')
    parser.add_argument('folderA')
    parser.add_argument('folderB')
    args = parser.parse_args()
    SCShowMissingFiles(args.folderA, args.folderB)
    return 0

# </SCShowMissingFiles>

# <SCCreateEmptyFileWithSpecificSize>


def SCCreateEmptyFileWithSpecificSize(name: str, size_string: str) -> int:
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


def SCCreateEmptyFileWithSpecificSize_cli() -> int:
    parser = argparse.ArgumentParser(description='Creates a file with a specific size')
    parser.add_argument('name', help='Specifies the name of the created file')
    parser.add_argument('size', help='Specifies the size of the created file')
    args = parser.parse_args()
    return SCCreateEmptyFileWithSpecificSize(args.name, args.size)

# </SCCreateEmptyFileWithSpecificSize>

# <SCCreateHashOfAllFiles>


def SCCreateHashOfAllFiles(folder: str):
    for file in absolute_file_paths(folder):
        with open(file+".sha256", "w+") as f:
            f.write(get_sha256_of_file(file))


def SCCreateHashOfAllFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Calculates the SHA-256-value of all files in the given folder and stores the hash-value in a file next to the hashed file.')
    parser.add_argument('folder', help='Folder where the files are stored which should be hashed')
    args = parser.parse_args()
    SCCreateHashOfAllFiles(args.folder)
    return 0

# </SCCreateHashOfAllFiles>

# <SCOrganizeLinesInFile>


def SCOrganizeLinesInFile(file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False, remove_empty_lines: bool = True) -> int:
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


def SCOrganizeLinesInFile_cli() -> int:
    parser = argparse.ArgumentParser(description='Processes the lines of a file with the given commands')

    parser.add_argument('file', help='File which should be transformed')
    parser.add_argument('--encoding', default="utf-8", help='Encoding for the file which should be transformed')
    parser.add_argument("--sort", help="Sort lines", action='store_true')
    parser.add_argument("--remove_duplicated_lines", help="Remove duplicate lines", action='store_true')
    parser.add_argument("--ignore_first_line", help="Ignores the first line in the file", action='store_true')
    parser.add_argument("--remove_empty_lines", help="Removes lines which are empty or contains only whitespaces", action='store_true')

    args = parser.parse_args()
    return SCOrganizeLinesInFile(args.file, args.encoding, args.sort, args.remove_duplicated_lines, args.ignore_first_line, args.remove_empty_lines)


# </SCOrganizeLinesInFile>

# <SCGenerateSnkFiles>


def SCGenerateSnkFiles(outputfolder, keysize=4096, amountofkeys=10) -> int:
    ensure_directory_exists(outputfolder)
    for _ in range(amountofkeys):
        file = os.path.join(outputfolder, str(uuid.uuid4())+".snk")
        argument = f"-k {keysize} {file}"
        execute("sn", argument, outputfolder)


def SCGenerateSnkFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Generate multiple .snk-files')
    parser.add_argument('outputfolder', help='Folder where the files are stored which should be hashed')
    parser.add_argument('--keysize', default='4096')
    parser.add_argument('--amountofkeys', default='10')

    args = parser.parse_args()
    SCGenerateSnkFiles(args.outputfolder, args.keysize, args.amountofkeys)
    return 0

# </SCGenerateSnkFiles>


# <SCReplaceSubstringsInFilenames>


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


def SCReplaceSubstringsInFilenames_cli() -> int:
    parser = argparse.ArgumentParser(description='Replaces certain substrings in filenames. This program requires "pip install Send2Trash" in certain cases.')

    parser.add_argument('folder', help='Folder where the files are stored which should be renamed')
    parser.add_argument('substringInFilename', help='String to be replaced')
    parser.add_argument('newSubstringInFilename', help='new string value for filename')
    parser.add_argument('conflictResolveMode', help='Set a method how to handle cases where a file with the new filename already exits and the files have not the same content. Possible values are: ignore, preservenewest, merge')

    args = parser.parse_args()

    SCReplaceSubstringsInFilenames(args.folder, args.substringInFilename, args.newSubstringInFilename, args.conflictResolveMode)
    return 0

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


def SCSearchInFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Searchs for the given searchstrings in the content of all files in the given folder. This program prints all files where the given searchstring was found to the console')

    parser.add_argument('folder', help='Folder for search')
    parser.add_argument('searchstring', help='string to look for')

    args = parser.parse_args()
    SCSearchInFiles(args.folder, args.searchstring)
    return 0

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
    write_message_to_stdout(f"{displayname} ({emailaddress}):")
    write_message_to_stdout(qrcode_content)
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
    return 0

# </SCShow2FAAsQRCode>

# <SCUpdateNugetpackagesInCsharpProject>


def SCUpdateNugetpackagesInCsharpProject(csprojfile: str) -> int:
    outdated_packages = get_nuget_packages_of_csproj_file(csprojfile, True)
    write_message_to_stdout("The following packages will be updated:")
    for outdated_package in outdated_packages:
        write_message_to_stdout(outdated_package)
        update_nuget_package(csprojfile, outdated_package)
    write_message_to_stdout(f"{len(outdated_packages)} package(s) were updated")
    return 0 < len(outdated_packages)


def SCUpdateNugetpackagesInCsharpProject_cli() -> int:

    parser = argparse.ArgumentParser(description="""TODO""")
    parser.add_argument('csprojfile')
    args = parser.parse_args()
    if SCUpdateNugetpackagesInCsharpProject(args.csprojfile):
        return 1
    else:
        return 0
    return 2

# </SCUpdateNugetpackagesInCsharpProject>

# <SCUploadFileToFileHost>


def SCUploadFileToFileHost(file: str, host: str) -> int:
    try:
        write_message_to_stdout(upload_file_to_file_host(file, host))
        return 0
    except Exception as exception:
        write_exception_to_stderr_with_traceback(exception, traceback)
        return 1


def SCUploadFileToFileHost_cli() -> int:

    parser = argparse.ArgumentParser(description="""Uploads a file to a filesharing-service.
Caution:
You are responsible, accountable and liable for this upload. This trivial script only automates a process which you would otherwise do manually.
Be aware of the issues regarding
- copyright/licenses
- legal issues
of the file content. Furthermore consider the terms of use of the filehoster.
Currently the following filesharing-services will be supported:
- anonfiles.com
- bayfiles.com
""")
    parser.add_argument('file', required=True)
    parser.add_argument('host', required=False)
    args = parser.parse_args()
    return SCUploadFileToFileHost(args.file, args.host)

# </SCUploadFileToFileHost>

# <SCFileIsAvailableOnFileHost>


def SCFileIsAvailableOnFileHost(file: str) -> int:
    try:
        if file_is_available_on_file_host(file):
            write_message_to_stdout(f"'{file}' is available")
            return 0
        else:
            write_message_to_stdout(f"'{file}' is not available")
            return 1
    except Exception as exception:
        write_exception_to_stderr_with_traceback(exception, traceback)
        return 2


def SCFileIsAvailableOnFileHost_cli() -> int:

    parser = argparse.ArgumentParser(description="""Determines whether a file on a filesharing-service supported by the UploadFile-function is still available.""")
    parser.add_argument('link')
    args = parser.parse_args()
    return SCFileIsAvailableOnFileHost(args.link)

# </SCFileIsAvailableOnFileHost>


# <SCCalculateBitcoinBlockHash>


def SCCalculateBitcoinBlockHash(version: str, previousblockhash: str, transactionsmerkleroot: str, timestamp: str, target: str, nonce: str) -> str:
    # Example-values:
    # version: "00000020"; previousblockhash: "66720b99e07d284bd4fe67ff8c49a5db1dd8514fcdab61000000000000000000"; transactionsmerkleroot: "7829844f4c3a41a537b3131ca992643eaa9d093b2383e4cdc060ad7dc5481187"; timestamp: "51eb505a"; target: "c1910018"; nonce: "de19b302"
    header = str(version + previousblockhash + transactionsmerkleroot + timestamp + target + nonce)
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(binascii.unhexlify(header)).digest()).digest()[::-1]).decode('utf-8')


def SCCalculateBitcoinBlockHash_cli() -> int:
    parser = argparse.ArgumentParser(description='Calculates the Hash of the header of a bitcoin-block.')
    parser.add_argument('--version', help='Block-version', required=True)
    parser.add_argument('--previousblockhash', help='Hash-value of the previous block', required=True)
    parser.add_argument('--transactionsmerkleroot', help='Hashvalue of the merkle-root of the transactions which are contained in the block', required=True)
    parser.add_argument('--timestamp', help='Timestamp of the block', required=True)
    parser.add_argument('--target', help='difficulty', required=True)
    parser.add_argument('--nonce', help='Arbitrary 32-bit-integer-value', required=True)
    args = parser.parse_args()

    args = parser.parse_args()
    write_message_to_stdout(SCCalculateBitcoinBlockHash(args.version, args.previousblockhash, args.transactionsmerkleroot, args.timestamp, args.target, args.nonce))
    return 0

# </SCCalculateBitcoinBlockHash>

# <SCChangeHashOfProgram>


def SCChangeHashOfProgram(inputfile: str):
    valuetoappend = str(uuid.uuid4())

    outputfile = inputfile + '.modified'

    copy2(inputfile, outputfile)
    file = open(outputfile, 'a')
    # TODO use rcedit for .exe-files instead of appending valuetoappend ( https://github.com/electron/rcedit/ )
    # background: you can retrieve the "original-filename" from the .exe-file like discussed here: https://security.stackexchange.com/questions/210843/is-it-possible-to-change-original-filename-of-an-exe
    # so removing the original filename with rcedit is probably a better way to make it more difficult to detect the programname.
    # this would obviously also change the hashvalue of the program so appending a whitespace is not required anymore.
    file.write(valuetoappend)
    file.close()


def SCChangeHashOfProgram_cli() -> int:
    parser = argparse.ArgumentParser(description='Changes the hash-value of arbitrary files by appending data at the end of the file.')
    parser.add_argument('--inputfile', help='Specifies the script/executable-file whose hash-value should be changed', required=True)
    args = parser.parse_args()
    SCChangeHashOfProgram(args.inputfile)
    return 0

# </SCChangeHashOfProgram>


# <SCCreateISOFileWithObfuscatedFiles>

def _private_adjust_folder_name(folder: str) -> str:
    result = os.path.dirname(folder).replace("\\", "/")
    if result == "/":
        return ""
    else:
        return result


def _private_create_iso(folder, iso_file):
    created_directories = []
    files_directory = "FILES"
    iso = pycdlib.PyCdlib()
    iso.new()
    files_directory = files_directory.upper()
    iso.add_directory("/" + files_directory)
    created_directories.append("/" + files_directory)
    for root, _, files in os.walk(folder):
        for file in files:
            full_path = os.path.join(root, file)
            content = open(full_path, "rb").read()
            path_in_iso = '/' + files_directory + _private_adjust_folder_name(full_path[len(folder)::1]).upper()
            if not (path_in_iso in created_directories):
                iso.add_directory(path_in_iso)
                created_directories.append(path_in_iso)
            iso.add_fp(BytesIO(content), len(content), path_in_iso + '/' + file.upper() + ';1')
    iso.write(iso_file)
    iso.close()


def SCCreateISOFileWithObfuscatedFiles(inputfolder: str, outputfile: str, printtableheadline, createisofile, extensions):
    if (os.path.isdir(inputfolder)):
        namemappingfile = "name_map.csv"
        files_directory = inputfolder
        files_directory_obf = files_directory + "_Obfuscated"
        SCObfuscateFilesFolder(inputfolder, printtableheadline, namemappingfile, extensions)
        os.rename(namemappingfile, os.path.join(files_directory_obf, namemappingfile))
        if createisofile:
            _private_create_iso(files_directory_obf, outputfile)
            shutil.rmtree(files_directory_obf)
    else:
        raise Exception(f"Directory not found: '{inputfolder}'")


def SCCreateISOFileWithObfuscatedFiles_cli() -> int:
    parser = argparse.ArgumentParser(description='Creates an iso file with the files in the given folder and changes their names and hash-values. This script does not process subfolders transitively.')

    parser.add_argument('--inputfolder', help='Specifies the foldere where the files are stored which should be added to the iso-file', required=True)
    parser.add_argument('--outputfile', default="files.iso", help='Specifies the output-iso-file and its location')
    parser.add_argument('--printtableheadline', default=False, action='store_true', help='Prints column-titles in the name-mapping-csv-file')
    parser.add_argument('--createnoisofile', default=False, action='store_true', help="Create no iso file")
    parser.add_argument('--extensions', default="exe,py,sh", help='Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
    args = parser.parse_args()

    SCCreateISOFileWithObfuscatedFiles(args.inputfolder, args.outputfile, args.printtableheadline, not args.createnoisofile, args.extensions)
    return 0

# </SCCreateISOFileWithObfuscatedFiles>

# <SCFilenameObfuscator>


def SCFilenameObfuscator(inputfolder: str, printtableheadline, namemappingfile: str, extensions: str):
    obfuscate_all_files = extensions == "*"
    if(not obfuscate_all_files):
        obfuscate_file_extensions = extensions.split(",")

    if (os.path.isdir(inputfolder)):
        printtableheadline = string_to_boolean(printtableheadline)
        files = []
        if not os.path.isfile(namemappingfile):
            with open(namemappingfile, "a"):
                pass
        if printtableheadline:
            append_line_to_file(namemappingfile, "Original filename;new filename;SHA2-hash of file")
        for file in absolute_file_paths(inputfolder):
            if os.path.isfile(os.path.join(inputfolder, file)):
                if obfuscate_all_files or _private_extension_matchs(file, obfuscate_file_extensions):
                    files.append(file)
        for file in files:
            hash = get_sha256_of_file(file)
            extension = pathlib.Path(file).suffix
            new_file_name_without_path = str(uuid.uuid4())[0:8] + extension
            new_file_name = os.path.join(os.path.dirname(file), new_file_name_without_path)
            os.rename(file, new_file_name)
            append_line_to_file(namemappingfile, os.path.basename(file) + ";" + new_file_name_without_path + ";" + hash)
    else:
        raise Exception(f"Directory not found: '{inputfolder}'")


def SCFilenameObfuscator_cli() -> int:
    parser = argparse.ArgumentParser(description='Obfuscates the names of all files in the given folder. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

    parser.add_argument('--printtableheadline', type=string_to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
    parser.add_argument('--namemappingfile', default="NameMapping.csv", help='Specifies the file where the name-mapping will be written to')
    parser.add_argument('--extensions', default="exe,py,sh", help='Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
    parser.add_argument('--inputfolder', help='Specifies the foldere where the files are stored whose names should be obfuscated', required=True)

    args = parser.parse_args()
    SCFilenameObfuscator(args.inputfolder, args.printtableheadline, args.namemappingfile, args.extensions)
    return 0

# </SCFilenameObfuscator>

# <SCObfuscateFilesFolder>


def SCObfuscateFilesFolder(inputfolder: str, printtableheadline, namemappingfile: str, extensions: str):
    obfuscate_all_files = extensions == "*"
    if(not obfuscate_all_files):
        if "," in extensions:
            obfuscate_file_extensions = extensions.split(",")
        else:
            obfuscate_file_extensions = [extensions]
    newd = inputfolder+"_Obfuscated"
    shutil.copytree(inputfolder, newd)
    inputfolder = newd
    if (os.path.isdir(inputfolder)):
        for file in absolute_file_paths(inputfolder):
            if obfuscate_all_files or _private_extension_matchs(file, obfuscate_file_extensions):
                SCChangeHashOfProgram(file)
                os.remove(file)
                os.rename(file + ".modified", file)
        SCFilenameObfuscator(inputfolder, printtableheadline, namemappingfile, extensions)
    else:
        raise Exception(f"Directory not found: '{inputfolder}'")


def SCObfuscateFilesFolder_cli() -> int:
    parser = argparse.ArgumentParser(description='Changes the hash-value of the files in the given folder and renames them to obfuscated names. This script does not process subfolders transitively. Caution: This script can cause harm if you pass a wrong inputfolder-argument.')

    parser.add_argument('--printtableheadline', type=string_to_boolean, const=True, default=True, nargs='?', help='Prints column-titles in the name-mapping-csv-file')
    parser.add_argument('--namemappingfile', default="NameMapping.csv", help='Specifies the file where the name-mapping will be written to')
    parser.add_argument('--extensions', default="exe,py,sh", help='Comma-separated list of file-extensions of files where this tool should be applied. Use "*" to obfuscate all')
    parser.add_argument('--inputfolder', help='Specifies the folder where the files are stored whose names should be obfuscated', required=True)

    args = parser.parse_args()
    SCObfuscateFilesFolder(args.inputfolder, args.printtableheadline, args.namemappingfile, args.extensions)
    return 0

# </SCObfuscateFilesFolder>


# <git>


def get_parent_commit_ids_of_commit(directory: str, commit_id: str) -> str:
    return execute_and_raise_exception_if_exit_code_is_not_zero("git", f'log --pretty=%P -n 1 "{commit_id}"', directory)[1].replace("\r", "").replace("\n", "").split(" ")


def _private_datetime_to_string_for_git(datetime: datetime.datetime) -> str:
    return datetime.strftime('%Y-%m-%d %H:%M:%S')


def get_commit_ids_between_dates(directory: str, since: datetime, until: datetime):
    since_as_string = _private_datetime_to_string_for_git(since)
    until_as_string = _private_datetime_to_string_for_git(until)
    return filter(lambda line: not string_is_none_or_whitespace(line), execute_and_raise_exception_if_exit_code_is_not_zero("git", f'log --since "{since_as_string}" --until "{until_as_string}" --pretty=format:"%H" --no-patch', directory)[1].split("\n").replace("\r", ""))


def git_repository_has_new_untracked_files(repository_folder: str) -> bool:
    return _private_git_repository_has_uncommitted_changes(repository_folder, "ls-files --exclude-standard --others")


def git_repository_has_unstaged_changes(repository_folder: str) -> bool:
    if(_private_git_repository_has_uncommitted_changes(repository_folder, "diff")):
        return True
    if(git_repository_has_new_untracked_files(repository_folder)):
        return True
    return False


def git_repository_has_staged_changes(repository_folder: str) -> bool:
    return _private_git_repository_has_uncommitted_changes(repository_folder, "diff --cached")


def git_repository_has_uncommitted_changes(repository_folder: str) -> bool:
    if(git_repository_has_unstaged_changes(repository_folder)):
        return True
    if(git_repository_has_staged_changes(repository_folder)):
        return True
    return False


def _private_git_repository_has_uncommitted_changes(repository_folder: str, argument: str) -> bool:
    return not string_is_none_or_whitespace(execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, repository_folder, 3600, 0)[1])


def git_get_current_commit_id(repository_folder: str, commit: str = "HEAD") -> str:
    result = execute_and_raise_exception_if_exit_code_is_not_zero("git", f"rev-parse --verify {commit}", repository_folder, 30, 0)
    return result[1].replace('\r', '').replace('\n', '')


def git_fetch(folder: str, remotename: str = "--all", printErrorsAsInformation: bool = True):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f"fetch {remotename} --tags --prune", folder, 3600, 1, False, None, printErrorsAsInformation)


def git_push(folder: str, remotename: str, localbranchname: str, remotebranchname: str, forcepush: bool = False, pushalltags: bool = False):
    argument = f"push {remotename} {localbranchname}:{remotebranchname}"
    if (forcepush):
        argument = argument+" --force"
    if (pushalltags):
        argument = argument+" --tags"
    result = execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, folder, 7200, 1, False, None, True)
    return result[1].replace('\r', '').replace('\n', '')


def git_clone_if_not_already_done(clone_target_folder: str, remote_repository_path: str, include_submodules: bool = True, mirror: bool = False):
    original_cwd = os.getcwd()
    try:
        if(not os.path.isdir(clone_target_folder)):

            if include_submodules:
                include_submodules_argument = " --recurse-submodules --remote-submodules"
            else:
                include_submodules_argument = ""

            if mirror:
                mirror_argument = " --mirror"
            else:
                mirror_argument = ""

            ensure_directory_exists(clone_target_folder)
            argument = f"clone {remote_repository_path}{include_submodules_argument}{mirror_argument}"
            execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, clone_target_folder)
    finally:
        os.chdir(original_cwd)


def git_get_all_remote_names(directory) -> list:
    lines = execute_and_raise_exception_if_exit_code_is_not_zero("git", "remote", directory)[1]
    result = []
    for line in lines:
        if(not string_is_none_or_whitespace(line)):
            result.append(line.strip())
    return result


def repository_has_remote_with_specific_name(directory: str, remote_name: str) -> bool:
    return remote_name in git_get_all_remote_names(directory)


def git_add_or_set_remote_address(directory: str, remote_name: str, remote_address: str):
    if (repository_has_remote_with_specific_name(directory, remote_name)):
        execute_and_raise_exception_if_exit_code_is_not_zero("git", f'remote set-url {remote_name} "{remote_address}"', directory, 3600, 1, False, "Stage", False)
    else:
        execute_and_raise_exception_if_exit_code_is_not_zero("git", f'remote add {remote_name} "{remote_address}"', directory, 3600, 1, False, "Stage", False)


def git_stage_all_changes(directory: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "add -A", directory, 3600, 1, False, "Stage", False)


def git_unstage_all_changes(directory: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "reset", directory, 3600, 1, False, "Unstage", False)


def git_stage_file(directory: str, file: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f'stage -- "{file}"', directory, 3600, 1, False, "Stage", False)


def git_unstage_file(directory: str, file: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f'reset -- "{file}"', directory, 3600, 1, False, "Unstage", False)


def git_discard_unstaged_changes_of_file(directory: str, file: str):
    """Caution: This method works really only for 'changed' files yet. So this method does not work properly for new or renamed files."""
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f'checkout -- "{file}"', directory, 3600, 1, False, "Discard", False)


def git_discard_all_unstaged_changes(directory: str):
    """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f'clean -df', directory, 3600, 1, False, "Discard", False)
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f'checkout -- .', directory, 3600, 1, False, "Discard", False)


def git_commit(directory: str, message: str, author_name: str = None, author_email: str = None, stage_all_changes: bool = True, allow_empty_commits: bool = False):
    do_commit = False
    if (git_repository_has_uncommitted_changes(directory)):
        write_message_to_stdout(f"Committing all changes in {directory}...")
        if stage_all_changes:
            git_stage_all_changes(directory)
        if(author_name is not None and author_email is not None):
            author = f' --author="{author_name} <{author_email}>"'
        else:
            author = ""
        do_commit = True
        allowempty = ""
    else:
        if allow_empty_commits:
            do_commit = True
            allowempty = " --allow-empty"
        else:
            write_message_to_stdout(f"There are no changes to commit in {directory}")
    if do_commit:
        execute_and_raise_exception_if_exit_code_is_not_zero("git", f'commit --message="{message}"{author}{allowempty}', directory, 600, 1, False, "Commit", False)

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


def git_undo_all_changes(directory: str):
    """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
    git_unstage_all_changes(directory)
    git_discard_all_unstaged_changes(directory)


def _private_undo_changes(repository: str):
    if(git_repository_has_uncommitted_changes(repository)):
        git_undo_all_changes(repository)


def _private_repository_has_changes(repository: str):
    if(git_repository_has_uncommitted_changes(repository)):
        write_message_to_stderr(f"'{repository}' contains uncommitted changes")
        return True
    else:
        return False

# </git>

# <miscellaneous>


def absolute_file_paths(directory: str) -> list:
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.abspath(os.path.join(dirpath, filename))


def upload_file_to_file_host(file: str, host: str) -> int:
    if(host is None):
        return upload_file_to_random_filesharing_service(file)
    elif host == "anonfiles.com":
        return upload_file_to_anonfiles(file)
    elif host == "bayfiles.com":
        return upload_file_to_bayfiles(file)
    write_message_to_stderr("Unknown host: "+host)
    return 1


def upload_file_to_random_filesharing_service(file: str) -> int:
    host = randrange(2)
    if host == 0:
        return upload_file_to_anonfiles(file)
    if host == 1:
        return upload_file_to_bayfiles(file)


def upload_file_to_anonfiles(file) -> int:
    return upload_file_by_using_simple_curl_request("https://api.anonfiles.com/upload", file)


def upload_file_to_bayfiles(file) -> int:
    return upload_file_by_using_simple_curl_request("https://api.bayfiles.com/upload", file)


def upload_file_by_using_simple_curl_request(api_url: str, file: str) -> int:
    write_message_to_stderr("Notimplemented yet")
    return 1  # TODO


def file_is_available_on_file_host(file) -> int:
    write_message_to_stderr("Notimplemented yet")
    return 1  # TODO


def current_user_has_elevated_privileges() -> bool:
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1


def get_nuget_packages_of_csproj_file(csproj_file: str, only_outdated_packages: bool) -> bool:
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'restore --disable-parallel --force --force-evaluate "{csproj_file}"')
    if only_outdated_packages:
        only_outdated_packages_argument = " --outdated"
    else:
        only_outdated_packages_argument = ""
    stdout = execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'list "{csproj_file}" package{only_outdated_packages_argument}')[1]
    result = []
    for line in stdout.splitlines():
        trimmed_line = line.replace("\t", "").strip()
        if trimmed_line.startswith(">"):
            result.append(trimmed_line[2:].split(" ")[0])
    return result


def update_nuget_package(csproj_file: str, name: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'add "{csproj_file}" package {name}')


def ensure_path_is_not_quoted(path: str) -> str:
    if (path.startswith("\"") and path.endswith("\"")) or (path.startswith("'") and path.endswith("'")):
        path = path[1:]
        path = path[:-1]
        return path
    else:
        return path


def get_missing_files(folderA: str, folderB: str) -> list:
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


def read_lines_from_file(file: str, encoding="utf-8") -> list:
    return read_text_from_file(file, encoding).split(os.linesep)


def read_text_from_file(file: str, encoding="utf-8") -> str:
    return bytes_to_string(read_binary_from_file(file), encoding)


def read_binary_from_file(file: str) -> bytes:
    with open(file, "rb") as file_object:
        return file_object.read()


def rename_names_of_all_files_and_folders(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    for file in get_direct_files_of_folder(folder):
        replace_in_filename(file, replace_from, replace_to, replace_only_full_match)
    for sub_folder in get_direct_folders_of_folder(folder):
        rename_names_of_all_files_and_folders(sub_folder, replace_from, replace_to, replace_only_full_match)
    replace_in_foldername(folder, replace_from, replace_to, replace_only_full_match)


def get_direct_files_of_folder(folder: str) -> list:
    result = [os.path.join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]
    return result


def get_direct_folders_of_folder(folder: str) -> list:
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


def _private_should_get_replaced(input_text, search_text, replace_only_full_match) -> bool:
    if replace_only_full_match:
        return input_text == search_text
    else:
        return search_text in input_text


def str_none_safe(variable) -> str:
    if variable is None:
        return ''
    else:
        return str(variable)


def get_sha256_of_file(file: str) -> str:
    sha256 = hashlib.sha256()
    with open(file, "rb") as fileObject:
        for chunk in iter(lambda: fileObject.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def remove_duplicates(input) -> list:
    result = []
    for item in input:
        if not item in result:
            result.append(item)
    return result


def print_stacktrace():
    for line in traceback.format_stack():
        write_message_to_stdout(line.strip())


def string_to_boolean(value: str) -> bool:
    value = value.strip().lower()
    if value in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise Exception(f"Can not convert '{value}' to a boolean value")


def file_is_empty(file: str) -> bool:
    return os.stat(file).st_size == 0


def folder_is_empty(folder: str) -> bool:
    return len(get_direct_files_of_folder(folder)) == 0 and len(get_direct_folders_of_folder(folder)) == 0


def get_time_based_logfile_by_folder(folder: str, name: str = "Log") -> str:
    return os.path.join(folder, name+"_"+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+".log")


def bytes_to_string(payload: bytes, encoding: str = 'utf-8') -> str:
    return payload.decode(encoding, errors="ignore")


def string_to_bytes(payload: str, encoding: str = 'utf-8') -> bytes:
    return payload.encode(encoding, errors="ignore")


def epew_is_available() -> bool:
    return find_executable("epew") is not None


def _private_adapt_workingdirectory(workingdirectory: str) -> str:
    if workingdirectory == None:
        return os.getcwd()
    else:
        return resolve_relative_path_from_current_working_directory(workingdirectory)


def _private_log_program_start(program: str, arguments: str, workingdirectory: str, verbosity: int = 1):
    if(verbosity == 2):
        write_message_to_stdout(f"Start '{workingdirectory}>{program} {arguments}'")


def start_program_asynchronously(program: str, arguments: str = "", workingdirectory: str = "", verbosity: int = 1, use_epew: bool = False) -> int:
    workingdirectory = _private_adapt_workingdirectory(workingdirectory)
    _private_log_program_start(program, arguments, workingdirectory, verbosity)
    if use_epew:
        raise Exception("start_program_asynchronously using epew is not implemented yet")
    else:
        start_argument_as_array = [program]
        start_argument_as_array.extend(arguments.split())
        start_argument_as_string = f"{program} {arguments}"
        return Popen(start_argument_as_string, stdout=PIPE, stderr=PIPE, cwd=workingdirectory, shell=True).pid


def execute_and_raise_exception_if_exit_code_is_not_zero(program: str, arguments: str = "", workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity: int = 1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None, write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero: bool = True):
    result = start_program_synchronously(program, arguments, workingdirectory, print_errors_as_information, log_file, timeoutInSeconds, verbosity, addLogOverhead, title, True)
    if result[0] == 0:
        return result
    else:
        if(write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero):
            write_message_to_stderr(result[2])
        raise Exception(f"'{workingdirectory}>{program} {arguments}' had exitcode {str(result[0])}")


def execute(program: str, arguments: str, workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity=1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None) -> int:
    result = start_program_synchronously(program, arguments, workingdirectory, verbosity, print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title)
    return result[0]


def start_program_synchronously(program: str, arguments: str, workingdirectory: str = None, verbosity: int = 1, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 3600, addLogOverhead: bool = False, title: str = None, throw_exception_if_exitcode_is_not_zero: bool = False, prevent_using_epew: bool = False, write_output_to_standard_output: bool = True, log_namespace: str = ""):
    workingdirectory = _private_adapt_workingdirectory(workingdirectory)
    _private_log_program_start(program, arguments, workingdirectory, verbosity)
    if (epew_is_available() and not prevent_using_epew):
        if string_is_none_or_whitespace(title):
            title_for_message = ""
            title_argument = f'{workingdirectory}>{program} {arguments}'
        else:
            title_for_message = f"for task '{title}' "
            title_argument = title
        title_local = f"epew {title_for_message}('{workingdirectory}>{program} {arguments}')"
        tempdir = tempfile.gettempdir()
        output_file_for_stdout = os.path.join(tempdir, str(uuid.uuid4()) + ".epew-temp.txt")
        output_file_for_stderr = os.path.join(tempdir, str(uuid.uuid4()) + ".epew-temp.txt")
        output_file_for_exit_code = os.path.join(tempdir, str(uuid.uuid4()) + ".epew-temp.txt")
        output_file_for_pid = os.path.join(tempdir, str(uuid.uuid4()) + ".epew-temp.txt")
        base64argument = base64.b64encode(arguments.encode('utf-8')).decode('utf-8')
        argument = f'--Program "{program}"'
        argument = argument+f' --Argument {base64argument}'
        argument = argument+f' --ArgumentIsBase64Encoded'
        argument = argument+f' --Workingdirectory "{workingdirectory}"'
        argument = argument+f' --StdOutFile "{output_file_for_stdout}"'
        argument = argument+f' --StdErrFile "{output_file_for_stderr}"'
        argument = argument+f' --ExitCodeFile "{output_file_for_exit_code}"'
        argument = argument+f' --ProcessIdFile "{output_file_for_pid}"'
        argument = argument+f' --TimeoutInMilliseconds {str(timeoutInSeconds*1000)}'
        argument = argument+f' --Title "{title_argument}"'
        argument = argument+f' --LogNamespace "{log_namespace}"'
        if not string_is_none_or_whitespace(log_file):
            argument = argument+f' --LogFile "{log_file}"'
        if write_output_to_standard_output:
            argument = argument+f' --WriteOutputToConsole'
        if print_errors_as_information:
            argument = argument+" --PrintErrorsAsInformation"
        if addLogOverhead:
            argument = argument+" --AddLogOverhead"
        if verbosity == 0:
            argument = argument+" --Verbosity Quiet"
        if verbosity == 1:
            argument = argument+" --Verbosity Normal"
        if verbosity == 2:
            argument = argument+" --Verbosity Verbose"
        argument = argument.replace('"', '\\"')
        if verbosity == 2:
            write_message_to_stdout(f"Start executing '{title_local}'")
        process = Popen(f'epew {argument}')
        process.wait()
        stdout = _private_load_text(output_file_for_stdout)
        stderr = _private_load_text(output_file_for_stderr)
        exit_code = _private_get_number_from_filecontent(_private_load_text(output_file_for_exit_code))
        pid = _private_get_number_from_filecontent(_private_load_text(output_file_for_pid))
        if verbosity == 2:
            write_message_to_stdout(f"Finished executing '{title_local}' with exitcode "+str(exit_code))
        return (exit_code, stdout, stderr, pid)
    else:
        start_argument_as_array = [program]
        start_argument_as_array.extend(arguments.split())
        start_argument_as_string = f"{program} {arguments}"
        process = Popen(start_argument_as_string, stdout=PIPE, stderr=PIPE, cwd=workingdirectory, shell=True)
        pid = process.pid
        stdout, stderr = process.communicate()
        exit_code = process.wait()
        stdout = bytes_to_string(stdout).replace('\r', '')
        stderr = bytes_to_string(stderr).replace('\r', '')
        if write_output_to_standard_output:
            for line in stdout.splitlines():
                write_message_to_stdout(line)
            for line in stderr.splitlines():
                write_message_to_stderr(line)
        if throw_exception_if_exitcode_is_not_zero and exit_code != 0:
            raise Exception(f"'{workingdirectory}>{program} {arguments}' had exitcode {str(exit_code)}")
        return (exit_code, stdout, stderr, pid)


def _private_get_number_from_filecontent(filecontent: str) -> int:
    return int(filecontent.splitlines()[-1].strip().split(':')[1])


def _private_load_text(file: str) -> str:
    if os.path.isfile(file):
        with io.open(file, mode='r', encoding="utf-8") as f:
            content = f.read()
        os.remove(file)
        return content
    else:
        return ""


def append_line_to_file(file: str, line: str, encoding: str = "utf-8"):
    if(not file_is_empty(file)):
        line = os.linesep+line
    append_to_file(file, line, encoding)


def append_to_file(file: str, content: str, encoding: str = "utf-8"):
    with open(file, "a", encoding=encoding) as fileObject:
        fileObject.write(content)


def ensure_directory_exists(path: str):
    if(not os.path.isdir(path)):
        os.makedirs(path)


def ensure_file_exists(path: str):
    if(not os.path.isfile(path)):
        with open(path, "a+"):
            pass


def ensure_directory_does_not_exist(path: str):
    if(os.path.isdir(path)):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)


def ensure_file_does_not_exist(path: str):
    if(os.path.isfile(path)):
        os.remove(path)


def format_xml_file(filepath: str, encoding: str):
    with codecs.open(filepath, 'r', encoding=encoding) as file:
        text = file.read()
    text = xml.dom.minidom.parseString(text).toprettyxml()
    with codecs.open(filepath, 'w', encoding=encoding) as file:
        file.write(text)


def get_clusters_and_sectors_of_disk(diskpath: str):
    sectorsPerCluster = ctypes.c_ulonglong(0)
    bytesPerSector = ctypes.c_ulonglong(0)
    rootPathName = ctypes.c_wchar_p(diskpath)
    ctypes.windll.kernel32.GetDiskFreeSpaceW(rootPathName, ctypes.pointer(sectorsPerCluster), ctypes.pointer(bytesPerSector), None, None)
    return (sectorsPerCluster.value, bytesPerSector.value)


def extract_archive_with_7z(unzip_program_file: str, zipfile: str, password: str, output_directory: str):
    password_set = not password is None
    file_name = Path(zipfile).name
    file_folder = os.path.dirname(zipfile)
    argument = "x"
    if password_set:
        argument = f"{argument} -p\"{password}\""
    argument = f"{argument} -o {output_directory}"
    argument = f"{argument} {file_name}"
    return execute(unzip_program_file, argument, file_folder)


def get_internet_time() -> datetime.datetime:
    response = ntplib.NTPClient().request('pool.ntp.org')
    return datetime.datetime.fromtimestamp(response.tx_time)


def system_time_equals_internet_time(maximal_tolerance_difference: datetime.timedelta) -> bool:
    return abs(datetime.datetime.now() - get_internet_time()) < maximal_tolerance_difference


def timedelta_to_simple_string(delta) -> str:
    return (datetime.datetime(1970, 1, 1, 0, 0, 0) + delta).strftime('%H:%M:%S')


def resolve_relative_path_from_current_working_directory(path: str) -> str:
    return resolve_relative_path(path, os.getcwd())


def resolve_relative_path(path: str, base_path: str):
    if(os.path.isabs(path)):
        return path
    else:
        return str(Path(os.path.join(base_path, path)).resolve())


def get_metadata_for_file_for_clone_folder_structure(file: str) -> str:
    size = os.path.getsize(file)
    last_modified_timestamp = os.path.getmtime(file)
    hash_value = get_sha256_of_file(file)
    last_access_timestamp = os.path.getatime(file)
    return f'{{"size":"{size}","sha256":"{hash_value}","mtime":"{last_modified_timestamp}","atime":"{last_access_timestamp}"}}'


def clone_folder_structure(source: str, target: str, copy_only_metadata: bool):
    source = resolve_relative_path(source, os.getcwd())
    target = resolve_relative_path(target, os.getcwd())
    length_of_source = len(source)
    for source_file in absolute_file_paths(source):
        target_file = target+source_file[length_of_source:]
        ensure_directory_exists(os.path.dirname(target_file))
        if copy_only_metadata:
            with open(target_file, 'w', encoding='utf8') as f:
                f.write(get_metadata_for_file_for_clone_folder_structure(source_file))
        else:
            copyfile(source_file, target_file)


def system_time_equals_internet_time_with_default_tolerance() -> bool:
    return system_time_equals_internet_time(get_default_tolerance_for_system_time_equals_internet_time())


def check_system_time(maximal_tolerance_difference: datetime.timedelta):
    if not system_time_equals_internet_time(maximal_tolerance_difference):
        raise ValueError("System time may be wrong")


def check_system_time_with_default_tolerance():
    check_system_time(get_default_tolerance_for_system_time_equals_internet_time())


def get_default_tolerance_for_system_time_equals_internet_time() -> datetime.timedelta:
    return datetime.timedelta(hours=0, minutes=0, seconds=3)


def write_message_to_stdout(message: str, encoding: str = "utf-8"):
    sys.stderr.buffer.write(string_to_bytes(str_none_safe(message)+"\n", encoding))
    sys.stdout.flush()


def write_message_to_stderr(message: str, encoding: str = "utf-8"):
    sys.stderr.buffer.write(string_to_bytes(str_none_safe(message)+"\n", encoding))
    sys.stderr.buffer.flush()


def write_exception_to_stderr(exception: Exception, extra_message: str = None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr(")")


def write_exception_to_stderr_with_traceback(exception: Exception, traceback, extra_message: str = None):
    write_message_to_stderr("Exception(")
    write_message_to_stderr("Type: "+str(type(exception)))
    write_message_to_stderr("Message: "+str(exception))
    if str is not None:
        write_message_to_stderr("Extra-message: "+str(extra_message))
    write_message_to_stderr("Traceback: "+traceback.format_exc())
    write_message_to_stderr(")")


def string_has_content(string: str) -> bool:
    if string is None:
        return False
    else:
        return 0 < len(string)


def string_has_nonwhitespace_content(string: str) -> bool:
    if string is None:
        return False
    else:
        return 0 < len(string.strip())


def string_is_none_or_empty(string: str) -> bool:
    if string is None:
        return True
    if type(string) == str:
        return string == ""
    else:
        raise Exception("expected string-variable in argument of string_is_none_or_empty but the type was 'str'")


def string_is_none_or_whitespace(string: str) -> bool:
    if string_is_none_or_empty(string):
        return True
    else:
        return string.strip() == ""


def strip_new_lines_at_begin_and_end(string: str) -> str:
    return string.lstrip('\r').lstrip('\n').rstrip('\r').rstrip('\n')


def get_semver_version_from_gitversion(folder: str) -> str:
    return get_version_from_gitversion(folder, "MajorMinorPatch")


def get_version_from_gitversion(folder: str, variable: str) -> str:
    # called tweice as workaround for bug 1877 in gitversion ( https://github.com/GitTools/GitVersion/issues/1877 )
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


def replace_underscores_in_text(text: str, replacements: dict) -> str:
    changed = True
    while changed:
        changed = False
        for key, value in replacements.items():
            previousValue = text
            text = text.replace(f"__{key}__", value)
            if(not text == previousValue):
                changed = True
    return text


def replace_underscores_in_file(file: str, replacements: dict, encoding: str = "utf-8"):
    text = read_text_from_file(file, encoding)
    text = replace_underscores_in_text(text, replacements)
    write_text_to_file(file, text, encoding)


def _private_extension_matchs(file: str, obfuscate_file_extensions) -> bool:
    for extension in obfuscate_file_extensions:
        if file.lower().endswith("."+extension.lower()):
            return True
    return False


def get_ScriptCollection_version() -> str:
    return version

# </miscellaneous>
