
import sys
import re
import ast
import time

# Mqtt
import paho.mqtt.client as mqtt
# Perso
import CStrip as CStrip
import Colors as CColors

# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, rc):
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    print("[DEBUG] Other_Server : Listen",MQTT_TOPIC,"on",MQTT_HOST,flush=True)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    msg = msg.payload.decode()
    C = None

    print("[DEBUG] Other_Server : received",msg,flush=True)

MQTT_HOST="mosquitto"
MQTT_HOST="localhost"
MQTT_TOPIC = "pydarts/StripLeds"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_HOST, 1883, 60)

client.loop_forever()

