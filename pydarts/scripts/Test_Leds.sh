#!/bin/sh

if [ $# -ne 2 ]
then
	echo ""
	echo "./Test_Leds.sh <PIN> <NbLeds>"
	echo ""
	echo "exemple :"
	echo "./Test_Leds.sh 21 187"
	echo ""
	exit 0
else
	GPIO=21
	NBLEDS=187

	python3 Test_Leds.py $GPIO $NBLEDS
fi

