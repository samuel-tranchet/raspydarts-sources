#!/bin/sh

files2save_maj="/pydarts/to_delete.lst /pydarts/RaspyDarts.sh /pydarts/raspydarts.py /pydarts/VERSION /pydarts/locales/ /pydarts/include/*.py /pydarts/games/*/*.py /pydarts/addons/*.py /pydarts/images/background.png /pydarts/scripts/*.sh"
files2save_full="/pydarts/*"

Usage(){
	echo ""
	echo "	MakeUpdate.sh maj|full|only [<fichiers>]"
	echo ""
	echo "	maj : Génère une mise à jour"
	echo "	full : Crée un full"

	echo "	Prépare un fichier de mise à jour (raspydarts_<version>.tgz)"
	echo "	Génère une nouvelle version à partir du fichier VERSION - seul l'horodatage de la mise à jour est calculé"
	echo "	Le fichier CHANGELOG est copié en CHANGELOG.<version>"
	echo ""
	echo "	Par défaut, les répertoires et fichiers suivants sont inclus dans la mise à jour :"
	echo "		- $files2save_maj" | sed -e 's/ /\n\t\t- /g'
	echo ""
	echo "	Dans le cas d'un full :"
	echo "		- $files2save_full" | sed -e 's/ /\n\t\t- /g'
	echo ""
	echo "	Les <fichiers> passés en paramètre sont ajoutés à la liste des fichiers par défaut"
	echo ""
	echo "	 /\e[33m!\\Les <fichiers> à ajouter doivent être en chemin absolu : /pydarts/...\e[39m"
	echo ""
}

if [ "$1" = '-force' ]
then
	force=true
	shift
else
	force=false
fi

if [ $# -lt 1 ]
then
	Usage
	exit
elif [ "$1" = "--help" ]
then
	Usage
	exit
elif [ "$1" = "maj" -o "$1" = "only" ]
then
	full=false
	if [ "$1" = "maj" ]
	then
		shift
		files2save="$files2save_maj $@"
	else
		shift
		files2save="$@"
	fi
	while [ $# -ge 1 ]
	do
		if [ `expr "$1" : '^/pydarts/'` -ne 9 -a "$force" = false ]
		then
			Usage
			echo "	 \e[31mErreur:\e[39m $1 doit être en chemin absolu. \e[32m/pydarts/$1 peut-être ???\e[39m"
			echo ""
			exit
		fi
		shift
	done
	files2save="`echo $files2save | sed -e 's/\s/\n/g' | sort | uniq | sed -e 's/\n/\s/g'`"

elif [ "$1" = "full" ]
then
	shift
	files2save="$files2save_full $@"
	full=true
else
	Usage
	exit
fi

v=`cat /pydarts/VERSION | cut -d_ -f1`
d=`date +%Y%m%d`
h=`date +%H%M`

version="${v}_${d}_$h"
#file="/pydarts/backup/update_$version.tgz"
if [ "$full" = "true" ]
then
	file="/pydarts/backup/raspydarts_$version.tgz"
else
	file="/pydarts/backup/update_$version.tgz"
fi

echo "version=$version"
echo "file=$file"

echo "==========================="
echo "=== Version : \e[96m$version\e[39m"
echo "=== Fichier : \e[95m$file\e[39m"
echo "==========================="

cd /pydarts


echo $version > VERSION
if [ -s /pydarts/CHANGELOG ]
then
	cp -p /pydarts/CHANGELOG /pydarts/CHANGELOG.$version
	files2save="$files2save /pydarts/CHANGELOG.$version"
fi

echo "Generation de la mise à jour en cours..."
tar --exclude='__init__.py' --exclude='__pycache__' --exclude='*.tgz' --exclude='*.log' -zcvf $file $files2save > /pydarts/logs/backup.log
if [ $? -eq 0 ]
then
	echo "\e[32mDone\e[39m"
else
	echo "\e[31mKo\e[39m"
fi

