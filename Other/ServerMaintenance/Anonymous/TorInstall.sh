#! /bin/bash
# This script is intended to be run as user with root privileges.
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
# TODO (payload)
pushd $(dirname $0)
echo "deb http://deb.torproject.org/torproject.org $(lsb_release -cs) main" | sudo tee -a /etc/apt/sources.list.d/tor.list
apt-get -y update -qq
apt-get -y install tor
popd
