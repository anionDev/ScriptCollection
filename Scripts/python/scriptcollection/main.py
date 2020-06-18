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

# <SCDotNetCreateReleaseBuildGeneral>


def SCDotNetCreateReleaseBuildGeneral(configurationfile: str):
    configurationfile = configurationfile
    write_message_to_stdout(f"Run generic releasescript-part '{os.path.basename(__file__)}' with configurationfile '{configurationfile}'")

    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    build_tools_folder = abspath(f"..{os.path.sep}GeneralTasks")
    repository_folder = configparser.get('general', 'repository')
    version = get_semver_version_from_gitversion(repository_folder)
    publish_directory = get_publishdirectory(configparser, version)
    code_coverage_folder = publish_directory
    runtime_for_tests = configparser.get('build', 'testruntime')

    for runtime in get_target_runtimes(configparser):
        publish_directory_for_runtime = os.path.join(publish_directory, runtime)
        ensure_directory_exists(publish_directory_for_runtime)
        argument = ""

        # parameter for project
        argument = argument + ' --folder_of_csproj_file '+encapsulate_with_quotes(configparser.get('build', 'folderofcsprojfile'))
        argument = argument + ' --csproj_filename '+encapsulate_with_quotes(configparser.get('build', 'csprojfilename'))
        argument = argument + ' --publish_directory '+encapsulate_with_quotes(publish_directory_for_runtime)
        argument = argument + ' --output_directory '+encapsulate_with_quotes(configparser.get('build', 'buildoutputdirectory'))
        argument = argument + ' --framework '+configparser.get('build', 'dotnetframework')
        argument = argument + ' --runtimeid '+runtime

        # parameter for testproject
        if configparser.getboolean('build', 'hastestproject') and runtime_for_tests == runtime:
            argument = argument + ' --has_test_project'
            argument = argument + ' --folder_of_test_csproj_file '+encapsulate_with_quotes(configparser.get('build', 'folderoftestcsprojfile'))
            argument = argument + ' --test_csproj_filename '+encapsulate_with_quotes(configparser.get('build', 'testcsprojfilename'))
            argument = argument + ' --test_output_directory '+encapsulate_with_quotes(configparser.get('build', 'testoutputfolder'))
            argument = argument + ' --test_framework '+encapsulate_with_quotes(configparser.get('build', 'testdotnetframework'))
            argument = argument + ' --test_runtimeid '+encapsulate_with_quotes(runtime_for_tests)
            argument = argument + ' --publish_coverage '+str(True)
            argument = argument + ' --code_coverage_folder '+encapsulate_with_quotes(code_coverage_folder)

        # parameter for project and testproject
        argument = argument + f' --clear_output_directory {str(True)}'
        argument = argument + f' --productname "'+configparser.get('general', 'productname')+'"'
        argument = argument + f' --buildconfiguration "' + configparser.get('build', 'buildconfiguration')+'"'

        # build and execute testcases
        execute_and_raise_exception_if_exit_code_is_not_zero("python", f"{build_tools_folder}{os.path.sep}BuildTestprojectAndExecuteTests.py {argument}", os.getcwd(), 3600, 1, False, "Build "+configparser.get('general', 'productname'))

        # sign assembly
        if configparser.getboolean('build', 'signfiles'):
            for file_to_sign in configparser.get('build', 'filestosign').split(","):
                file_to_sign = file_to_sign.strip()
                snkfile = configparser.get('build', 'snkfile')
                SCDotNetCreateReleaseSignAssembly(publish_directory_for_runtime+os.path.sep+file_to_sign, snkfile)


def SCDotNetCreateReleaseBuildGeneral_cli():

    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCDotNetCreateReleaseBuildGeneral(args.configurationfile)

# </SCDotNetCreateReleaseBuildGeneral>

# <SCDotNetCreateReleaseBuildProject>


def SCDotNetCreateReleaseBuildProject():
    pass  # todo


