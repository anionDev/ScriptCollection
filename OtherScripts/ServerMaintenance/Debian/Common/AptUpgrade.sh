#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "This script is expected to be executed with elevated privileges."
  exit
fi

apt-get -y update
apt-get -y upgrade
