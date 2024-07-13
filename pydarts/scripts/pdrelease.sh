#!/bin/bash
prefix="pydarts_v"
dev=$2
if [ "$1" = "" ] || [ "$1" = "dev" ] || [ "$2" = "" ] ; then
	echo "Usage $0 version dev_folder"
	exit 1
fi
if [ -d ${prefix}${1} ] ; then
	echo "Error : folder ${prefix}${1} already exists. Exiting"
	exit 2
fi
# Find pydarts version - should be the same than in argument here
ver=$(cat ${dev}/include/CConfig.py | grep "self.pyDartsVersion" | cut -d"=" -f2 | tr -d '"' )
if [ "$ver" != "$1" ] ; then
	echo "Actual version of pydarts $ver differ from your arg $1. Aborting"
	exit 3
fi
cp -R $dev ${prefix}${1}
find ${prefix}${1} -type f -name *.pyc -exec rm -rf {} \;
find ${prefix}${1} -type d -name __pycache__ -exec rm -rf {} \;
rm -rf ${prefix}${1}/.git
rm -rf ${prefix}${1}/.gitignore
rm -rf ${prefix}${1}/NOTES
rm -rf ${prefix}${1}/web
rm -rf ${prefix}${1}/scripts
zip -r9 ${prefix}${1}.zip ${prefix}${1}
rm -rf ${prefix}${1}


