
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

SON = None

def usage(msg):
    print("")
    print("TargetLeds_Server.py [-host={}] [-leds=raspyleds] [-bgcolors={}] [-bgbrightness={}] <DMA_CHANNEL> <TOPIC> <CONFIG> <PIN> <BRIGHTNESS>".format(MQTT_HOST, 'blue,red,white', 10))
    print("")
    print(" ERROR : {}".format(msg))
    print("")
    sys.exit(9)

# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, rc):
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    print(f"[DEBUG] TargetLeds_Server : Listen {MQTT_TOPIC} on {MQTT_HOST}", flush=True)

def animation(t_event, msg):

    C = None

    if msg[0:3:1] == 'ack':
        Ack = True
        msg = msg[4::]
    else :
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
        animation = 'Wait'
        try:
            wait_time = int(msg.split(",")[1]) * int(msg.split(",")[3])
        except:
            wait_time = 500
    elif msg[0:4:1] != 'leds' and msg[0:4:1] != 'goal':
        try:
            animation = msg.split(',')[0]
            iterations = int(msg.split(',')[1])
            color = msg.split(',')[2]
            delay = int(msg.split(',')[3])
            try:
                add = msg.split(',')[4]
            except:
                add = None
        except:
            iterations = 1
            delay = 10
            color = None
    else:
        animation = msg
        iterations = 1

    if C is None:
        try:
            C = Colors.GetColor(color)
        except:
            C = Colors.GetColor()

    
    print(f"[DEBUG] TargetLeds_Server : Launch {animation}", flush=True)
    try:
        if animation == 'quit' :
            print("[DEBUG] TargetLeds_Server : Disconnect. Sleep 1s", flush=True)
            time.sleep(1)
            client.publish(MQTT_TOPIC + '-ack',"ack")
            client.disconnect()

        elif animation == 'Wait':
            CStrip.Wait(wait_time)

        elif animation == 'off' :
            CStrip.AllLeds(Colors.GetColor('black'))

        # Animations
        elif animation == 'Alain':
            CStrip.TA_Alain(t_event, delay, C, iterations)
        elif animation == 'Alain2':
            CStrip.TA_Alain2(t_event, delay, C, iterations)
        elif animation.startswith('blink:'):
            pattern = re.compile("^blink:.*$")
            if (pattern.match(animation)):
                CStrip.TA_Blink(t_event, 150, C, animation.split(':')[1])
        elif animation == 'Alfred':
            CStrip.TA_Alfred(t_event, delay, C, iterations)
        elif animation == 'DoubleBull':
            CStrip.TA_DoubleBull(t_event, delay, C, iterations)
        elif animation == 'FadeInOut':
            CStrip.TA_FadeInOut(t_event, delay, C, iterations)
        elif animation == 'FadeRGB':
            CStrip.TA_FadeRGB(t_event, delay, C, iterations)
        elif animation == 'Georges':
            CStrip.TA_Georges(t_event, delay, C, iterations)
        elif animation == 'Hue':
            CStrip.TA_Hue(t_event, delay, C, iterations)
        elif animation == 'Light':
            CStrip.TA_Light(C)
# Added by Manu script
        elif animation == 'Lotus':
            CStrip.TA_Lotus(t_event, delay, C, iterations)
