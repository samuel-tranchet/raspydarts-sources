#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from RPi import GPIO as gpio

import pygame
import pyautogui

# For GPIO Extender
from . import cgpio_extender

MAX_GPIO = 27
# pylint: disable=no-member
USEREVENT = pygame.USEREVENT
# pylint: enable=no-member

gamecontext = {
          'escape' : 'GAMEBUTTON'
         ,'space' : 'PLAYERBUTTON'
         ,'+' : 'VOLUME-UP'
         ,'-' : 'VOLUME-DOWN'
         ,'[+]' : 'VOLUME-UP'
         ,'[-]' : 'VOLUME-DOWN'
         ,'b' : 'BACKUPBUTTON'
         ,'j' : 'JOKER'
         ,'c' : 'CHEAT'
         ,'m' : 'MISSDART'
         ,'r' : 'BACK'
         ,'g' : 'GAMEBUTTON'
         ,'u' : 'VOLUME-MUTE'
         }

numbers = {
         '0' : '0'
        ,'1' : '1'
        ,'2' : '2'
        ,'3' : '3'
        ,'4' : '4'
        ,'5' : '5'
        ,'6' : '6'
        ,'7' : '7'
        ,'8' : '8'
        ,'9' : '9'
        }

shiftnumbers = {
         'world 64' : '0'
        ,'0'        : '0'
        ,'&'        : '1'
        ,'1'        : '1'
        ,'world 73' : '2'
        ,'"'        : '3'
        ,'3'        : '3'
        ,"'"        : '4'
        ,"4"        : '4'
        ,'('        : '5'
        ,'5'        : '5'
        ,'-'        : '6'
        ,'6'        : '6'
        ,'world 72' : '7'
        ,'_'        : '8'
        ,'8'        : '8'
        ,'world 71' : '9'
        }

shiftalpha = {
         'world 64' : 'à',
         'world 71' : 'ç',
         'world 72' : 'è',
         'world 73' : 'é',
         ';':'.'
        }

shiftmath = {
        ':':':',
        '=':'+'
        }

buttons_list = ['NEXTPLAYER', 'BACK', 'GAMEBUTTON', 'VALIDATE', 'CANCEL', 'UP',
            'DOWN', 'LEFT', 'RIGHT', 'PLUS', 'MINUS', 'VOLUME_UP',
            'VOLUME_DOWN', 'VOLUME_MUTE', 'DEMOLED', 'CPTPLAYER']

events_list = {
         'LIGHT_FLASH': 1,
         'LIGHT_CELEBRATION': 2,
         'LIGHT_CELEBRATION2': 3,
         'STROBE': 4,
         'EVENT': 5,
         'SOUND': 6,
         'DMD': 7
#         'SCREEN': 7
         }

def simkeypress():
    '''
    In order to wake-up from screen saver
    '''
    pyautogui.FAILSAFE = False
    print(f"[DEBUG] simkeypress()")
    pyautogui.keyDown('shift')
    pyautogui.keyUp('shift')

####################
# New Fresh class that handle raspberry GPIO created by Remi D. (Reredede)
####################

