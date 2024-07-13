#!/bin/sh

cd /pydarts
touch restart

cat to_delete.lst \
| while read f
do
	if [ -s "$f" ]
	then
		sudo rm -rf "$f"
	fi
done
while [ -f restart ]
do
	rm -f restart

	if [ -s logs/raspydarts.log ]
	then
		cp logs/raspydarts.log logs/raspydarts.log.bck
	fi
	sudo kill -9 `ps -lef | grep 'Server.py' | sed -e 's/  */ /g' | cut -f4 -d' '` 2> /dev/null

	python3 raspydarts.py 2>&1 > logs/raspydarts.log
done

