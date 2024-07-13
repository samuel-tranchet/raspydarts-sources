
"""
Manage MCP2307 I/O
"""

import time
import board
import busio

from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017

DEFAULTS = {
    'EXTENDED_GPIO': '1',
    'PIN_UP': 'A0',
    'PIN_DOWN': 'A1',
    'PIN_LEFT': 'A2',
    'PIN_RIGHT': 'A3',
    'PIN_PLUS': 'A4',
    'PIN_MINUS': 'A5',
    'PIN_VALIDATE': 'A6',
    'PIN_CANCEL':'A7',
    'PIN_NEXTPLAYER':'B0',
    'PIN_BACK':'B1',
    'PIN_GAMEBUTTON':'B2',
    'PIN_VOLUME_UP':'B3',
    'PIN_VOLUME_DOWN':'B4',
    'PIN_VOLUME_MUTE':'B5',
    'PIN_CPTPLAYER':'B6',
    'PIN_DEMOLED':'B7',
    'LIGHT_NEXTPLAYER':'',
    'LIGHT_BACK':'',
    'LIGHT_NAVIGATE':'',
    'LIGHT_VALIDATE':'',
    'LIGHT_LASER':'',
    'LIGHT_FLASH':'',
    'LIGHT_PLAYERS':'',
    'LIGHT_CELEBRATION':'',
    'LIGHT_CELEBRATION2':'',
    'LIGHT_LIGHT':''
}

class Gpio_extender:
    """
    Manage MCP2307 I/O
    """

    def __init__(self, buttons=None):
        """
        Init self.mcp and buttons
        """
        i2c = busio.I2C(board.SCL, board.SDA)
        self.mcp = MCP23017(i2c)

        # Make a list of all the pins (a.k.a 0-16)
        pins = []
        for pin in range(0, 16):
            pins.append(self.mcp.get_pin(pin))
            # Set pin to input
            pins[pin].direction = Direction.INPUT
            pins[pin].pull = Pull.UP

        # Apply configuration
        if buttons:
            self.set_buttons(buttons)
        else:
            self.set_defaults()

        self.pin_switcher = {}
        self.light_switcher = {}
        self.buttons_list = []
        self.light_list = []
        self.pull_up = Pull.UP
        self.all_io = [f"{chr}{num}" for chr in ['A', 'B'] for num in [0, 1, 2, 3, 4, 5, 6, 7]]

    def decode(self, value):
        """
        Decode string to numeric (B3 => 11)
        """
        try:
            return (ord(value[0]) - 65) * 8 + int(value[1::])
        except: # pylint: disable=bare-except
            return None

    def set_buttons(self, buttons):
        """
        Set buttons (init or after config)
        Init self.pin_switcher for further use
        Init self.buttons_list (list of inputs)
        Init self.light_list (list of outputs)
        """
        self.pin_switcher = {}
        self.light_switcher = {}
        self.buttons_list = []
        self.light_list = []

        for button in buttons:
            numeric_pin = self.decode(buttons[button].upper())
            if numeric_pin is not None:
                pin = self.mcp.get_pin(numeric_pin)

                if button != 'EXTENDED_GPIO' \
                        and button.startswith('PIN_') \
                        and len(buttons[button]) == 2 \
                        and buttons[button][0] in ('A', 'B') \
                        and buttons[button][1] in ('0', '1', '2', '3', '4', '5', '6', '7'):
                    self.pin_switcher[buttons[button]] = button.upper()
                    self.buttons_list.append(numeric_pin)
                    pin.direction = Direction.INPUT
                    pin.pull = Pull.UP

                elif button.startswith('LIGHT_'):
                    self.light_switcher[button.upper()] = buttons[button]
                    self.light_list.append(numeric_pin)
                    pin.direction = Direction.OUTPUT
                    pin.value = 0

    def get_defaults(self):
        """
        Get default configuration
        """
        return DEFAULTS

    def set_defaults(self):
        """
        Set default configuration
        """
        self.set_buttons(DEFAULTS)

    def read_entries(self):
        """
        Read self.mcp
        """
        # False/0 si appuie sur le bouton
        value = hex(self.mcp.gpio)
        return_value = None

        for button in self.buttons_list:
            if not int(value, 16) & 2**button:
                key = chr(65 + int(button / 8)) + chr(48 + button % 8)    # Compute A0..B7
                return_value = self.pin_switcher.get(key, "")

        self.mcp.clear_ints()
        return return_value

    def test_entries(self):
        """
        Read self.mcp and returns list of pressed buttons ['A0'[,'B1']]
        """
        # False/0 si appuie sur le bouton
        value = hex(self.mcp.gpio)

        pressed_buttons = []

        for button in self.buttons_list:
            if not int(value, 16) & 2**button:
                # Compute A0..B7
                pressed_buttons.append(chr(65 + int(button / 8)) + chr(48 + button % 8))

        self.mcp.clear_ints()
        return pressed_buttons

    def strobe_buttons(self, buttons, iterations=3, delay=10, delay_off=100):
        """
        Strobe light
        """
        pins = []
        org_pins = {}
        for button in buttons:
            try:
                pins.append(self.mcp.get_pin(self.decode(self.light_switcher[button])))
            except: # pylint: disable=bare-except
                return

        for iteration in range(iterations):
            for pin in pins:
                if pin.value:
                    pin.value = 0
                else:
                    pin.value = 1
            time.sleep(delay_off / 1000)
            for pin in pins:
                if pin.value:
                    pin.value = 0
                else:
                    pin.value = 1
            if iteration + 1 < iterations:
                time.sleep(delay / 1000)

    def light_buttons(self, buttons, light=True):
        """
        Light a button
        """
        pins = []
        for button in buttons:
            try:
                pins.append(self.mcp.get_pin(self.decode(self.light_switcher[button])))
            except: # pylint: disable=bare-except
                pass

        for pin in pins :
            if light:
                pin.value = 1
            else:
                pin.value = 0
