#! /bin/bash
# This script is intended to be run as user with sudo privileges.
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
pushd $(dirname $0)
../Common/AptUpdate.sh
sudo apt-get -y install php7.0
sudo apt-get -y install php7.0-mysql
sudo apt-get -y install php7.0-mcrypt
sudo apt-get -y install libapache2-mod-php7.0
sudo apt-get -y install php7.0-curl
sudo apt-get -y install php7.0-json
sudo apt-get -y install php7.0-cgi
sudo apt-get -y install php7.0-xml
sudo apt-get -y install sendmail
./PHPHardening.sh
popd