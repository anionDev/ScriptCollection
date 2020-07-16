from setuptools import setup, find_packages
version = "1.2.5"

productname = "ScriptCollection"
packages= [package for package in find_packages() if not package.endswith("Tests")]

with open("..\\..\\ReadMe.md", "r", encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=productname,
    version=version,
    description=f"The scriptcollection is the place for little scripts which are maybe also useful in future.",
    packages=packages,
    author='Marius Göcke',
    author_email='marius.goecke@gmail.com',
    url='https://github.com/anionDev/ScriptCollection',
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
        "Topic :: Terminals"
    ],
    platforms=["windows10", "linux"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "epew>=3.3.5",
        "keyboard>=0.13.5",
        "ntplib>=0.3.4",
        "PyPDF2>=1.26.0",
        "qrcode>=6.1",
        "send2trash>=1.5.0",
    ],
    entry_points={
        'console_scripts': [
            f"SCDotNetReleaseExecutable = ScriptCollection.core:SCDotNetReleaseExecutable_cli",
            f"SCDotNetBuildExecutableAndRunTests = ScriptCollection.core:SCDotNetBuildExecutableAndRunTests_cli",
            f"SCDotNetCreateExecutableRelease = ScriptCollection.core:SCDotNetCreateExecutableRelease_cli",
            f"SCDotNetCreateNugetRelease = ScriptCollection.core:SCDotNetCreateNugetRelease_cli",
            f"SCDotNetBuildNugetAndRunTests = ScriptCollection.core:SCDotNetBuildNugetAndRunTests_cli",
            f"SCDotNetReleaseNuget = ScriptCollection.core:SCDotNetReleaseNuget_cli",
            f"SCDotNetReference = ScriptCollection.core:SCDotNetReference_cli",
            f"SCDotNetBuild = ScriptCollection.core:SCDotNetBuild_cli",
            f"SCDotNetRunTests = ScriptCollection.core:SCDotNetRunTests_cli",
            f"SCDotNetsign = ScriptCollection.core:SCDotNetsign_cli",
            f"SCPythonCreateWheelRelease = ScriptCollection.core:SCPythonCreateWheelRelease_cli",
            f"SCPythonBuildWheelAndRunTests = ScriptCollection.core:SCPythonBuildWheelAndRunTests_cli",
            f"SCPythonBuild = ScriptCollection.core:SCPythonBuild_cli",
            f"SCPythonRunTests = ScriptCollection.core:SCPythonRunTests_cli",
            f"SCPythonReleaseWheel = ScriptCollection.core:SCPythonReleaseWheel_cli",
            f"SCGenerateThumbnail = ScriptCollection.core:SCGenerateThumbnail_cli",
            f"SCKeyboardDiagnosis = ScriptCollection.core:SCKeyboardDiagnosis_cli",
            f"SCMergePDFs = ScriptCollection.core:SCMergePDFs_cli",
            f"SCOrganizeLinesInFile = ScriptCollection.core:SCOrganizeLinesInFile_cli",
            f"SCGenerateSnkFiles = ScriptCollection.core:SCGenerateSnkFiles_cli",
            f"SCReplaceSubstringsInFilenames = ScriptCollection.core:SCReplaceSubstringsInFilenames_cli",
            f"SCSearchInFiles = ScriptCollection.core:SCSearchInFiles_cli",
            f"SCShow2FAAsQRCode = ScriptCollection.core:SCShow2FAAsQRCode_cli",
        ],
    },
)
