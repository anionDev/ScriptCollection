#!/bin/bash
#set -e
#set -o pipefail

# Source https://wiki.debian.org/DebianInstaller/Preseed/EditIso

scriptfolder="$( dirname -- "$0"; )"
cwd=$PWD
cd $scriptfolder
temp_folder="$(mktemp -d)"
preseed_template_file="preseedTemplate.cfg"
preseed_file="preseed.cfg"

isofile=$1
hostname=$2
ssh_public_key=$3
user_password=$4
root_password=$5
locale=$6
keymap=$7
architecture=$8
result_folder=$9
ssh_port="${10}"
disk_size="${11}"
# allowed values/formats for disk_size are: "max", "75%" and "250GB"

echo "Step 1: Prepare"
isofile_without_extension=${isofile::-4}
iso_filename="$hostname-installer"
preseed_target_file="$result_folder/$iso_filename.iso"
if [ -f "$preseed_target_file" ] ; then
  rm -f "$preseed_target_file"
fi
if [ -d "$temp_folder" ] ; then
  rm -rf "$temp_folder"
fi
if [ -d "$preseed_file" ] ; then
  rm -f "$preseed_file"
fi

echo "Step 2: Generate preseed-file"
cp $preseed_template_file $preseed_file
sed -i "s/__\[hostname\]__/$hostname/g" $preseed_file
sed -i "s/__\[ssh_public_key\]__/$ssh_public_key/g" $preseed_file
sed -i "s/__\[user_password\]__/$user_password/g" $preseed_file
sed -i "s/__\[root_password\]__/$root_password/g" $preseed_file
sed -i "s/__\[locale\]__/$locale/g" $preseed_file
sed -i "s/__\[keymap\]__/$keymap/g" $preseed_file
sed -i "s/__\[ssh_port\]__/$ssh_port/g" $preseed_file
sed -i "s/__\[disk_size\]__/$disk_size/g" $preseed_file

echo "Preseed-file:"
cat $preseed_file

echo "Step 3: Adding preseed-file to the Initrd"
7z x -o$temp_folder $isofile
chmod +w -R $temp_folder/install.$architecture/
gunzip $temp_folder/install.$architecture/initrd.gz
echo $preseed_file | cpio -H newc -o -A -F $temp_folder/install.$architecture/initrd
gzip $temp_folder/install.$architecture/initrd
chmod -w -R $temp_folder/install.$architecture/

echo "Step 4  Update boot-configuration"

menu_config_file="$temp_folder/isolinux/menu.cfg"
sed -i "s/include gtk.cfg/#include gtk.cfg/g" $menu_config_file
sed -i "s/include adgtk.cfg/#include adgtk.cfg/g" $menu_config_file
sed -i "s/include adspkgtk.cfg/#include adspkgtk.cfg/g" $menu_config_file
sed -i "s/include adspk.cfg/#include adspk.cfg/g" $menu_config_file
sed -i "s/include spkgtk.cfg/#include spkgtk.cfg/g" $menu_config_file
sed -i "s/include spk.cfg/#include spk.cfg/g" $menu_config_file
sed -i "/menu title.*Debian.*GNU/c\\menu title $iso_filename" $menu_config_file

txt_config_file="$temp_folder/isolinux/txt.cfg"
sed -i "$ a\timeout 100" $txt_config_file
sed -i "$ a\ontimeout install" $txt_config_file

echo "Step 5: Regenerating md5sum.txt"
cd $temp_folder
chmod +w md5sum.txt
find -follow -type f ! -name md5sum.txt -print0 | xargs -0 md5sum > md5sum.txt
chmod -w md5sum.txt
cd -

echo "Step 6: Creating a New Bootable ISO Image"
# (May require "sudo apt install -y genisoimage")
output_file="$preseed_target_file"
genisoimage -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $output_file $temp_folder

echo "Step 7: Clean-up"
rm -f $preseed_file
chmod -R 777 $temp_folder
rm -rf $temp_folder
cd $cwd


#echo "Step 8: Test image"
# (Manual task; May require "sudo apt install -y qemu-system-x86")
#qemu-system-i386 -net user -cdrom $output_file
