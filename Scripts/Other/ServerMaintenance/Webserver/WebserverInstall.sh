#! /bin/bash
pushd $(dirname $0)
sudo bash ../Common/AptUpdate.sh
sudo apt-get -y install apache2
./WebserverHardening.sh
popd
