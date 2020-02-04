#!/bin/bash
sudo apt-get install apache2
awk '/<Directory \/var\/www\/>/,/AllowOverride None/{sub("None", "All",$0)}{print}' /var/etc/apache2/apache2.conf