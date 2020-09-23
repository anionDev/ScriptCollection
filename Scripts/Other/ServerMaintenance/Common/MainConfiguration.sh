#! /bin/bash
# This script is intended to be run as root.

username="user"
userhomedirectory="/home/$username"
sshport="1755"
sshauthorizedkeyforuser="...."

apt update
apt install ssh sudo curl sendmail net-tools nano git python3 python3-pip lsof tcpdump unattended-upgrades mlocate
apt upgrade -y
sudo adduser $username sudo
echo $sshauthorizedkeyforuser | tee -a $userhomedirectory/.ssh/authorized_keys

#set sshd-config
truncate -s0 /etc/ssh/sshd_config
echo "Port $sshport" >> /etc/ssh/sshd_config
echo "PermitRootLogin no" >> /etc/ssh/sshd_config
echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config
echo "UsePAM no" >> /etc/ssh/sshd_config
echo "X11Forwarding yes" >> /etc/ssh/sshd_config
echo "PrintMotd no" >> /etc/ssh/sshd_config
echo "AcceptEnv Lang LC_*" >> /etc/ssh/sshd_config
echo "Subsystem sftp /usr/lib/openssh/sftp-server" >> /etc/ssh/sshd_config

service ssh restart
service sshd restart
