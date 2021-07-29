#! /bin/bash
# This script is intended to be executed inside as user with elevated privileges.

pushd $(dirname $0)

apk add gpg sudo wget curl

popd
