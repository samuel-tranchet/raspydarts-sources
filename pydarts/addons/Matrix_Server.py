
# Minimum
from datetime import datetime
import time
import random
import re

# Communication module
import paho.mqtt.client as mqtt

from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT

MQTT_SERVER = "mosquitto"
MQTT_PATH = "matrix"

MATRIX_BRIGHTNESS=1
MATRIX_COUNT=7
MATRIX_ORIENTATION=-90
MATRIX_ROTATE=2

def on_connect(client, userdata, flags, rc):
    print("Connected")

    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    msg=msg.payload.decode()

    r = random.randint(0,10)

    if ( msg == 'Darts' ):
        Dart()
    elif ( msg == 'Time' ):
        Time()
    else:
        if ( len(msg)> 8):
           Message(msg,0.01)
           return

        pattern=re.compile("^[S,D,T][0-9][0-9]?$")
        if ( pattern.match(msg) or msg == 'SB' or msg == 'DB' ):
            Flash(msg)
        else:
          rnd=random.randint(0,7)

          if ( rnd == 0 ):
                HScrolling(msg,'Left')
          elif ( rnd == 1 ):
                HScrolling(msg,'Right')
          elif ( rnd == 2 ):
                VScrolling(msg,'Up')
          elif ( rnd == 3 ):
                VScrolling(msg,'Down')
          elif ( rnd == 4 ):
                Polices(msg,2)
          elif ( rnd == 5 ):
                Polices(msg,3)
          else:
                Polices(msg,1)

def Message(msg,vitesse=0.1):
    show_message(device,msg,fill="white",font=proportional(CP437_FONT), scroll_delay=vitesse)


def Dart():
    # create matrix device

    l1=4
    l2=5
    l3=6
    l4=7

    virtual = viewport(device, width=device.width*3, height= 10)
    with canvas(virtual) as draw:
        o=device.width
        for i in range(0,l1+1):
            draw.point((i+o,4),fill="white")
        o+=l1
        for i in range(0,l2+1):
            draw.point((i+o,4),fill="white")
            draw.point((i+o,3),fill="white")
            draw.point((i+o,5),fill="white")
        o+=l2
        for i in range(0,l3+1):
            draw.point((i+o,4),fill="white")
        o+=l3
        for i in range(0,l4+1):
            if ( i == 0):
                draw.point((i+o,4),fill="white")
            elif ( i == 1):
                draw.point((i+o,3),fill="white")
                draw.point((i+o,4),fill="white")
                draw.point((i+o,5),fill="white")
            elif ( i == l4):
                draw.point((i+o,2),fill="white")
                draw.point((i+o,6),fill="white")
            elif ( i == l4-1):
                draw.point((i+o,2),fill="white")
                draw.point((i+o,3),fill="white")
                draw.point((i+o,5),fill="white")
                draw.point((i+o,6),fill="white")
            else:
                draw.point((i+o,2),fill="white")
                draw.point((i+o,3),fill="white")
                draw.point((i+o,4),fill="white")
                draw.point((i+o,5),fill="white")
                draw.point((i+o,6),fill="white")
        o+=l4
    device.show()

    for i in range(0,o+2):
        if ( i < 15 ):
            virtual.set_position((i,0))
        elif ( i < 30):
            virtual.set_position((i,1))
        elif ( i > 60):
            virtual.set_position((i,0))
        elif ( i > 45):
            virtual.set_position((i,1))
        else:
            virtual.set_position((i,2))
        time.sleep(0.007)

def Flash(msg):
    with canvas(device) as draw:
        text(draw, (20, 0), msg, fill="white", font=proportional(CP437_FONT))
    device.show()
    for i in range(5):
        for c in (MATRIX_BRIGHTNESS,255,5):
            device.contrast(c)
            time.sleep(0.02)
        for c in (MATRIX_BRIGHTNESS,254,5):
            device.contrast(255-c)
            time.sleep(0.02)
    device.clear()
    device.contrast(MATRIX_BRIGHTNESS)

def Time():
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    with canvas(device) as draw:
        text(draw, (13, 0), time_str, fill="white", font=proportional(CP437_FONT))
    device.show()
    
