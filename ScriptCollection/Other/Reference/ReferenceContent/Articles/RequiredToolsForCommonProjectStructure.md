# Required tools for CommonProjectStructure

## Hints

[ScriptCollection](https://github.com/anionDev/ScriptCollection) contains scripts to implement a repository-structure defined by the [`CommonProjectStructure`](<https://projects.aniondev.de/PublicProjects/Common/ProjectTemplates/-/blob/main/Conventions/RepositoryStructure/CommonProjectStructure/CommonProjectStructure.md>).
To be able to run the scripts specified by the `CommonProjectStructure` successfully some tools may be required dependent on your project.
For typically used tools the [Tools](#tools)-section contains a short description how to install them.

## Tools

### coverage

[coverage](https://github.com/nedbat/coveragepy) is required to create test-coverage-reports for [python](https://www.python.org)-projects.
The package can be installed using `pip install coverage`.

### docfx

[DocFX](https://github.com/dotnet/docfx) is a tool to generate HTML-references by markdown-files.
It is primary used for references based on [documentation-comments](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/language-specification/documentation-comments) in the source-code of .NET-projects.
The commandline-tool can be installed using `choco install docfx`.

### docker

[docker](https://www.docker.com) is required to create docker-images from a dockerfile.
Install-instructions can be found [here](https://github.com/christian-korneck/docker-pushrm#installation).

### docker pushrm

[pushrm](https://github.com/christian-korneck/docker-pushrm) is a commandline-tool to edit descriptions of a docker-image on [hub.docker.com](https://hub.docker.com).
Install-instructions can be found [here](https://docs.docker.com/engine/install/).

### dotnet

[dotnet](https://learn.microsoft.com/de-de/dotnet/core/tools/dotnet) is the CLI-command to provide commands for working with .NET projects and run .NET applications.
Install-instructions for the commandline-tool can be found [here](https://dotnet.microsoft.com/en-us/download).

### dotnet cyclonedx

[CycloneDX for .NET-projects](https://github.com/CycloneDX/cyclonedx-dotnet) is a tool to generate `sbom.xml` in the `BOM`-artifact for .NET-projects.
The commandline-tool can be installed using `dotnet tool install --global CycloneDX`.

### dotnet-coverage

[dotnet-coverage](https://learn.microsoft.com/en-us/dotnet/core/additional-tools/dotnet-coverage) is a tool to run testcases and generate a coverage-report for .NET-projects.
The commandline-tool can be installed using `dotnet tool install --global dotnet-coverage`.

### epew

TODO

### gh

[gh](https://cli.github.com/) is a GitHub's commandline-tool to interact with [github.com](github.com) from commandline.
The commandline-tool can be installed using `choco install gh`.
Further installation-instructions are on the [official website](https://cli.github.com/manual/installation).

### git

[git](https://git-scm.com/) is a common version control system.

### gitversion

[gitversion](https://gitversion.net) is a tool to calculate the project-version based on the git-history.
The commandline-tool can be installed using `choco install gitversion.portable` in a shell with elevated privileges.

### java

[java](https://openjdk.org/) is the commandline-tool for running [Java](https://docs.oracle.com/en/java)-programs.

### nuget

[NuGet](https://www.nuget.org/) is required to create [NuGet-packages](https://www.nuget.org/packages).
The commandline-tool can be installed using `choco install nuget.commandline`.

### scriptcollection

[ScriptCollection](https://github.com/anionDev/ScriptCollection) is required to run the scripts (`Build.py`, etc.).
The package can be installed using `pip install ScriptCollection`.

### sh

The shell `sh` is already pre-installed on most linux-systems.
On Windows a windows-port called `sh.exe` is contained in [git for windows](https://git-scm.com/download/win) and can be found usually in `C:\Program Files\Git\usr\bin`.

### sn

The [Strong Name tool](https://learn.microsoft.com/en-us/dotnet/framework/tools/sn-exe-strong-name-tool) (Sn.exe) helps sign assemblies with strong names.
It is contained the [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/).

### swagger

[Swagger](https://swagger.io) is required to generate the `APISpecification`-artifact for .NET-WebAPI-Projects.
The commandline-tool can be installed using `dotnet tool install --global swashbuckle.aspnetcore.cli`.

### python

[Python](https://www.python.org) is a common script-language.

### ng

[ng](https://github.com/angular/angular-cli) is a CLI-tool to manage angular-projects.
The commandline-tool can be installed using `npm i @angular/cli`.

### npm

[npm](https://www.npmjs.com) is the package-manager of [node](https://nodejs.org/en).
The command `npm` is usually be available after you have installed node.

### reportgenerator

[ReportGenerator](https://reportgenerator.io/) is required to generate HTML-reports from test-coverage-reports.
The commandline-tool can be installed using `choco install reportgenerator.portable`.

### t4

[t4](https://github.com/mono/t4) is a tool to generate C#-files from [T4](https://learn.microsoft.com/en-us/visualstudio/modeling/code-generation-and-t4-text-templates)-templates.
It can be installed using `dotnet tool install --global dotnet-t4`.
It is an alternative implementation for [TextTransform](https://learn.microsoft.com/en-us/visualstudio/modeling/generating-files-with-the-texttransform-utility).

### twine

[Twine](https://twine.readthedocs.io/en/stable/) is a utility for publishing [python](https://www.python.org) packages to PyPI and other repositories.
The commandline-tool can be installed using `pip install twine`.
