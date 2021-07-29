#! /bin/bash
# This script is intended to be executed inside as user with elevated privileges.

pushd $(dirname $0)

apk add gnupg sudo wget curl tree procps git bmon slurm iftop gdb

popd
