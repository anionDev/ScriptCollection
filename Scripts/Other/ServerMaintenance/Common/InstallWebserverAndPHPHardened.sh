#! /bin/bash
# This script is intended to be run as user with sudo privileges
pushd $(dirname $0)
../Webserver/WebserverInstall.sh
../PHP/PHPInstall.sh
../Docker/HardeningContainer.sh
popd
