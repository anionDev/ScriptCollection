#!/bin/bash

# Source https://wiki.debian.org/DebianInstaller/Preseed/EditIso

# Variables
isofile=$1
architecture=$2
outputfolder=$3
hostname=$4
ssh_public_key=$5
user_password=$6
root_password=$7
locale=$8
keymap=$9

# Prepare
echo "Start"
script_directory="$( dirname -- "${BASH_SOURCE[0]}"; )";
preseed_template_file="$script_directory/preseed_template.cfg"
temp_folder="$(mktemp -d)"

isofile_without_extension=${isofile::-4}
preseed_target_file="$outputfolder/$isofile_without_extension-preseeded.iso"
preseed_file="$temp_folder/preseed.cfg"

cp $preseed_template_file $temp_folder/preseed.cfg

sed -i "s/__\[hostname\]__/$hostname/g" $preseed_file
sed -i "s/__\[ssh_public_key\]__/$ssh_public_key/g" $preseed_file
sed -i "s/__\[user_password\]__/$user_password/g" $preseed_file
sed -i "s/__\[root_password\]__/$root_password/g" $preseed_file
sed -i "s/__\[locale\]__/$locale/g" $preseed_file
sed -i "s/__\[keymap\]__/$keymap/g" $preseed_file


temp_folder_img=$temp_folder/img
mkdir $temp_folder_img
# Extracting the Initrd from an ISO Image
7z x -o$temp_folder_img $isofile

# Adding a Preseed File to the Initrd
chmod +w -R $temp_folder_img/install.$architecture/
gunzip $temp_folder_img/install.$architecture/initrd.gz
echo $preseed_file | cpio -H newc -o -A -F $temp_folder_img/install.$architecture/initrd
gzip $temp_folder_img/install.$architecture/initrd
chmod -w -R $temp_folder_img/install.$architecture/


# Regenerating md5sum.txt
chmod +w $temp_folder_img/md5sum.txt
find $temp_folder_img -follow -type f ! -name md5sum.txt -print0 | xargs -0 md5sum > $temp_folder_img/md5sum.txt
chmod -w $temp_folder_img/md5sum.txt

# Creating a New Bootable ISO Image
# (May require "sudo apt install -y genisoimage")
genisoimage -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $preseed_target_file $temp_folder_img

# Remove temp-files
chmod 700 -R $temp_folder
rm -rf $temp_folder

# Test image
# (Manual task; May require "sudo apt install -y qemu-system-x86")
#qemu-system-i386 -net user -cdrom "$preseed_target_file"

