#! /bin/bash
# This script is intended to be run as root-user.

#Arguments:
environmentStage="$1" # Allowed values: "Development", "QualityCheck", "Productive". This variable is case-sensitive.
scriptCollectionFolder="$2"
hardeningApplicationstokeep="$3" # Semicolon-separated list
hardeningAdditionalFolderToRemove="$4" # Semicolon-separated list

echo "Configure system for environment $environmentStage"

if [ "$environmentStage" == "Development" ] ; then
    "$scriptCollectionFolder/Other/ServerMaintenance/Debian/Common/InstallSystemUtilities.sh"
    # TODO make system more verbose by default
    exit 0
elif [ "$environmentStage" == "QualityCheck" ] ; then
    "$scriptCollectionFolder/Other/ServerMaintenance/Debian/Common/InstallSystemUtilities.sh"
    exit 0
elif [ "$environmentStage" == "Productive" ] ; then
    "$scriptCollectionFolder/Other/ServerMaintenance/Debian/Common/Hardening.sh" "$hardeningApplicationstokeep" "$hardeningAdditionalFolderToRemove"
    exit 0
else
    exit 1
fi
