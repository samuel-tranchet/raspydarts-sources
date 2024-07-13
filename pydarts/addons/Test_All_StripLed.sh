

#python3 Test_Strip_Publish.py 'Fireworks,1,random,1'
#python3 Test_Strip_Publish.py 'Fireworks,1,random,5'
#python3 Test_Strip_Publish.py 'Fireworks,1,random,10'
#python3 Test_Strip_Publish.py 'Fireworks,1,random,20'
#python3 Test_Strip_Publish.py 'Fireworks,1,random,30'

#python3 Test_Strip_Publish.py 'NewKitt,2,random,50'
python3 Test_Strip_Publish.py 'RunningLights,20,random,50'

grep SA_ CStrip.py  | cut -d'(' -f1 | cut -d'_' -f2 \
| grep -v FillDown \
| grep -v TheaterChaseRainbow \
| while read a
do
	python3 Test_Strip_Publish.py "$a,2,random,1"
done
