
import sys
import re
import ast
import time

from threading import Thread
from threading import Event

# Mqtt
import paho.mqtt.client as mqtt
# Perso
import CStrip as CStrip
import Colors as CColors

def usage(msg):
    print("")
    print("StripLeds_Server.py [-host={}] <DMA_CHANNEL> <TOPIC> <PIN> <NB_PIXELS> <BRIGHTNESS>".format(MQTT_HOST))
    print("")
    print(" ERROR : {}".format(msg))
    print("")
    sys.exit(9)

# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, rc):
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    print("[DEBUG] StripLeds_Server : Listen",MQTT_TOPIC,"on",MQTT_HOST,flush=True)

# The callback for when a PUBLISH message is received from the server.
def animation(t_event, msg):

    C = None
    color = None

    if msg.startswith('ack:'):
        Ack = True
        msg = msg[4::]
    else:
        Ack = False

    if msg[0:5:1] == 'Light':
        animation = 'Light'
        iterations = 1
        color = msg.replace(' ','').split(",",2)[2].replace('(','').replace(')','')
        try:
            red = int(color.split(",")[0])
            green = int(color.split(",")[1])
            blue = int(color.split(",")[2])
            C = (red,green,blue)
        except:
            color = msg.split(',')[2]

        delay = None
    elif msg[0:4:1] == 'Wait':
        animation = 'wait'
        try:
            wait_time = int(msg.replace(' ','').split(",")[1]) * int(msg.replace(' ','').split(",")[3])
        except:
            wait_time = 500

    elif msg[0:4:1] != 'leds':
        try:
            animation = msg.split(',')[0]
            iterations = int(msg.split(',')[1])
            color = msg.split(',')[2]
            delay = int(msg.split(',')[3])
        except:
            iterations = 1
            delay = 10
            color = None
    else:
        animation = msg
        iterations = 1

    if C is None :
        try:
            C = Colors.GetColor(color)
        except:
            C = Colors.GetColor()

            if color is None:
                print("[DEBUG] StripLeds_Server : color is None", flush=True)
            else:
                print(f"[DEBUG] StripLeds_Server : color is {color}", flush=True)

    try:
        if animation == 'quit' :
            print("[DEBUG] StripLeds_Server : Disconnect. Sleep 2")
            time.sleep(1)
            client.publish(MQTT_TOPIC + '-ack',"ack")
            client.disconnect()
        elif animation == 'wait':
            CStrip.Wait(wait_time)
        elif animation == 'off' :
            CStrip.AllLeds(Colors.GetColor('black'))
        elif animation == 'Alain':
            CStrip.SA_Alain(t_event, delay, C, iterations)
        elif animation == 'Alain2':
            CStrip.SA_Alain2(t_event, delay, C, iterations)
        elif animation == 'ColorWipe':
            CStrip.SA_ColorWipe(t_event, delay, C, iterations)
        elif animation == 'ColorWipeReverse':
            CStrip.SA_ColorWipeReverse(t_event, delay, C, iterations)
        elif animation == 'Cylon':
            CStrip.SA_Cylon(t_event, delay, C, iterations)
        elif animation == 'CylonDouble':
            CStrip.SA_CylonDouble(t_event, delay, C, iterations)
        elif animation == 'FadeInOut':
            CStrip.SA_FadeInOut(t_event, delay, C, iterations)
        elif animation == 'FadeRGB':
            CStrip.SA_FadeRGB(t_event, delay, C, iterations)
        elif animation == 'FallColor':
            CStrip.SA_FallColor(t_event, delay, C, iterations)
        elif animation == 'FallDouble':
            CStrip.SA_FallDouble(t_event, delay, C, iterations)
        elif animation == 'FallReverse':
            CStrip.SA_FallReverse(t_event, delay, C, iterations)
        elif animation == 'Fall':
            CStrip.SA_Fall(t_event, delay, C, iterations)
        elif animation == 'FireworksReverse' :
            CStrip.SA_FireworksReverse(t_event, delay, C, iterations,5)
        elif animation == 'Fireworks' :
            CStrip.SA_Fireworks(t_event, delay, C, iterations,5)
        elif animation == 'Flames':
            CStrip.SA_Flames(t_event, delay, C, iterations)
        elif animation == 'Light':
            CStrip.SA_Light(C)
        elif animation == 'FillDown':
            CStrip.SA_FillDown(t_event, delay, C, iterations)
        elif animation == 'Police':
            CStrip.SA_Police(t_event, delay, C, iterations)
        elif animation == 'NewKitt':
            CStrip.SA_NewKitt(t_event, delay, C, iterations)
        elif animation == 'Rainbow':
            CStrip.SA_Rainbow(t_event, delay, C, iterations)
        elif animation == 'RunningLights':
            CStrip.SA_RunningLights(t_event, delay, C, iterations)
        elif animation == 'RandomColor':
            CStrip.SA_RandomColor(t_event, delay, C, iterations)
        elif animation == 'Sparkle':
            CStrip.SA_Sparkle(t_event, delay, C, iterations)
        elif animation == 'Strobe':
            CStrip.SA_Strobe(t_event, delay, C, iterations)
        elif animation == 'TheaterChase':
            CStrip.SA_TheaterChase(t_event, delay, C, iterations)
        elif animation == 'TheaterChaseRainbow':
            CStrip.SA_TheaterChaseRainbow(t_event, delay, C, iterations)
        elif animation == 'Twinkle':
            CStrip.SA_Twinkle(t_event, delay, C, iterations)
        elif animation == 'USPolice':
            CStrip.SA_USPolice(t_event, delay, C, iterations)

        elif animation == 'stroke:DB':
            C = Colors.GetColor("goldenrod")
            CStrip.SA_Strobe(t_event, delay, C, iterations)

        elif animation.split('|')[0] == 'leds' :
            CStrip.TestSegment(animation.split('|')[1],WaitTime=1500)
        elif animation == 'debug':
            CStrip.Debug(delay,C,1)
        elif animation.startswith('brightness:') :
            # Change brightness
            CStrip.SetBrightness(animation.split(':')[1])

        elif animation != 'stroke' and animation != 'stroke:' :
            # Dart stroke segment
            pattern=re.compile("^stroke:[S,D,T][0-9][0-9]?$")
            if ( pattern.match(animation) or animation == 'stroke:SB' ):
                C=Colors.GetColor()
                #CStrip.Segment(50,C,3,animation.split(':')[1],False)
                CStrip.SA_Strobe(t_event, 100, C, 3)
    except:
        print("[WARNING] StripLeds_Server : Animation error :",animation,flush=True)

    if Ack :
        print("[DEBUG] StripLeds_Server : publish Ack")
        client.publish(MQTT_TOPIC,'ack')


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global SON
    message = msg.payload.decode()

    try:
        if SON.is_alive():
            t_event.set()
            while SON.is_alive():
                time.sleep(0.01)
            t_event.clear()
            SON.join()
    except:
        pass

    if message != 'ack' and (message.startswith('thread') \
            or message.startswith('ack:thread') \
            or message.startswith('Flames')):
        message = message.replace('thread:', '')
        SON = Thread(target=animation, args=(t_event, message))
        SON.start()
    elif message != 'ack':
        animation(None, message)

