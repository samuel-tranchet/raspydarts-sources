#!/bin/sh

if [ $# -ge 1 ]
then
	while [ $# -ge 1 ]
	do
		python3 Test_Dmx_Publish.py "Data:$1"
		python3 Test_Dmx_Publish.py "Wait:500"
		shift
	done
else
	python3 Test_Dmx_Publish.py "Data:0,0,0,255,255,255,0,0"
fi