def SCDotNetCreateReleaseBuildProject_cli():

    parser = argparse.ArgumentParser(description='Compiles a csproj-file. This scripts also download required nuget-packages.')
    parser.add_argument('--folder_of_csproj_file', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file which should be compiled')
    parser.add_argument('--buildconfiguration', help='Specifies the Buildconfiguration (e.g. Debug or Release)')
    parser.add_argument('--additional_build_arguments', help='Specifies arbitrary arguments which are passed to the build-process')
    parser.add_argument('--output_directory', help='Specifies output directory for the compiled program')
    parser.add_argument('--folder_for_nuget_restore', help='Specifies folder where nuget should be executed to restore the required nuget-packages')
    parser.add_argument('--clear_output_directory', type=string_to_boolean, nargs='?', const=True, default=False, help='If true then the output directory will be cleared before compiling the program')
    parser.add_argument('--runtimeid', default="win10-x64", help='Specifies runtime-id-argument for build-process')
    parser.add_argument('--verbosity', default="minimal", help='Specifies verbosity for build-process')
    parser.add_argument('--framework', default="netcoreapp3.1", help='Specifies targetframework')

    args = parser.parse_args()

    # clear output-directory if desired
    if os.path.isdir(args.output_directory) and args.clear_output_directory:
        shutil.rmtree(args.output_directory)
    ensure_directory_exists(args.output_directory)

    argument = f'"{args.csproj_filename}"'
    argument = argument + f' --no-incremental'
    argument = argument + f' --verbosity {args.verbosity}'
    argument = argument + f' --configuration {args.buildconfiguration}'
    argument = argument + f' --framework {args.framework}'
    argument = argument + f' --runtime {args.runtimeid}'
    if not string_is_none_or_whitespace(args.output_directory):
        argument = argument + f' --output "{args.output_directory}"'
    argument = argument + f' {args.additional_build_arguments}'

    # run dotnet build
    execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f'build {argument}', args.folder_of_csproj_file, 3600, True, False, "Build")

# </SCDotNetCreateReleaseBuildProject>

# <SCDotNetCreateReleaseBuildTestprojectAndExecuteTests>


def SCDotNetCreateReleaseBuildTestprojectAndExecuteTests():
    pass  # todo


