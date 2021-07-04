#! /bin/bash
# This script is intended to be executed as root-user.
# Content semantically from: https://support.torproject.org/apt/tor-deb-repo/
# After execution usually the following paths will be used by default:
# /etc/tor (configuration)
# /var/log/tor (logs)

pushd $(dirname $0)

../Common/InstallSystemUtilities.sh

echo "deb http://deb.torproject.org/torproject.org buster main" | tee -a /etc/apt/sources.list.d/tor.list
echo "deb-src https://deb.torproject.org/torproject.org buster main" | tee -a /etc/apt/sources.list.d/tor.list

gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -

apt-get -y update
apt-get -y install tor deb.torproject.org-keyring

popd
