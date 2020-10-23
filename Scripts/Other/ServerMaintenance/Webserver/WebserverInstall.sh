#! /bin/bash
pushd $(dirname $0)
../Common/AptUpdate.sh
apt-get -y install apache2
./WebserverHardening.sh
popd