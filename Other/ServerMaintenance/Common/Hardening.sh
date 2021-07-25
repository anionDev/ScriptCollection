#! /bin/bash
# This script is intended to be run as user with root privileges.

pushd $(dirname $0)
applicationstokeep="$1"
# TODO:
# - deinstall/disable sudo, wget, ls, ping, git, find, chown, chmod, etc. and all other applications which are not listed in $applicationstokeep
# - generally disable root-login
# - shrink rights of all user as much as possible
# - prevent writing files using something like "echo x > y"
# - prevent executing files as much as possible
# etc.
popd
