#! /bin/bash
# After execution usually the following paths will be used:
# TODO (configuration)
# TODO (logs)
pushd $(dirname $0)
sudo bash ../Common/AptUpdate.sh
sudo apt-get -y install apache2
sudo ./WebserverHardening.sh
popd
