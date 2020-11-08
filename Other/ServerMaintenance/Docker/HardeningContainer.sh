#! /bin/bash
# This script is intended to be executed inside a container as user with root privileges.
pushd $(dirname $0)
../Common/Hardening.sh
popd