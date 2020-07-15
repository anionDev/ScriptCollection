from setuptools import setup, find_packages
version = "1.0.9"

productname = "scriptCollection"
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
    url='https://github.com/anionDev/scriptCollection',
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
        "epew>=3.3.3",
        "keyboard>=0.13.5",
        "ntplib>=0.3.4",
        "PyPDF2>=1.26.0",
        "qrcode>=6.1",
        "send2trash>=1.5.0",
    ],
    entry_points={
        'console_scripts': [
            f"SCDotNetReleaseExecutable = core:SCDotNetReleaseExecutable_cli",
            f"SCDotNetBuildExecutableAndRunTests = core:SCDotNetBuildExecutableAndRunTests_cli",
            f"SCDotNetCreateExecutableRelease = core:SCDotNetCreateExecutableRelease_cli",
            f"SCDotNetCreateNugetRelease = core:SCDotNetCreateNugetRelease_cli",
            f"SCDotNetBuildNugetAndRunTests = core:SCDotNetBuildNugetAndRunTests_cli",
            f"SCDotNetReleaseNuget = core:SCDotNetReleaseNuget_cli",
            f"SCDotNetReference = core:SCDotNetReference_cli",
            f"SCDotNetBuild = core:SCDotNetBuild_cli",
            f"SCDotNetRunTests = core:SCDotNetRunTests_cli",
            f"SCDotNetsign = core:SCDotNetsign_cli",
            f"SCPythonCreateWheelRelease = core:SCPythonCreateWheelRelease_cli",
            f"SCPythonBuildWheelAndRunTests = core:SCPythonBuildWheelAndRunTests_cli",
            f"SCPythonBuild = core:SCPythonBuild_cli",
            f"SCPythonRunTests = core:SCPythonRunTests_cli",
            f"SCPythonReleaseWheel = core:SCPythonReleaseWheel_cli",
            f"SCGenerateThumbnail = core:SCGenerateThumbnail_cli",
            f"SCKeyboardDiagnosis = core:SCKeyboardDiagnosis_cli",
            f"SCMergePDFs = core:SCMergePDFs_cli",
            f"SCOrganizeLinesInFile = core:SCOrganizeLinesInFile_cli",
            f"SCGenerateSnkFiles = core:SCGenerateSnkFiles_cli",
            f"SCReplaceSubstringsInFilenames = core:SCReplaceSubstringsInFilenames_cli",
            f"SCSearchInFiles = core:SCSearchInFiles_cli",
            f"SCShow2FAAsQRCode = core:SCShow2FAAsQRCode_cli",
        ],
    },
)