# End added by Manu script.
        elif animation == 'Mireille':
            CStrip.TA_Mireille(t_event, delay, C, iterations)
        elif animation == 'Pacman':
            CStrip.TA_Pacman(t_event, delay, C, iterations)
        elif animation == 'Police':
            CStrip.TA_Police(t_event, delay, C, iterations)
        elif animation == 'Rainbow':
            CStrip.TA_Rainbow(t_event, delay, C, iterations)
        elif animation == 'Rainbow2':
            CStrip.TA_Rainbow2(t_event, delay, C, iterations)
        elif animation == 'RandomColor':
            CStrip.TA_RandomColor(t_event, delay, C, iterations)
        elif animation == 'Ring':
            CStrip.TA_Ring(t_event, delay, C, iterations)
        elif animation == 'Snake':
            CStrip.TA_Snake(t_event, delay, C, iterations)
        elif animation == 'Simone' or animation == 'Daisy':
            CStrip.TA_Daisy(t_event, delay, C, iterations) #by Manu script.
        elif animation == 'SimpleBull':
            CStrip.TA_SimpleBull(t_event, delay, C, iterations)
        elif animation == 'Sparkle':
            CStrip.TA_Sparkle(t_event, delay, C, iterations)
        elif animation == 'Strobe':
            CStrip.TA_Strobe(t_event, delay, C, iterations)
        elif animation == 'TheaterChase':
            CStrip.TA_TheaterChase(t_event, delay, C, iterations)
        elif animation == 'Twinkle':
            CStrip.TA_Twinkle(t_event, delay, C, iterations)

        elif animation.startswith('custom'):
            CStrip.TA_Perso(animation)

        elif animation == 'stroke:DB':
            C = Colors.GetColor("gold")
            CStrip.DoubleBull(t_event, 5, C, 3)
        elif animation == 'stroke:SB':
            C = Colors.GetColor("silver")
            CStrip.SimpleBull(t_event, 5, C, 2)
        elif animation.split('|')[0] == 'leds' :
            CStrip.TestSegment(animation.split('|')[1])

        elif animation == 'Debug':
            CStrip.Debug(delay,C,1)
        elif animation == 'DebugSeg':
            CStrip.DebugSeg(delay,C,1,int(add))
        elif animation == 'Background':
            CStrip.Background()
        elif animation == 'brightness':
            # Change brightness
            CStrip.SetBrightness(animation.split(':')[1])

        elif animation.startswith('stroke:'):
            # Dart stroke segment
            pattern = re.compile("^stroke:[S,D,T][0-9][0-9]?$")
            if (pattern.match(animation) or animation == 'stroke:SB' ):
                C = Colors.GetColor()
                CStrip.Segment(50,C,3,animation.split(':')[1],True)

        elif animation.startswith('goal:'):
            # Segment(s) to be stroked
            pattern = re.compile("^goal:.*$")
            if pattern.match(animation) :
                print(f"Target : animation = {animation}", flush=True)
                CStrip.Segment(50,None,3,animation.split(':')[1],False)

        elif animation.startswith('simon:'):
            # Segment(s) to be stroked
            pattern = re.compile("^simon:.*$")
            if pattern.match(animation) :
                CStrip.Simon(50,None,3,animation.split(':')[1],False)
    except:
        print(f"[ERROR] TargetLeds_Server : Animation error : {animation}", flush=True)

    if Ack :
        print(f"[DEBUG] TargetLeds_Server : publish Ack", flush=True)
        client.publish(MQTT_TOPIC,"ack")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global SON
    message = msg.payload.decode().replace(' ','')

    try:
        if SON.is_alive():
            # Stop old thread
            t_event.set()
            while SON.is_alive():
                time.sleep(0.01)
            t_event.clear()
            SON.join()
    except:
        pass
    if message != 'ack' and (message.startswith('thread') or message.startswith('blink')):
        message = message.replace('thread:', '')
        SON = Thread(target=animation, args=(t_event, message))
        SON.start()
    elif message != 'ack':
        animation(None, message)


MQTT_HOST = "localhost"
MQTT_TOPIC = "pydarts/TargetLeds"
DMA = 10
leds_type = None
BGBRIGHTNESS = None
BGCOLORS = None

if len(sys.argv) < 5 or len(sys.argv) > 9 :
    usage("Bad number of arguments : {}".format(len(sys.argv)))
