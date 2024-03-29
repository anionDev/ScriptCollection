#! /bin/bash
# This script is intended to be run as root

#Arguments:
username="$1"
userhomedirectory="$2"
userhaspassword="$3"
userpassword="$4"
userShouldBeSudoer="$5"
userCanUseSudoWithoutPassword="$6"

pushd $(dirname $0)

if [ "$userhomedirectory" = "" ] ; then
    addgroup -S usergroup && adduser $username -G usergroup
else
    addgroup -S usergroup && adduser $username -G usergroup -h $userhomedirectory
fi

if [ "$userhaspassword" == "true" ] ; then
    echo "$username:$userpassword" | chpasswd
fi

if [ "$userShouldBeSudoer" == "true" ] ; then
    ../Common/AptUpdate.sh
    apk add sudo
    sudo adduser $username sudo
    if [ "$userCanUseSudoWithoutPassword" == "true" ] ; then
        echo "$username ALL=(ALL) NOPASSWD: ALL" | tee -a /etc/sudoers
    fi
fi

popd
