FROM debian:stable-slim

ARG TargetEnvironmentType
ARG Version="3.5.0"
LABEL maintainer="marius.goecke@gmail.com"
LABEL description="SCBuilder is a container-image with a build-framework for software-projects."
LABEL targetEnvironmentType="$TargetEnvironmentType"
LABEL version="$Version"
LABEL de.aniondev.projects.image-provides-tool-python="v3.11"
LABEL de.aniondev.projects.image-provides-tool-pip3="v22"
LABEL de.aniondev.projects.image-provides-tool-git="v2.39"
LABEL de.aniondev.projects.image-provides-tool-gitversion="v5"
LABEL de.aniondev.projects.image-provides-tool-dotnet="v7"
LABEL de.aniondev.projects.image-provides-tool-nodejs="v20"
LABEL de.aniondev.projects.image-provides-tool-docfx="v2"
LABEL de.aniondev.projects.image-provides-tool-dotnetcoverage="v17"
LABEL de.aniondev.projects.image-provides-tool-reportgenerator="v5"
LABEL de.aniondev.projects.image-provides-tool-scriptcollection="v$Version"
#TODO implement demands

RUN mkdir /Workspace \
    && mkdir /Workspace/Scripts \
    && mkdir /Workspace/Tools \
    && apt update \
    && apt install -y sudo iputils-ping curl wget \
    && adduser user \
    && echo "user:pass" | chpasswd \
    && usermod -aG sudo user \
    && echo "user ALL=(ALL:ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/user
COPY ./SCBuilder/EntryPointScript.sh /Workspace/Scripts/EntryPointScript.sh
WORKDIR /Workspace/Scripts
USER user

ADD ./Other/Resources/DependentCodeUnits/ScriptCollection/BuildResult_Wheel /Workspace/Tools/ScriptCollectionArtifacts

RUN sudo apt install -y python3 python3-pip git \
    && sudo pip3 install /Workspace/Tools/ScriptCollectionArtifacts/ScriptCollection-$Version-py3-none-any.whl --break-system-packages

RUN sudo wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && sudo dpkg -i packages-microsoft-prod.deb \
    && sudo rm packages-microsoft-prod.deb \
    && sudo apt-get update \
    && sudo apt-get install -y dotnet-sdk-7.0
ENV PATH="${PATH}:/opt/gtk/bin"

RUN dotnet tool install --global GitVersion.Tool
RUN sudo ln -s /home/user/.dotnet/tools/dotnet-gitversion /usr/bin/gitversion

#TODO install required tools which should be definable by specific demands passed as argument

RUN sudo chmod 777 -R /Workspace

ENTRYPOINT ["/Workspace/Scripts/EntryPointScript.sh"]