MQTT_HOST = "localhost"
MQTT_TOPIC = "pydarts/TargetLeds"
DMA = 10

if len(sys.argv) < 5 or len(sys.argv) > 7 :
    usage("Bad number of arguments")
else :

    i = 1
    if sys.argv[1][0:6] == '-host=':
        MQTT_HOST = sys.argv[1].split('=')[1]
        i += 1

    try :
        DMA = int(sys.argv[i])
    except :
        usage("DMA {} not allowed (Only 9/10)".format(DMA))
    if DMA not in (9,10) :
        usage("DMA {} not allowed (Only 9/10)".format(DMA))

    MQTT_TOPIC = sys.argv[i+1]

    try :
        PIN = int(sys.argv[i+2])
    except :
        usage("PIN {} not allowed (Only 10/12/18/21)".format(sys.argv[i]))
    if PIN not in (10,12,18,21) :
        usage("PIN {} not allowed (Only 10/12/18/21)".format(PIN))

    try :
        NB_PIXELS = int(sys.argv[i+3])
        if NB_PIXELS == 0:
            usage("NB_PIXELS must be greater than 0")

    except :
        usage("NB_PIXELS must be an integer")

    try :
        BRIGHTNESS = float(sys.argv[i+4])
    except :
        usage("BRIGHTNESS must be a float between 0 and 1")
    if BRIGHTNESS > 1 and BRIGHTNESS <= 100:
        BRIGHTNESS /= 100

    if BRIGHTNESS < 0 or BRIGHTNESS > 1 :
        usage("BRIGHTNESS must be a float between 0 and 1")

    CStrip = CStrip.CStrip(PIN, NB_PIXELS, BRIGHTNESS, DMA, 'STRIP')
    Colors = CColors.CColors()

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        t_event = Event()
        client.on_message = on_message

        client.connect(MQTT_HOST, 1883, 60)

        client.loop_forever()
    except Exception as e:
        print("[ERROR] StripLeds_Server : Cannot connect to", MQTT_HOST)
        print(f"[ERROR] Stripleds_Server : Exception is {e}")
        sys.exit(9)