def SCDotNetCreateReleaseBuildTestprojectAndExecuteTests_cli():

    parser = argparse.ArgumentParser(description='Builds a program using msbuild and execute the defined testcases')

    # parameter for mainproject
    parser.add_argument('--folder_of_csproj_file', help='Specifies the folder where the csproj-file is located')
    parser.add_argument('--csproj_filename', help='Specifies the csproj-file-name which should be compiled')
    parser.add_argument('--publish_directory', help='Specifies release-target-directory for the compiled program when the compile-process was successful.')
    parser.add_argument('--clear_publish_directory', type=string_to_boolean, nargs='?', const=True, default=False, help='If true then the publish directory will be cleared before compiling the program')
    parser.add_argument('--output_directory', help='Specifies output directory for the compiled program')
    parser.add_argument('--runtimeid', default="win10-x64", help='Specifies runtime-id-argument for build-process')
    parser.add_argument('--framework', default="netstandard2.1", help='Specifies targetframework')

    # parameter for testproject
    parser.add_argument('--folder_of_test_csproj_file', help='Specifies the folder where the test-csproj-file is located')
    parser.add_argument('--test_csproj_filename', help='Specifies the test-csproj-file-name which should be compiled')
    parser.add_argument('--test_output_directory', help='Specifies output directory for the compiled test-dll')
    parser.add_argument('--additional_test_arguments', default="", help='Specifies arbitrary arguments which are passed to vstest')
    parser.add_argument('--test_runtimeid', default="win10-x64", help='Specifies runtime-id-argument for build-process of the testproject')
    parser.add_argument('--test_framework', default="netcoreapp3.1", help='Specifies targetframework of the testproject')
    parser.add_argument('--code_coverage_folder', help='Specifies the folder for the code-coverage-file')
    parser.add_argument('--has_test_project', type=string_to_boolean, nargs='?', const=True, default=False, help='')
    parser.add_argument('--publish_coverage', type=string_to_boolean, nargs='?', const=True, default=False, help='Specifies whether the testcoverage-result should be copied to the publish-directory')

    # parameter for build project and testproject
    parser.add_argument('--verbosity', default="minimal", help='Specifies verbosity for build-process')
    parser.add_argument('--productname', help='Specifies the name of the product')
    parser.add_argument('--buildconfiguration', help='Specifies the Buildconfiguration (e.g. "debug" or "release")')
    parser.add_argument('--additional_build_arguments', default="", help='Specifies arbitrary arguments which are passed to msbuild')
    parser.add_argument('--clear_output_directory', type=string_to_boolean, nargs='?', const=True, default=False, help='If true then the output directory will be cleared before compiling the program')

    args = parser.parse_args()

    # build project
    argument = ""
    argument = argument+" --folder_of_csproj_file "+args.folder_of_csproj_file
    argument = argument+" --csproj_filename "+args.csproj_filename
    argument = argument+" --buildconfiguration "+args.buildconfiguration
    argument = argument+" --additional_build_arguments "+f'"{str_none_safe(args.additional_build_arguments)}"'
    argument = argument+" --output_directory "+args.output_directory
    argument = argument+" --clear_output_directory "+str_none_safe(args.clear_output_directory)
    argument = argument+" --runtimeid "+args.runtimeid
    argument = argument+" --verbosity "+args.verbosity
    argument = argument+" --framework "+args.framework
    execute_and_raise_exception_if_exit_code_is_not_zero("SCDotNetCreateReleaseBuildProject", argument, "", 3600, True, False, "Build project")

    # testproject
    if args.has_test_project:
        testargument = ""
        testargument = testargument+" --folder_of_csproj_file "+args.folder_of_test_csproj_file
        testargument = testargument+" --csproj_filename "+args.test_csproj_filename
        testargument = testargument+" --buildconfiguration "+args.buildconfiguration
        testargument = testargument+" --additional_build_arguments "+f'"{str_none_safe(args.additional_build_arguments)}"'
        testargument = testargument+" --output_directory "+args.test_output_directory
        testargument = testargument+" --clear_output_directory "+str_none_safe(args.clear_output_directory)
        testargument = testargument+" --runtimeid "+args.test_runtimeid
        testargument = testargument+" --verbosity "+args.verbosity
        testargument = testargument+" --framework "+args.test_framework
        execute_and_raise_exception_if_exit_code_is_not_zero("SCDotNetBuildProjectGeneral", testargument, "", 3600, True, False, "Build testproject")

        # execute testcases
        testcoveragefilename = args.productname+".TestCoverage.opencover.xml"
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", "test "+args.test_csproj_filename+" -c " + args.buildconfiguration + " --verbosity normal --no-build /p:CollectCoverage=true /p:CoverletOutput="+testcoveragefilename+" /p:CoverletOutputFormat=opencover "+str_none_safe(args.additional_test_arguments), args.folder_of_test_csproj_file, 3600, True, False, "Execute tests")

    # clear publish-directory if desired
    if os.path.isdir(args.publish_directory) and args.clear_publish_directory:
        shutil.rmtree(args.publish_directory)
    ensure_directory_exists(args.publish_directory)

    # export program
    copytree(args.output_directory, args.publish_directory)
    if args.publish_coverage and args.has_test_project:
        shutil.copy(args.folder_of_test_csproj_file+os.path.sep+testcoveragefilename, args.code_coverage_folder)

# </SCDotNetCreateReleaseBuildTestprojectAndExecuteTests>

# <SCdotnetCreateReleaseGeneral>