else :
    Colors = CColors.CColors()

    i = 1
    if sys.argv[i][0:6] == '-host=' :
        MQTT_HOST = sys.argv[i].split('=')[1]
        i += 1

    if sys.argv[i][0:6] == '-leds=' :
        if sys.argv[i].split('=')[1] == 'raspyleds':
            leds_type = 'raspyleds'

        LEDS_TYPE = sys.argv[i].split('=')[1]
        i += 1

    if sys.argv[i][0:10] == '-bgcolors=':
        colors = sys.argv[i].split('=')[1].split(',')
        BGCOLORS = []

        for color in colors:
            try:
                BGCOLORS.append(Colors.GetColor(color))
            except:
                usage("Unknown background color {}".format(color))
        i += 1

    if sys.argv[i][0:14] == '-bgbrightness=':
        try:
            BGBRIGHTNESS = int(sys.argv[i].split('=')[1])
            if BGBRIGHTNESS < 0 or BGBRIGHTNESS > 100:
                usage("bgbrightness must be an interger between 0 and 100 : {} not allowed".format(sys.argv[i].split('=')[1]))
        except:
            usage("bgbrightness must be an interger between 0 and 100")
        i += 1

    try:
        DMA = int(sys.argv[i])
    except:
        usage("DMA {} not -- allowed (Only 9/10)".format(sys.argv[i]))

    if DMA not in [9, 10]:
        usage("DMA {} not allowed (Only 9/10)".format(DMA))

    MQTT_TOPIC = sys.argv[i+1]

    CONFIG = sys.argv[i+2]
    try:
        conf = ast.literal_eval(CONFIG)
    except:
        usage("CONFIG must be a valid dict")

    try:
        PIN = int(sys.argv[i+3])
    except:
        usage("PIN {} not allowed (Only 10/12/18/21)".format(PIN))

    try:
        BRIGHTNESS = float(sys.argv[i+4])
    except:
        usage("BRIGHTNESS must be a float between 0 and 1")
    if BRIGHTNESS > 1 and BRIGHTNESS <= 100:
        BRIGHTNESS /= 100

    if BRIGHTNESS < 0 or BRIGHTNESS > 1 :
        usage("BRIGHTNESS must be a float between 0 and 1")

    # Compute NB_PIXELS
    NB_PIXELS = 0
    for c in conf :
        for pixel in conf[c].split(','):
            if pixel != '' and int(pixel) >= NB_PIXELS:
                NB_PIXELS = int(pixel)+1

    CStrip = CStrip.CStrip(PIN, NB_PIXELS, BRIGHTNESS, DMA, 'TARGET', configuration=CONFIG, leds_type=leds_type, bgcolors=BGCOLORS, bgbrightness=BGBRIGHTNESS)

    if CStrip.target_leds_count == 0:
        print("[WARNING] No leds configured")
        sys.exit(0)

    print(f"[DEBUG] TargetLeds_Server : Starting server with following parameters")
    print(f"[DEBUG] TargetLeds_Server : host={MQTT_HOST}")
    print(f"[DEBUG] TargetLeds_Server : Dma channel={DMA}")
    print(f"[DEBUG] TargetLeds_Server : Pin={PIN}")
    print(f"[DEBUG] TargetLeds_Server : Topic={MQTT_TOPIC}")
    print(f"[DEBUG] TargetLeds_Server : Nb pixels={NB_PIXELS}")
    print(f"[DEBUG] TargetLeds_Server : Brightness={BRIGHTNESS}")
    print(f"[DEBUG] TargetLeds_Server : config={CONFIG}", flush=True)

    if BGBRIGHTNESS is not None:
        print(f"[DEBUG] TargetLeds_Server : bgbrightness={BGBRIGHTNESS}", flush=True)
    if BGCOLORS is not None:
        print(f"[DEBUG] TargetLeds_Server : bgcolors={BGCOLORS}", flush=True)

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        t_event = Event()
        client.on_message = on_message

        client.connect(MQTT_HOST, 1883, 60)
        print("[INFO] TargetLeds_Server : Connected", flush=True)
        client.loop_forever()

    except:
        print("[ERROR] TargetLeds_Server : Cannot connect to",MQTT_HOST)
        sys.exit(9)

