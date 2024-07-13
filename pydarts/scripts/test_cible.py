import RPi.GPIO as GPIO
from time import sleep

print("---------------------------------------------")
print("|-------------------------------------------|")
print(" Bienvenue dans cette petite mise en bouche")
print("|-------------------------------------------|")
print("---------------------------------------------")
print("   ")
print(" ====> Attente detection appuie sur cible")
print("   ")


########################################################################
##                       DEBUT
########################################################################


outs = [None] * 7
outs[0] = PIN_0 = 9 # Pin number on BCM Raspberry
outs[1] = PIN_1 = 10 # Pin number on BCM Raspberry
outs[2] = PIN_2 = 14 # Pin number on BCM Raspberry
outs[3] = PIN_3 = 15 # Pin number on BCM Raspberry
outs[4] = PIN_4 = 17 # Pin number on BCM Raspberry
outs[5] = PIN_5 = 22 # Pin number on BCM Raspberry
outs[6] = PIN_6 = 27 # Pin number on BCM Raspberry

ins = [None] * 12
ins[0] = PIN_7 = 6 # Pin number on BCM Raspberry
ins[1] = PIN_8 = 7 # Pin number on BCM Raspberry
ins[2] = PIN_9 = 8 # Pin number on BCM Raspberry
ins[3] = PIN_10 = 13 # Pin number on BCM Raspberry
ins[4] = PIN_11 = 16 # Pin number on BCM Raspberry
ins[5] = PIN_12 = 18 # Pin number on BCM Raspberry
ins[6] = PIN_13 = 19 # Pin number on BCM Raspberry
ins[7] = PIN_14 = 20 # Pin number on BCM Raspberry
ins[8] = PIN_15 = 23 # Pin number on BCM Raspberry
ins[9] = PIN_16 = 24 # Pin number on BCM Raspberry
ins[10] = PIN_17 = 25 # Pin number on BCM Raspberry
ins[11] = PIN_18 = 26 # Pin number on BCM Raspberry

keymap = [None] * 7
keymap[0] = ['0','1','2','4','5','6','7','8','9','*','/','_']
keymap[1] = ['a','b','c','d','e','f','g','h','i','?','!','<']
keymap[2] = ['j','k','l','m','n','o','p','q','r','&','$','>']
keymap[3] = ['s','t','u','v','w','x','y','z','A','@','#',',']
keymap[4] = ['B','C','D','E','F','G','H','I','J','}','(','"']
keymap[5] = ['K','L','M','N','O','P','Q','R','S',')','=','ยง']
keymap[6] = ['T','U','V','W','X','Y','Z','+','-',']','[','%']

# Seul les broches peuvent être utilisée 10, 12, 18 ou 21
# -> les fichiers CLeds_10.py, CLeds_12.py, CLeds_18.py et CLeds_21.py
# https://montetoncab.fr/tctedg-ou-the-cheapest-target-electronic-dart-game-ou-raspydarts-ajout-ledstrip/
PIN_LEDSTRIP = False

# Il faut se brancher sur les pins SDA/SCL = GPIO 2-3 OU Broche 3-5 fond gris
# Si vous vous servez de l'extension GPIO, il faut brancher tout vos boutons dessus! Merci!
# https://montetoncab.fr/tctedg-ou-the-cheapest-target-electronic-dart-game-ou-raspydarts-ajout-extension-gpio/
EXTENDED_GPIO = False

########################################################################
##                              FIN
########################################################################

GPIO.setmode(GPIO.BCM)

for pin in ins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

for pin in outs:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

print(f"ins={ins}")
print(f"outs={outs}")

for pin in ins:
    print(f'pin {pin} = {GPIO.input(pin)}')

#GPIO.cleanup()

def dartTouch(pinin,pinout):
    print(f"======= out = {pinout} =============")
    for pin in ins:
        if GPIO.input(pin):
            print(f"=== {pin}{pinout}")
    sleep(0.5)

try:
    while True:
        for pinout in outs:
            GPIO.output(pinout, GPIO.HIGH)
            for pinin in ins:
                if GPIO.input(pinin) == GPIO.HIGH:
                    dartTouch(pinin, pinout)
            GPIO.output(pinout, GPIO.LOW)

except KeyboardInterrupt:
    GPIO.cleanup()
