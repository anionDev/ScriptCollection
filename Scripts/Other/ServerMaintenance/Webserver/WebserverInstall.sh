#! /bin/bash
# This script is intended to be run as user with sudo privileges.
# After execution usually the following paths will be used:
# /etc/apache2 (configuration)
# /var/log/apache2 (logs)
# /var/www/html (payload)

pushd $(dirname $0)

../Common/AptUpdate.sh

sudo apt-get -y install apache2

sudo chmod -R 777 /var/log/apache2


./WebserverHardening.sh

popd