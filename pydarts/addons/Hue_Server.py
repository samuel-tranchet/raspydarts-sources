
"""
Hue Server : In order to light your Hue lights from raspydarts
"""

import sys
import re
import time
import json

import requests

from rgbxy import Converter
from rgbxy import GamutA

# Mqtt
import paho.mqtt.client as mqtt
# Perso
import Colors as CColors

DISCOVERY_URL = "https://discovery.meethue.com/"
GATEWAY_FILE = "/home/pi/.pydarts/other/gateway.hue"

converter = Converter(GamutA)

def warning(msg):
    print(f"[WARNING] Hue_Server : {msg}", flush=True)

def debug(msg):
    print(f"[DEBUG] Hue_Server : {msg}", flush=True)

def usage(msg):
    print("")
    print("Usage 1:")
    print(f"    Hue_Server.py [-host={MQTT_HOST}] [-gateway=<ip>] INIT")
    print("    In order to init communication with Hue gateway")
    print("")
    print("Usage 2:")
    print("    Hue_Server.py [-gateway=<ip>] <topic>")
    print("    Run use case")
    print("")
    print(f" ERROR : {msg}")
    print("")
    sys.exit(9)

def init(gateway=None, nb_attempts=30):

    print("========================")
    print("==== INITIALISATION ====")
    print("========================")
    print("")
    print("1. Identification de la passerelle")
    gateway = init_gateway(gateway)
    if gateway is None:
        print("")
        print("Aucune passerelle Hue trouvée sur le réseau")
        print("Vérifiez que l'url suivante répond dans un navigateur")
        print(f"{DISCOVERY_URL}")
        print("")
        print("Si elle ne répond pas, merci de relancer cette procédure")
        print("lorsque l'url répondra")
        print("")
        print("Abandon de la procédure")
        print("")
        sys.exit(8)
    else:
        print(f" Passerelle trouvée : {gateway}")

    print("")
    print("Appuyez sur le bouton d'appairage sur la passerelle Hue")
    print("")
    print("La tentative d'appairage débutera dans 10 secondes")
    print("")

    time.sleep(3)

    attempt = 1
    while attempt < nb_attempts:
        username = get_username(gateway)
        if username is None:
            attempt += 1
            time.sleep(1)
        else:
            break

    if attempt >= nb_attempts:
        print("")
        print("Appairage impossible !")
        print("")
        print("Abandon de la procédure")
        print("")
    else:
        print(f"Got a username : {username}")

    store_gateway(gateway, username)

    print("")
    print("Initialisation done")
    print("")
    print("List of availables lights :")
    test = list_lights(gateway, username)
    print("")
    print("Test en cours :")
    print(f"L'ampoule {test} va s'allumer et s'éteindre 2 fois")
    test_light(gateway, username, test)

def is_ip(ip_address):
    """
    Returns True if given string is a valid IP Address, else False
    """
    match_obj = re.search(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip_address)
    if match_obj is None:
        return False
    else:
        for value in match_obj.groups():
            if int(value) > 255:
                return False
    return True

def is_hue(handle):
    """
    Returns True if given string is a valid IP Address, else False
    """
    match_obj = re.search(r"^\((\d{1,3}),(\d{1,3}),(\d{1,3}),(\d{1,3})\)$", handle)
    if match_obj is None:
        return False
    else:
        for value in match_obj.groups():
            if int(value) > 255:
                return False
    return True

def init_gateway(gateway):
    """
    Init gateway
    """

    if gateway is None:
        try:
            request = requests.get('https://discovery.meethue.com/')
            gateway = request.json()[0]['internalipaddress']
        except:
            gateway = None

    return gateway

def get_username(gateway):
    """
    Get token
    """
    try:
        data = {"devicetype": "raspydarts"}
        post = requests.post(f'http://{gateway}{API}', json=data)
        username = post.json()[0]['success']['username']
        return username
    except:
        print(f"No response from http://{gateway}{API}")
        return None

def load_gateway():
    """
    Load gateway and username from gateway.hue
    """

    try:
        with open (GATEWAY_FILE, "r") as gateway_file:
            data = gateway_file.readlines()

        data = json.loads(data[0].strip())

        return data['gateway'], data['username']
    except:
        usage(f"Could not open {GATEWAY_FILE} for reading !!")

def store_gateway(gateway, username):
    """
    Store gateway and username into gateway.hue
    """

    try:
        f = open(GATEWAY_FILE, "w")
        f.write(f'{{"gateway": "{gateway}", "username": "{username}"}}')
        f.close()
    except:
        usage(f"Could not open {GATEWAY_FILE} for writting !!")

def list_lights(gateway, username):
    """
    Print a list of avalaible lights
    """
    get = requests.get(f'http://{gateway}{API}/{username}/lights')
    lights = get.json()

    test = None
    if lights is not None and len(lights) > 0:
        print("Id| State | Name                   | Type                   | Product name")
        print("--+-------|------------------------+------------------------+-------------------------")
        for index, (key, value) in enumerate(lights.items()):
            light_id = key
            name = value['name']
            if bool(value['state']['on']):
                state = "ON"
            else:
                state = "OFF"
            light_type = value['type']
            product_name =  value['productname']
            print(f"{light_id.ljust(2)}|{state.ljust(7)}|{name.ljust(24)}|{light_type.ljust(24)}|{product_name}")
            test = key
    else:
        print("No light available :(")
    return test

