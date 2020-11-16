import os
from setuptools import setup, find_packages

productname = "ScriptCollection"
version = "2.0.7"

packages = [package for package in find_packages() if not package.endswith("Tests")]

folder_of_current_file = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(folder_of_current_file, "ReadMe.md"), "r", encoding='utf-8') as file:
    long_description = file.read()

setup(
    name=productname,
    version=version,
    description="The scriptcollection is the place for little scripts which are maybe also useful in future.",
    packages=packages,
    author="Marius Göcke",
    author_email="marius.goecke@gmail.com",
    url="https://github.com/anionDev/ScriptCollection",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Terminals",
    ],
    platforms=[
        "windows10",
        "linux",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "keyboard>=0.13.5",
        "ntplib>=0.3.4",
        "pycdlib>=1.10.0",
        "PyPDF2>=1.26.0",
        "qrcode>=6.1",
        "send2trash>=1.5.0",
    ],
    entry_points={
        'console_scripts': [
            f"SCCalculateBitcoinBlockHash = {productname}.core:SCCalculateBitcoinBlockHash_cli",
            f"SCChangeHashOfProgram = {productname}.core:SCChangeHashOfProgram_cli",
            f"SCCreateEmptyFileWithSpecificSize = {productname}.core:SCCreateEmptyFileWithSpecificSize_cli",
            f"SCCreateHashOfAllFiles = {productname}.core:SCCreateHashOfAllFiles_cli",
            f"SCCreateISOFileWithObfuscatedFiles = {productname}.core:SCCreateISOFileWithObfuscatedFiles_cli",
            f"SCCreateRelease = {productname}.core:SCCreateRelease_cli",
            f"SCDebCreateInstallerRelease = {productname}.core:SCDebCreateInstallerRelease_cli",
            f"SCDotNetBuild = {productname}.core:SCDotNetBuild_cli",
            f"SCDotNetBuildExecutableAndRunTests = {productname}.core:SCDotNetBuildExecutableAndRunTests_cli",
            f"SCDotNetBuildNugetAndRunTests = {productname}.core:SCDotNetBuildNugetAndRunTests_cli",
            f"SCDotNetCreateExecutableRelease = {productname}.core:SCDotNetCreateExecutableRelease_cli",
            f"SCDotNetCreateNugetRelease = {productname}.core:SCDotNetCreateNugetRelease_cli",
            f"SCDotNetReference = {productname}.core:SCDotNetReference_cli",
            f"SCDotNetReleaseNuget = {productname}.core:SCDotNetReleaseNuget_cli",
            f"SCDotNetRunTests = {productname}.core:SCDotNetRunTests_cli",
            f"SCDotNetsign = {productname}.core:SCDotNetsign_cli",
            f"SCFileIsAvailable = {productname}.core:SCFileIsAvailable_cli",
            f"SCFilenameObfuscator = {productname}.core:SCFilenameObfuscator_cli",
            f"SCGenerateSnkFiles = {productname}.core:SCGenerateSnkFiles_cli",
            f"SCGenerateThumbnail = {productname}.core:SCGenerateThumbnail_cli",
            f"SCKeyboardDiagnosis = {productname}.core:SCKeyboardDiagnosis_cli",
            f"SCMergePDFs = {productname}.core:SCMergePDFs_cli",
            f"SCObfuscateFilesFolder = {productname}.core:SCObfuscateFilesFolder_cli",
            f"SCOrganizeLinesInFile = {productname}.core:SCOrganizeLinesInFile_cli",
            f"SCPythonBuild = {productname}.core:SCPythonBuild_cli",
            f"SCPythonBuildWheelAndRunTests = {productname}.core:SCPythonBuildWheelAndRunTests_cli",
            f"SCPythonCreateWheelRelease = {productname}.core:SCPythonCreateWheelRelease_cli",
            f"SCPythonReleaseWheel = {productname}.core:SCPythonReleaseWheel_cli",
            f"SCPythonRunTests = {productname}.core:SCPythonRunTests_cli",
            f"SCReplaceSubstringsInFilenames = {productname}.core:SCReplaceSubstringsInFilenames_cli",
            f"SCSearchInFiles = {productname}.core:SCSearchInFiles_cli",
            f"SCShow2FAAsQRCode = {productname}.core:SCShow2FAAsQRCode_cli",
            f"SCShowMissingFiles = {productname}.core:SCShowMissingFiles_cli",
            f"SCUpdateNugetpackagesInCsharpProject = {productname}.core:UpdateNugetpackagesInCsharpProject_cli",
            f"SCUploadFile = {productname}.core:SCUploadFile_cli",
        ],
    },
)
