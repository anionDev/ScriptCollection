#! /bin/bash
pushd $(dirname $0)
../Common/AptUpdate.sh
apt-get -y install php7.0
apt-get -y install php7.0-mysql
apt-get -y install php7.0-mcrypt
apt-get -y install libapache2-mod-php7.0
apt-get -y install php7.0-curl
apt-get -y install php7.0-json
apt-get -y install php7.0-cgi
apt-get -y install php7.0-xml
apt-get -y install sendmail
./PHPHardening.sh
popd