def test_light(gateway, username, light):
    """
    Light on / off a light
    """
    true = 'true'
    false = 'false'
    for index in range(4):
        if index % 2 == 0:
            data = '{"on": true}'
        else:
            data = '{"on": false}'

        put = requests.put(f'http://{gateway}{API}/{username}/lights/{light}/state', data=data)
        debug(f"Respond {put.json()}")
        if index < 3:
            time.sleep(3)

def change_light(gateway, username, light, on=True):
    """
    Put a light ON or OFF
    """
    if on:
        data = '{"on": true}'
    else:
        data = '{"on": false}'

    put = requests.put(f'http://{gateway}{API}/{username}/lights/{light}/state', data=data)
    debug(f"Respond {put.json()}")

def change_color(gateway, username, light, X, Y, Z=None):
    """
    Send new color to a light
    """
    #data = f'{{"on":true, "hue":{int(X * 65536)}, "sat":255,"bri":255}}'
    data = f'{{"on":true, "xy": [{X}, {Y}]}}'
    put = requests.put(f'http://{gateway}{API}/{username}/lights/{light}/state', data=data)
    debug(f"Respond {put.json()}")

def on_connect(client, userdata, flags, rc):
    """
    The callback for when the client receives a connect response from the server.
    """
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    debug("Listen {MQTT_TOPIC} on {MQTT_HOST}")

# The callback for when a PUBLISH message is received from the server.
def animation(gateway, username, msg):

    color = None
    verb = ''
    X = None
    Y = None
    Z = None

    if msg.startswith('ack:'):
        Ack = True
        msg = msg[4::]
    else:
        Ack = False

    debug(f"received msg={msg}")
    if msg[0:4:1] == 'hue:':
        animation = msg[4::]
        light = animation.split('|')[0]
        verb = animation.split('|')[1]

        if light == 'wait':
            wait_time = int(verb)
            verb = 'wait'

        elif verb == 'color':
            color = animation.split('|')[2]
            if is_hue(color):
                R = color.replace('(', '').split(',')[0]
                G = color.split(',')[1]
                B = color.replace(')', '').split(',')[2]
                (X, Y) = converter.rgb_to_xy(R, G, B)
            else:
                try:
                    C = Colors.GetColor(color)
                except:
                    warning(f"Unrecognized color : {color}")
                    C = Colors.GetColor()
                (X, Y) = converter.rgb_to_xy(C[0], C[1], C[2])

        elif verb == 'random':
            C = Colors.GetColor()
            if C == (0, 0, 0):
                verb = 'OFF'
                debug(f"color is (0, 0, 0), set light to OFF")
            else:
                debug(f"random color is {C}")
                (X, Y) = converter.rgb_to_xy(C[0], C[1], C[2])
    else:
         warning(f"Unrecognized animation : {msg}")
         return

    try:
        if verb.upper() == 'ON':
            change_light(gateway, username, light, True)

        elif verb.upper() == 'OFF':
            change_light(gateway, username, light, False)

        elif verb.upper() in ('COLOR', 'RANDOM'):
            change_color(gateway, username, light, X, Y)

        elif animation == 'quit' :
            debug("Disconnect. Sleep 2")
            time.sleep(1)
            client.publish(MQTT_TOPIC + '-ack',"ack")
            client.disconnect()

        elif verb.upper() == 'WAIT':
            time.sleep(wait_time / 1000)

        else:
            warning(f"Unrecognized animation : {animation}")
    except:
        warning(f"Animation error : {animation}")

    if Ack :
        debug("publish Ack")
        client.publish(MQTT_TOPIC,'ack')


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global GATEWAY
    global USERNAME

    message = msg.payload.decode().replace(' ','')

    if message != 'ack':
        animation(GATEWAY, USERNAME, message)

MQTT_HOST = "localhost"
MQTT_TOPIC = "raspydarts/hue"
GATEWAY = None
USERNAME = None
API = '/api'

if len(sys.argv) < 2 or len(sys.argv) > 4 :
    usage("Bad number of arguments")
else :

    i = 1
    if sys.argv[1][0:6] == '-host=':
        MQTT_HOST = sys.argv[1].split('=')[1]
        i += 1

    if sys.argv[i][0:9] == '-gateway=' :
        GATEWAY = sys.argv[i].split('=')[1]
        if not is_ip(GATEWAY):
            usage(f"{GATEWAY} is not a valid ip address")
        i += 1

    if sys.argv[i] == "INIT":
        init(GATEWAY)
        sys.exit(0)

    GATEWAY, USERNAME = load_gateway()
    MQTT_TOPIC = sys.argv[i]

    Colors = CColors.CColors()

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_HOST, 1883, 60)

        client.loop_forever()
    except:
        print(f"[ERROR] Hue_Server : Cannot connect to {MQTT_HOST}")
        sys.exit(9)

