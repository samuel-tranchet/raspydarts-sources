

#python3 Test_Target_Publish.py 'Fireworks,1,random,1'
#python3 Test_Target_Publish.py 'Fireworks,1,random,5'
#python3 Test_Target_Publish.py 'Fireworks,1,random,10'
#python3 Test_Target_Publish.py 'Fireworks,1,random,20'
#python3 Test_Target_Publish.py 'Fireworks,1,random,30'

#python3 Test_Target_Publish.py 'NewKitt,2,random,50'

#python3 Test_Target_Publish.py 'goal:T20#red|D18#blue|E18#green|E15#gold'
#python3 Test_Target_Publish.py 'stroke:S12'
#python3 Test_Target_Publish.py 'stroke:D16'
#python3 Test_Target_Publish.py 'stroke:T15'
python3 Test_Target_Publish.py 'stroke:S1'

grep 'def TA_' CStrip.py  | cut -d'(' -f1 | cut -d'_' -f2- \
| while read a
do
	python3 Test_Target_Publish.py "$a,2,random,2"
done
