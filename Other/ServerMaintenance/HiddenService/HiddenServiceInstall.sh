#! /bin/bash
pushd $(dirname $0)
../Common/AptUpdate.sh
#TODO
../HiddenService/HiddenServiceHardening.sh
popd