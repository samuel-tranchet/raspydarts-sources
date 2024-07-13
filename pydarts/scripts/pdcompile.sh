#!/bin/bash
# Please copy this script out of the pydarts directory, adapt it to your config and run it.
# CONFIG
# Path of pyinstaller (pip3 install pyinstaller)
pyipath="$HOME/.local/bin/pyinstaller"
path="$HOME/"
folder="pydarts_dev"
fullpath="${path}/${folder}"
scriptpath="${fullpath}/pydarts.py"

# Temporary force python3
shopt -s expand_aliases
alias python='/usr/bin/python3'
echo "Using python version : python --version"

#exit 1

if [[ "$1" == "run" ]] ; then
	cd dist/pydarts
	./pydarts $2
	cd ../..

echo "You run this script from : $path"
echo "You want to compile : $folder"
echo "Which is located in : $fullpath"
echo "pyDarts main file is located in : $scriptpath"


elif [[ "$1" == "" ]] ; then
$pyipath \
	--clean \
	--path="$fullpath" \
	--add-data="${folder}/locales:locales" \
	--add-data="${folder}/sounds:sounds" \
	--add-data="${folder}/images:images" \
	--add-data="${folder}/fonts:fonts" \
	--add-data="${folder}/licence:licence" \
	--add-data="${folder}/arduino:arduino" \
	--add-data="${folder}/desktop:desktop" \
	--add-data="${folder}/CREDITS:." \
	--add-data="${folder}/README:." \
	--hidden-import="games.321_Zlip" \
	--hidden-import="games.Cricket" \
	--hidden-import="games.Practice" \
	--hidden-import="games.Ho_One" \
	--hidden-import="games.Sample_game" \
	--hidden-import="games.Kinito" \
	--hidden-import="games.Killer" \
	--hidden-import="games.Kapital" \
	--hidden-import="games.Shanghai" \
	-y \
	${scriptpath}
fi
# --onefile
