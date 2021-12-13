#!/bin/bash

# This script is intended to be run as user with root privileges.

#Arguments:
applicationstokeep="$2" #semicolon-separated list
additionalFolderToRemove="$3" #semicolon-separated list

IFS=';' read -ra ADDR <<< "$additionalFolderToRemove"
for i in "${ADDR[@]}"; do
  rm -rf "$i"
done

cd /

#-----------------------------------------------------------------------------------------------
#!/bin/bash

function list_include_item {
  local list="$1"
  local item="$2"
  if [[ $list =~ (^|[[:space:]])"$item"($|[[:space:]]) ]] ; then
    # yes, list include item
    result=0
  else
    result=1
  fi
  return $result
}

applicationstokeepasstring="openjdk-17-jre-headless
git
bash"

SAVEIFS=$IFS   # Save current IFS
IFS=$'\n'      # Change IFS to new line
applicationstokeep=($applicationstokeepasstring) # split to array applicationstokeep
IFS=$SAVEIFS   # Restore IFS

applicationstodelete=("git" "bash" "curl" "wget")

for (( i=0; i<${#applicationstodelete[@]}; i++ ))
do
    applicationtodelete=$applicationstodelete[$i]
    if [[ " ${applicationstokeep} " =~ " ${applicationtodelete} " ]]; then
        echo "$applicationtodelete"
    fi
done


#-----------------------------------------------------------------------------------------------

apt-get autoremove
apt-get clean

# TODO:
# - deinstall/disable sudo, wget, ls, ping, git, find, chown, chmod, apt etc. and all other applications which are not listed in $applicationstokeep
# - generally disable root-login
# - shrink rights of all user as much as possible
# - prevent writing files using something like "echo x > y"
# - prevent executing files as much as possible
# etc.
