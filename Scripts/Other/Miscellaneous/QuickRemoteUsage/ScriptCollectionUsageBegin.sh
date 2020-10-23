#! /bin/bash
apt-get update -qq
apt-get -y install git
git clone https://github.com/anionDev/ScriptCollection.git
find ./ScriptCollection -type f -iname "*.sh" -exec chmod +x {} \;
