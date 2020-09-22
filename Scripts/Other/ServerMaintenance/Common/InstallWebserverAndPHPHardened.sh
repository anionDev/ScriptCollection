#! /bin/bash
pushd $(dirname $0)
../Webserver/WebserverInstall.sh
../PHP/PHPInstall.sh
../Docker/HardeningContainer.sh
popd