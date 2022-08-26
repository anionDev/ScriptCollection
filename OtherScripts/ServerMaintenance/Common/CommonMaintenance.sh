#! /bin/bash
# This script is intended to be executed as user with elevated privileges.

#TOOD check if docker is available
#remove unused docker-container
docker volume prune --force
#remove unused images
docker rmi $(docker images --filter "dangling=true" -q --no-trunc)
