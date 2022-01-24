#!/usr/bin/python3

# This script is intended to be called from Hardening.py

import argparse
import traceback
from ScriptCollection.core import ScriptCollection, to_list, ensure_directory_does_not_exist, write_exception_to_stderr_with_traceback, write_message_to_stdout


class Hardening:

    _private_sc: ScriptCollection = ScriptCollection()
    applicationstokeep: "list[str]" = None
    additionalfolderstoremove: "list[str]" = None
    applicationstodelete: "list[str]" = [
        "git", "curl", "wget", "sudo", "sendmail", "net-tools", "nano", "lsof", "tcpdump",
        "unattended-upgrades", "mlocate", "gpg", "htop", "netcat", "gcc-10", "gdb", "perl-modules-*",
        "binutils-common", "bash", "tar", "vi"
    ]

    def __init__(self, applicationstokeep, additionalfoldertoremove):
        self.applicationstokeep = to_list(applicationstokeep, ";")
        self.additionalfolderstoremove = to_list(additionalfoldertoremove, ";")

    def run(self):
        try:
            write_message_to_stdout("Hardening-configuration:")
            write_message_to_stdout(f"  applicationstokeep: {self.applicationstokeep}")
            write_message_to_stdout(f"  additionalFolderToRemove: {self.additionalfolderstoremove}")

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
                write_message_to_stdout(f"Remove folder {additionalfoldertoremove}...")
                ensure_directory_does_not_exist(additionalfoldertoremove)

            # Remove undesired packages
            for applicationtodelete in self.applicationstodelete:
                if not applicationtodelete in self.applicationstokeep and self._private_package_is_installed(applicationtodelete):
                    write_message_to_stdout(f"Remove application {applicationtodelete}...")
                    self._private_execute("apt-get", f"purge -y {applicationtodelete}")
        except Exception as exception:
            write_exception_to_stderr_with_traceback(exception, traceback, "Exception occurred while hardening.")

    def _private_package_is_installed(self, package: str) -> bool:
        return True  # TODO see https://askubuntu.com/questions/660305/how-to-tell-if-a-certain-package-exists-in-the-apt-repos

    def _private_execute(self, program: str, argument: str, workding_directory: str = None):
        return self._private_sc.start_program_synchronously(program, argument, workding_directory, throw_exception_if_exitcode_is_not_zero=True, prevent_using_epew=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--applicationstokeep', required=True)
    parser.add_argument('--additionalfolderstoremove', required=True)
    args = parser.parse_args()
    Hardening(args.applicationstokeep, args.additionalfolderstoremove).run()
