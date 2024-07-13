#!/usr/bin/env python3

# def TA animation: Animation available for Target Leds
# def SA animation: Animation available for Strip Leds

import os
import sys
import time
import colorsys
import random
import ast
import numpy as np
from datetime import datetime

#import neopixel
from rpi_ws281x import PixelStrip, Color

# Parametrage Leds
import Colors as CL

# Pour des bandes NeoPixel RGBW, changez ORDER de RGBW à GRBW.
OFF = [np.uint8(0), np.uint8(0), np.uint8(0)]
MULT_COLOR = {'S': [0, 255, 0], 'D': [0, 0, 255], 'T': [255, 0, 0], 'E': [129, 12, 128]}
TARGET_ORDER = [1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]

class CStrip(object):

    ######################
    ### Init functions ###
    ######################

    def __init__(self, pin, strip_length, brightness, dma_channel, device, configuration=None, leds_type=None, bgcolors=None, bgbrightness=None):
        freq = 800000  # LED signal frequency in hertz (usually 800khz)
        if pin in (13, 19, 41, 45, 53):
            # set to '1' for GPIOs 13, 19, 41, 45 or 53
            channel = 1
        else:
            channel = 0

        if bgcolors is None:
            bgcolors=[[0, 0, 255], [255, 0, 0], [255, 255, 255]]

        if bgbrightness is None:
            bgbrightness=10

        self.strip = PixelStrip(strip_length, pin, freq, dma_channel, False, int(brightness*255), channel)

        self.strip.begin()
        self.strip_length = strip_length
        self.handle = [[np.uint8(0), np.uint8(0), np.uint8(0)] for _a in range(self.strip_length)]
        self.pixel_min = None
        self.pixel_max = None
        self.customs = {}

        if device == 'TARGET' and configuration is not None:
            if leds_type == 'raspyleds':
                self.jimmy = True
            else:
                self.jimmy = False
            self.InitTarget(configuration, bgcolors, bgbrightness)

        self.colors = CL.CColors()
        self.userpath = os.path.expanduser('~pi')
        self.customDir = '{}/.pydarts/addons'.format(self.userpath)
        self.LoadCustoms()

        self.background = False

    """
    Print proper logs
    """
    def Logs(self, message, facility='DEBUG'):
        print(("[{}] {} - {}").format(facility, datetime.now(), message),flush=True)

    """
    Load custom animations
    """
    def LoadCustoms(self):

        try :
            custom_files = os.listdir(self.customDir)

            for animation in custom_files:
                if animation.startswith("custom"):
                    try:
                        self.Logs("Try to load {}".format(animation))
                        self.customs[animation] = []
                        with open("{}/{}".format(self.customDir, animation), "r") as custom_animation:
                            for line in custom_animation.readlines():
                                self.customs[animation].append(line.replace('\r','').replace('\n',''))

                        self.Logs("{} loaded : {}".format(animation,self.customs[animation]))

                    except:
                        self.Logs("Error with {}".format(animation), facility="ERROR")
                        pass
        except :
            self.Logs("No custom animation found")

    def InitTarget(self, configuration, colors, bgbrightness):

        configuration = ast.literal_eval(configuration)

        self.segments = {}
        self.tire = {}
        self.pieces = [[] for _n in TARGET_ORDER]
        self.ordered_pieces = [[] for _n in range(0, len(TARGET_ORDER)+1)]
        self.target_leds_count = 0

        # Store segments leds
        for segment in [f'{_s}{_n}' for _s in ['S', 'D', 'T'] for _n in range(1, 21)]+['SB', 'DB']:
            try:
                self.segments[segment] = [int(_v) for _v in configuration[segment].split(',') if _v != '']
                self.target_leds_count += len(self.segments[segment])
            except:
                self.Logs(f"No leds initialized for {segment}")
                self.segments[segment] = []

        if self.target_leds_count == 0:
            self.tire_only = True
            self.Logs(f"Tire only mode")
        else:
            self.tire_only = False

        # Store tire's leds
        for segment in ['E{}'.format(_n) for _n in range(1, 21)]:
            try:
                self.tire[segment] = [int(_v) for _v in configuration[segment].split(',') if _v != '']
                self.target_leds_count += len(self.tire[segment])
            except:
                self.Logs(f"No leds initialized for {segment}")
                self.segments[segment] = []

        if self.target_leds_count == 0:
            self.Logs("No configuration found")
            return False
        else:
            self.Logs(f"Found {self.target_leds_count} leds in configuration")

        # Store target pieces (Target order)
        piece = 0
        for number in TARGET_ORDER:
            for multiplier in ['S', 'D', 'T']:
                try:
                    self.pieces[piece].extend([int(_v) for _v in configuration['{}{}'.format(multiplier, number)].split(',')])
                except:
                    self.Logs(f"No leds initialized for {multiplier}{number}")
            piece += 1

        for number in TARGET_ORDER:
            for multiplier in ['S', 'D', 'T']:
                try:
                    self.ordered_pieces[number].extend([int(_p) for _p in configuration['{}{}'.format(multiplier, number)].split(',')])
                except:
                    self.Logs(f"No leds initialized for {multiplier}{number}")

        # Initialize circles:
        # 0 => Double bullseye
        # 1 => Bullseye
        # ...
        # 5 => Triples
        # ...
        # 10 => Doubles

        # Compute number df oircles
        if self.tire_only:
            nb_circles = 1
            circles = []
            for segment in TARGET_ORDER:
                try:
                    circles[0].extend([int(_a) for _a in configuration.get('E{}'.format(segment)).split(',') if _a != ''])
                except:
                    self.Logs(f"No leds initialized for E{segment}")

            self.triple_circle = 0
        else:
            nb_circles = 0
            for number in range(1, 21):
                simple = "S{}".format(number)
                if len(configuration.get(simple).split(',')) > nb_circles:
                    try:
                        nb_circles = len(configuration.get(simple).split(','))
                    except:
                        self.Logs(f"No leds initialized for {simple}")

            if nb_circles > 0:
                self.triple_circle = int((nb_circles + 1) / 2) + 1
            else:
                self.triple_circle = 0

            self.Logs("Found {nb_circles} leds per Simple segment")
            if self.jimmy :
                add = 1
            else:
                add = 0
            circles = [[] for circle in range(nb_circles + 4 - add)]    # + SB, DB, Triples and Doubles

            if nb_circles > 0:
                circles[0].extend([int(pixel) for pixel in configuration.get("DB").split(',')])
                circles[1].extend([int(pixel) for pixel in configuration.get("SB").split(',')])

                for number in TARGET_ORDER:
                    simple = 'S{}'.format(number)
                    double = 'D{}'.format(number)
                    triple = 'T{}'.format(number)

                    triple_done = 0
                    jimmy_done = 0
                    target = 2
                    for circle in range(0,nb_circles + 2 - add):
                        try:
                            if circle + 2 == self.triple_circle:
                                circles[target].extend([int(_a) for _a in configuration.get(triple).split(',')])
                                triple_done = 1

                            elif target == nb_circles + 3 - add:
                                circles[target].extend([int(_a) for _a in configuration.get(double).split(',')])

                            elif self.jimmy and circle == 5:
                                circles[target].append(int(configuration.get(simple).split(',')[circle]))
                                circles[target].append(int(configuration.get(simple).split(',')[circle - 1]))
                                jimmy_done = 1
                            elif not (self.jimmy and circle == 5):
                                circles[target].append(int(configuration.get(simple).split(',')[circle - triple_done + jimmy_done]))

                            target += 1
                        except:
                            if circle == self.triple_circle - 1:
                                triple_done = 1

        self.nb_circles = nb_circles
        self.circles = circles

        # Initialize list of leds in target (versus sides leds)
        self.TargetLeds = []
        for pixels in configuration:
            leds = configuration.get(pixels, '')
            for pixel in leds.split(','):
                self.TargetLeds.append(pixel)
                if pixel != '' and (self.pixel_min is None or int(pixel) < self.pixel_min):
                    self.pixel_min = int(pixel)
                if pixel != '' and (self.pixel_max is None or int(pixel) > self.pixel_max):
                    self.pixel_max = int(pixel)

        # Init segments color => When dart stroke segment, it blink with the appropriate color
        #if S20 == 'blue':
        #    color1 = [0, 0, 255]        # blue
        #    color2 = [255, 0, 0]        # red
        #    color3 = [255, 255, 255]    # white
        #else:
        #    color1 = [255, 255, 255]    # white
        #    color2 = [0, 0, 255]        # blue
        #    color3 = [255, 0, 0]        # red
        color1 = colors[0]
        color2 = colors[1]
        color3 = colors[2]
        self.bgbrithness = min(bgbrightness, 100)

        self.segment_color = {}
        list1 = [1, 4, 6, 15, 17, 19, 16, 11, 9, 5]
        list2 = [18, 13, 10, 2, 3, 7, 8, 14, 12, 20]

        self.segment_color['SB'] = [0, 0, 255]
        self.segment_color['DB'] = [255, 0, 0]

        for number in list1:
            self.segment_color[f'T{number}'] = color2
            self.segment_color[f'D{number}'] = color2
            self.segment_color[f'S{number}'] = color3
        for number in list2:
            self.segment_color[f'T{number}'] = color3
            self.segment_color[f'D{number}'] = color3
            self.segment_color[f'S{number}'] = color1

    ####################################
    ### Backup / Restore strip state ###
    ####################################


    def Backup(self):
        self.Backup = []
        for pixel in range(self.strip_length):
            self.Backup.append(self.strip.getPixelColor(pixel))

    def Restore(self):
        if self.Backup is None:
            return

        for pixel in range(self.strip_length):
            self.strip.setPixelColor(self.Backup[pixel])
        del self.Backup

    #######################
    ### Basic functions ###
    #######################

    def Reset(self):
        for pixel in range(self.strip_length):
            if (self.pixel_min is None or pixel >= self.pixel_min) and (self.pixel_max is None or pixel <= self.pixel_max):
                self.handle[pixel] = OFF

    def SetBrightness(self, Brightness):
        self.strip.setBrightness(int(float(Brightness)*255))
        self.Logs("Brightness is now {}".format(int(float(Brightness)*255)))

    def AllLeds(self, color, wait_time=0):
        for pixel in range(self.strip_length):
            if (self.pixel_min is None or pixel >= self.pixel_min) and (self.pixel_max is None or pixel <= self.pixel_max):
                self.strip.setPixelColor(pixel, int(Color(color[0], color[1], color[2])))

        self.strip.show()

        if wait_time > 0:
            time.sleep(wait_time/1000)

        if color == OFF:
            self.Reset()

    def BlitColors(self, wait_time=1, pixel_min=0, pixel_max=0, reset=False):
        # Light leds strip and wait wait_time/1000 seconds

        if pixel_max == 0:
            pixel_max = self.strip_length

        for pixel in range(pixel_min, pixel_max):
            self.strip.setPixelColor(pixel, int(Color(self.handle[pixel][0], self.handle[pixel][1], self.handle[pixel][2])))

        self.strip.show()

        if wait_time > 0:
            time.sleep(wait_time/1000)

        if reset:
            self.Reset()

    def FadePin(self, value, fade_value):
        if value <= 10:
            return 0
        else:
            return np.uint8(value - (fade_value * value / 256))

    def FadeToBlack(self, led, fade_value):
        return [self.FadePin(self.handle[led][0], fade_value),\
                self.FadePin(self.handle[led][1], fade_value),\
                self.FadePin(self.handle[led][2], fade_value)]

    def SetBlock(self, length, position, color, reverse=False, double=False):
        for _ in range(length):
            if position < 0:
                return
            if reverse or double:
                self.handle[self.strip_length - position - 1] = color
            if not reverse or double:
                self.handle[position] = color
            position += 1

    def TestSegment(self, segments, wait_time=1500):
        simples = []
        doubles = []
        triples = []

        for segment in segments.split('-'):
            if segment != '':
                color = MULT_COLOR[segment.split(':')[0]]
                pixels = segment.split(':')[1].split(',')

                if segment.split(':')[0] == 'S':
                    for pixel in pixels:
                        simples.append(int(pixel))

                elif segment.split(':')[0] == 'D':
                    for pixel in pixels:
                        doubles.append(int(pixel))

                elif segment.split(':')[0] == 'T':
                    for pixel in pixels:
                        triples.append(int(pixel))

                for pixel in pixels:
                    self.handle[int(pixel)] = color

        self.BlitColors(wait_time, True)
        self.AllLeds(OFF)

        color = MULT_COLOR['S']
        for pixel in simples:
            self.handle[pixel] = color
            self.BlitColors(wait_time / 3)

        self.AllLeds(OFF)

        color = MULT_COLOR['D']
        for pixel in doubles:
            self.handle[pixel] = color
            self.BlitColors(wait_time / 3)

        self.AllLeds(OFF)

        color = MULT_COLOR['T']
        for pixel in triples:
            self.handle[pixel] = color
            self.BlitColors(wait_time / 3)

        self.AllLeds(OFF)

    def WheelColor(self, wheel_position):
        if wheel_position < 85:
            return [wheel_position * 3, 255 -  wheel_position * 3, 0]

        elif wheel_position < 170:
            wheel_position -= 85
            return [255 -  wheel_position * 3, 0, wheel_position * 3]

        else:
            wheel_position -= 170
            return [0, wheel_position * 3, 255 - wheel_position * 3]

    def Debug(self, wait_time, color, iterations):

        for iteration in range(iterations):
            for step in range(self.strip_length):
                for pixel in range(self.strip_length):
                    if step == pixel:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF
                self.BlitColors(wait_time)
        self.AllLeds(OFF)

    def DebugSeg(self, wait_time, color, iterations, debug_segment=None):

        for iteration in range(iterations):
            if debug_segment is None:
                for segment in TARGET_ORDER:
                    for pixel in self.ordered_pieces[segment]:
                        self.handle[pixel] = color
                else:
                    for pixel in self.ordered_pieces[debug_segment]:
                        self.handle[pixel] = color

                self.BlitColors(wait_time)
            self.AllLeds(OFF)

    def IsAround(self, depth, center_x, center_y, pixel_x, pixel_y):

        diff_x = min(abs(center_x - pixel_x), 20 - abs(center_x - pixel_x))
        dff_y = abs(center_y - pixel_y)

        if int(pow(diff_x**2 + dff_y**2, 2)) <= depth:
            return True
        else:
            return False

    def GetAround(self, depth, center_x, center_y):
        if depth < 1:
            return []

        around = []
        pos_x = 0
        for piece in self.pieces:
            pos_y = 0
            for temp in piece:
                if self.IsAround(depth, center_x, center_y, pos_x, pos_y):
                    around.append(self.pieces[pos_x][pos_y])
                pos_y += 1
            pos_x += 1

        return around

    def Explode(self, event, pos_x, pos_y, size, wait_time):
        for step in range(4):
            around = self.GetAround(size, pos_x, pos_y)
            for pixel in around:
                if event is not None and event.is_set(): return
                self.handle[pixel] = [255, 0, 0]
            self.BlitColors(wait_time/10)

            for pixel in around:
                if event is not None and event.is_set(): return
                self.handle[pixel] = [255, 255, 0]
            self.BlitColors(wait_time/10)

    ##################
    ### Animations ###
    ##################
    def Background(self):
        for segment in [f'{m}{n}' for m in ['S','D','T'] for n in range(1,21)] + ['SB','DB']:
            color = self.colors.MultColor(self.segment_color[segment], self.bgbrithness / 100)
            for pixel in self.segments.get(segment,[]):
                self.handle[pixel] = color

        self.BlitColors()
        self.background = True

    def TA_Alain(self, event, wait_time, color, iterations, offset=None):
        self.Alain(event, wait_time, color, iterations, offset, mode=1)

    def TA_Alain2(self, event, wait_time, color, iterations, offset=None):
        self.Alain(event, wait_time, color, iterations, offset, mode=2)

    def Alain(self, event, wait_time, color, iterations, offset=None, mode=1):

        self.AllLeds(OFF)

        if offset is None:
            offset = random.randint(0, 20)

        for iteration in range(iterations):
            for piece in range(len(self.pieces)):
                for pixel in self.pieces[piece]:
                    if event is not None and event.is_set(): return
                    if mode == 1:
                        self.handle[pixel] = self.colors.ShakeColor(color, iteration + piece + offset)
                    else:
                        self.handle[pixel] = self.colors.ShakeColor(color, int(((iteration + piece + offset) % 20) / 7))

            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_Alain(self, event, wait_time, color, iterations, offset=None):
        self.Alain_sa(event, wait_time, color, iterations, offset, mode=1)

    def SA_Alain2(self, event, wait_time, color, iterations, offset=None):
        self.Alain_sa(event, wait_time, color, iterations, offset, mode=2)

    def Alain_sa(self, event, wait_time, color, iterations, offset=None, mode=1):

        self.AllLeds(OFF)

        if offset is None:
            offset = random.randint(0, 20)

        piece = 10
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                if mode == 1:
                    self.handle[pixel] = self.colors.ShakeColor(color, iteration + offset + int(pixel / 10))
                else:
                    self.handle[pixel] = self.colors.ShakeColor(color, int(((iteration + int(pixel / 10) + offset) % 20) / 7))

            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Alfred(self, event, wait_time, color, iterations, offset=0):
        self.Alfred(event, wait_time, color, iterations, offset)

    def Alfred(self, event, wait_time, color, iterations, offset):
        self.AllLeds(OFF)

        start = offset

        for iteration in range(iterations):
            for count in range(3):
                color = [color[1], color[2], color[0]]

                for part in range(7):
                    for pixel in self.pieces[start % 20]:
                        if event is not None and event.is_set(): return
                        self.handle[pixel] = color
                    start += 1
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Blink(self, event, wait_time, color, segment):
        self.Blink(event, wait_time, color, segment)

    def Blink(self, event, wait_time, color, segment):

        handle_on = [[np.uint8(0), np.uint8(0), np.uint8(0)] for _a in range(self.strip_length)]
        handle_off = [[np.uint8(0), np.uint8(0), np.uint8(0)] for _a in range(self.strip_length)]

        for pixel in range(self.strip_length):
            color = self.strip.getPixelColor(pixel)
            handle_on[pixel] = handle_off[pixel] = ((color >> 16) & 255,(color >> 8) & 255, color & 255)

        for goal in segment.split('|'):
            segment = goal.split('#')[0]
            if segment == 'TB':
                continue
            color = self.colors.GetColor(goal.split('#')[1])
            for pixel in self.segments.get(segment,[]) + self.tire.get(segment,[]):
                handle_on[pixel] = color

        while True:
            if event is not None and event.is_set(): return
            self.handle = handle_on[::]
            self.BlitColors(wait_time)

            if event is not None and event.is_set(): return
            self.handle = handle_off[::]
            self.BlitColors(wait_time)

    def SA_ColorWipe(self, event, wait_time, color, iterations):
        self.ColorWipe(event, wait_time, color, iterations, 'up')

    def SA_ColorWipeReverse(self, event, wait_time, color, iterations):
        self.ColorWipe(event, wait_time, color, iterations, 'down')

    def ColorWipe(self, event, wait_time, color, iterations, direction):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            if direction == 'up':
                for pixel in range(self.strip_length):
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                    self.BlitColors(wait_time)
            else:
                for pixel in range(self.strip_length - 1, 0, -1):
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                    self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_Cylon(self, event, wait_time, color, iterations, size=None):
        self.Cylon(event, wait_time, color, iterations, size)

    def Cylon(self, event, wait_time, color, iterations, size, side=0):
        self.AllLeds(OFF)

        if size is None:
            size = int(self.strip_length / 10)

        for iteration in range(iterations):
            for step in range(self.strip_length + size):
                for pixel in range(self.strip_length):
                    if event is not None and event.is_set(): return
                    if step - size <= pixel <= step + size:
                        self.handle[pixel] = color
                    elif side > 0 and pixel in (step - size - 1, step + size + 1):
                        self.handle[pixel] = self.colors.MultColor(color, 1 / size)
                    else:
                        self.handle[pixel] = OFF

                self.BlitColors(wait_time)

            for step in range(self.strip_length + size, 0, -1):
                for pixel in range(self.strip_length):
                    if event is not None and event.is_set(): return
                    opposite_pixel = self.strip_length - pixel - 1
                    if step - size <= opposite_pixel <= step + size:
                        self.handle[opposite_pixel] = color
                    elif side > 0 and opposite_pixel in (step - size - 1, step + size + 1):
                        self.handle[opposite_pixel] = self.colors.MultColor(color, 1 / size)
                    else:
                        self.handle[opposite_pixel] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_CylonDouble(self, event, wait_time, color, iterations, size=None):
        self.CylonDouble(event, wait_time, color, iterations, size)

    def CylonDouble(self, event, wait_time, color, iterations, size, side=0):
        self.AllLeds(OFF)

        if size is None:
            size = int(self.strip_length / 10)

        for iteration in range(2 * iterations):
            for step in range(int((self.strip_length + size) / 2)):
                for pixel in range(int((self.strip_length + 1) /2)):
                    if event is not None and event.is_set(): return
                    opposite_pixel = self.strip_length - pixel - 1
                    if step - size <= pixel <= step + size:
                        self.handle[pixel] = color
                        self.handle[opposite_pixel] = color

                    elif side > 0 and pixel in (step - size - 1, step + size + 1):
                        self.handle[pixel] = self.colors.MultColor(color, 1 / side)
                        self.handle[opposite_pixel] = self.colors.MultColor(color, 1 / side)
                    else:
                        self.handle[pixel] = OFF
                        self.handle[opposite_pixel] = OFF

                self.BlitColors(wait_time)

            for step in range(int((self.strip_length + size) / 2), 0, -1):
                for pixel in range(int((self.strip_length+1)/2)):
                    if event is not None and event.is_set(): return
                    opposite_pixel = self.strip_length - pixel - 1
                    if step - size <= pixel <= step + size:
                        self.handle[pixel] = color
                        self.handle[opposite_pixel] = color
                    elif side > 0 and pixel in (step - size - 1, step + size + 1):
                        self.handle[pixel] = self.colors.MultColor(color, 1 / side)
                        self.handle[opposite_pixel] = self.colors.MultColor(color, 1 / side)
                    else:
                        self.handle[pixel] = OFF
                        self.handle[opposite_pixel] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_FadeInOut(self, event, wait_time, color, iterations):
        self.FadeInOut(event, wait_time, color, iterations)

    def TA_FadeInOut(self, event, wait_time, color, iterations):
        self.FadeInOut(event, wait_time, color, iterations)

    def FadeInOut(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            #Fade In.
            for step in range(0, 256, 2):
                if event is not None and event.is_set(): return
                red = int(color[0] * step / 256)
                green = int(color[1] * step / 256)
                blue = int(color[2] * step / 256)
                self.AllLeds([red, green, blue], wait_time)
            for step in range(256, 0, -2):
                if event is not None and event.is_set(): return
                red = int(color[0] * step / 256)
                green = int(color[1] * step / 256)
                blue = int(color[2] * step / 256)
                self.AllLeds([red, green, blue], wait_time)

        self.AllLeds(OFF)

    def TA_FadeRGB(self, event, wait_time, color, iterations):
        self.FadeRGB(event, wait_time, color, iterations)

    def SA_FadeRGB(self, event, wait_time, color, iterations):
        self.FadeRGB(event, wait_time, color, iterations)

    def FadeRGB(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            for step in range(3):
                for component in range(255, 3):
                    if event is not None and event.is_set(): return
                    if step == 0:
                        self.AllLeds([component, 0, 0], wait_time)
                    elif step == 1:
                        self.AllLeds([0, component, 0], wait_time)
                    else:
                        self.AllLeds([0, 0, component], wait_time)
                for component in range(255, 0, -3):
                    if event is not None and event.is_set(): return
                    if step == 0:
                        self.AllLeds([component, 0, 0], wait_time)
                    elif step == 1:
                        self.AllLeds([0, component, 0], wait_time)
                    else:
                        self.AllLeds([0, 0, component], wait_time)
        self.AllLeds(OFF)

    def SA_Fall(self, event, wait_time, color, iterations):
        self.Fall(event, wait_time, color, iterations, reverse=False, change_color=False)

    def SA_FallColor(self, event, wait_time, color, iterations):
        self.Fall(event, wait_time, color, iterations, reverse=False, change_color=True)

    def SA_FallReverse(self, event, wait_time, color, iterations):
        self.Fall(event, wait_time, color, iterations, reverse=True, change_color=False)

    def SA_FallDouble(self, event, wait_time, color, iterations):
        self.Fall(event, wait_time, color, iterations, double=True, change_color=False)

    def Fall(self, event, wait_time, color, iterations, reverse=False, double=False, change_color=False):
        self.AllLeds(OFF)

        block_length = iterations
        speed = 0
        gravity = 0.20
        coef = 0.85
        min_speed = 0.3
        old_start = -1

        start = self.strip_length - block_length - 1
        counter = 0

        while True:
            if not(start > 0 or speed > min_speed):
                break
            while start > 0:
                if event is not None and event.is_set(): return
                if change_color:
                    color = self.WheelColor(counter % 255)
                # Tombe
                self.SetBlock(block_length, start, color, reverse, double)
                self.BlitColors(wait_time)
                self.SetBlock(block_length, start, OFF, reverse, double)

                speed += gravity
                start = int(start - speed)
                old_start = start
                counter += 1
            start = 0

            while speed > min_speed:
                if event is not None and event.is_set(): return
                if change_color:
                    color = self.WheelColor(counter % 255)
                # Rebondit
                self.SetBlock(block_length, start, color, reverse, double)
                self.BlitColors(wait_time)
                self.SetBlock(block_length, start, OFF, reverse, double)

                speed -= (gravity * coef)
                start = int(start + speed)

                if start == old_start:
                    break

                counter += 1
                old_start = start

            self.SetBlock(block_length, start, color, reverse, double)
            self.BlitColors(wait_time * 3)
        self.AllLeds(OFF)

    def SA_FillDown(self, event, wait_time, color, iterations):
        self.FillDown(event, wait_time, color, iterations)

    def FillDown(self, event, wait_time, color, iterations):

        for iteration in range(iterations):
            for step in range(self.strip_length):
                for pixel in range(self.strip_length - step):
                    if event is not None and event.is_set(): return
                    if pixel - 1 > 0:
                        self.handle[pixel - 1] = OFF
                    self.handle[pixel] = color
                    self.BlitColors(wait_time)

            for step in range(self.strip_length-1, 0, -1):
                for pixel in range(step, self.strip_length):
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = OFF
                    if pixel < self.strip_length - 1:
                        self.handle[pixel + 1] = color
                    self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_Fireworks(self, event, wait_time, color, iterations, meteor_size):
        self.Fireworks(event, wait_time, color, iterations, meteor_size, 90, True)

    def SA_FireworksReverse(self, event, wait_time, color, iterations, meteor_size):
        self.Fireworks(event, wait_time, color, iterations, meteor_size, 90, True, direction='down')

    def Fireworks(self, event, wait_time, color, iterations, meteor_size, meteor_trail_decay, meteor_random_decay, direction='up'):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            for step in range(0, self.strip_length + meteor_size):
                for pixel in range(0, self.strip_length):
                    if event is not None and event.is_set(): return
                    if not meteor_random_decay or random.randint(0, 10) > 5:
                        if direction == 'up':
                            p = pixel
                        else:
                            p = self.strip_length - 1 - pixel
                            p = pixel
                        self.handle[p] = self.FadeToBlack(p, meteor_trail_decay)
                # Draw meteor
                for pixel in range(0, meteor_size):
                    if event is not None and event.is_set(): return
                    if step - pixel < self.strip_length and step - pixel >= 0:
                        if  direction == 'up':
                            p = step - pixel
                        else:
                            p = self.strip_length - 1 - (step - pixel)
                        self.handle[p] = color
                self.BlitColors(wait_time)

            self.AllLeds(OFF)

    
    def SA_Flames(self, event, wait_time, color, iterations):
        self.Flames(event, wait_time, color, iterations)

    def Flames(self, event, wait_time, color, iterations):

        color = (255, 145, 0)
        color = (255, 115, 0)

        self.AllLeds(OFF)

        while True:
            for pixel in range(0, self.strip_length):
                if event is not None and event.is_set(): return
                flicker = random.randint(0, 155)
                flicker2 = random.randint(0, 155)
                self.handle[pixel] = (max(0, color[0] - flicker2), max(0, color[1] - flicker), max(0, color[2] - flicker))
            self.BlitColors(wait_time * random.randint(310, 620) / 100)

# Added by Manu script.
    def TA_Lotus(self, event, wait_time, color, iterations, offset=0):
        self.Lotus(event, wait_time, color, iterations, offset)

    def Lotus(self, event, wait_time, color, iterations, offset=0):
        for iteration in range(iterations):
            self.AllLeds(OFF)
            for piece in range(9, 20):
                for pixel in self.pieces[(piece + offset) % 20]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                for pixel in self.pieces[(18 - piece + offset) % 20]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            for piece in range(19, -1, -1):
                for pixel in self.pieces[(piece + offset) % 20]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = OFF
                for pixel in self.pieces[(18 - piece + offset) % 20]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)
# End added by Manu script.

    def TA_Hue(self, event, wait_time, color, iterations, offset=None):
        self.Hue(event, wait_time, color, iterations, offset)

    def Hue(self, event, wait_time, color, iterations, offset=None):
        self.AllLeds(OFF)

        if offset is None:
            offset = random.randint(0, 20)

        if self.jimmy:
            nb = 8
        else:
            nb = self.nb_circles - 2

        for iteration in range(iterations):
            for piece in range(len(self.pieces)):
                jimmy = 0
                step = 0
                double = 0
                for pixel in self.pieces[piece]:
                    if event is not None and event.is_set(): return
                    step += 1
                    if not ((self.jimmy and step == 7) or step == len(self.pieces[piece]) - 1):
                        rgb_color = colorsys.hsv_to_rgb((iteration + piece + offset) % 20 / 20, (step - double) / nb, 1)
                        color = self.colors.MultColor(rgb_color, 255)
                    else:
                        double += 1
                    self.handle[pixel] = color

            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_Light(self, color):
        self.Light(color)

    def TA_Light(self, color):
        self.Light(color)

    def Light(self, color):
        self.AllLeds(color)

    def TA_Mireille(self, event, wait_time, color, iterations, offset=None):
        self.Mireille(event, wait_time, color, iterations)

    def Mireille(self, event, wait_time, color, iterations, offset=None):
        if offset is None:
            offset = random.randint(0, 20)
        self.AllLeds(OFF)

        for iteration in range(iterations):
            for piece in range(len(self.pieces)):
                for pixel in self.pieces[piece]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            self.AllLeds(OFF)

    def SA_NewKitt(self, event, wait_time, color, iterations):
        self.NewKitt(event, wait_time, color, iterations)

    def NewKitt(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        length = int(self.strip_length/15)

        for iteration in range(0, iterations):
            self.Cylon(event, wait_time, color, 1, length, side=length)
            self.CylonDouble(event, wait_time, color, 1, length, side=length)

    def TA_Pacman(self, event, wait_time, color, iterations):
        self.Pacman(event, wait_time, color, iterations)

    def Pacman(self, event, wait_time, color, iterations, offset=None):
        self.AllLeds(OFF)

        if not self.tire_only:
            for piece in [2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20, 1, 18]:
                for pixel in self.ordered_pieces[piece][0:3]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color

            for pixel in self.circles[0] + self.circles[1]:
                if event is not None and event.is_set(): return
                self.handle[pixel] = color

            self.handle[self.ordered_pieces[18][1]] = OFF
            self.handle[self.ordered_pieces[1][1]] = OFF
            self.handle[self.ordered_pieces[6][1]] = color
            self.BlitColors(wait_time)

            for iteration in range(iterations):
                for piece in [4, 15, 13, 6, 10]:
                    for pixel in self.ordered_pieces[piece][0:3]:
                        if event is not None and event.is_set(): return
                        self.handle[pixel] = color
                self.BlitColors(wait_time)

                for piece in [4, 15, 13, 6, 10]:
                    for pixel in self.ordered_pieces[piece][0:3]:
                        if event is not None and event.is_set(): return
                        self.handle[pixel] = OFF
                self.handle[self.ordered_pieces[6][1]] = color
                self.BlitColors(wait_time)

            self.AllLeds(OFF, wait_time)

    def TA_Police(self, event, wait_time, color, iterations):
        self.Police(event, wait_time, color, iterations, True)

    def SA_Police(self, event, wait_time, color, iterations):
        self.Police(event, wait_time, color, iterations, False)

    def Police(self, event, wait_time, color, iterations, target=False):
        self.AllLeds(OFF)

        if target:
            add = 2
        else:
            add = 0

        for iteration in range(iterations*2):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                if (pixel <= int(self.strip_length + add / 2) and iteration % 2 == 0) \
                or (pixel > int(self.strip_length + add / 2) and iteration % 2 == 1):
                    self.handle[pixel] = [255, 0, 0]
                else:
                    self.handle[pixel] = [0, 0, 255]
            self.BlitColors(wait_time)
        self.AllLeds(OFF)

    def TA_Rainbow(self, event, wait_time, color, iterations):
        self.Rainbow(event, wait_time, color, iterations)

    def SA_Rainbow(self, event, wait_time, color, iterations):
        self.Rainbow(event, wait_time, color, iterations)

    def Rainbow(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        offset = random.randint(0, 255)

        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                self.handle[pixel] = self.WheelColor((pixel + offset + iteration) % 255)
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Rainbow2(self, event, wait_time, color, iterations, offset=None):
        self.Rainbow2(event, wait_time, color, iterations)

    def Rainbow2(self, event, wait_time, color, iterations, offset=None):
        self.AllLeds(OFF)

        if offset is None:
            offset = random.randint(0, 20)

        for iteration in range(iterations):
            if self.tire_only:
                step = 0
                for segment in self.tire:
                    for pixel in self.tire[segment]:
                        if event is not None and event.is_set(): return
                        rgb_color = colorsys.hsv_to_rgb((1 + step + offset + iteration) % 40 / 40, 1, 1)
                        self.handle[pixel] = self.colors.MultColor(rgb_color, 255)
                        step += 1
            else:
                for piece in range(len(self.pieces)):
                    for pixel in self.pieces[piece] + self.circles[0] + self.circles[1]:
                        if event is not None and event.is_set(): return
                        rgb_color = colorsys.hsv_to_rgb((1 + piece + offset + iteration) % 20 / 20, 1, 1)
                        self.handle[pixel] = self.colors.MultColor(rgb_color, 255)
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_RandomColor(self, event, wait_time, color, iterations):
        self.RandomColor(event, wait_time, color, iterations)

    def TA_RandomColor(self, event, wait_time, color, iterations):
        self.RandomColor(event, wait_time, color, iterations)

    def RandomColor(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                color = self.colors.GetColor()
                self.handle[pixel] = color
            self.BlitColors(wait_time)
        self.AllLeds(OFF)

    def TA_Ring(self, event, wait_time, color, iterations, ratio=None):
        self.Ring(event, wait_time, color, iterations, ratio)

    def Ring(self, event, wait_time, color, iterations, ratio=3):
        self.AllLeds(OFF)

        if ratio is None:
            ratio = 3

        temp = 0
        increment = 0
        for iteration in range(iterations):
            if self.tire_only:
                for segment in self.tire:
                    for pixel in self.tire[segment]:
                        if event is not None and event.is_set(): return
                        increment += 1
                        if increment % ratio == 0:
                            self.handle[pixel] = color
                        else:
                            self.handle[pixel] = OFF
            else:
                temp = (temp + 1) % 3
                for pixel in self.circles[1]:   # SB
                    if event is not None and event.is_set(): return
                    increment += 1
                    if increment % ratio == temp:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF
                for pixel in self.circles[self.triple_circle]:   # Triple
                    if event is not None and event.is_set(): return
                    increment += 1
                    if increment % ratio == temp:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF
                for pixel in self.circles[-1]:  # Double
                    if event is not None and event.is_set(): return
                    increment += 1
                    if increment % ratio == temp:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF

            self.BlitColors(wait_time)
            self.AllLeds(OFF)

    def SA_RunningLights(self, event, wait_time, color, iterations, length=None):
        self.RunningLights(event, wait_time, color, iterations, length)

    def RunningLights(self, event, wait_time, color, iterations, length=None):
        self.AllLeds(OFF)

        if length is None:
            length = int(self.strip_length / 5)

        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                multiplier = ((pixel + iteration) % length) / length
                self.handle[pixel] = self.colors.MultColor(color, multiplier)
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Daisy(self, event, wait_time, color, iterations, offset=0):
        self.Daisy(event, wait_time, color, iterations, offset) #by Manu script.

    def Daisy(self, event, wait_time, color, iterations, offset=0):

        for iteration in range(iterations):
            self.AllLeds(OFF)
            for piece in range(0, 20):
                for pixel in self.pieces[(piece + offset) % 20]:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            for piece in range(0, 20):
                for pixel in self.pieces[(piece + offset) % 20]:
                    self.handle[pixel] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Snake(self, event, wait_time, color, iterations):
        self.Snake(event, wait_time, color, iterations)

    def Snake(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        if not self.tire_only:
            positions = []
            pos_x = random.randint(0, 19)
            pos_y = 0
            pixel = self.pieces[pos_x][pos_y]
            self.handle[pixel] = color
            self.BlitColors(wait_time)

            positions.append(pixel)
            direction = 1  # Exterieur
            for iteration in range(iterations):
                while True:
                    if event is not None and event.is_set(): return
                    rand_direction = random.randint(0, 4)
                    if rand_direction == (direction + 2) % 4:    # Opposite -> refused
                         continue
                    elif rand_direction in (1, 3):
                        break               # Ok to go left or right
                    elif rand_direction == 0 and pos_y < self.nb_circles:
                        break               # Ok, go up
                    elif rand_direction == 2 and pos_y > 0:
                        break               # Ok, go down
                direction = rand_direction

                while True:
                    if event is not None and event.is_set(): return
                    length = random.randint(0, self.nb_circles)
                    if direction in (1, 3):
                        break
                    elif direction == 0:
                        length = min(length, self.nb_circles - pos_y)
                        break
                    elif direction == 2:
                        length = min(length, pos_y)
                        break

                for step in range(length):
                    if event is not None and event.is_set(): return
                    if direction == 0:
                        pos_y += 1
                    elif direction == 1:
                        pos_x -= 1
                    elif direction == 2:
                        pos_y -= 1
                    else:
                        pos_x += 1

                    pixel = self.pieces[(20 + pos_x) % 20][pos_y]
                    if pixel in positions: # Explode
                        self.Explode(event, (20 + pos_x) % 20, pos_y, 4, wait_time)
                        self.Explode(event, (20 + pos_x) % 20, pos_y, 8, wait_time)
                        self.Explode(event, (20 + pos_x) % 20, pos_y, 4, wait_time)
                        self.AllLeds(OFF)
                        return
                    else:
                        positions.append(pixel)

                    self.handle[pixel] = color
                    self.BlitColors(wait_time)

            self.AllLeds(OFF)
    def SA_Sparkle(self, event, wait_time, color, iterations):
        self.Sparkle(event, wait_time, color, iterations)

    def TA_Sparkle(self, event, wait_time, color, iterations):
        self.Sparkle(event, wait_time, color, iterations)

    def Sparkle(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        #
        # Flash random leds
        #
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                self.handle[random.randrange(self.strip_length)] = color
            self.BlitColors(wait_time)
            self.AllLeds(OFF)

    def TA_Strobe(self, event, wait_time, color, iterations):
        self.Strobe(event, wait_time, color, iterations)

    def SA_Strobe(self, event, wait_time, color, iterations):
        self.Strobe(event, wait_time, color, iterations)

    def Strobe(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                self.handle[pixel] = color
            self.BlitColors(wait_time)

            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                self.handle[pixel] = OFF
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SnowSparkle(self, event, wait_time, color, iterations):
        for iteration in range(iterations):
            self.AllLeds(color, wait_time)

        self.AllLeds(OFF)

    def TA_TheaterChase(self, event, wait_time, color, iterations):
        self.TheaterChase(event, wait_time, color, iterations)

    def SA_TheaterChase(self, event, wait_time, color, iterations):
        self.TheaterChase(event, wait_time, color, iterations)

    def TheaterChase(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        for iteration in range(iterations):
            for temp in range(3):

                for pixel in range(0, self.strip_length - 3, 3):
                    if event is not None and event.is_set(): return
                    self.handle[pixel + temp] = color
                self.BlitColors(wait_time)

                for pixel in range(0, self.strip_length - 3, 3):
                    if event is not None and event.is_set(): return
                    self.handle[pixel + temp] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_TheaterChaseRainbow(self, event, wait_time, color, iterations):
        self.TheaterChaseRainbow(event, wait_time, color, iterations)

    def TheaterChaseRainbow(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        for iteration in range(iterations):
            for temp in range(3):

                for pixel in range(0, self.strip_length - 3, 3):
                    if event is not None and event.is_set(): return
                    self.handle[pixel + temp] = self.WheelColor((pixel + iteration) % 255)
                    self.BlitColors(wait_time)

                for pixel in range(0, self.strip_length - 3, 3):
                    if event is not None and event.is_set(): return
                    self.handle[pixel + temp] = OFF
                    self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Twinkle(self, event, wait_time, color, iterations):
        self.Twinkle(event, wait_time, color, iterations)

    def SA_Twinkle(self, event, wait_time, color, iterations):
        self.Twinkle(event, wait_time, color, iterations)

    def Twinkle(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                if event is not None and event.is_set(): return
                self.handle[random.randrange(self.strip_length)] = color
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def Heart(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        for iteration in range(iterations):
            for circle in self.circles[:10]:
                for pixel in circle:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            time.sleep(2 * wait_time/100)

            for circle in self.circles[:10]:
                for pixel in circle:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            self.reset()

    def ForEach(self, event, wait_time, color, iterations):
        rnd = int(self.strip_length / 2)

        for iteration in range(iterations):
            for number in range(21):
                for pixel in range(self.strip_length):
                    if event is not None and event.is_set(): return
                    if int(pixel/7) == number:
                        rand = random.randint(0, 100)
                        if rand < 30:
                            color = [64, 0, 0]
                        elif rand < 70:
                            color = [0, 64, 0]
                        else:
                            color = [0, 0, 64]
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF
                self.BlitColors(wait_time)
        self.reset()

    def TA_DoubleBull(self, event, wait_time, color, iterations):
        self.DoubleBull(event, wait_time, color, iterations)

    def DoubleBull(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)

        for iteration in range(iterations):
            for circle in self.circles:
                for pixel in circle:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

                self.AllLeds(OFF)

    def TA_SimpleBull(self, event, wait_time, color, iterations):
        self.SimpleBull(event, wait_time, color, iterations)

    def SimpleBull(self, event, wait_time, color, iterations):

        for iteration in range(iterations):
            for circle in reversed(self.circles):
                for pixel in circle:
                    if event is not None and event.is_set(): return
                    self.handle[pixel] = color
                self.BlitColors(wait_time)
                self.AllLeds(OFF)

    def Simon(self, wait_time, color, iterations, segment, blink=True):
        pixels = []

        for goal in segment.split('|'):
            segment = goal.split('#')[0]
            if segment == 'TB':
                continue
            color = self.colors.GetColor(goal.split('#')[1])
            for pixel in self.segments.get(segment,[]) + self.tire.get(segment,[]):
                pixels.append((pixel,color))

        for iteration in range(iterations):
            for pixel,color in pixels:
                self.handle[pixel] = color
            self.BlitColors(wait_time)

            for pixel,color in pixels:
                self.handle[pixel] = OFF
            self.BlitColors(wait_time)

    def Segment(self, wait_time, color, iterations, segment, blink=True):
        if blink:
            color = self.segment_color[segment]

            for iteration in range(iterations):
                tire = 'E{}'.format(segment[1::])

                for pixel in self.segments.get(segment,[]) + self.tire.get('E{}'.format(segment[1::]),[]):
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

                for pixel in self.segments.get(segment,[]) + self.tire.get('E{}'.format(segment[1::]),[]):
                    self.handle[pixel] = OFF
                self.BlitColors(wait_time)

            self.AllLeds(OFF)

        else:
            if not self.background:
                self.AllLeds(OFF)
            # S18#blue|S19|blue|S18#red ...
            # Marque dans 18 et Bull
            # 11 a fermer

            for goal in segment.split('|'):
                segment = goal.split('#')[0]
                if segment == 'TB':
                    continue
                color = self.colors.GetColor(goal.split('#')[1])
                for pixel in self.segments.get(segment,[]) + self.tire.get(segment,[]):
                    self.handle[pixel] = color

            self.BlitColors(wait_time)

    def SA_USPolice(self, event, wait_time, color, iterations):
        self.US_Police(event, wait_time, color, iterations)

    def US_Police(self, event, wait_time, color, iterations):
        self.AllLeds(OFF)
        for iteration in range(iterations):
            for step in range(5):
                if step < 4:
                    for pixel in range(self.strip_length):
                        if event is not None and event.is_set(): return
                        if (pixel <= int(self.strip_length / 2) and step % 2 == 0) \
                        or (pixel > int(self.strip_length / 2) and step % 2 == 1):
                            self.handle[pixel] = [255, 0, 0]
                        else:
                            self.handle[pixel] = [0, 0, 255]
                    self.BlitColors(wait_time)
                else:
                    for blink in range(5):
                        self.AllLeds([255, 255, 255], 30)
                        self.AllLeds(OFF, 30)

        self.AllLeds(OFF, 10)

    def SA_Wait(self, wait_time):
        self.Wait(wait_time)

    def TA_Wait(self, wait_time):
        self.Wait(wait_time)

    def Wait(self, wait_time):
        time.sleep(wait_time / 1000)

    def TA_Perso(self, custom=None):

        try:
            custom_animation = self.customs[custom]

            for step in custom_animation:
                if step.startswith('wait'):
                    wait_time = int(step.split(':')[1])
                    time.sleep(wait_time / 1000)
                else:
                    # pixel#color|pixel2#color2
                    for data in step.split('|'):
                        pixel = int(data.split('#')[0])
                        color = self.colors.GetColor(data.split('#')[1])

                        self.handle[pixel] = color
                    self.BlitColors()

        except Exception as e:
            self.Logs("{}".format(e), facility='ERROR')
