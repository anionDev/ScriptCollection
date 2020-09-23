#! /bin/bash
# This script is intended to be run as root.
pushd $(dirname $0)
../Common/AptUpdate.sh
useradd -m -d /userhome user
apt-get -y install sudo
sudo adduser user sudo
echo "user ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers
popd