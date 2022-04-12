import os
from setuptools import setup, find_packages


version = "2.8.6"


def create_wheel_file():

    productname = "ScriptCollection"

    executables_namespace = f"{productname}.Executables"

    folder_of_current_file = os.path.dirname(os.path.realpath(__file__))
    packages = [package for package in find_packages(folder_of_current_file) if not package.endswith(".Tests")]

    with open(os.path.join(folder_of_current_file, "ReadMe.md"), "r", encoding='utf-8') as file:
        long_description = file.read()

    setup(
        name=productname,
        version=version,
        description="The ScriptCollection is the place for reusable scripts.",
        packages=packages,
        author="Marius Göcke",
        author_email="marius.goecke@gmail.com",
        url="https://github.com/anionDev/ScriptCollection",
        license="MIT",
        classifiers=[
            "Programming Language :: Python :: 3.10",
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
            "defusedxml>=0.7.1",
            "keyboard>=0.13.5",
            "lxml>=4.8.0",
            "ntplib>=0.3.4",
            "pycdlib>=1.10.0",
            "PyPDF2>=1.26.0",
            "qrcode>=6.1",
            "send2trash>=1.5.0",
        ],
        entry_points={
            'console_scripts': [
                f"SCCalculateBitcoinBlockHash = {executables_namespace}:CalculateBitcoinBlockHash",
                f"SCChangeHashOfProgram = {executables_namespace}:ChangeHashOfProgram",
                f"SCCreateEmptyFileWithSpecificSize = {executables_namespace}:CreateEmptyFileWithSpecificSize",
                f"SCCreateHashOfAllFiles = {executables_namespace}:CreateHashOfAllFiles",
                f"SCCreateISOFileWithObfuscatedFiles = {executables_namespace}:CreateISOFileWithObfuscatedFiles",
                f"SCCreateRelease = {executables_namespace}:CreateRelease",
                f"SCDebCreateInstallerRelease = {executables_namespace}:DebCreateInstallerRelease",
                f"SCDotNetBuild = {executables_namespace}:DotNetBuild",
                f"SCDotNetCreateExecutableRelease = {executables_namespace}:DotNetCreateExecutableRelease",
                f"SCDotNetCreateNugetRelease = {executables_namespace}:DotNetCreateNugetRelease",
                f"SCDotNetReference = {executables_namespace}:DotNetReference",
                f"SCDotNetReleaseNuget = {executables_namespace}:DotNetReleaseNuget",
                f"SCDotNetRunTests = {executables_namespace}:DotNetRunTests",
                f"SCDotNetsign = {executables_namespace}:DotNetsign",
                f"SCFileIsAvailable = {executables_namespace}:FileIsAvailable",
                f"SCFilenameObfuscator = {executables_namespace}:FilenameObfuscator",
                f"SCGenerateSnkFiles = {executables_namespace}:GenerateSnkFiles",
                f"SCGenerateThumbnail = {executables_namespace}:GenerateThumbnail",
                f"SCHardening = {executables_namespace}:Hardening",
                f"SCHealthcheck = {executables_namespace}:Healthcheck",
                f"SCKeyboardDiagnosis = {executables_namespace}:KeyboardDiagnosis",
                f"SCMergePDFs = {executables_namespace}:MergePDFs",
                f"SCObfuscateFilesFolder = {executables_namespace}:ObfuscateFilesFolder",
                f"SCOrganizeLinesInFile = {executables_namespace}:OrganizeLinesInFile",
                f"SCPythonBuild = {executables_namespace}:PythonBuild",
                f"SCPythonBuildWheelAndRunTests = {executables_namespace}:PythonBuildWheelAndRunTests",
                f"SCPythonCreateWheelRelease = {executables_namespace}:PythonCreateWheelRelease",
                f"SCPythonReleaseWheel = {executables_namespace}:PythonReleaseWheel",
                f"SCPythonRunTests = {executables_namespace}:PythonRunTests",
                f"SCReplaceSubstringsInFilenames = {executables_namespace}:ReplaceSubstringsInFilenames",
                f"SCSearchInFiles = {executables_namespace}:SearchInFiles",
                f"SCCreateSimpleMergeWithoutRelease = {executables_namespace}:CreateSimpleMergeWithoutRelease",
                f"SCShow2FAAsQRCode = {executables_namespace}:Show2FAAsQRCode",
                f"SCShowMissingFiles = {executables_namespace}:ShowMissingFiles",
                f"SCUpdateNugetpackagesInCsharpProject = {executables_namespace}:UpdateNugetpackagesInCsharpProject",
                f"SCUploadFile = {executables_namespace}:UploadFile",
            ],
        },
    )


create_wheel_file()
