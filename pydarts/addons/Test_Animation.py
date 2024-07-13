#!/usr/bin/env python3

# def TA animation: Animation available for Target Leds
# def SA animation: Animation available for Strip Leds

import time
import colorsys
import random
import ast
import numpy as np

#import neopixel
from rpi_ws281x import PixelStrip, Color

# Parametrage Leds
import Colors as CL

# Pour des bandes NeoPixel RGBW, changez ORDER de RGBW à recordBW.
OFF = [np.uint8(0), np.uint8(0), np.uint8(0)]
MULT_COLOR = {'S': [0, 255, 0], 'D': [0, 0, 255], 'T': [255, 0, 0], 'E': [129, 12, 128]}
TARGET_ORDER = [1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]

class CStrip(object):

    ######################
    ### Init functions ###
    ######################

    def __init__(self, pin, strip_length, brightness, dma_channel, device, configuration=None, S20='blue', leds_type=None):
        freq = 800000  # LED signal frequency in hertz (usually 800khz)
        if pin in (13, 19, 41, 45, 53):
            # set to '1' for GPIOs 13, 19, 41, 45 or 53
            channel = 1
        else:
            channel = 0

        self.strip = PixelStrip(strip_length, pin, freq, dma_channel, False, int(brightness*255), channel)

        self.strip.begin()
        self.strip_length = strip_length
        self.handle = [[np.uint8(0), np.uint8(0), np.uint8(0)] for _a in range(self.strip_length)]

        if device == 'TARGET' and configuration is not None:
            if leds_type == 'raspyleds':
                self.jimmy = True
            else:
                self.jimmy = False
            print("[DEBUG] Raspyleds:",self.jimmy)
            self.InitTarget(configuration, S20)

        self.colors = CL.CColors()

    def InitTarget(self, configuration, S20):

        configuration = ast.literal_eval(configuration)

        self.segments = {}
        self.tire = {}
        self.pieces = [[] for _n in TARGET_ORDER]
        self.ordered_pieces = [[] for _n in range(0, len(TARGET_ORDER)+1)]
        self.target_leds_count = 0

        # Store segments leds
        for segment in ['{}{}'.format(_s, _n) for _s in ['S', 'D', 'T'] for _n in range(1, 21)]+['SB', 'DB']:
            try:
                self.segments[segment] = [int(_v) for _v in configuration[segment].split(',') if _v != '']
                self.target_leds_count += len(self.segments[segment])
            except:
                print("[DEBUG] No leds initialized for {}".format(segment))
                self.segments[segment] = []

        if self.target_leds_count == 0:
            self.tire_only = True
        else:
            self.tire_only = False

        print("[DEBUG] Tire only {}".format(self.tire_only))

        # Store tire's leds
        for segment in ['E{}'.format(_n) for _n in range(1, 21)]:
            try:
                self.tire[segment] = [int(_v) for _v in configuration[segment].split(',') if _v != '']
                self.target_leds_count += len(self.tire[segment])
            except:
                print("[DEBUG] No leds initialized for {}".format(segment))
                self.segments[segment] = []

        if self.target_leds_count == 0:
            print("[DEBUG] No configuration found")
            return False
        else:
            print("[DEBUG] Found {} leds in configuration".format(self.target_leds_count))

        # Store target pieces (Target order)
        piece = 0
        for number in TARGET_ORDER:
            for multiplier in ['S', 'D', 'T']:
                try:
                    self.pieces[piece].extend([int(_v) for _v in configuration['{}{}'.format(multiplier, number)].split(',')])
                except:
                    print("[DEBUG] No leds initialized for {}{}".format(multiplier, number))
            piece += 1

        for number in TARGET_ORDER:
            for multiplier in ['S', 'D', 'T']:
                try:
                    self.ordered_pieces[number].extend([int(_p) for _p in configuration['{}{}'.format(multiplier, number)].split(',')])
                except:
                    print("[DEBUG] No leds initialized for {}{}".format(multiplier, number))

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
                    print("[DEBUG] No leds initialized for T{}".format(segment))

            self.triple_circle = 0
        else:
            nb_circles = 0
            for number in range(1, 21):
                simple = "S{}".format(number)
                if len(configuration.get(simple).split(',')) > nb_circles:
                    try:
                        nb_circles = len(configuration.get(simple).split(','))
                    except:
                        print("[DEBUG] No leds initialized for {}".format(simple))

            if nb_circles > 0:
                self.triple_circle = int((nb_circles + 1) / 2) + 1
            else:
                self.triple_circle = 0

            print("[DEBUG] Found {} leds per Simple segment".format(nb_circles))
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

        for circle in range(len(self.circles)):
            print("[DEBUG] circles[{}]={}".format(circle, self.circles[circle]))

        # Initialize list of leds in target (versus sides leds)
        self.TargetLeds = []
        for pixels in configuration:
            leds = configuration.get(pixels, '')
            for pixel in leds.split(','):
                self.TargetLeds.append(pixel)

        # Init segments color => When dart stroke segment, it blink with the appropriate color
        if S20 == 'blue':
            color1 = [0, 0, 255]        # blue
            color2 = [255, 0, 0]        # red
            color3 = [255, 255, 255]    # white
        else:
            color1 = [255, 255, 255]    # white
            color2 = [0, 0, 255]        # blue
            color3 = [255, 0, 0]        # red

        self.segment_color = {}
        list1 = [1, 4, 6, 15, 17, 19, 16, 11, 9, 5]
        list2 = [18, 13, 10, 2, 3, 7, 8, 14, 12, 20]

        self.segment_color['SB'] = [0, 0, 255]
        self.segment_color['DB'] = [255, 0, 0]

        for number in list1:
            self.segment_color['T{}'.format(number)] = color2
            self.segment_color['D{}'.format(number)] = color2
            self.segment_color['S{}'.format(number)] = color3
        for number in list2:
            self.segment_color['T{}'.format(number)] = color3
            self.segment_color['D{}'.format(number)] = color3
            self.segment_color['S{}'.format(number)] = color1

    ####################################
    ### Backup / Restore strip state ###
    ####################################


    def Backup(self):
        self.Backup = []
        for pixel in range(self.strip_length):
            self.Backup.append(self.strip.getPixelColor)

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
            self.handle[pixel] = OFF

    def SetBrightness(self, Brightness):
        self.strip.setBrightness(int(float(Brightness)*255))
        print("[DEBUG] Brightness is now {}".format(int(float(Brightness)*255)))

    def AllLeds(self, color, wait_time=0):
        for pixel in range(self.strip_length):
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

    def TestSegment(self, segments, wait_time=1500):
        simples = []
        doubles = []

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

    def WheelColor(self, wheel_position):
        if  wheel_position < 85:
            return [wheel_position*3, 255 -  wheel_position * 3, 0]

        elif  wheel_position < 170:
            wheel_position -= 85
            return [255 -  wheel_position*3, 0, wheel_position * 3]

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

    def Explode(self, pos_x, pos_y, size, wait_time):
        for step in range(4):
            around = self.GetAround(size, pos_x, pos_y)
            for pixel in around:
                self.handle[pixel] = [255, 0, 0]
            self.BlitColors(wait_time/10)

            for pixel in around:
                self.handle[pixel] = [255, 255, 0]
            self.BlitColors(wait_time/10)

    ##################
    ### Animations ###
    ##################

    def SA_Light(self, color):
        self.Light(color)

    def TA_Light(self, color):
        self.Light(color)

    def Light(self, color):
        self.AllLeds(color)

    def TA_Hue(self, wait_time, color, iterations, offset=None):
        self.Hue(wait_time, color, iterations, offset)

    def Hue(self, wait_time, color, iterations, offset=None):

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
                    step += 1
                    if not ((self.jimmy and step == 7) or step == len(self.pieces[piece]) - 1):
                        rgb_color = colorsys.hsv_to_rgb((iteration + piece + offset) % 20 / 20, (step - double) / nb, 1)
                        color = self.colors.MultColor(rgb_color, 255)
                    else:
                        double += 1
                    self.handle[pixel] = color

            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Rainbow2(self, wait_time, color, iterations, offset=None):
        self.Rainbow2(wait_time, color, iterations)

    def Rainbow2(self, wait_time, color, iterations, offset=None):

        if offset is None:
            offset = random.randint(0, 20)

        for iteration in range(iterations):
            if self.tire_only:
                step = 0
                for segment in self.tire:
                    for pixel in self.tire[segment]:
                        rgb_color = colorsys.hsv_to_rgb((1 + step + offset + iteration) % 40 / 40, 1, 1)
                        self.handle[pixel] = self.colors.MultColor(rgb_color, 255)
                        step += 1
            else:
                for piece in range(len(self.pieces)):
                    for pixel in self.pieces[piece] + self.circles[0] + self.circles[1]:
                        rgb_color = colorsys.hsv_to_rgb((1 + piece + offset + iteration) % 20 / 20, 1, 1)
                        self.handle[pixel] = self.colors.MultColor(rgb_color, 255)
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Alain(self, wait_time, color, iterations, offset=None):
        self.Alain(wait_time, color, iterations, offset, mode=1)

    def TA_Alain2(self, wait_time, color, iterations, offset=None):
        self.Alain(wait_time, color, iterations, offset, mode=2)

    def Alain(self, wait_time, color, iterations, offset=None, mode=1):

        if offset is None:
            offset = random.randint(0, 20)

        for iteration in range(iterations):
            for piece in range(len(self.pieces)):
                for pixel in self.pieces[piece]:
                    if mode == 1:
                        self.handle[pixel] = self.colors.ShakeColor(color, iteration + piece + offset)
                    else:
                        self.handle[pixel] = self.colors.ShakeColor(color, int(((iteration + piece + offset) % 20) / 7))

            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Pacman(self, wait_time, color, iterations):
        self.Pacman(wait_time, color, iterations)

    def Pacman(self, wait_time, color, iterations, offset=None):

        if not self.tire_only:
            for piece in [2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20, 1, 18]:
                for pixel in self.ordered_pieces[piece][0:3]:
                    self.handle[pixel] = color

            for pixel in self.circles[0] + self.circles[1]:
                self.handle[pixel] = color

            self.handle[self.ordered_pieces[18][1]] = OFF
            self.handle[self.ordered_pieces[1][1]] = OFF
            self.handle[self.ordered_pieces[6][1]] = color
            self.BlitColors(wait_time)

            for iteration in range(iterations):
                for piece in [4, 15, 13, 6, 10]:
                    for pixel in self.ordered_pieces[piece][0:3]:
                        self.handle[pixel] = color
                self.BlitColors(wait_time)

                for piece in [4, 15, 13, 6, 10]:
                    for pixel in self.ordered_pieces[piece][0:3]:
                        self.handle[pixel] = OFF
                self.handle[self.ordered_pieces[6][1]] = color
                self.BlitColors(wait_time)

            self.AllLeds(OFF, wait_time)

    def TA_Mireille(self, wait_time, color, iterations, offset=None):
        self.Mireille(wait_time, color, iterations)

    def Mireille(self, wait_time, color, iterations, offset=None):
        if offset is None:
            offset = random.randint(0, 20)

        for iteration in range(iterations):
            for piece in range(len(self.pieces)):
                for pixel in self.pieces[piece]:
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            self.AllLeds(OFF)

    def TA_Police(self, wait_time, color, iterations):
        self.Police(wait_time, color, iterations, True)

    def SA_Police(self, wait_time, color, iterations):
        self.Police(wait_time, color, iterations, False)

    def Police(self, wait_time, color, iterations, target=False):

        if target:
            add = 2
        else:
            add = 0

        for iteration in range(iterations*2):
            for pixel in range(self.strip_length):
                if (pixel <= int(self.strip_length + add / 2) and iteration % 2 == 0) \
                or (pixel > int(self.strip_length + add / 2) and iteration % 2 == 1):
                    self.handle[pixel] = [255, 0, 0]
                else:
                    self.handle[pixel] = [0, 0, 255]
            self.BlitColors(wait_time)
        self.AllLeds(OFF)

    def SA_USPolice(self, wait_time, color, iterations):
        self.US_Police(wait_time, color, iterations)

    def US_Police(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for step in range(5):
                if step < 4:
                    for pixel in range(self.strip_length):
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

    def TA_FadeRGB(self, wait_time, color, iterations):
        self.FadeRGB(wait_time, color, iterations)

    def SA_FadeRGB(self, wait_time, color, iterations):
        self.FadeRGB(wait_time, color, iterations)

    def FadeRGB(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for step in range(3):
                for component in range(255, 3):
                    if step == 0:
                        self.AllLeds([component, 0, 0], wait_time)
                    elif step == 1:
                        self.AllLeds([0, component, 0], wait_time)
                    else:
                        self.AllLeds([0, 0, component], wait_time)
                for component in range(255, 0, -3):
                    if step == 0:
                        self.AllLeds([component, 0, 0], wait_time)
                    elif step == 1:
                        self.AllLeds([0, component, 0], wait_time)
                    else:
                        self.AllLeds([0, 0, component], wait_time)
        self.AllLeds(OFF)

    def SA_FadeInOut(self, wait_time, color, iterations):
        self.FadeInOut(wait_time, color, iterations)

    def TA_FadeInOut(self, wait_time, color, iterations):
        self.FadeInOut(wait_time, color, iterations)

    def FadeInOut(self, wait_time, color, iterations):
        for iteration in range(iterations):
            #Fade In.
            for step in range(0, 256, 2):
                red = int(color[0] * step / 256)
                green = int(color[1] * step / 256)
                blue = int(color[2] * step / 256)
                self.AllLeds([red, green, blue], wait_time)
            for step in range(256, 0, -2):
                red = int(color[0] * step / 256)
                green = int(color[1] * step / 256)
                blue = int(color[2] * step / 256)
                self.AllLeds([red, green, blue], wait_time)

        self.AllLeds(OFF)

    def SA_Cylon(self, wait_time, color, iterations, size=None):
        self.Cylon(wait_time, color, iterations, size)

    def Cylon(self, wait_time, color, iterations, size, side=0):
        if size is None:
            size = int(self.strip_length / 10)

        for iteration in range(iterations):
            for step in range(self.strip_length + size):
                for pixel in range(self.strip_length):
                    if step - size <= pixel <= step + size:
                        self.handle[pixel] = color
                    elif side > 0 and pixel in (step - size - 1, step + size + 1):
                        self.handle[pixel] = self.colors.MultColor(color, 1 / size)
                    else:
                        self.handle[pixel] = OFF

                self.BlitColors(wait_time)

            for step in range(self.strip_length + size, 0, -1):
                for pixel in range(self.strip_length):
                    opposite_pixel = self.strip_length - pixel - 1
                    if step - size <= opposite_pixel <= step + size:
                        self.handle[opposite_pixel] = color
                    elif side > 0 and opposite_pixel in (step - size - 1, step + size + 1):
                        self.handle[opposite_pixel] = self.colors.MultColor(color, 1 / size)
                    else:
                        self.handle[opposite_pixel] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_CylonDouble(self, wait_time, color, iterations, size=None):
        self.CylonDouble(wait_time, color, iterations, size)

    def CylonDouble(self, wait_time, color, iterations, size, side=0):
        if size is None:
            size = int(self.strip_length / 10)

        for iteration in range(2 * iterations):
            for step in range(int((self.strip_length + size) / 2)):
                for pixel in range(int((self.strip_length + 1) /2)):
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

    def SA_ColorWipe(self, wait_time, color, iterations):
        self.ColorWipe(wait_time, color, iterations, 'up')

    def SA_ColorWipeReverse(self, wait_time, color, iterations):
        self.ColorWipe(wait_time, color, iterations, 'down')

    def ColorWipe(self, wait_time, color, iterations, direction):
        for iteration in range(iterations):
            if direction == 'up':
                for pixel in range(self.strip_length):
                    self.handle[pixel] = color
                    self.BlitColors(wait_time)
            else:
                for pixel in range(self.strip_length - 1, 0, -1):
                    self.handle[pixel] = color
                    self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_Fireworks(self, wait_time, color, iterations, meteor_size):
        self.Fireworks(wait_time, color, iterations, meteor_size, 90, True)

    def Fireworks(self, wait_time, color, iterations, meteor_size, meteor_trail_decay, meteor_random_decay):
        for iteration in range(iterations):
            for step in range(0, self.strip_length + meteor_size):
                for pixel in range(0, self.strip_length):
                    if not meteor_random_decay or random.randint(0, 10) > 5:
                        self.handle[pixel] = self.FadeToBlack(pixel, meteor_trail_decay)
                # Draw meteor
                for pixel in range(0, meteor_size):
                    if step - pixel < self.strip_length and step - pixel >= 0:
                        self.handle[step - pixel] = color
                self.BlitColors(wait_time)

            self.AllLeds(OFF)

    def SA_NewKitt(self, wait_time, color, iterations):
        self.NewKitt(wait_time, color, iterations)

    def NewKitt(self, wait_time, color, iterations):
        length = int(self.strip_length/15)

        for iteration in range(0, iterations):
            self.Cylon(wait_time, color, 1, length, side=length)
            self.CylonDouble(wait_time, color, 1, length, side=length)

    def SA_RunningLights(self, wait_time, color, iterations, length=None):
        self.RunningLights(wait_time, color, iterations, length)

    def RunningLights(self, wait_time, color, iterations, length=None):

        if length is None:
            length = int(self.strip_length / 5)

        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                multiplier = ((pixel + iteration) % length) / length
                self.handle[pixel] = self.colors.MultColor(color, multiplier)
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_Sparkle(self, wait_time, color, iterations):
        self.Sparkle(wait_time, color, iterations)

    def TA_Sparkle(self, wait_time, color, iterations):
        self.Sparkle(wait_time, color, iterations)

    def Sparkle(self, wait_time, color, iterations):
        #
        # Flash random leds
        #
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                self.handle[random.randrange(self.strip_length)] = color
            self.BlitColors(wait_time)
            self.AllLeds(OFF)

    def TA_Strobe(self, wait_time, color, iterations):
        self.Strobe(wait_time, color, iterations)

    def SA_Strobe(self, wait_time, color, iterations):
        self.Strobe(wait_time, color, iterations)

    def Strobe(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                self.handle[pixel] = color
            self.BlitColors(wait_time)

            for pixel in range(self.strip_length):
                self.handle[pixel] = OFF
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SnowSparkle(self, wait_time, color, iterations):
        for iteration in range(iterations):
            self.AllLeds(color, wait_time)

        self.AllLeds(OFF)

    def TA_TheaterChase(self, wait_time, color, iterations):
        self.TheaterChase(wait_time, color, iterations)

    def SA_TheaterChase(self, wait_time, color, iterations):
        self.TheaterChase(wait_time, color, iterations)

    def TheaterChase(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for temp in range(3):

                for pixel in range(0, self.strip_length - 3, 3):
                    self.handle[pixel + temp] = color
                self.BlitColors(wait_time)

                for pixel in range(0, self.strip_length - 3, 3):
                    self.handle[pixel + temp] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_TheaterChaseRainbow(self, wait_time, color, iterations):
        self.TheaterChaseRainbow(wait_time, color, iterations)

    def TheaterChaseRainbow(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for temp in range(3):

                for pixel in range(0, self.strip_length - 3, 3):
                    self.handle[pixel + temp] = self.WheelColor((pixel + iteration) % 255)
                    self.BlitColors(wait_time)

                for pixel in range(0, self.strip_length - 3, 3):
                    self.handle[pixel + temp] = OFF
                    self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_FillDown(self, wait_time, color, iterations):
        self.FillDown(wait_time, color, iterations)

    def FillDown(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for step in range(self.strip_length):
                for pixel in range(self.strip_length - step):
                    if pixel - 1 > 0:
                        self.handle[pixel - 1] = OFF
                    self.handle[pixel] = color
                    self.BlitColors(wait_time)

            for step in range(self.strip_length-1, 0, -1):
                for pixel in range(step, self.strip_length):
                    self.handle[pixel] = OFF
                    if pixel < self.strip_length - 1:
                        self.handle[pixel + 1] = color
                    self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def SA_RandomColor(self, wait_time, color, iterations):
        self.RandomColor(wait_time, color, iterations)

    def TA_RandomColor(self, wait_time, color, iterations):
        self.RandomColor(wait_time, color, iterations)

    def RandomColor(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                color = self.colors.GetColor()
                self.handle[pixel] = color
            self.BlitColors(wait_time)
        self.AllLeds(OFF)

    def TA_Rainbow(self, wait_time, color, iterations):
        self.Rainbow(wait_time, color, iterations)

    def SA_Rainbow(self, wait_time, color, iterations):
        self.Rainbow(wait_time, color, iterations)

    def Rainbow(self, wait_time, color, iterations):
        offset = random.randint(0, 255)

        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                self.handle[pixel] = self.WheelColor((pixel + offset + iteration) % 255)
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Ring(self, wait_time, color, iterations, ratio=None):
        self.Ring(wait_time, color, iterations, ratio)

    def Ring(self, wait_time, color, iterations, ratio=3):

        if ratio is None:
            ratio = 3

        temp = 0
        increment = 0
        for iteration in range(iterations):
            if self.tire_only:
                for segment in self.tire:
                    for pixel in self.tire[segment]:
                        increment += 1
                        if increment % ratio == 0:
                            self.handle[pixel] = color
                        else:
                            self.handle[pixel] = OFF
            else:
                temp = (temp + 1) % 3
                for pixel in self.circles[1]:   # SB
                    increment += 1
                    if increment % ratio == temp:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF
                for pixel in self.circles[self.triple_circle]:   # Triple
                    increment += 1
                    if increment % ratio == temp:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF
                for pixel in self.circles[-1]:  # Double
                    increment += 1
                    if increment % ratio == temp:
                        self.handle[pixel] = color
                    else:
                        self.handle[pixel] = OFF

            self.BlitColors(wait_time)
            self.AllLeds(OFF)

    def TA_Twinkle(self, wait_time, color, iterations):
        self.Twinkle(wait_time, color, iterations)

    def SA_Twinkle(self, wait_time, color, iterations):
        self.Twinkle(wait_time, color, iterations)

    def Twinkle(self, wait_time, color, iterations):
        for iteration in range(iterations):
            for pixel in range(self.strip_length):
                self.handle[random.randrange(self.strip_length)] = color
            self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Alfred(self, wait_time, color, iterations, offset=0):
        self.Alfred(wait_time, color, iterations, offset)

    def Alfred(self, wait_time, color, iterations, offset):
        start = offset

        for iteration in range(iterations):
            for count in range(3):
                color = [color[1], color[2], color[0]]

                for part in range(7):
                    for pixel in self.pieces[start % 20]:
                        self.handle[pixel] = color
                    start += 1
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Simone(self, wait_time, color, iterations, offset=0):
        self.Simone(wait_time, color, iterations, offset)

    def Simone(self, wait_time, color, iterations, offset=0):
        for iteration in range(iterations):
            for piece in range(0, 20):
                for pixel in self.pieces[(piece + offset) % 20]:
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

            for piece in range(0, 20):
                for pxel in self.pieces[(piece + offset) % 20]:
                    self.handle[pixel] = OFF
                self.BlitColors(wait_time)

        self.AllLeds(OFF)

    def TA_Snake(self, wait_time, color, iterations):
        self.Snake(wait_time, color, iterations)

    def Snake(self, wait_time, color, iterations):
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
                        self.Explode((20 + pos_x) % 20, pos_y, 4, wait_time)
                        self.Explode((20 + pos_x) % 20, pos_y, 8, wait_time)
                        self.Explode((20 + pos_x) % 20, pos_y, 4, wait_time)
                        self.AllLeds(OFF)
                        return
                    else:
                        positions.append(pixel)

                    self.handle[pixel] = color
                    self.BlitColors(wait_time)

            self.AllLeds(OFF)

        def Heart(self, wait_time, color, iterations):
            for iteration in range(iterations):
                for circle in self.circles[:10]:
                    for pixel in circle:
                        self.handle[pixel] = color
                    self.BlitColors(wait_time)

                time.sleep(2 * wait_time/100)

                for circle in self.circles[:10]:
                    for pixel in circle:
                        self.handle[pixel] = color
                    self.BlitColors(wait_time)

                self.reset()

        def ForEach(self, wait_time, color, iterations):
            rnd = int(self.strip_length / 2)

            for iteration in range(iterations):
                for number in range(21):
                    for pixel in range(self.strip_length):
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

    def TA_DoubleBull(self, wait_time, color, iterations):
        self.DoubleBull(wait_time, color, iterations)

    def DoubleBull(self, wait_time, color, iterations):

        for iteration in range(iterations):
            for circle in self.circles:
                for pixel in circle:
                    self.handle[pixel] = color
                self.BlitColors(wait_time)

                self.AllLeds(OFF)

    def TA_SimpleBull(self, wait_time, color, iterations):
        self.SimpleBull(wait_time, color, iterations)

    def SimpleBull(self, wait_time, color, iterations):

        for iteration in range(iterations):
            for circle in reversed(self.circles):
                for pixel in circle:
                    self.handle[pixel] = color
                self.BlitColors(wait_time)
                self.AllLeds(OFF)

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
            # S18#blue|S19|blue|S18#red ...
            # Marque dans 18 et Bull
            # 11 a fermer

            self.AllLeds(OFF)

            for goal in segment.split('|'):
                segment = goal.split('#')[0]
                if segment == 'TB':
                    continue
                color = self.colors.GetColor(goal.split('#')[1])
                for pixel in self.segments.get(segment,[]) + self.tire.get(segment,[]):
                    self.handle[pixel] = color

            self.BlitColors(wait_time)

    def Background(self):
        for segment in ['{}{}'.format(m,n) for m in ['S','D','T'] for n in range(1,21)]+['SB','DB']:
            color = self.colors.MultColor(self.segment_color[segment],1/50)
            for pixel in self.segments.get(segment,[]):
                self.handle[pixel] = color

        self.BlitColors()

    def test(self,wait_time, color, iterations, longueur):

        # J'éteins tout
        self.AllLeds(OFF)

        for iteration in range(iterations):                         # Jouer x fois l'anomations
            for step in range(self.strip_length - longueur) :       # Pour chaque "image" de mon animation
                for pixel in range(self.strip_length):              # Iteration sur chaque pixel, dois-je l'allumer ?
                    if step - longueur <= pixel and pixel <= step + longueur:  # Condition, à adapter à ton animation
                        # self.handle est un tableau, en mémoire, qui stocke l'état des pixels
                        # Le contenu du tableau est "envoyé" au bandeau led recordâce à la fonction BlitColors
                        self.handle[pixel] = color                  # J'allume le pixel dans la couleur demandée
                    else:
                        self.handle[pixel] = OFF                    # Sinon, je l'éteins

                self.BlitColors(wait_time)                          # J'envoie les données sur le bandeau led et j'attends <wait_time> ms
                                                                    # Cette fonction est à appeler pour chaque "image" de ton animation.
                                                                    # Surtout pas pour chaque pixel, sinon, ça va ramer

        # J'éteins tout
        self.AllLeds(OFF)

    def test2(self,wait_time, color, iterations, longueur):

        # J'éteins tout
        self.AllLeds(OFF)

        for iteration in range(iterations):                         # Jouer x fois l'anomations
            for step in range(self.strip_length - longueur) :       # Pour chaque "image" de mon animation
                for pixel in range(self.strip_length):              # Iteration sur chaque pixel, dois-je l'allumer ?
                    # J'allume un pixel sur 20, qui vont se déplacer, d'un pixel à chaque image
                    if ( pixel + step ) % 20 == 1:
                        self.handle[pixel] = color                  # J'allume le pixel dans la couleur demandée
                    else:
                        self.handle[pixel] = OFF                    # Sinon, je l'éteins

                self.BlitColors(wait_time)                          # J'envoie les données sur le bandeau led et j'attends <wait_time> ms
                                                                    # Cette fonction est à appeler pour chaque "image" de ton animation.
                                                                    # Surtout pas pour chaque pixel, sinon, ça va ramer

        # J'éteins tout
        self.AllLeds(OFF)

PIN=12
NB_PIXELS=72
BRIGHTNESS=0.7
DMA=10

Objet = CStrip(PIN,NB_PIXELS,BRIGHTNESS,DMA,'STRIP')                # Instentiation d'un bandeau led
Colors = CL.CColors()                                               # Instentiation de la classe "Color"

# Définition des paramètres de l'animation
delai = 1
C = Colors.GetColor('red')
iterations = 3
longueur = 5

Objet.test(delai,C,iterations,longueur)                             # Appel de l'animations de test
delai = 5
C = Colors.GetColor('blue')
Objet.test2(delai,C,iterations,longueur)                             # Appel de l'animations de test



