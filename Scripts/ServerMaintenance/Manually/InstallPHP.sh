#!/bin/bash
sudo apt-get install php7.0 libapache2-mod-php7.0 php7.0-mysql php7.0-curl php7.0-intl
sudo a2enmod rewrite
sudo service apache2 restart