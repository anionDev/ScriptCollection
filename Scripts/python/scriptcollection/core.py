from distutils.dir_util import copy_tree
from functools import lru_cache
import keyboard
import re
import ntplib
import base64
import os
from shutil import copytree
from subprocess import Popen, PIPE
import hashlib
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
scriptcollection_version = "1.0.0"


# idea for new structure:

# SCPython:
# SCPythonCreateWheelRelease: does: <prepare>;calls: SCPythonRunTests,SCPythonReleaseWheel
# SCPythonRunTests: does: <call pyTest-script>
# SCPythonReleaseWheel: does: <Release, upload>

# <Build>

# <SCDotNetReleaseExecutable>

def SCDotNetReleaseExecutable(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    return 0  # TODO


def SCDotNetReleaseExecutable_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetReleaseExecutable(args.configurationfile)

# </SCDotNetReleaseExecutable>

# <SCDotNetBuildExecutableAndRunTests>


def SCDotNetBuildExecutableAndRunTests(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    return 0  # TODO


def SCDotNetBuildExecutableAndRunTests_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetBuildExecutableAndRunTests(args.configurationfile)

# </SCDotNetBuildExecutableAndRunTests>

# <SCDotNetCreateExecutableRelease>


def SCDotNetCreateExecutableRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    return 0  # TODO


def SCDotNetCreateExecutableRelease_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetCreateExecutableRelease(args.configurationfile)

# </SCDotNetCreateExecutableRelease>

# <SCDotNetCreateNugetRelease>


def SCDotNetCreateNugetRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    version=_private_get_version(configparser)
    if(configparser.getboolean('prepare','prepare')):
        git_checkout(_private_get_config_item(configparser,'general','repository'),_private_get_config_item(configparser,'prepare','developmentbranchname'))
        if(configparser.getboolean('prepare','updateversionsincsprojfile')):
            csproj_file_with_path=_private_get_config_item(configparser,'build','folderofcsprojfile')+os.path.sep+_private_get_config_item(configparser,'build','csprojfilename')
            update_version_in_csproj_file(csproj_file_with_path, version)
            git_commit(configparser.get('general','repository'), "Updated version in '"+_private_get_config_item(configparser,'build','csprojfilename')+"' to "+version)
        git_merge(_private_get_config_item(configparser,'general','repository'), _private_get_config_item(configparser,'prepare','developmentbranchname'), _private_get_config_item(configparser,'prepare','masterbranchname'),False, False)
    try:
        exitcode=SCDotNetBuildNugetAndRunTests(configurationfile)
        build_was_successful= exitcode==0
        if not build_was_successful:
            write_exception_to_stderr("Building nuget and running testcases resulted in exitcode "+exitcode)
    except Exception as exception:
        build_was_successful=False
        write_exception_to_stderr(exception,"Building nuget and running testcases resulted in an error")
    if configparser.getboolean('prepare','prepare'):
        if build_was_successful:
            commit_id=git_commit( _private_get_config_item(configparser,'general','repository'),"Merged branch '"+ _private_get_config_item(configparser,'prepare','developmentbranchname')+"' into branch '"+_private_get_config_item(configparser,'prepare','masterbranchname')+"'")
            git_create_tag(_private_get_config_item(configparser,'general','repository'), commit_id, version)
            git_merge(_private_get_config_item(configparser,'general','repository'), _private_get_config_item(configparser,'prepare','masterbranchname'), _private_get_config_item(configparser,'prepare','developmentbranchname'),True)
        else:
            git_merge_abort(_private_get_config_item(configparser,'general','repository'))
            git_checkout(_private_get_config_item(configparser,'general','repository'),_private_get_config_item(configparser,'prepare','developmentbranchname'))
            write_message_to_stderr("Building and executing testcases was not successful")
            return 1
    SCDotNetReference(configurationfile)
    SCDotNetReleaseNuget(configurationfile)
    git_commit(configparser.get('release','releaserepository'), "Added "+_private_get_config_item(configparser,'general','productname')+" "+_private_get_config_item(configparser,'prepare','gittagprefix')+" "+version)
    return 0

def SCDotNetCreateNugetRelease_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetCreateNugetRelease(args.configurationfile)

# </SCDotNetCreateNugetRelease>

# <SCDotNetBuildNugetAndRunTests>


nuget_template_file_content = r"""<?xml version="1.0" encoding="utf-8"?>
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
    if configparser.getboolean('build', 'hastestproject'):
        SCDotNetRunTests(configurationfile)
    for runtime in _private_get_config_items(configparser, 'build', 'runtimes'):
        custom_replacement={'runtime':runtime}
        SCDotNetBuild(_private_get_config_item(configparser, 'build', 'folderofcsprojfile'), _private_get_config_item(configparser, 'build', 'csprojfilename'), _private_get_config_item(configparser, 'build', 'buildoutputdirectory',custom_replacement), _private_get_config_item(configparser, 'build', 'buildconfiguration'), runtime, _private_get_config_item(configparser, 'build', 'dotnetframework'), True, "normal",  _private_get_config_item(configparser, 'build', 'filestosign'), _private_get_config_item(configparser, 'build', 'snkfile'))
    publishdirectory = _private_get_config_item(configparser, 'build', 'publishdirectory')
    publishdirectory_binary = publishdirectory+os.path.sep+"Binary"
    ensure_directory_does_not_exist(publishdirectory)
    ensure_directory_exists(publishdirectory_binary)
    copy_tree(_private_get_config_item(configparser, 'build', 'buildoutputdirectory'), publishdirectory_binary)

    nuspec_content = _private_replace_underscores(nuget_template_file_content, configparser)
    nuspecfilename = configparser.get('general', 'productname')+".nuspec"
    nuspecfile = os.path.join(publishdirectory, nuspecfilename)
    with open(nuspecfile, encoding="utf-8", mode="w") as f:
        f.write(nuspec_content)
    execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}", publishdirectory)
    return 0

def SCDotNetBuildNugetAndRunTests_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetBuildNugetAndRunTests(args.configurationfile)

# </SCDotNetBuildNugetAndRunTests>

# <SCDotNetReleaseNuget>


def SCDotNetReleaseNuget(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    version = _private_get_version(configparser)
    publishdirectory = _private_get_config_item(configparser, 'build', 'publishdirectory')
    latest_nupkg_file = configparser.get('general', 'productname')+"."+version+".nupkg"
    for localnugettarget in _private_get_config_items(configparser,'release', 'localnugettargets'):
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}", publishdirectory)
    commitmessage = f"Added {_private_get_config_item(configparser,'general','productname')} {_private_get_config_item(configparser,'prepare','gittagprefix')}{version}"
    for localnugettargetrepository in _private_get_config_items(configparser,'release', 'localnugettargetrepositories'):
        git_commit(localnugettargetrepository, commitmessage)
    return 0

def SCDotNetReleaseNuget_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCDotNetReleaseNuget(args.configurationfile)

# </SCDotNetReleaseNuget>

# <SCDotNetReference>


def SCDotNetReference(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    if configparser.getboolean('reference','generatereference'):
        docfx_file=_private_get_config_item(configparser,'reference','docfxfile')
        docfx_filename=os.path.basename(docfx_file)
        docfx_filefolder=os.path.dirname(docfx_file)
        _private_replace_underscore_in_file(_private_get_config_item(configparser, 'reference', 'referencerepositoryindexfile'),configparser)
        execute_and_raise_exception_if_exit_code_is_not_zero("docfx", docfx_file, docfx_filefolder)
        shutil.copyfile(_private_get_config_item(configparser, 'build', 'folderoftestcsprojfile')+os.path.sep+_private_get_coverage_filename(configparser),_private_get_config_item(configparser,'reference','coveragefolder')+os.path.sep+os.path.sep+_private_get_coverage_filename(configparser))
        execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator", '-reports:"'+_private_get_coverage_filename(configparser)+'" -targetdir:"'+configparser.get('reference','coveragereportfolder')+'"',_private_get_config_item(configparser,'reference','coveragefolder'))
        git_commit(_private_get_config_item(configparser,'reference','referencerepository'),"Updated reference")
        if configparser.getboolean('reference','generatereference'):
            git_push(_private_get_config_item(configparser, 'reference', 'referencerepository'),_private_get_config_item(configparser, 'reference', 'exportreferenceremotename'),"master","master")
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    return 0


def SCDotNetReference_cli():
    parser = argparse.ArgumentParser(description='TODO')
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
    parser = argparse.ArgumentParser(description='Builds a DotNet-project by a given C#-project. Requires dotnet as available commandline-command.')
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
    runtime=_private_get_config_item(configparser, 'build', 'testruntime')
    custom_replacement={'runtime':runtime}
    SCDotNetBuild(_private_get_config_item(configparser, 'build', 'folderoftestcsprojfile'), _private_get_config_item(configparser, 'build', 'testcsprojfilename'), _private_get_config_item(configparser, 'build', 'testoutputfolder',custom_replacement), _private_get_config_item(configparser, 'build', 'buildconfiguration'), runtime, _private_get_config_item(configparser, 'build', 'testdotnetframework'), True, "normal", None,None)
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", "test "+_private_get_config_item(configparser, 'build', 'testcsprojfilename')+" --no-build -c " + _private_get_config_item(configparser, 'build', 'buildconfiguration') + " --verbosity normal /p:CollectCoverage=true /p:CoverletOutput=" + _private_get_coverage_filename(configparser)+" /p:CoverletOutputFormat=opencover ", _private_get_config_item(configparser, 'build', 'folderoftestcsprojfile'), 3600, True, False, "Execute tests")
    return 0  # TODO


def SCDotNetRunTests_cli():
    parser = argparse.ArgumentParser(description='TODO')
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
    return 0  # TODO


def SCPythonCreateWheelRelease_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonCreateWheelRelease(args.configurationfile)

# </SCPythonCreateWheelRelease>

# <SCPythonRunTests>


def SCPythonRunTests(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    return 0  # TODO


def SCPythonRunTests_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonRunTests(args.configurationfile)

# </SCPythonRunTests>

# <SCPythonReleaseWheel>


def SCPythonReleaseWheel(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    return 0  # TODO


def SCPythonReleaseWheel_cli():
    parser = argparse.ArgumentParser(description='TODO')
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    return SCPythonReleaseWheel(args.configurationfile)

# </SCPythonReleaseWheel>

# <Helper>


def _private_get_config_item(configparser: ConfigParser, section: str, propertyname: str,custom_replacements:dict={}):
    return _private_replace_underscores(configparser.get(section, propertyname), configparser,custom_replacements)

def _private_get_config_items(configparser: ConfigParser, section: str, propertyname: str,custom_replacements:dict={}):
    itemlist_as_string =_private_replace_underscores(configparser.get(section, propertyname), configparser,custom_replacements)
    if ',' in itemlist_as_string:
        return [item.strip() for item in itemlist_as_string.split(',')]
    else:
        return [itemlist_as_string.strip()]


def _private_get_coverage_filename(configparser: ConfigParser):
    return configparser.get("general", "productname")+".TestCoverage.opencover.xml"


def _private_get_version(configparser: ConfigParser):
    return _private_get_version_helper(configparser.get('general', 'repository'))

@lru_cache(maxsize=None)
def _private_get_version_helper(folder:str):
    return get_semver_version_from_gitversion(folder)

def _private_get_publishdirectory(configparser):
    result = _private_get_config_item(configparser, 'build', 'publishdirectory')
    ensure_directory_exists(result)
    return result

def _private_replace_underscore_in_file(file:str,configparser: ConfigParser,replacements:dict={},encoding="utf-8"):
    with codecs.open(file, 'r', encoding=encoding) as f:
        text = f.read()
    text = _private_replace_underscores(text,configparser,replacements)
    with codecs.open(file, 'w', encoding=encoding) as f:
        f.write(text)

def _private_replace_underscores(string: str, configparser: ConfigParser,replacements:dict={}):
    replacements["productname"]=configparser.get('general', 'productname')
    replacements["version"]= _private_get_version(configparser)
    replacements["author"]=configparser.get('general', 'author')
    replacements["description"]=configparser.get('general', 'description')
    replacements["developmentbranchname"]=configparser.get('prepare', 'developmentbranchname')
    replacements["masterbranchname"]=configparser.get('prepare', 'masterbranchname')
    replacements["year"]=str(datetime.datetime.now().year)
    replacements["dotnetframework"]= configparser.get('build', 'dotnetframework')
    replacements["buildconfiguration"]=configparser.get('build', 'buildconfiguration')
    for key, value in replacements.items():
        string = string.replace(f"__{key}__", value)
    return string

# </Helper>

# </Build>

# <SCGenerateThumbnail>


def _private_calculate_lengh_in_seconds(file: str, wd: str):
    argument = '-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "'+file+'"'
    return float(execute_and_raise_exception_if_exit_code_is_not_zero("ffprobe", argument, wd)[1])


def _private_create_thumbnails(file: str, length_in_seconds: float, amount_of_images: int, wd: str, tempname_for_thumbnails):
    rrp = length_in_seconds/(amount_of_images-2)
    argument = '-i "'+file+'" -r 1/'+str(rrp)+' -vf scale=-1:120 -vcodec png '+tempname_for_thumbnails+'-%002d.png'
    execute_and_raise_exception_if_exit_code_is_not_zero("ffmpeg", argument, wd)


def _private_create_thumbnail(outputfilename: str, wd: str, length_in_seconds: float, tempname_for_thumbnails):
    duration = datetime.timedelta(seconds=length_in_seconds)
    info = timedelta_to_simple_string(duration)
    argument = '-title "'+outputfilename+" ("+info+')" -geometry +4+4 '+tempname_for_thumbnails+'*.png "'+outputfilename+'.png"'
    execute_and_raise_exception_if_exit_code_is_not_zero("montage", argument, wd)


def SCGenerateThumbnail(file: str):
    tempname_for_thumbnails = "t"+str(uuid.uuid4())

    amount_of_images = 16
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
    parser = argparse.ArgumentParser(description='Takes some pdf-files and merge them to one single pdf-file. Usage: "python MergePDFs.py myfile1.pdf,myfile2.pdf,myfile3.pdf result.pdf"')
    parser.add_argument('files', help='Comma-separated filenames')
    parser.add_argument('outputfile', help='File for the resulting pdf-document')
    args = parser.parse_args()
    SCMergePDFs(args.files.split(','), args.outputfile)

# </SCMergePDFs>

# <SCOrganizeLinesInFile>


def SCOrganizeLinesInFile(file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False, remove_empty_lines: bool = True):
    if os.path.isfile(file):

        # read file
        with open(file, 'r', encoding=encoding) as f:
            content = f.read()
        lines = content.splitlines()

        # remove trailing newlines
        temp = []
        for line in lines:
            temp.append(line.rstrip())
        lines = temp

        # store first line if desired
        if(len(lines) > 0 and ignore_first_line):
            first_line = lines.pop(0)

        # remove empty lines if desired
        if remove_empty_lines and False:
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

        # concat lines separated by newline
        result = ""
        is_first_line = True
        for line in lines:
            if(is_first_line):
                result = line
                is_first_line = False
            else:
                result = result+'\n'+line

        # write result to file
        with open(file, 'w', encoding=encoding) as f:
            f.write(result)
    else:
        write_message_to_stdout(f"File '{file}' does not exist")


def SCOrganizeLinesInFile_cli():
    parser = argparse.ArgumentParser(description='Processes the lines of a file with the given commands')

    parser.add_argument('file', help='File which should be transformed')
    parser.add_argument('--encoding', default="utf-8", help='Encoding for the file which should be transformed')
    parser.add_argument("--sort", type=string_to_boolean, nargs='?', const=True, default=False, help="Sort lines")
    parser.add_argument("--remove_duplicated_lines", type=string_to_boolean, nargs='?', const=True, default=False, help="Remove duplicate lines")
    parser.add_argument("--ignore_first_line", type=string_to_boolean, nargs='?', const=True, default=False, help="Ignores the first line in the file")
    parser.add_argument("--remove_empty_lines", type=string_to_boolean, nargs='?', const=True, default=False, help="Removes lines which are empty or contains only whitespaces")

    args = parser.parse_args()
    SCOrganizeLinesInFile(args.file, args.encoding, args.sort, args.remove_duplicated_lines, args.ignore_first_line, args.remove_empty_lines)


# </SCOrganizeLinesInFile>

# <miscellaneous>


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
    if(private_should_get_replaced(filename, replace_from, replace_only_full_match)):
        folder_of_file = os.path.dirname(file)
        os.rename(file, os.path.join(folder_of_file, filename.replace(replace_from, replace_to)))


def replace_in_foldername(folder: str, replace_from: str, replace_to: str, replace_only_full_match=False):
    foldername = Path(folder).name
    if(private_should_get_replaced(foldername, replace_from, replace_only_full_match)):
        folder_of_folder = os.path.dirname(folder)
        os.rename(folder, os.path.join(folder_of_folder, foldername.replace(replace_from, replace_to)))


def private_should_get_replaced(input_text, search_text, replace_only_full_match):
    if replace_only_full_match:
        return input_text == search_text
    else:
        return search_text in input_text


def absolute_file_paths(directory: str):
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            yield os.path.abspath(os.path.join(dirpath, filename))


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


def execute_and_raise_exception_if_exit_code_is_not_zero(program: str, arguments: str = "", workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity=1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None, write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero: bool = False):
    result = execute_full(program, arguments, workingdirectory, print_errors_as_information, log_file, timeoutInSeconds, verbosity, addLogOverhead, title)
    if result[0] == 0:
        return result
    else:
        if(write_strerr_of_program_to_local_strerr_when_exitcode_is_not_zero):
            write_message_to_stderr(result[2])
        raise Exception(f"'{workingdirectory}>{program} {arguments}' had exitcode {str(result[0])}")


def execute(program: str, arguments: str, workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity=1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None):
    result = execute_raw(program, arguments, workingdirectory, timeoutInSeconds, verbosity, addLogOverhead, title, print_errors_as_information, log_file)
    return result[0]


def execute_raw(program: str, arguments: str, workingdirectory: str = "", timeoutInSeconds: int = 3600, verbosity=1, addLogOverhead: bool = False, title: str = None, print_errors_as_information: bool = False, log_file: str = None):
    return execute_full(program, arguments, workingdirectory, print_errors_as_information, log_file, timeoutInSeconds, verbosity, addLogOverhead, title)


def execute_full(program: str, arguments: str, workingdirectory: str = "", print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds=3600, verbosity=1, addLogOverhead: bool = False, title: str = None):
    if string_is_none_or_whitespace(title):
        title_for_message = ""
    else:
        title_for_message = f"for task '{title}' "
    title_local = f"epew {title_for_message}('{workingdirectory}>{program} {arguments}')"
    if verbosity == 2:
        write_message_to_stdout(f"Start executing {title_local}")
    write_message_to_stdout(f"Start executing {title_local}")
    if workingdirectory == "":
        workingdirectory = os.getcwd()
    else:
        if not os.path.isabs(workingdirectory):
            workingdirectory = os.path.abspath(workingdirectory)

    output_file_for_stdout = tempfile.gettempdir() + os.path.sep+str(uuid.uuid4()) + ".temp.txt"
    output_file_for_stderr = tempfile.gettempdir() + os.path.sep+str(uuid.uuid4()) + ".temp.txt"

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
    argument = argument+' -t "'+str_none_safe(title)+'"'
    process = Popen("epew "+argument)
    exit_code = process.wait()
    stdout = private_load_text(output_file_for_stdout)
    stderr = private_load_text(output_file_for_stderr)
    if verbosity == 2:
        write_message_to_stdout(f"Finished executing {title_local} with exitcode "+str(exit_code))
    return (exit_code, stdout, stderr)


def private_load_text(file: str):
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


def get_clusters_and_sectors(dispath: str):
    sectorsPerCluster = ctypes.c_ulonglong(0)
    bytesPerSector = ctypes.c_ulonglong(0)
    rootPathName = ctypes.c_wchar_p(dispath)
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
        string == ""
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
    return strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("gitversion", "/showVariable "+variable, folder, 30, 0)[1])


def move_content_of_folder(srcDir, dstDir):
    srcDirFull = resolve_relative_path_from_current_working_directory(srcDir)
    dstDirFull = resolve_relative_path_from_current_working_directory(dstDir)
    for file in get_direct_files_of_folder(srcDirFull):
        shutil.move(file, dstDirFull)
    for sub_folder in get_direct_folders_of_folder(srcDirFull):
        shutil.move(sub_folder, dstDirFull)


def replace_xmltag_in_file(file, tag: str, new_value: str, encoding="utf-8"):
    with open(file, encoding=encoding, mode="r") as f:
        content = f.read()
        content = re.sub(f"<{tag}>.*</{tag}>", f"<{tag}>{new_value}</{tag}>", content)
    with open(file, encoding=encoding, mode="w") as f:
        f.write(content)


def update_version_in_csproj_file(file: str, version: str):
    replace_xmltag_in_file(file, "Version", version)
    replace_xmltag_in_file(file, "AssemblyVersion", version + ".0")
    replace_xmltag_in_file(file, "FileVersion", version + ".0")


def _private_get_publishdirectory(configparser, version: str):
    result = configparser.get('build', 'publishdirectory')
    result = result.replace("__version__", version)
    ensure_directory_exists(result)
    return result


def get_scriptcollection_version():
    return scriptcollection_version


def get_target_runtimes(configparser):
    result = []
    for runtime in configparser.get('build', 'runtimes').split(","):
        result.append(runtime.strip())
    return result

# </miscellaneous>

# <git>


def git_repository_has_new_untracked_files(repository_folder: str):
    return private_git_repository_has_uncommitted_changes(repository_folder, "ls-files --exclude-standard --others")


def git_repository_has_unstaged_changes(repository_folder: str):
    if(private_git_repository_has_uncommitted_changes(repository_folder, "diff")):
        return True
    if(git_repository_has_new_untracked_files(repository_folder)):
        return True
    return False


def git_repository_has_staged_changes(repository_folder: str):
    return private_git_repository_has_uncommitted_changes(repository_folder, "diff --cached")


def git_repository_has_uncommitted_changes(repository_folder: str):
    if(git_repository_has_unstaged_changes(repository_folder)):
        return True
    if(git_repository_has_staged_changes(repository_folder)):
        return True
    return False


def private_git_repository_has_uncommitted_changes(repository_folder: str, argument: str):
    return not string_is_none_or_whitespace(execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, repository_folder, 3600, 0)[1])


def git_get_current_commit_id(repository_folder: str):
    result = execute_and_raise_exception_if_exit_code_is_not_zero("git", "rev-parse --verify HEAD", repository_folder, 30, 0)
    return result[1].replace('\r', '').replace('\n', '')


def git_push(folder: str, remotename: str, localbranchname: str, remotebranchname: str):
    argument = f"push {remotename} {localbranchname}:{remotebranchname}"
    result = execute_and_raise_exception_if_exit_code_is_not_zero("git", argument, folder)
    if not (result[0] == 0):
        raise ValueError(f"'git {argument}' results in exitcode "+str(result[0]))
    return result[1].replace('\r', '').replace('\n', '')


def git_clone_if_not_already_done(folder: str, link: str):
    exit_code = -1
    original_cwd = os.getcwd()
    try:
        if(not os.path.isdir(folder)):
            argument = f"clone {link} --recurse-submodules --remote-submodules"
            execute_exit_code = execute_and_raise_exception_if_exit_code_is_not_zero(f"git {argument}", argument, original_cwd)[0]
            if execute_exit_code != 0:
                write_message_to_stdout(f"'git {argument}' had exitcode {str(execute_exit_code)}")
                exit_code = execute_exit_code
    finally:
        os.chdir(original_cwd)
    return exit_code


def git_commit(directory: str, message: str):
    if (git_repository_has_uncommitted_changes(directory)):
        write_message_to_stdout(f"Committing all changes in {directory}...")
        execute_and_raise_exception_if_exit_code_is_not_zero("git", "add -A", directory, 3600)[0]
        execute_and_raise_exception_if_exit_code_is_not_zero("git", f'commit -m "{message}"', directory, 600)[0]
    else:
        write_message_to_stdout(f"There are no changes to commit in {directory}")
    return git_get_current_commit_id(directory)


def git_create_tag(directory: str, target_for_tag: str, tag: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", f"tag {tag} {target_for_tag}", directory, 3600)


def git_checkout(directory: str, branch: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "checkout "+branch, directory, 3600)


def git_merge_abort(directory: str):
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "merge --abort", directory, 3600)


def git_merge(directory: str, sourcebranch: str, targetbranch: str, fastforward: bool = True, commit:bool=True):
    git_checkout(directory, targetbranch)
    if(fastforward):
        ff = ""
    else:
        ff = "--no-ff "
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "merge --no-commit "+ff+sourcebranch, directory, 3600)
    if commit:
        return git_commit(directory, f"Merge branch '{sourcebranch}' into '{targetbranch}'")
    else:
        git_get_current_commit_id(directory)

# </git>
