#!/bin/bash
scriptpath="$( cd "$(dirname "$0")" ; pwd -P )"
echo $( dirname $0 )
basepath=$scriptpath'/../locales'

msgfmt=$( which msgfmt )

if [ "$msgfmt" = "" ] ; then
        echo "[ERROR] Please install msgfmt to convert .po files to .mo"
        exit 1
fi


for f in ${basepath}/*; do
        if [[ -d $f && "$f" != '.' ]] ; then
                msgpath="${f}/LC_MESSAGES/pydarts"
                if [ -f "${msgpath}.po" ]; then
                        echo "Converting ${msgpath}.po to ${msgpath}.mo"
                        msgfmt ${msgpath}.po -o ${msgpath}.mo
                else
                        echo "[WARNING] ${msgpath}.po does not exists. Ingoring."
                fi
        fi
done

