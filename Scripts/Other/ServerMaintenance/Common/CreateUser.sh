#! /bin/bash
# This script is intended to be run as root
pushd $(dirname $0)
sudo ../Common/AptUpdate.sh
useradd -m -d /userhome user
apt-get install -y sudo
sudo adduser user sudo
popd
