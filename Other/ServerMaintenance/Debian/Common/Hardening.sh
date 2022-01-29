#!/bin/bash

#Arguments:
applicationstokeep="$1" #semicolon-separated list
additionalfolderstoremove="$2" #semicolon-separated list

apt-get install -y python3 python3-pip
pip3 install ScriptCollection

SCHardening --applicationstokeep "$applicationstokeep" --additionalfolderstoremove "$additionalfolderstoremove"

# Remove unnecessary binaries
apt-get remove -y python-pip3 python3
apt-get autoclean -y
apt-get autoremove -y
apt-get clean
apt-get remove -y --allow-remove-essential apt
rm /bin/chgrp
rm /bin/chmod
rm /bin/chown
rm /bin/dpkg
rm /bin/echo
rm /bin/grep
rm /bin/hostname
rm /bin/mount
rm /bin/sh
rm /bin/touch
rm /bin/umount
rm /bin/uname
rm /bin/su
rm /usr/bin/tree
rm /usr/bin/truncate
rm /usr/bin/sudo
rm /usr/bin/xargs
rm /bin/ls
rm /usr/bin/find
rm /usr/bin/which
