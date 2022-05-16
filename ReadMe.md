# ScriptCollection

![PyPI](https://img.shields.io/pypi/v/ScriptCollection)
[![CodeFactor](https://www.codefactor.io/repository/github/aniondev/scriptcollection/badge/main)](https://www.codefactor.io/repository/github/aniondev/scriptcollection/overview/main)
![Coverage](./ScriptCollection/Other/QualityCheck/TestCoverage/Badges/badge_shieldsio_linecoverage_blue.svg)
![Libraries.io dependency status for GitHub repo](https://img.shields.io/librariesio/github/anionDev/ScriptCollection)
[![Downloads](https://pepy.tech/badge/scriptcollection)](https://pepy.tech/project/scriptcollection)
[![Downloads](https://pepy.tech/badge/scriptcollection/month)](https://pepy.tech/project/scriptcollection)
![GitHub repo size](https://img.shields.io/github/repo-size/anionDev/ScriptCollection)

The ScriptCollection is the place for reusable scripts.

## Reference

The reference can be found [here]("https://aniondev.github.io/ScriptCollectionReference/").

## Hints

Most of the scripts are written in [python](https://www.python.org) 3.

Caution: Before executing **any** script of this repository read the sourcecode of the script (and the sourcecode of all functions called by this function directly or transitively) carefully and verify that the script does exactly what you want to do and nothing else.

Some functions are not entirely available on windows or require common third-party tools. See the [Runtime-Dependencies](#Runtime-Dependencies)-section for more information.

When using ScriptCollection it is not required but recommended for better usability to have [epew](https://github.com/anionDev/Epew) installed.

## Get ScriptCollection

ScriptCollection requires [Python](https://www.python.org) 3.10.

### Installation via pip

`pip3 install ScriptCollection`

See the [PyPI-site for ScriptCollection](https://pypi.org/project/ScriptCollection)

### Download sourcecode using git

You can simply git-clone the ScriptCollection and then use the scripts under the provided license.

`git clone https://github.com/anionDev/ScriptCollection.git`

It may be more easy to pip-install the ScriptCollection but technically pip is not required. Actually you need to git-clone (or download as zip-file from [GitHub](https://github.com/anionDev/ScriptCollection) the ScriptCollection to use the scripts in this repository which are not written in python.

## Troubleshooting

It is recommended to always use only the newest version of the ScriptCollection. If you have an older version: Update it (e. g. using `pip3 install ScriptCollection --upgrade` if you installed the ScriptCollection via pip). If you still have problems, then feel free to create an [issue](https://github.com/anionDev/ScriptCollection/issues).

If you have installed the ScriptCollection as pip-package you can simply check the version using Python with the following commands:

```lang-bash
from ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
ScriptCollectionCore.get_scriptcollection_version()
```

Or you can simply run `pip3 freeze` folder to get information about (all) currently installed pip-packages.

## Development

### Branching-system

This repository applies the [GitFlowSimplified](https://projects.aniondev.de/Common/Templates/ProjectTemplates/-/blob/main/Templates/Conventions/BranchingSystem/GitFlowSimplified.md)-branching-system.

### Install dependencies

To develop ScriptCollection it is obviously required that the following commandline-commands are available on your system:

- `python` (on some systems `python3`)
- `pip3`

The pip-packages which are required for developing on this project are defined in `requirements.txt`.

### IDE

The recommended IDE for developing ScriptCollection is Visual Studio Code.
The recommended addons for developing ScriptCollection with Visual Studio Code are:

- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Spell Right](https://marketplace.visualstudio.com/items?itemName=ban.spellright)
- [docs-markdown](https://marketplace.visualstudio.com/items?itemName=docsmsft.docs-markdown)

### Build

To Create an installable whl-package simply execute `python Setup.py bdist_wheel --dist-dir .`.

When doing this multiple times you should also clean temporary files created by python before creating the whl-package.
To do this and install the local created package the steps are:

```bash
python ScriptCollection/Other/Build/Build.py
pip3 uninstall -y ScriptCollection
pip3 install ScriptCollection-x.x.x-py3-none-any.whl
```

### Coding style

In this repository [pylint](https://pylint.org/) will be used to report linting-issues.
If you change code in this repository please ensure pylint does not find any issues before creating a pull-request.

## Runtime-Dependencies

The usual Python-dependencies will be installed automagically by `pip`.

For functions to to read or change the permissions or the owner of a file the ScriptCollection relies on the functionality of the following tools:

- chmod
- chown
- ls

This tools must be available on the system where the functions should be executed. Meanwhile this tools are also available on Windows but may have a slightly limited functionality.

## License

See [License.txt](https://raw.githubusercontent.com/anionDev/ScriptCollection/main/License.txt) for license-information.