def HScrolling(msg,Sens):

    # Right to Left
    virtual = viewport(device, width=device.width*2, height= 8)
    if ( Sens == 'Left' ):
        with canvas(virtual) as draw:
            text(draw, (device.width, 0), msg, fill="white", font=proportional(CP437_FONT))
        device.show()

        for i in range(0,device.width+1):
            virtual.set_position((i,0))
            time.sleep(0.01)

        # Go back
       # for i in range(0,device.width):
       #     virtual.set_position((device.width-i,0))
       #     time.sleep(0.01)
    else:
        # Left ro right
        with canvas(virtual) as draw:
            text(draw, (0, 0), msg, fill="white", font=proportional(CP437_FONT))
        device.show()

        for i in range(0,device.width+1):
            virtual.set_position((device.width-i,0))
            time.sleep(0.01)

        # Go back
       # for i in range(0,device.width):
       #     virtual.set_position((i,0))
       #     time.sleep(0.01)


def VScrolling(msg,Sens):

    # Right to Left
    virtual = viewport(device, width=device.width, height= 16)
    if ( Sens == 'Up' ):
        with canvas(virtual) as draw:
            text(draw, (0,8), msg, fill="white", font=proportional(CP437_FONT))
        device.show()

        for i in range(0,9):
            virtual.set_position((0,i))
            time.sleep(0.1)

        # Go back
        #for i in range(0,8):
        #    virtual.set_position((0,8-i))
        #    time.sleep(0.1)
    else:
        # Left ro right
        with canvas(virtual) as draw:
            text(draw, (0, 0), msg, fill="white", font=proportional(CP437_FONT))
        device.show()

        for i in range(0,9):
            virtual.set_position((0,8-i))
            time.sleep(0.1)

        # Go back
        #for i in range(0,8):
        #    virtual.set_position((0,i))
        #    time.sleep(0.1)

def printMatrix(msg):

    # create matrix device
    show_message(device, msg, fill="white", font=proportional(CP437_FONT))
    with canvas (device) as draw :
        text(draw,(0,0),msg,fill="white",font=proportional(CP437_FONT))

    # Brightness
    for i in range(0,3):
        for b in range(MATRIX_BRIGHTNESS,256,64):
            device.contrast(b)
            time.sleep(0.015)
        for b in range(MATRIX_BRIGHTNESS,256,64):
            device.contrast(255-b)
            time.sleep(0.015)

def randPoint():
    virtual = viewport(device, width=device.width*3, height= 10)
    with canvas(virtual) as draw:
        for i in range(0,30):
            x=random.randint(0,device.width)
            y=random.randint(0,8)
            print("x=",x," y=",y)
            draw.point((x,y), fill="white")
            time.sleep(0.1)

def Rectangle():
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
    time.sleep(1)

def Polices(msg,numPolice):

    with canvas(device) as draw:
        if (numPolice == 1):
                text(draw, (0, 0), msg, fill="white", font=proportional(CP437_FONT))
        elif ( numPolice == 2):
                text(draw, (0, 0), msg, fill="white", font=proportional(SINCLAIR_FONT))
        elif ( numPolice == 3):
                text(draw, (0, 0), msg, fill="white", font=proportional(LCD_FONT))
        else:
                text(draw, (0, 0), msg, fill="white", font=proportional(TINY_FONT))


if __name__ == "__main__":
    try:
        global device
        serial = spi(port=0, device=0, gpio=noop())
        device = max7219(serial, cascaded=MATRIX_COUNT, block_orientation=MATRIX_ORIENTATION,
                     rotate=MATRIX_ROTATE, blocks_arranged_in_reverse_order=False)
        device.contrast(MATRIX_BRIGHTNESS)
        device.clear()
        with canvas(device) as draw:
            text(draw, (0, 0), "PYDARTS", fill="white", font=proportional(CP437_FONT))
        time.sleep(2)
        device.clear()

        client = mqtt.Client()
        client.on_connect = on_connect

        client.connect(MQTT_SERVER, 1883, 60)
        client.on_message = on_message

        client.loop_forever()

    except KeyboardInterrupt:
        pass

