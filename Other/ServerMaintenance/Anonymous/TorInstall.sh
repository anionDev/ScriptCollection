#! /bin/bash
# This script is intended to be run as user with root privileges.
# After execution usually the following paths will be used:
# From Content semantically from: https://support.torproject.org/apt/tor-deb-repo/
# TODO (configuration)
# TODO (logs)
# TODO (payload)
pushd $(dirname $0)
apt-get --allow-unauthenticated -y update -qq
apt-get --allow-unauthenticated -y install gpg
echo "deb http://deb.torproject.org/torproject.org $(lsb_release -cs) main" | tee -a /etc/apt/sources.list.d/tor.list
echo "deb-src https://deb.torproject.org/torproject.org $(lsb_release -cs) main" | tee -a /etc/apt/sources.list.d/tor.list


gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -
apt-get -y update -qq
apt-get -y install tor deb.torproject.org-keyring
popd
