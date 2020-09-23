#! /bin/bash
# This script is intended to be run as user with sudo privileges.
# After execution usually the following paths will be used:
# /etc/nginx (configuration)
# /var/log/nginx (logs)
# /usr/share/nginx/html (payload)

pushd $(dirname $0)

../Common/AptUpdate.sh

sudo apt-get -y install nginx
#TODO
sudo nginx

./ReverseProxyHardening.sh

popd