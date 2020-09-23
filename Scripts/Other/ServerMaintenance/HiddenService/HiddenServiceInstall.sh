#! /bin/bash
# This script is intended to be run as user with sudo privileges.
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
# TODO (payload)
pushd $(dirname $0)
../TorInstall.sh
#TODO
../HiddenService/HiddenServiceHardening.sh
popd