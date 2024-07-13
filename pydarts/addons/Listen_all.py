
import sys
import re
import ast
import time

# Mqtt
import paho.mqtt.client as mqtt
# Perso

# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, rc):
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    print(f"[DEBUG] Listen {MQTT_TOPIC} on {MQTT_HOST}", flush=True)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #msg = msg.payload.decode()

    print(f"[DEBUG] Received {msg.payload} on {msg.topic}", flush=True)

MQTT_HOST="localhost"
MQTT_TOPIC = "raspydarts/#"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_HOST, 1883, 60)

client.loop_forever()

