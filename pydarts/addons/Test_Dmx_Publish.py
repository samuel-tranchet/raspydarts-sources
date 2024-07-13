
import paho.mqtt.client as mqtt
import random
import time
import sys
import ast

messages=[]
#messages=['FadeInOut,2,gold,1','FadeRGB,1,random,2','Cylon,5,blue,0']
#messages=['leds|-S:12,13-D:14,15-T:16,17,18,19-E:20,21','Police,5,random,100']


# ,'Flash,300,red,10','Police,10,red,100','US_Police,5,yellow,50','Cylon,5,blue,0']
#messages=['Cylon,5,blue,0']

topic='pydarts/Other'
Broker='mosquitto'
Port=1883

client_id='pydarts-mqtt-{}'.format(random.randint(0,1000))

CONTINUE=True
MqttClient = mqtt.Client(client_id)
MqttClient.connect(Broker,Port)

def MessageIsAck(client,userdata,msg):
    global CONTINUE
    if msg.payload.decode() == 'ack' :
        CONTINUE=False

def WaitAck(topic) :
    MqttClient.subscribe(topic + '/ack')
    MqttClient.on_message = MessageIsAck
    i=0
    while i < 100 and CONTINUE == True:
        MqttClient.loop()
        i+=1
        time.sleep(0.001)

for i in range(1,len(sys.argv)):
    messages.append(sys.argv[i])

for m in messages :
    m = "ack:{}".format(m)
    print("send",m,"on",topic,flush=True)
    MqttClient.publish(topic,m)
    #WaitAck(topic)
    CONTINUE=True



