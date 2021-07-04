#! /bin/bash
# This script is intended to be executed inside a container as user with root privileges.

pushd $(dirname $0)

./AptUpgrade.sh
apt-get -y install gpg sudo wget curl net-tools iputils-ping tree procps apt-utils apt-transport-https git lsb-release
popd