class Craspberry():
    """
    Raspberry class
    """

    def __init__(self, logs, config, conf_target_led, event, t_event=None):
        self.logs = logs
        self.shift = False
        self.config = config
        #self.myDisplay = myDisplay
        self.event = event

        self.pins = {}
        for button in buttons_list:
            self.pins[button] = False

        self.extended_gpio = False
        self.pin_stripled = 0
        self.nbr_stripled = 0
        self.bri_stripled = 0.5
        self.pin_targetled = 0
        self.nbr_target_leds = 0
        self.bri_targetled = 0.5
        self.inputs = []
        self.outputs = []

        self.keys = config.config['SectionKeys']
        self.buttons = config.config['Raspberry']
        self.conf_outputs = config.config['Raspberry_BoardPinsOuts']
        self.conf_inputs = config.config['Raspberry_BoardPinsIns']
        self.leds = config.leds
        self.last_click = 0
        self.conf_target_led = conf_target_led
        self.target_leds = ""
        self.target_leds_blink = ""
        self.newresolution = []

        if config.file_exists:
            # Apply config file configuration
            for pin_gpio in [pin for pin in self.conf_inputs.values() if pin != '']:
                self.set_inputs(pin_gpio)

            for pin_gpio in [pin for pin in self.conf_outputs.values() if pin != '']:
                self.set_outputs(pin_gpio)

            # Compute number of leds on target
            for key, value in self.conf_target_led.items():
                for led in value.split(','):
                    if led != '' and int(led) >= self.nbr_target_leds:
                        self.nbr_target_leds = int(led) + 1

            for key, value in self.leds.items():
                if key == 'pin_stripled':
                    self.pin_stripled = int(value)
                elif key == 'nbr_stripled':
                    self.nbr_stripled = int(value)
                elif key == 'bri_stripled':
                    self.bri_stripled = float(value)
                elif key == 'pin_targetled':
                    self.pin_targetled = int(value)
                elif key == 'bri_targetled':
                    self.bri_targetled = float(value)

        if int(self.buttons['EXTENDED_GPIO']) == 1:
            self.gpio = cgpio_extender.Gpio_extender(self.buttons)
        else:
            self.gpio = None

        self.logs.log("DEBUG", f"self.buttons={self.buttons}")

        self.set_buttons(self.buttons)
        self.play_sound = None
        self.send_insult = None
        self.t_event = t_event
        self.sleep = False
        self.old_detection = bool(config.config['SectionAdvanced']['richard-mode'])

    def set_play_sound(self, method):
        """
        In order to play sound from here
        """
        self.play_sound = method

    def set_send_insult(self, method):
        """
        In order to send text to DMD
        """
        self.send_insult = method

    def get_max_gpio():
        """
        Get max(GPIO)
        """
        return MAX_GPIO

    def reset_gpio(self):
        """
        Init target's GPIO
        """
        for pin in self.inputs:
            gpio.setup(pin, gpio.IN)

        for pin in self.outputs:
            gpio.setup(pin, gpio.OUT)

        if not self.extended_gpio:
            for pin in [pin for pin in self.pins.values() if pin is not False]:
                if 0 < int(pin) <= MAX_GPIO:
                    self.logs.log("DEBUG", f"GPIO {pin} set to input")
                    gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)

    def init_gpio(self, pins, direction):
        """
        Init GPIO
        """
        for pin in pins:
            if direction == 'OUT':
                gpio.setup(int(pins[pin]), gpio.OUT)
            else:
                gpio.setup(int(pins[pin]), gpio.IN)

    def set_inputs(self, pin_gpio):
        """
        Set inputs configuration
        """
        if pin_gpio != '' and 0 < int(pin_gpio) <= MAX_GPIO:
            self.inputs.append(int(pin_gpio))

    def set_outputs(self, pin_gpio):
        """
        Set outputs configuration
        """
        if pin_gpio != '' and 0 < int(pin_gpio) <= MAX_GPIO:
            self.outputs.append(int(pin_gpio))

    def set_buttons_conf(self, conf_buttons):
        """
        Set buttons configuration
        """
        for key in conf_buttons:
            self.buttons[key] = conf_buttons[key]

    def set_keys_conf(self, conf_keys):
        """
        Set keys configuration
        """
        for key in conf_keys:
            self.keys[key] = conf_keys[key]

    def set_inputs_conf(self, conf_inputs):
        """
        Set input pin's configuration
        """
        for key in conf_inputs:
            self.conf_inputs[key] = conf_inputs[key]
            self.config.inputs[key] = conf_inputs[key]

        self.logs.log("DEBUG", f"conf_inputs[key]={conf_inputs[key]}")
        self.logs.log("DEBUG", f"self.conf_inputs[key]={self.conf_inputs[key]}")
        self.logs.log("DEBUG", f"self.config.inputs[key]={self.config.inputs[key]}")


    def set_outputs_conf(self, conf_outputs):
        """
        Set output pin's configuration
        """
        for key in conf_outputs:
            self.conf_outputs[key] = conf_outputs[key]
            self.config.outputs[key] = conf_outputs[key]

    def set_leds_conf(self, config_leds):
        """
        Set leds configuration
        """
        self.pin_stripled = int(config_leds['PIN_STRIPLED'])
        self.nbr_stripled = int(config_leds['NBR_STRIPLED'])
        self.bri_stripled = int(config_leds['BRI_STRIPLED'])
        self.pin_targetled = int(config_leds['PIN_TARGETLED'])
        self.bri_targetled = int(config_leds['BRI_TARGETLED'])

        self.config.config['Raspberry_Leds'] = config_leds

    def set_buttons(self, buttons):
        """
        set buttons
        """
        if int(buttons['EXTENDED_GPIO']) == 1:
            self.extended_gpio = True
            if self.gpio is None:
                try:
                    self.gpio = cgpio_extender.Gpio_extender(self.buttons)
                    self.gpio.set_buttons(buttons)
                except:
                    self.extended_gpio = False
                    return False
            else:
                self.gpio.set_buttons(buttons)
        else:
            self.extended_gpio = False
            if self.gpio:
                del self.gpio
            self.gpio = None
            for button in buttons_list:
                pin = f'PIN_{button}'
                if buttons[pin] == '0':
                    self.pins[pin] = False
                else:
                    try:
                        self.pins[pin] = int(buttons[pin])
                        gpio.setup(self.pins[pin], gpio.IN, pull_up_down=gpio.PUD_UP)
                    except: # pylint: disable=bare-except
                        self.pins[pin] = False
        return True

    def set_target_leds(self, valeur):
        """
        Set target leds values
        """
        self.target_leds = valeur

    def set_target_leds_blink(self, valeur):
        """
        Set target leds to blink
        """
        self.target_leds_blink = valeur

    def gpio_connect(self):
        """
        Not realy need to connect like Serial port
        """
        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)

    def gpio_flush(self):
        """
        Flush GPIO values
        """
        gpio.cleanup()

    def test_gpio(self):
        """
        Test GPIO inputs (Target's)
        """
        gpio_input = []
        # Read segments (S1, D2, T4...)
        if self.inputs and self.outputs:
            for pinout in self.outputs:
                gpio.output(pinout, gpio.HIGH)

                for pinin in self.inputs:
                    gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
                    if gpio.input(pinin):
                        gpio_input.append(f"{pinin}{pinout}")

                gpio.output(pinout, gpio.LOW)

        if gpio_input:
            # Return all possible values
            segments = []
            for segment, pin_gpio in self.keys.items():
                for gpio_in in gpio_input:
                    if pin_gpio == gpio_in:
                        segments.append(segment)

            if len(segments) == 0:
                return [1, f'ERREUR : Code : {gpio_input}']
            if len(segments) > 1:
                return [2, f"ATTENTION : {'/'.join(segments)}"]
            return [0, segments[0]]

        return gpio_input

    def listen_gpio(self):
        """
        Read GPIO inputs (Target's)
        """
        gpio_input = None
        # Read segments (S1, D2, T4...)
        if self.inputs and self.outputs:
            # Make GPIO readable and value is False / Down / 0
            #for pinin in self.inputs:
            #    gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

            # Force output to False / Down / 0
            #gpio.output(self.outputs, gpio.LOW)

            if self.old_detection:
                for pinout in self.outputs:
                    gpio.output(pinout, gpio.HIGH)

                    for pinin in self.inputs:
                        gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
                        if gpio.input(pinin):
                            gpio_input = f'{pinin}{pinout}'

                    gpio.output(pinout, gpio.LOW)
            else:
                # Make GPIO readable and value is False / Down / 0
                for pinin in self.inputs:
                    gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

                # Force output to False / Down / 0
                gpio.output(self.outputs, gpio.LOW)

                for pinout in self.outputs:
                    gpio.output(pinout, gpio.HIGH)

                    for pinin in self.inputs:
                        if gpio.input(pinin):
                            gpio_input = f'{pinin}{pinout}'

                    gpio.output(pinout, gpio.LOW)


        if gpio_input:
            for segment, pin_gpio in self.keys.items():
                if pin_gpio == gpio_input:
                    return segment

        return gpio_input

    def read_gpio(self):
        """
        Read GPIO (Button's)
        """

        for key in self.pins:
            if self.pins[key] is not False and gpio.input(self.pins[key]) == gpio.LOW :
                # Button pressed
                return key.replace('PIN_','BTN_')
        return False

    def test_buttons(self):
        """
        Return list of pressed buttons or key pressed if any
        Used in Test Buttons Menu
        """

        if not self.extended_gpio:
            return 'nogpio'

        key_pressed = None

        pygame.time.set_timer(USEREVENT, 0)
        pygame.time.set_timer(USEREVENT, 10000)

        while True:

            key_pressed = self.gpio.test_entries()

            if len(key_pressed) > 0:
                self.logs.log("DEBUG", f"Input debug (GPIO) : {key_pressed}")
                pygame.time.set_timer(USEREVENT, 0)
                return key_pressed

            key_pressed = self.keyboard_mouse(['num', 'alpha', 'fx', 'arrows'],['enter', 'tab', 'backspace', 'left shift', 'escape', 'space', 'double-click', 'single-click', 'resize'],'menue')
            if key_pressed:
                self.logs.log("DEBUG", f"Input debug (pyGame) : {key_pressed}")
                pygame.time.set_timer(USEREVENT, 0)
                return key_pressed
            if key_pressed is False:
                return False

    def reset_timers(self):
        """
        Called after key perssed
        """
        for index in (5, 6, 7):
            pygame.time.set_timer(USEREVENT + index, 0)

    def listen_inputs(self, k_type=['num', 'alpha', 'fx', 'arrows'], specials=['enter', 'tab', 'backspace', 'left shift', 'escape', 'space', 'double-click', 'single-click', 'resize'], wait_for=None, context='menus', timeout=0, light=None, events=None, firstname=None):
        """
        Read input : MXP, GPIO, keyboard, mouse, ...
        """

        inputs = None
        gpio.setmode(gpio.BCM)
        self.reset_gpio()

        if timeout > 0:
            pygame.time.set_timer(USEREVENT, 0)
            pygame.time.set_timer(USEREVENT,timeout)

        if events is not None:
            for event in events:
                if event[1] == 'STROBE' and self.extended_gpio and event[0] > 0:
                    self.logs.log("DEBUG", f"Event {event[2]} initialized every {event[0]}ms")
                    pygame.time.set_timer(USEREVENT + events_list['STROBE'], event[0])
                elif event[1] in ('EVENT', 'SOUND', 'DMD') and event[0] > 0:
                    self.logs.log("DEBUG", f"Event {event[2]} initialized every {event[0]}ms")
                    pygame.time.set_timer(USEREVENT + events_list[event[1]], event[0])

        count = 0
        while True:
            if self.sleep:
                time.sleep(self.config.delay)
                self.sleep = False
            count += 1
            if count % 1000 == 0:
                count = 0
                pygame.mouse.set_visible(False)
            # Read buttons
            if self.extended_gpio:
                if light is not None:
                    self.gpio.light(light)

                # Read button from extend card
                if context == 'test':
                    inputs = self.gpio.test_entries()
                else:
                    inputs = self.gpio.read_entries()

                if inputs and isinstance(inputs, str):
                    self.logs.log("DEBUG",f"Input debug (ext GPIO) : {inputs.replace('PIN_', 'BTN_')}")
                    if timeout > 0:
                        pygame.time.set_timer(USEREVENT, 0)
                    if inputs in ('PIN_LEFT', 'PIN_RIGHT', 'PIN_UP', 'PIN_DOWN', 'PIN_VALIDATE'):
                        self.gpio.strobe_buttons(['LIGHT_NAVIGATE'], iterations=2)
                    if inputs in ('PIN_PLUS', 'PIN_MINUS'):
                        self.gpio.strobe_buttons(['LIGHT_PLAYERS'], iterations=2)
                    self.reset_timers()
                    self.sleep = True
                    simkeypress()
                    return inputs.replace('PIN_', 'BTN_')
            else:
                # Wihout extend card
                inputs = self.read_gpio()
                if inputs:
                    self.logs.log("DEBUG", f"Input debug (GPIO) : {inputs}")
                    self.reset_timers()
                    simkeypress()
                    return inputs

            # Read target
            if context == 'test':
                inputs = self.test_gpio()
            else:
                inputs = self.listen_gpio()

            if inputs:
                self.logs.log("DEBUG", f"Input debug (Serial) : {inputs}")
                self.reset_timers()
                if not self.extended_gpio:
                    self.sleep = True
                simkeypress()
                return inputs

            # If serial returns false, try to read keyboard
            inputs = self.keyboard_mouse(k_type, specials, context, events, firstname)
            if inputs is not None:
                self.logs.log("DEBUG", f"Input debug (pyGame) : {inputs}")
                if inputs is not False:
                    simkeypress()

            # Return Serial input if expected (or if nothing expected)
            if inputs is False or (inputs is not None and (wait_for is None or str(inputs) in wait_for)):
                self.reset_timers()
                return inputs

    def keyboard_mouse(self, k_type, specials, context=None, wait_events=None, firstname=None):
        """ KEYBOARD & MOUSE (from pygame)
        Context can be different, dependanding from where this method is used.  So
        far : 'menus' or 'game' or 'editing'

        pygame events are consumed here
        """
        realkey = -1
        events = pygame.event.get()

        # Look for events
        for event in events:

            if event.type == USEREVENT:
                pygame.time.set_timer(USEREVENT, 0)
                return False

            if event.type == USEREVENT + 1:
                self.light_buttons(['LIGHT_FLASH'], False)

            #elif event.type == USEREVENT + events_list['SCREEN']:
            #    self.t_event.set()

            elif event.type == USEREVENT + 2:
                self.light_buttons(['LIGHT_CELEBRATION'], False)

            elif event.type == USEREVENT + 3:
                self.light_buttons(['LIGHT_CELEBRATION2'], False)

            elif event.type == USEREVENT + events_list['STROBE'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'STROBE':
                        self.gpio.strobe_buttons(wait_event[2], 1)

            elif event.type == USEREVENT + events_list['EVENT'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'EVENT':
                        self.event.publish(wait_event[2])

            elif event.type == USEREVENT + events_list['SOUND'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'SOUND':
                        self.play_sound(wait_event[2], duration=5000)

            elif event.type == USEREVENT + events_list['DMD'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'DMD':
                        self.send_insult(firstname)

            # If pyGame return Exit
            elif event.type == pygame.QUIT:
                self.logs.log("DEBUG","Please exit any network game before killing pyDarts :)")
                if context in ('game', 'waitcomputer'):
                    return 'GAMEBUTTON'
                return 'escape'
            # Case of Key UP
            if event.type == pygame.KEYUP:
                if pygame.key.name(event.key) == 'left shift':
                    self.shift = False

            # Case of key DOWN
            elif event.type == pygame.KEYDOWN:
                keyname = pygame.key.name(event.key)
                unicodekey = event.dict['unicode']
                if len(keyname) == 1 and unicodekey != '':
                    keycouple = self.real_key(unicodekey, context)
                else:
                    keycouple = self.real_key(keyname, context)
                realkey = keycouple[1]  # Get pydarts translation of key

                if realkey in specials or keycouple[0] in k_type: # return special key if allowed
                    return realkey
            # Case of resizing window - must be before click or click will take
            # precedence
            elif event.type == pygame.VIDEORESIZE:
                self.newresolution = [event.w, event.h]
                return 'resize'
            # Case of MOUSE BUTTON PRESSED
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pygame.mouse.set_visible(True)
                #on click
                if 'single-click' in specials:
                    position = pygame.mouse.get_pos()
                    return position
            elif event.type == pygame.MOUSEMOTION:
                pygame.mouse.set_visible(True)
        # Everything above failed, return -1 (0 is a valid char)
        return None

    def real_key(self, key_pressed, context):
        """
        Return real key pressed from keyboard
        """
        if key_pressed[0:3:2] == '[]':
            key_pressed = key_pressed[1:2:1]

        #####################
        ## IN GAME CONTEXT ##
        #####################
        if context in ('game', 'waitcomputer'):
            # In-game context
            k_value = gamecontext.get(key_pressed, None)

            if k_value is not None:
                return ['special', k_value]
        ######################
        ## EDITING CONTEXT ###
        ######################
        if key_pressed == 'f' and context == 'editing':
            return ['alpha', 'f']
        #######################################
        ## NO CONTEXT SET (Default is menus) ##
        #######################################

        if not self.shift:
            k_value = numbers.get(key_pressed, None)
            if k_value is not None:
                return ['num', int(k_value)]
            k_value = shiftalpha.get(key_pressed, None)
            if k_value is not None:
                return ['alpha', k_value]

            if key_pressed in ('*', '+', '/', '-', '='):
                return ['math', key_pressed]
        else:
            # shift
            k_value = shiftnumbers.get(key_pressed, None)
            if k_value is not None:
                return ['num', int(k_value)]

            k_value = shiftmath.get(key_pressed, None)
            if k_value is not None:
                return ['num', k_value]

        if key_pressed in ('down', 'up', 'left', 'right'):
            k_value = key_pressed
            k_type = 'arrows'
        elif key_pressed in ('escape', 'space', 'backspace', 'tab', 'left shift', 'resize'): # All other context,  space means 'space'
            k_value = key_pressed
            k_type = 'special'
            if key_pressed == 'left shift':
                self.shift = True #Enable Shift !
        elif key_pressed in ('enter', 'return'): # Enter and Return are comfunded volontarily
            k_value = 'enter'
            k_type = 'special'
        elif key_pressed in ('f', 'double-click'): # Everywhere else, 'f' and double-click means "Fullscreen"
            k_value = 'TOGGLEFULLSCREEN'
            k_type = 'special'
        # Other special chars, need to be at the end (based on length)
        elif len(key_pressed) in (2,3) and key_pressed[:1] == 'f': # Detect Fx keys
            k_value = key_pressed.upper()
            k_type = 'fx'
        else:
        # Detect any other key (simple alpha keys)
            k_value = key_pressed
            k_type = 'alpha'

        return [k_type, k_value]

    def get_user_event(self, light):
        """
        Get USER_EVENT according to light
        """
        return events_list.get(light, None)

    def light_buttons(self, buttons, state=True, delay=None):
        """
        Put OFF or ON a light, and, if applicable, start a timer to OFF the light
        """
        self.logs.log("DEBUG", f"light_buttons : {state} : {buttons}")
        if self.extended_gpio and buttons:
            self.gpio.light_buttons(buttons, state)

            for button in buttons:
                event = self.get_user_event(button)
                if event:
                    # Reset or cancel
                    pygame.time.set_timer(USEREVENT + event, 0)
                    if state and delay:
                        pygame.time.set_timer(USEREVENT + event, delay)

    def strobe_buttons(self, buttons, iterations=3, delay=10, delay_off=100):
        if self.extended_gpio and buttons:
            self.gpio.strobe_buttons(buttons, iterations, delay, delay_off)

    def get_defaults(self):
        """
        In case of no GPIO
        """
        return cgpio_extender.DEFAULTS
