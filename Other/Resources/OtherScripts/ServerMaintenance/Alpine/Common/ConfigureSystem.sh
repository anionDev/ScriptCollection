#! /bin/bash
# This script is intended to be run as root-user.

#Arguments:
environmentStage="$1" # Allowed values: "Development", "QualityCheck", "Productive". This variable is case-sensitive.
scriptCollectionFolder="$2"
hardeningApplicationstokeep="$3" # Semicolon-separated list
hardeningAdditionalFolderToRemove="$4" # Semicolon-separated list

echo "Configure system as environment $environmentStage"

if [ "$environmentStage" == "Development" ] ; then
    "$scriptCollectionFolder/Other/ServerMaintenance/Alpine/Common/InstallSystemUtilities.sh"
    # TODO make system more verbose by default
fi

if [ "$environmentStage" == "QualityCheck" ] ; then
    "$scriptCollectionFolder/Other/ServerMaintenance/Alpine/Common/InstallSystemUtilities.sh"
fi

if [ "$environmentStage" == "Productive" ] ; then
    "$scriptCollectionFolder/Other/ServerMaintenance/Alpine/Common/Hardening.sh" "$hardeningApplicationstokeep" "$hardeningAdditionalFolderToRemove"
fi
