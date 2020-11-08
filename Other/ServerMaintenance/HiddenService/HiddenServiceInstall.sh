#! /bin/bash
# This script is intended to be run as user with root privileges.
pushd $(dirname $0)
../Common/AptUpdate.sh
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
# TODO (payload)
pushd $(dirname $0)
../TorInstall.sh
#TODO
../HiddenService/HiddenServiceHardening.sh
popd