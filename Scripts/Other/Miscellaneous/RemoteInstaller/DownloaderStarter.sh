apt-get update
apt-get -y install git
git clone https://github.com/anionDev/ScriptCollection.git
pushd /ScriptCollection/Scripts/Other/ServerMaintenance/Common
./CreateUser.sh
chmod chown -R user:user ./ScriptCollection
