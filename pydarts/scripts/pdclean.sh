#!/bin/bash
if [ "$1" == "" ] ; then
	echo "Usage : $0 pydarts_folder"
	exit 1
fi
find ${1} -type f -name *.pyc -exec rm -rf {} \;
