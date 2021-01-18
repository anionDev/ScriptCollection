#! /bin/bash
# This script is intended to be run as user with root privileges.
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
# TODO (payload)
pushd $(dirname $0)
../Common/AptUpdate.sh
../Anonymous/TorInstall.sh
#TODO
../Anonymous/HiddenServiceHardening.sh
pushd $(dirname $0)
