#!/bin/bash

command="scbuildcodeunits --repositoryfolder $repositoryfolder --verbosity $verbosity --targetenvironment $targetenvironment"
echo "Run '$command'..."
bash -c "$command"
