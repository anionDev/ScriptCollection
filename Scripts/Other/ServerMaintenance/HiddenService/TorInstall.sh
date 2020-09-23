#! /bin/bash
# This script is intended to be run as user with sudo privileges.
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
pushd $(dirname $0)
../Common/AptUpdate.sh
sudo apt-get -y install gpg
echo "deb https://deb.torproject.org/torproject.org Buster main" | sudo tee -a /etc/apt/sources.list
../Common/AptUpdate.sh
sudo apt-get -y install deb.torproject.org-keyring
sudo apt-get -y install tor
#TODO
../HiddenService/HiddenServiceHardening.sh
popd