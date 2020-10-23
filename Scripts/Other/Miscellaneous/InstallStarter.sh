apt-get update
apt-get -y install git
mkdir /TempInstallation
git clone https://github.com/anionDev/ScriptCollection.git /TempInstallation
pushd /TempInstallation/ScriptCollection/Scripts/Other/ServerMaintenance/Common
./CreateUser.sh
chmod chown -R user:user /TempInstallation
