#!/bin/bash
cd pydarts_dev
if [ "$1" = "" ] ; then
	./pydarts.sh --noserial --gametype=local --localplayers=michel,andre,poilou,keke,cici,vivi,hehe,simon,patrick,mqmq,pepe,prpr --selectedgame=Ho_One --debuglevel=1
elif [ "$1" = "menus" ] ; then
	./pydarts.sh --noserial --localplayers=michel,andre,poilou,keke,cici,vivi,hehe,simon,patrick,mqmq,pepe,prpr --colorset=dark --debuglevel=1
elif [ "$1" == "3" ] ; then
	python3 pydarts.py --noserial --gametype=local --localplayers=michel,andre,poilou,keke,cici,vivi,hehe,simon,patrick,mqmq,pepe,prpr --selectedgame=Ho_One --debuglevel=1
elif [ "$1" == "mobile3" ] ; then
	python3 pydarts.py --noserial --gametype=local --localplayers=michel,andre,poilou,keke,cici,vivi,hehe,simon,patrick,mqmq,pepe,prpr --selectedgame=Ho_One --resx=300 --resy=600 --debuglevel=1
elif [ "$1" == "mobile" ] ; then
	./pydarts.sh --noserial --gametype=local --localplayers=michel,andre,poilou,keke,cici,vivi,hehe,simon,patrick,mqmq,pepe,prpr --selectedgame=Ho_One --resx=300 --resy=600 --debuglevel=1
fi
cd ..
