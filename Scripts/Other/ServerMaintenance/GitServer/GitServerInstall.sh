#! /bin/bash
# This script is intended to be run as user with sudo privileges.
# see https://git-scm.com/book/en/v2/Git-on-the-Server-Setting-Up-the-Server

pushd $(dirname $0)
sudo adduser git
su git
cd
mkdir .ssh && chmod 700 .ssh
touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
cat /tmp/authorized_key.pub >> ~/.ssh/authorized_keys
popd