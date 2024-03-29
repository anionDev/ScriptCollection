#! /bin/bash
# This script is intended to be executed on a debian-system as root-user.
# Content semantically from: https://support.torproject.org/apt/tor-deb-repo/
# After execution usually the following paths will be used by default:
# /etc/tor (configuration)
# /var/log/tor (logs)

pushd $(dirname $0)

# preparation:
../Common/AptUpgrade.sh
../Common/InstallSystemUtilities.sh

# import official tor-key:
echo "deb http://deb.torproject.org/torproject.org $(lsb_release -cs) main" | tee -a /etc/apt/sources.list.d/tor.list
echo "deb-src https://deb.torproject.org/torproject.org $(lsb_release -cs) main" | tee -a /etc/apt/sources.list.d/tor.list
wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --import
gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -

# install tor:
apt-get -y update
apt-get -y install tor deb.torproject.org-keyring

popd