def SCdotnetCreateReleaseGeneral(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    if configparser.getboolean('prepare', 'prepare'):
        SCDotNetCreateReleasePrepare(configurationfile)
    SCDotNetCreateReleaseBuildGeneral(configurationfile)
    SCDotNetCreateReleaseRelease(configurationfile)
    if configparser.getboolean('reference', 'generatereference'):
        SCDotNetCreateReleaseReference(configurationfile)


def SCdotnetCreateReleaseGeneral_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCdotnetCreateReleaseGeneral(args.configurationfile)


# </SCdotnetCreateReleaseGeneral>

# <SCDotNetCreateReleasePrepare>


def SCDotNetCreateReleasePrepare(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    git_checkout(configparser.get('general', 'repository'), configparser.get('prepare', 'developmentbranchname'))
    version = get_semver_version_from_gitversion(configparser.get('general', 'repository'))
    if(configparser.getboolean('prepare', 'updateversionsincsprojfile')):
        csproj_file_with_path = configparser.get('build', 'folderofcsprojfile')+os.path.sep+configparser.get('build', 'csprojfilename')
        update_version_in_csproj_file(csproj_file_with_path, version)
        git_commit(configparser.get('general', 'repository'), "Updated version in '"+configparser.get('build', 'csprojfilename')+"'")

    commit_id = git_merge(configparser.get('general', 'repository'), configparser.get('prepare', 'developmentbranchname'), configparser.get('prepare', 'masterbranchname'), False)
    git_create_tag(configparser.get('general', 'repository'), commit_id, configparser.get('prepare', 'gittagprefix') + version)
    git_merge(configparser.get('general', 'repository'), configparser.get('prepare', 'masterbranchname'), configparser.get('prepare', 'developmentbranchname'), True)


def SCDotNetCreateReleasePrepare_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCDotNetCreateReleasePrepare(args.configurationfile)

# </SCDotNetCreateReleasePrepare>

# <SCDotNetCreateReleaseReference>


def SCDotNetCreateReleaseReference(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    repository_folder = configparser.get('general', 'repository')
    version = get_semver_version_from_gitversion(repository_folder)

    publishdirectory = get_publishdirectory(configparser, version)
    opencoverreportfile = publishdirectory+os.path.sep+configparser.get('general', 'productname')+".TestCoverage.opencover.xml"

    execute_and_raise_exception_if_exit_code_is_not_zero("reportgenerator", '-reports:"'+opencoverreportfile+'" -targetdir:"'+configparser.get('reference', 'coveragereportfolder')+'"')

    docfx_file_with_path = configparser.get('reference', 'docfxfile')
    docfxfolder = os.path.dirname(docfx_file_with_path)
    docfxfile = os.path.basename(docfx_file_with_path)
    execute_and_raise_exception_if_exit_code_is_not_zero("docfx", docfxfile, docfxfolder)

    commitmessage = "Updated reference"
    git_commit(configparser.get('reference', 'referencerepository'), commitmessage)
    git_commit(configparser.get('release', 'releaserepository'), commitmessage)

    if configparser.getboolean('reference', 'exportreference'):
        execute_and_raise_exception_if_exit_code_is_not_zero(configparser.get('reference', 'exportreferencescriptfile'))


def SCDotNetCreateReleaseReference_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCDotNetCreateReleaseReference(args.configurationfile)

# </SCDotNetCreateReleaseReference>

# <SCDotNetCreateReleaseRelease>


def SCDotNetCreateReleaseRelease(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))
    repository_folder = configparser.get('general', 'repository')
    version = get_semver_version_from_gitversion(repository_folder)
    commitmessage = f"Added {configparser.get('general','productname')} {configparser.get('prepare','gittagprefix')}{version}"

    # build nugetpackage
    if configparser.getboolean('release', 'createnugetpackage'):
        commit_id = strip_new_lines_at_begin_and_end(execute_and_raise_exception_if_exit_code_is_not_zero("git", "rev-parse HEAD", repository_folder, 30, 0)[1])
        year = str(datetime.datetime.now().year)

        # todo move to new folder and then to versionbinarysubfolder
        tempdir = tempfile.gettempdir() + os.path.sep+str(uuid.uuid4())
        ensure_directory_exists(tempdir)
        move_content_of_folder(get_publishdirectory(configparser, version), tempdir)
        nuspecfilename = configparser.get('general', 'productname')+".nuspec"
        nuspecfolder = os.path.join(get_publishdirectory(configparser, version))
        ensure_directory_exists(nuspecfolder)
        nuspecfile = os.path.join(nuspecfolder, nuspecfilename)
        copyfile(configparser.get('release', 'nuspectemplatefile'), nuspecfile)
        newtarget = os.path.join(get_publishdirectory(configparser, version), "Binary")
        ensure_directory_exists(newtarget)
        move_content_of_folder(tempdir, newtarget)
        if configparser.getboolean('build', 'hastestproject'):
            shutil.move(os.path.join(newtarget, configparser.get('general', 'productname')+".TestCoverage.opencover.xml"), get_publishdirectory(configparser, version))
        os.chdir(get_publishdirectory(configparser, version))
        with open(nuspecfilename, encoding="utf-8", mode="r") as f:
            nuspec_content = f.read()
            nuspec_content = nuspec_content.replace('__version__', version)
            nuspec_content = nuspec_content.replace('__commitid__', commit_id)
            nuspec_content = nuspec_content.replace('__year__', year)
            nuspec_content = nuspec_content.replace('__productname__', configparser.get('general', 'productname'))
            nuspec_content = nuspec_content.replace('__author__', configparser.get('general', 'author'))
            nuspec_content = nuspec_content.replace('__description__', configparser.get('general', 'description'))
        with open(nuspecfilename, encoding="utf-8", mode="w") as f:
            f.write(nuspec_content)
        execute_and_raise_exception_if_exit_code_is_not_zero("nuget", f"pack {nuspecfilename}", get_publishdirectory(configparser, version))

        latest_nupkg_file = configparser.get('general', 'productname')+"."+version+".nupkg"
        ensure_directory_does_not_exist(tempdir)

        # publish to local nuget-feed
        localnugettarget = configparser.get('release', 'localnugettarget')
        execute_and_raise_exception_if_exit_code_is_not_zero("dotnet", f"nuget push {latest_nupkg_file} --force-english-output --source {localnugettarget}", get_publishdirectory(configparser, version))
        git_commit(configparser.get('release', 'localnugettargetrepository'), commitmessage)

    git_commit(configparser.get('build', 'publishtargetrepository'), commitmessage)
    git_commit(configparser.get('release', 'releaserepository'), commitmessage)


def SCDotNetCreateReleaseRelease_cli(configurationfile: str):
    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCDotNetCreateReleaseRelease(args.configurationfile)

# </SCDotNetCreateReleaseRelease>

# <SCDotNetCreateReleaseSignAssembly>


def SCDotNetCreateReleaseSignAssembly(dllfile: str, snkfile: str):
    snk_file = resolve_relative_path_from_current_working_directory(snkfile)
    if(os.path.isfile(snk_file)):
        dllfile = resolve_relative_path_from_current_working_directory(dllfile)
        directory = os.path.dirname(dllfile)
        filename = os.path.basename(dllfile)
        if filename.lower().endswith(".dll"):
            filename = filename[:-4]
            extension = "dll"
        elif filename.lower().endswith(".exe"):
            filename = filename[:-4]
            extension = "exe"
        else:
            raise Exception("Only .dll-files and .exe-files can be signed")
        execute_and_raise_exception_if_exit_code_is_not_zero("ildasm", f'/all /typelist /text /out="{filename}.il" "{filename}.{extension}"', directory, 3600, True, False, "ildasm")
        execute_and_raise_exception_if_exit_code_is_not_zero("ilasm", f'/{extension} /res:"{filename}.res" /optimize /key="{snk_file}" "{filename}.il"', directory, 3600, True, False, "ilasm")
        os.remove(directory+os.path.sep+filename+".il")
        os.remove(directory+os.path.sep+filename+".res")
    else:
        raise Exception(f".snk-file '{snk_file}' does not exist")


def SCDotNetCreateReleaseSignAssembly_cli():
    parser = argparse.ArgumentParser(description='Signs a dll-file')
    parser.add_argument('--dllfile', help='Specifies the dllfile which should be signed')
    parser.add_argument('--snkfile', help='Specifies the .snk-file which should be used')
    args = parser.parse_args()
    SCDotNetCreateReleaseSignAssembly(args.dllfile, args.snkfile)

# </SCDotNetCreateReleaseSignAssembly>

# <SCdotnetCreateReleaseStarter>


def SCdotnetCreateReleaseStarter(configurationfile: str):
    configparser = ConfigParser()
    configparser.read_file(open(configurationfile, mode="r", encoding="utf-8"))

    logfile = configparser.get('general', 'logfilefolder')+os.path.sep+configparser.get('general', 'productname')+"_BuildAndPublish_"+str(datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S'))+".log"
    execute_and_raise_exception_if_exit_code_is_not_zero("SCdotnetCreateRelease.py", configurationfile, "", 3600, 2, True, "Create"+configparser.get('general', 'productname')+"Release", False, logfile)


def SCdotnetCreateReleaseStarter_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCdotnetCreateReleaseStarter(args.configurationfile)

# </SCdotnetCreateReleaseStarter>

# <SCGenerateThumbnail>


def calculate_lengh_in_seconds(file: str, wd: str):
    argument = '-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "'+file+'"'
    return float(execute_and_raise_exception_if_exit_code_is_not_zero("ffprobe", argument, wd)[1])


def create_thumbnails(file: str, length_in_seconds: float, amount_of_images: int, wd: str, tempname_for_thumbnails):
    rrp = length_in_seconds/(amount_of_images-2)
    argument = '-i "'+file+'" -r 1/'+str(rrp)+' -vf scale=-1:120 -vcodec png '+tempname_for_thumbnails+'-%002d.png'
    execute_and_raise_exception_if_exit_code_is_not_zero("ffmpeg", argument, wd)


def create_thumbnail(outputfilename: str, wd: str, length_in_seconds: float, tempname_for_thumbnails):
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
        length_in_seconds = calculate_lengh_in_seconds(filename, folder)
        create_thumbnails(filename, length_in_seconds, amount_of_images, folder, tempname_for_thumbnails)
        create_thumbnail(filename_without_extension, folder, length_in_seconds, tempname_for_thumbnails)
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


def private_keyhook(event):
    print(str(event.name)+" "+event.event_type)


def SCKeyboardDiagnosis_cli():
    keyboard.hook(private_keyhook)
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
        print(f"File '{file}' does not exist")


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

# <SCPythonCreateRelease>


def SCPythonCreateRelease(configurationfile: str):
    pass  # todo


def SCPythonCreateRelease_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("configurationfile")
    args = parser.parse_args()
    SCPythonCreateRelease(args.configurationfile)

# </SCPythonCreateRelease>

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


def encapsulate_with_quotes(value: str):
    return '"'+value+'"'


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


def get_publishdirectory(configparser, version: str):
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
                print(f"'git {argument}' had exitcode {str(execute_exit_code)}")
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


def git_merge(directory: str, sourcebranch: str, targetbranch: str, fastforward: bool = True):
    git_checkout(directory, targetbranch)
    if(fastforward):
        ff = ""
    else:
        ff = "--no-ff "
    execute_and_raise_exception_if_exit_code_is_not_zero("git", "merge --no-commit "+ff+sourcebranch, directory, 3600)
    commit_id = git_commit(directory, f"Merge branch '{sourcebranch}' into '{targetbranch}'")
    return commit_id

# </git>
