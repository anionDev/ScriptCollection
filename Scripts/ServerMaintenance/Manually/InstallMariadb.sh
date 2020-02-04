#!/bin/bash
sudo apt-get install mariadb-server
sudo mysql --user=root mysql
CREATE USER 'dba'@'localhost' IDENTIFIED BY 'myPasswordForDba';
GRANT ALL PRIVILEGES ON *.* TO 'dba'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;