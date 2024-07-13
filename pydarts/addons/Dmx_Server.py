
import sys
import time

# Mqtt
import paho.mqtt.client as mqtt
# Curl
import requests

def usage(msg):
    print("")
    print("Dmx_Server.py [-host={}] <topic> <dmx_host> <dmx_universe>".format(MQTT_HOST))
    print("")
    print(" ERROR : {}".format(msg))
    print("")
    sys.exit(9)

# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, rc):
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    print("[DEBUG] Dmx_Server : Listen", MQTT_TOPIC, "on", MQTT_HOST, flush=True)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    msg = msg.payload.decode()

    print("[DEBUG] Dmx_Server : received",msg,flush=True)
    if msg != 'ack' :

        if msg.startswith('ack:'):
            Ack = True
            msg = msg[4::]
        else:
            Ack = False

        if msg == 'quit' :
                print("[DEBUG] Dmx_Server : Disconnect. Sleep 2")
                time.sleep(2)
                client.publish(MQTT_TOPIC + '-ack',"ack")
                client.disconnect()

        elif msg[0:4:1] == 'Wait':
            try:
                wait_time = int(msg.replace(' ','').split(",")[1]) * int(msg.replace(' ','').split(",")[3])
            except:
                wait_time = 500
            print("[DEBUG] Dmx_Server : sleep",wait_time)
            time.sleep(wait_time/1000)
        elif msg[0:4:1] == 'Data':
            data = [('u', OLA_UNIVERSE),('d',msg.split(':')[1])]
            requests.post("{}/set_dmx".format(OLA_HOST),data=data)
            print("[DEBUG] Dmx_Server : send {} to {}".format(data,OLA_HOST))
            #curl -d u=OLA_UNIVERSE -d d=0,0,0,0,0,0,0,0 http://localhost:9090/set_dmx

        if Ack :
            print("[DEBUG] Dmx_Server : publish Ack")
            client.publish(MQTT_TOPIC + '-ack','ack')

MQTT_HOST = "localhost"
MQTT_TOPIC = "pydarts/TargetLeds"

if len(sys.argv) < 5 or len(sys.argv) > 6 :
    usage("Bad number of arguments")
else :
    i = 1
    if sys.argv[1][0:6] == '-host=' :
        MQTT_HOST=sys.argv[1].split('=')[1]
        i += 1

    MQTT_TOPIC = sys.argv[i]
    OLA_HOST = sys.argv[i + 1]
    OLA_UNIVERSE = sys.argv[i + 2]

    #try:
    if True:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_HOST, 1883, 60)

        client.loop_forever()
    #except:
    else:
        print("[ERROR] Dmx_Server : Cannot connect to",MQTT_HOST)
        sys.exit(9)

