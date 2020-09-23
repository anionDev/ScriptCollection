#! /bin/bash
# This script is intended to be run inside a container as user with sudo privileges.
pushd $(dirname $0)
../Common/Hardening.sh
popd