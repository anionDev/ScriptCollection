#!/bin/bash
cd /var/www/html
wget http://wordpress.org/latest.tar.gz
tar xfz latest.tar.gz
rm latest.tar.gz
chown sudo chown -R www-data:www-data /wordpress