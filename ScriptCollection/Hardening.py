#!/usr/bin/python3

import traceback
from .Utilities import GeneralUtilities
from .Core import ScriptCollectionCore


class HardeningScript:

    _private_sc: ScriptCollectionCore = ScriptCollectionCore()
    applicationstokeep: "list[str]" = None
    additionalfolderstoremove: "list[str]" = None
    applicationstodelete: "list[str]" = [
        "git", "curl", "wget", "sudo", "sendmail", "net-tools", "nano", "lsof", "tcpdump",
        "unattended-upgrades", "mlocate", "gpg", "htop", "netcat", "gcc-10", "gdb", "perl-modules-*",
        "binutils-common", "bash", "tar", "vi"
    ]

    def __init__(self, applicationstokeep, additionalfoldertoremove):
        self.applicationstokeep = GeneralUtilities.to_list(applicationstokeep, ";")
        self.additionalfolderstoremove = GeneralUtilities.to_list(additionalfoldertoremove, ";")

    def run(self):
        try:
            GeneralUtilities.write_message_to_stdout("Hardening-configuration:")
            GeneralUtilities.write_message_to_stdout(f"  applicationstokeep: {self.applicationstokeep}")
            GeneralUtilities.write_message_to_stdout(f"  additionalFolderToRemove: {self.additionalfolderstoremove}")

            # TODO:
            # - kill applications which opens undesired ports
            # - generally disable root-login
            # - prevent creating/writing files using something like "echo x > y"
            # - prevent reading from files as much as possible
            # - prevent executing files as much as possible
            # - shrink rights of all user as much as possible
            # - deinstall/disable find, chown, chmod, apt etc. and all other applications which are not listed in $applicationstokeep
            # etc.
            # general idea: remove as much as possible from the file-system. all necessary binaries should already be available in the RAM usually.

            # Remove undesired folders
            for additionalfoldertoremove in self.additionalfolderstoremove:
                GeneralUtilities.write_message_to_stdout(f"Remove folder {additionalfoldertoremove}...")
                GeneralUtilities.ensure_directory_does_not_exist(additionalfoldertoremove)

            # Remove undesired packages
            for applicationtodelete in self.applicationstodelete:
                if not applicationtodelete in self.applicationstokeep and self._private_package_is_installed(applicationtodelete):
                    GeneralUtilities.write_message_to_stdout(f"Remove application {applicationtodelete}...")
                    self._private_execute("apt-get", f"purge -y {applicationtodelete}")
        except Exception as exception:
            GeneralUtilities.write_exception_to_stderr_with_traceback(exception, traceback, "Exception occurred while hardening.")

    def _private_package_is_installed(self, package: str) -> bool:
        return True  # TODO see https://askubuntu.com/questions/660305/how-to-tell-if-a-certain-package-exists-in-the-apt-repos

    def _private_execute(self, program: str, argument: str, workding_directory: str = None):
        return self._private_sc.start_program_synchronously(program, argument, workding_directory, throw_exception_if_exitcode_is_not_zero=True, prevent_using_epew=True)
