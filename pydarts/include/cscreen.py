# -*- coding: utf-8 -*-
import os
import os.path

import threading
from datetime import datetime

import sys
# Randomize player names / and create a random game name / ...
import random
# Run external commands (shell)
import subprocess
# Make hard calculation
import math
# For file list
import glob
# String to dict
import ast
# Reg exp
import re
# For personnalisation
import importlib
# For debug
import time
# For IP addresses
from netifaces import interfaces
from netifaces import ifaddresses
from netifaces import AF_INET
from PIL import Image
from threading import Thread
from functools import lru_cache

import pygame
from pygame.locals import *
from include.ColorSets import *

ENTER_KEYS = ['enter', 'BTN_GAMEBUTTON', 'BTN_VALIDATE', 'SB', 'DB', 'BTN_NEXTPLAYER']
ESCAPE_KEYS = ['escape', 'BTN_BACK', 'BTN_CANCEL']
MINUS_KEYS = ['-', 'BTN_MINUS', 'minus', 'S13']
PLUS_KEYS = ['+', 'BTN_PLUS', 'add', 'plus', 'S10']
UP_KEYS = ['up', 'BTN_UP', 'S20']
DOWN_KEYS = ['down', 'BTN_DOWN', 'S3']
LEFT_KEYS = ['left', 'BTN_LEFT', 'S11']
RIGHT_KEYS = ['right', 'BTN_RIGHT', 'S6']
DIRECTION_KEYS = UP_KEYS + DOWN_KEYS + LEFT_KEYS + RIGHT_KEYS
BACK_KEYS = ['backspace', 'BTN_BACK', 'S16']
SAVE_KEYS = ['save', 'S2']    #BTN_NEXTPLAYER
EXTRA_KEYS = ['BTN_CPTPLAYER', '/', 'S15']
CONTINUE_KEYS = ['continue', 'BTN_NEXTPLAYER', 'S2']
BACKUP_KEYS = ['backup', 'BTN_GAME_BUTTON', 'S2']
CLEAN_KEYS = ['clean', 'BTN_GAMEBUTTON']
TAB_KEYS = ['tab', 'shake']
VOLUME_UP_KEYS = ['+', 'BTN_PLUS', 'BTN_VOLUME_UP', 'VOLUME-UP', 'S14']
VOLUME_DOWN_KEYS = ['-', 'BTN_MINUS', 'BTN_VOLUME_DOWN', 'VOLUME-DOWN', 'S8']
VOLUME_MUTE = ['BTN_VOLUME_MUTE', 'VOLUME-MUTE', 'S7']

BTN_CHECK = 1
BTN_CHOICE = 2
BTN_VALUE = 3
BTN_LOGO = 4
BTN_DROPDOWN = 5

def debug(func):
    def wrapper(*args, **kargs):
        print(f"[DEBUG] {datetime.now()} - Calling {func.__name__} with args:{args}, kargs={kargs}", flush=True)
        start = time.perf_counter()
        result = func(*args, **kargs)
        duration = time.perf_counter() - start
        print(f"[DEBUG] {datetime.now()} - Result of {func.__name__} is {result}")
        print(f"[DEBUG] {datetime.now()} - {func.__name__} took {int(duration * 1000)} ms")
        return result
    return wrapper
     
class Screen(pygame.Surface):
    '''
    Class for display
    '''
    def __init__(self, config, logs, File, lang, rpi, dmd, video_player, Font=None, random_speed=False, wait_event_time=None, t_event=None):
        # Init
        self.gamepath = os.getcwd()
        self.backupscript = f"{self.gamepath}/scripts/Backup.sh"
        self.background = None
        self.file_class = File

        self.ips = self.get_ips()

        #
        self.netgamename = None
        self.netgamecreator = None
        # Store config in local value
        self.logs = logs
        self.lang = lang    # Import language values
        self.line_height = None    # Depends of player number - calculated later
        self.config = config
        self.colorsets = {}
        # Image cache (speed up pygame image load process
        self.imagecache = {}
        self.imagescalecache = {}
        # For drawing a dart board
        self.targets = {20: 1, 1: 2, 18: 3, 4: 4, 13: 5, 6: 6, 10: 7, 15: 8, 2: 9, 17: 10, 3: 11, 19: 12, 7: 13,
                         16: 14, 8: 15, 11: 16, 14: 17, 9: 18, 12: 19, 5: 20}
        # Set default Sound Volume (percent)
        try:
            self.sound_volume = int(self.config.get_value('SectionGlobals', 'soundvolume'))
        except:
            self.sound_volume = 50
        self.random_speed = random_speed
        self.old_volume = self.sound_volume
        self.sound_multiplier = 100

        pygame.init()
        # Used resolution
        self.res = {}
        # Minimal resolution
        self.resmin = {}

        # Create resolution prameters
        self.fullscreen = self.config.get_value('SectionGlobals', 'fullscreen')

        # create_screen Init or toggle screen
        self.create_screen()
        # Choose color set
        self.init_colorset()
        # Define constants - first without the required nb of players
        self.define_constants(Font = Font)
        # Define a boolean value to know if teaming is active (default is inactive)
        self.teaming = False
        self.selectedgame = ''
        #
        self.session_players = {}

        # Init Clickable zone
        self.click_zones = {}

        # Init menu item types
        self.selected = None
        # Margin
        self.margin = int(self.res['y'] / 200)
        self.rpi = rpi
        self.dmd = dmd
        self.video_player = video_player
        self.game_options = []

        self.game_background = None

        self.wait_event_time = wait_event_time
        self.t_event = t_event
        self.thread = None
        self.rects = []
        self.blinktime = int(self.config.get_value('SectionGlobals', 'blinktime'))
        self.selected_menu = {}

    def set_soundmultiplier(self, multiplier):
        self.sound_multiplier = int(multiplier) / 100
        self.logs.log("DEBUG", f"sound_multiplier is set to {self.sound_multiplier}")

    def set_blinktime(self, value):
        self.blinktime = int(value)

    def reset_mode(self):
        self.blinktime = int(self.config.get_value('SectionGlobals', 'blinktime'))
        self.video_player.level = int(self.config.get_value('SectionGlobals', 'videos'))

    def blit(self, source, destination, area=None):
        if str(pygame.version.ver) == '2.0.0':
            if area is not None:
                self.screen.blit(source, destination, area=area, special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                self.screen.blit(source, destination, special_flags=pygame.BLEND_ALPHA_SDL2)
        elif area is not None:
            self.screen.blit(source, destination, area=area)
        else:
            self.screen.blit(source, destination)

    def blit_screen(self, screen, source, destination, area=None):
        if area is None:
            if str(pygame.version.ver) == '2.0.0':
                screen.blit(source, destination, special_flags=pygame.BLEND_ALPHA_SDL2)
            else:
                screen.blit(source, destination)
        elif str(pygame.version.ver) == '2.0.0':
            screen.blit(source, destination, area=area, special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            screen.blit(source, destination,special_flags=pygame.BLEND_ALPHA_SDL2)

    def save_background(self):
        '''
        To use the game's screen instead of classic background
        '''
        # Grab screen
        rect = pygame.Rect(0, 0, self.res_x, self.res_y)
        sub = self.screen.subsurface(rect)
        screenshot = pygame.Surface((self.res_x, self.res_y))
        if str(pygame.version.ver) == '2.0.0':
            screenshot.blit(sub, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            screenshot.blit(sub, (0, 0))
        self.game_background = screenshot

    def restore_background(self, refresh=True):
        '''
        To use the game's screen instead of classic background
        '''
        if self.game_background is not None:
            self.blit(self.game_background, (0, 0))
            if refresh:
                self.update_screen()

    def reset_background(self):
        '''
        Go back to original background
        '''
        self.game_background = None

    def init_background(self, background):
        '''
        Init background
        '''
        self.logs.log("DEBUG", f"Cleaning image cache")
        if self.background is None or self.background != background:
            self.imagecache = {}
        self.background = background
        self.logs.log("DEBUG", f"Background is now {self.background}")

    def mcp_error(self, error):
        '''
        To avoid a violent back to desktop
        '''
        margin = self.res_y / 24
        color = (255,0 ,0)

        self.display_background()
        self.update_screen()

        rect = pygame.Rect(self.res_x / 64, self.res_y / 64, self.res_x  * 62 / 64, self.res_y * 62 / 64)
        self.new_blit_rect2(rect, self.colorset['bg-global'])

        rect = pygame.Rect(self.res_x / 32, self.res_y / 32, self.res_x * 28 / 32, self.res_y / 8)
        self.blit_text2("ATTENTION", rect, color)

        
        rect.y += rect.height * 2 + margin
        rect.height /= 2
        self.blit_text2("Une carte d'extension est déclarée mais n'a pas été détectée", rect, color)

        rect.y += margin * 2
        self.blit_text2("Le jeu va se lancer mais les boutons seront inutilisables.", rect, color)

        rect.y += margin
        self.blit_text2("La cible peut également ne pas fonctionner.", rect, color)

        rect.y += margin
        self.blit_text2("Utilisez la cible pour vous déplacer et arrêter le jeu proprement,", rect, color)

        rect.y += margin
        self.blit_text2("puis corrigez le problème (vérifiez que la carte est bien enfichée)", rect, color)

        rect.y += margin
        self.blit_text2("Et enfin redémarrez le jeu", rect, color)

        rect.y += margin * 2
        self.blit_text2(f"L'erreur est la suivante :", rect, color)

        rect.y += margin
        self.blit_text2(f"{error}", rect * 2, (152, 176, 2))

        rect.y += height * 2 + margin
        self.blit_text2("Appuyez sur la cible pour continuer.", rect, color)

        self.update_screen()
        self.wait_touch()

    def send_cheer(self):
        '''
        Send Cheer to dmd : usefull ??
        '''
        self.dmd.send_text(self.lang.translate('dmd-bestwin'), tempo=2)

    def get_ips(self):
        '''
        Get IP of the rpi
        '''
        ips = []
        for iface in interfaces():
            if iface != 'lo':
                ip = ifaddresses(iface).setdefault(AF_INET, [{'addr': 'None'}])[0]['addr']
                if ip != 'None':
                    ips.append((iface, ip))
        return ips

    def create_screen(self, Toggle=False, newresolution=False, Font=None):
        '''
        Create screen and optionnaly toggle Fullscreen/windowed
        '''

        if newresolution:
            self.imagecache = {}
        # Toggle if requested
        if self.fullscreen and Toggle:
            self.fullscreen = False
        elif Toggle:
            self.fullscreen = True
        # If toggle screen or resize
        if Toggle:
            # grab information before quitting actual screen
            self.screen = pygame.display.get_surface()    # Get a reference to the currently set display surface
            tmp = self.screen.convert() # change the pixel format of an image ? Can't remember why I do that ;)
            #cursor = pygame.mouse.get_cursor()    # Get the image for the system mouse cursor
            # Bye bye old screen !
            pygame.display.quit()

        if not pygame.display or Toggle:
            # Welcome new screen !
            pygame.display.init()
        # Define resolution
        self.init_resolution(newresolution)
        # Define screen constants (depends on resolution)
        self.define_constants(Font = Font)
        # Tell pygame it is fullscreen if it is
        if self.fullscreen:
            self.flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode((0, 0), self.flags, 16)    # Set fullscreen with actual resolution
        else:
            self.screen = pygame.display.set_mode((self.res['x'], self.res['y']), pygame.RESIZABLE) # Start windowed with settings

        # If Toggling, blit the new screen
        if Toggle:
            self.blit(tmp, (0, 0))

        # Get caption back
        pygame.display.set_caption(f'RaspyDarts v.{self.config.pyDartsVersion}')
        # Set pyDarts icon images
        imagefile = self.file_class.get_full_filename('icon', 'images')
        if imagefile is not None:
            iconimage = pygame.image.load(imagefile).convert_alpha()
            pygame.display.set_icon(iconimage)
        else:
            self.logs.log("WARNING", f"Unable to load icon image.")
        pygame.key.set_mods(0)    # HACK: work-a-round for a SDL bug??
        #if Toggle:
        #    pygame.mouse.set_cursor(*cursor)    # Duoas 16-04-2007
        self.display = pygame.display

    def init_colorset(self):
        '''
        Init the choosen ColorSet
        '''

        self.choosen_colorset = self.config.get_value('SectionGlobals', 'colorset')

        try:
            self.colorset = ColorSet[self.choosen_colorset]
        except:
            colorset_file = self.file_class.get_full_filename('Colorset', 'text')
            try:
                colorset_file = self.file_class.get_full_filename('Colorset', 'text')
                if colorset_file is None:
                    raise Exception(f"No Colorset.cfg in {self.file_class.theme_dir}/other")
                self.logs.log("INFO", f"Use {colorset_file} for color's customization")
                ColorSet['Colorset'] = self.config.read_colorset(colorset_file)
                self.colorset = ColorSet['Colorset']
                for key, value in ColorSet['clear'].items():
                    if key not in self.colorset:
                        self.colorset[key] = value
                    else:
                        self.logs.log("INFO", f"Customization : {key} is customized to {value}")
            except Exception as e:
                self.logs.log("WARNING", "Error during load of custom colorset")
                self.logs.log("WARNING", f"Error was {e}")
                self.colorset = ColorSet['clear']

        self.init_background(self.file_class.get_full_filename('background', 'images'))

        for colorset in ColorSet:
            self.colorsets[colorset] = ColorSet[colorset]

        self.online_icon = self.file_class.get_full_filename('online', 'images')

    def init_resolution(self, newresolution=False):
        '''
        Get best parametered display resolution or best resolution if fullscreen
        Init a dictionnary named "res" which contains x and y display resolutions
        '''
        self.resmin['x'] = 200
        self.resmin['y'] = 100
        if newresolution:
            self.res['x'] = int(newresolution[0])
            self.res['y'] = int(newresolution[1])
            self.logs.log("DEBUG", f"Using display mode : {self.res['x']}x{self.res['y']}")
        elif self.fullscreen is False:
            self.res['x'] = int(self.config.get_value('SectionGlobals', 'resx'))
            self.res['y'] = int(self.config.get_value('SectionGlobals', 'resy'))
            self.logs.log("DEBUG", f"Using display mode : {self.res['x']}x{self.res['y']}")
        else:
            infoObject = pygame.display.Info()
            self.res['x'] = infoObject.current_w
            self.res['y'] = infoObject.current_h
            self.logs.log("DEBUG", f"Ho yeah, going fullscreen : {self.res['x']}x{self.res['y']}")

        # Exit if resolution smaller than minimal size
        if self.res['x'] < self.resmin['x'] or self.res['y'] < self.resmin['y']:
            self.logs.log("WARNING",
                f"Cannot reduce resolution to something smaller than {self.resmin['x']}x{self.resmin['y']}, sorry.")
            self.res['x'] = self.resmin['x']
            self.res['y'] = self.resmin['y']

        self.res_x = self.res['x']
        self.res_y = self.res['y']
        self.mid_x = int(self.res['x'] / 2)
        self.mid_y = int(self.res['y'] / 2)
        self.quart_x = int(self.res['x'] / 4)
        self.quart_y = int(self.res['y'] / 4)
        self.res_x_16 = int(self.res['x'] / 16)
        self.res_y_15 = int(self.res['y'] / 15)
        self.res_y_8 = int(self.res['y'] / 8)
        self.res_y_16 = int(self.res['y'] / 16)

    def blit_rect(self, pos_x, pos_y, width, height, color, border=False, border_color=False, Alpha=None):
        '''
        Display a rect with transparency, with optionnal border
        '''
        if not color:    # If color is not set, put alpha to 100%
            color = self.colorset['message-bg']    # Arbitrary
            Alpha = 0
        if not color:
            return
        if Alpha is None:
            Alpha = self.alpha
        if not border_color:
            border_color = self.colorset['menu-border']

        surface = pygame.Surface((int(width), int(height)))    # the size of your rect
        surface.set_alpha(Alpha)    # alpha level
        surface.fill(color)    # this fills the entire surface
        self.blit(surface, (int(pos_x), int(pos_y)))    # (0, 0) are the top-left coordinates
        if border:
            pygame.draw.rect(self.screen, border_color, (int(pos_x), int(pos_y), int(width), int(height)), border)

    def get_font(self, size):
        '''
        Return the font with size given
        '''
        return pygame.font.Font(self.defaultfontpath, size)

    @lru_cache(maxsize=2048)
    def scale_text(self, text, width, height, dafont=None, divider=1.5, step=0.1):
        '''
        Return best text size to scale text in a given box size (usefull for responsive design)
        '''
        if dafont is None:
            dafont = self.defaultfontpath
        else:
            dafont = self.file_class.get_full_filename(f'{dafont}', 'fonts')

        while True:
            text_size = int(height / divider)
            font = pygame.font.Font(f'{dafont}', text_size)
            font_size = font.size(str(text))

            if text_size <= 0:
                self.logs.log("ERROR", f"Unable to find suitable text size for a box of size {width}x{height} and for text {text}")
                return None

            if font_size[0] < width and font_size[1] < height:
                # Returns Best text size, horizontal space needed to center text, vertical space to center text
                return [text_size, int((width - font_size[0]) / 2), int((height - font_size[1]) / 2), font_size[0], font_size[1]]

            divider += step

    #@debug
    def blit_text2(self, text, rect, color=None, font=None, align='Center', valign='center', margin=True, divider=1.5, alpha=255):
        self.blit_text(text, rect[0], rect[1], rect[2], rect[3], color=color, dafont=font, align=align, valign=valign, margin=margin, divider=divider, Alpha=alpha)
        return rect

    #@debug
    def blit_text(self, text, pos_x, pos_y, width, height, color=None, dafont=None, image=None, align='Center', valign='center', margin=True, divider=1.5, Alpha=255):
        '''
        Render text in a box, directly at best size
        '''
        if text is None or text == '':
            return
        if divider is None:
            divider = 1.5

        text = str(text)

        if dafont is None:
            dafont = self.defaultfontpath
        if color is None:
            color = self.colorset['menu-text-white']

        try:
            text = self.lang.translate(text)
        except Exception as e:
            self.logs.log("WARNING", "Issue in Screen.lit_text method.")
            self.logs.log("DEBUG", f"Issue is {e}")

        if margin:
            text_margin = self.margin
        else:
            text_margin = 0

        # Display Text
        scaled_text = self.scale_text(text, width - 2 * text_margin, height - 2 * text_margin, divider=divider, dafont=dafont)
        if dafont is None:
            font = pygame.font.Font(f'{self.defaultfontpath}', scaled_text[0])
        else:
            font = pygame.font.Font(self.file_class.get_full_filename(dafont, 'fonts'), scaled_text[0])
        # Render text
        text = font.render(text, True, color)
        # Calculate place of text
        if align == 'Center':
            text_x = int(pos_x + (width - scaled_text[3] + text_margin) / 2)
        elif align == 'Left':
            text_x = int(pos_x + text_margin)
        else : # Right
            text_x = int(pos_x + width - scaled_text[3] - 2 * text_margin)

        if valign == 'top':
            text_y = int(pos_y + text_margin)
        else:
            text_y = int(pos_y + scaled_text[2] + text_margin)

        if image != None:
            img = pygame.image.load(image).convert_alpha()
            img.set_alpha(Alpha)
            self.blit(img, [text_x, text_y])
        else:
            # Display text
            text.set_alpha(Alpha)
            self.blit(text, [text_x, text_y])

    def menu_header(self, text, subtxt=None, centertxt=None):
        '''
        All menus use the same header
        '''
        rect = pygame.Rect(0, int(self.res['y'] / 30), self.res['x'], int(self.res['y'] / 15))

        if self.colorset['menu-header'] is not None:
            self.new_blit_rect2(rect, self.colorset['menu-header'])
        self.blit_text2(text, rect, self.colorset['menu-text'])

        if subtxt:
            rect.y += rect.height
            if self.colorset['menu-header'] is not None:
                self.new_blit_rect2(rect, self.colorset['menu-header'], alpha=255)
            self.blit_text2(subtxt, rect, self.colorset['menu-text'])

        if centertxt is not None:
            rect.y = int(self.res['y'] * 6 / 14)

            if self.colorset['menu-header'] is not None:
                self.new_blit_rect2(rect, self.colorset['menu-header'], alpha=255)
            self.blit_text2(centertxt, rect, self.colorset['menu-text'])

    def wait_touch(self):
        '''
        Wait for touch
        '''

        press = self.rpi.listen_inputs(
                    ['alpha', 'num', 'fx', 'math', 'arrows'],
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'])
        return press

    def wait_validation(self, text):
        '''
        Wait for validation
        '''
        rect = pygame.Rect(0, int(self.res['y'] * 9 / 20), self.res['x'], self.res['y'] / 5)

        if self.colorset['border-radius'] == 'max':
            border_radius = int(rect.h / 2)
        else:
            border_radius = int(self.colorset['border-radius']) * 4

        self.save_background()
        self.display_background(image=True)

        minus = 10

        self.new_blit_rect2(rect, self.colorset['message-bg'], alpha=255, corners='All', border_radius=border_radius)
        self.blit_border(rect, (0, 0, 0), minus, alpha=255, corners='All', border_radius=border_radius)
        rect2 = rect.copy()
        rect2.height /= 2
        self.blit_text2(text, rect2, self.colorset['message-text'])
        rect2.y = rect2.bottom
        self.blit_text2("press-enter", rect2, self.colorset['message-text'])

        self.update_screen()
        if self.wait_touch() in ENTER_KEYS:
            self.restore_background()
            self.reset_background()
            return True

        self.restore_background()
        self.reset_background()
        return False

    def message(self, texts, wait=3000, color=None, pos_y=None, size=None, logo=None, refresh=True, bg_color=None):
        '''
        Main UI messaging method - can display multiple phrases, mutiple sizes, multiple places
        '''

        if logo is not None:
            size = self.res['y'] / 4
        else:
            if size == 'small':
                size = self.res['y'] / 40
            if size is None or size == 'normal':
                size = self.res['y'] / 20
            if size == 'big':
                size = self.res['y'] / 7
            if size == 'huge':
                size = self.res['y'] / 4

        # set the color of the Text
        text_color = self.colorset['message-text']
        if type(color) is tuple:
            text_color = color
        elif type(color) == str and color in self.colorset:
            text_color = self.colorset[color]

        # Constants
        width = self.res['x']
        rect_x = 0
        # Display background
        if refresh and self.game_background is None:
            self.display_background()
        elif refresh:
            self.blit(self.game_background, (0, 0))

        if bg_color is None:
            bg_color = self.colorset['message-bg']
        else:
            bg_color = self.colorset[bg_color]

        # For each sentence in list
        for text in texts:
            # Calculate Y
            if pos_y is None or pos_y == 'bottom':
                pos_y = self.res['y'] / 3 * 2
            if pos_y == 'fullbottom':
                pos_y = self.res['y'] - (size / 2)
            if pos_y == 'top':
                pos_y = self.res['y'] / 3
            if pos_y == 'middle':
                pos_y = self.res['y'] / 2
            # Calculate rect size and place
            rect_y = int(pos_y - (size / 2))
            # Display rect
            rect = pygame.Rect(rect_x, rect_y, width, size)
            self.new_blit_rect2(rect, bg_color)

            if logo is None:
                self.blit_text2(text, rect, text_color)
            else:
                self.blit_text2('' , rect, text_color)

                # Display LOGO
                width = int(self.res['x'] / 3)
                height = int(self.res['y'] / 4)
                pos_x = 0 + width
                pos_y = int(self.res['y'] / 2.7)
                # Display LOGO
                self.display_image(self.file_class.get_full_filename(logo, 'images'), pos_x, pos_y, width, height, False, True, True)

            if refresh:
                # Update screen
                self.update_screen()
                # Optionnaly wait a few sec between each message
                if wait is None:
                    pygame.time.wait(self.blinktime)
                elif wait > 0:
                    pygame.time.wait(wait)    # Wait X millisecond

        #return (rect_x, rect_y, width, size)

    def is_clicked(self, zones=None, click=False):
        '''
        Define if the click is inside the given zone
        '''
        # Eventually get Zones for current object if not provided
        if zones is None:
            zones = self.click_zones
        # Exit if we did not receive a click (maybe another input) or if Zones is not set
        if type(click) is not tuple or zones is None:
            return False
        # Try to expand all zones and compare them to click

        try:
            for key in zones.keys():
                if type(zones[key]) is pygame.Rect and zones[key].collidepoint(click[0], click[1]):
                    return key
                # Avoid getting an exception for integers
                if type(zones[key]) is not tuple:
                    continue
                # Compare
                if click[0] >= zones[key][0] and click[0] <= zones[key][0] + zones[key][2] and click[1] >= zones[key][1] and click[1] <= zones[key][1] + zones[key][3]:
                    return key
        except Exception as e:
            self.logs.log("WARNING", "Issue in cscreen.is_clicked method.")
            self.logs.log("DEBUG", f"Issue is {e}")
            return False

    def get_rpi_config(self):
        '''
        1st execution : get configuration
        '''
        self.logs.log("INFO", f"Lauch target's setup wizard")


        self.display_background()    # display basic screen
        self.display_ips(big=True)            # display IPs addresses
        self.menu_header("config-interface")
        self.update_screen()
        cards_dd = [['Ji', 'Cartes de Jimmy'], ['Jo', 'Carte de Joffrey'], ['Ch', 'La Chti Raspycard'], ['Jt', 'Carte de Julien'], ['Mm', 'MM-Workshop DartCab'], ['Re', 'DartBoard'], ['Au', 'card-other']]
        card = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, cards_dd)
        if card == 'escape':
            return False

        if card in ('Ji', 'Jo'):
            # Menu extendarts pour choix des matrices

            self.display_background()    # display basic screen
            self.menu_header("config-interface")
            self.update_screen()
            if card == 'Ji':
                cards_dd = [['Ji', 'RaspyCard'], ['Jiz', 'RaspyZcard'], ['Ji3', 'RaspYDartsCard'], ['Ji2', 'RaspyCard V4'], ['GB', 'RaspyBoard'], ['ED', 'ED900']]
            else:
                cards_dd = [['Jo', 'Cible ED110 7*10'], ['Jo416', 'Cible Pro 4*16'], ['Au', 'card-other'], ]
            card = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, cards_dd)
            if card == 'escape':
                return False

        if card in ('Jo', 'Re'):
            self.config.set_jo_card_config()
        elif card == 'Jo416':
            self.config.set_jo_416_card_config()
        elif card in ('Ji', 'Mm'):
            self.config.set_ji_card_config()
        elif card in ('Ji2', 'Ji3'):
            self.config.set_ji2_card_config()
        elif card == 'GB':
            self.config.set_gb_card_config()
        elif card == 'ED':
            self.config.set_ed900_card_config()
        elif card == 'Jt':
            self.config.set_jt_card_config()
        elif card == 'Jiz':
            self.config.set_jiz_card_config()
        elif card == 'Ch':
            self.config.set_clk_card_config()

        self.display_background()    # display basic screen
        self.menu_header("config-leds_choice", "config-leds_question")
        self.update_screen()
        leds_dd = [['yes', 'yes'], ['no', 'no']]
        leds_ji = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, leds_dd)

        used_pins = []
        if card == 'Au':
            i = 0
            total = 66

            # Out pins
            new_outputs = {}
            totalOuts = len(self.config.outputs)

            # In pins
            new_inputs = {}
            totalIns = len(self.config.inputs)

            # Buttons conf (extended card)
            new_buttons = {}
            totalButtons = len(self.config.buttons)

            # Target configuration
            new_keys = {}

            j = 0
            # Parametrage des pins de sortie
            while j < totalOuts:
                self.display_background()    # display basic screen
                key = list(self.config.outputs)[j]
                txt = f"{self.lang.translate('conf-fillin')} {key}"
                self.message([txt], 0, None, 'fullbottom', 'big', refresh=False)
                if j == 0:
                    esc_text = self.lang.translate('conf-esc1')
                else:
                    esc_text = self.lang.translate('conf-esc2')

                subtxt = self.lang.translate('conf-pin1').format(txt, esc_text)
                self.menu_header("config-pin_out", subtxt)
                self.update_screen()

                tmp = self.input_value_item('pins', '', 1, 27, align = 'Center')

                if tmp in ('', 'space'):
                    j = totalOuts
                elif tmp == 'escape':
                    j -= 1
                    if len(used_pins)>0:
                        used_pins.pop()
                    if j < 0:
                        return False
                elif tmp in used_pins:
                    self.message(["config-already"], 2000, None, 'fullbottom', 'big')
                else:
                    new_outputs[key] = tmp
                    self.rpi.set_outputs(tmp)
                    used_pins.append(tmp)
                    j += 1

            # Parametrage des pins d'entrée
            j = 0
            while j < totalIns:
                self.display_background()    # display basic screen
                key = list(self.config.inputs)[j]
                txt = f"{self.lang.translate('conf-fillin')} {key}"
                self.message([txt], 0, None, 'fullbottom', 'big', refresh=False)
                if j == 0:
                    esc_text = self.lang.translate('conf-esc1')
                else:
                    esc_text = self.lang.translate('conf-esc2')

                subtxt = self.lang.translate('conf-pin2').format(txt, esc_text)

                self.menu_header("Configuration des pins d'entrée de la cible", subtxt)
                self.update_screen()

                tmp = self.input_value_item('pins', '', 1, 27, align = 'Center')
                if tmp in ('', 'space'):
                    j = totalIns
                elif tmp == 'escape':
                    j -= 1
                    used_pins.pop()
                    if j < 1:
                        return False
                elif tmp in used_pins:
                    self.message(["config-already"], 2000, None, 'fullbottom', 'big')
                else:
                    new_inputs[key] = tmp
                    self.rpi.set_inputs(tmp)
                    used_pins.append(tmp)
                    j += 1

            # Parametrage des boutons

            self.display_background()    # display basic screen
            self.menu_header("Configuration des boutons")
            self.message(["Avez-vous une carte d'extension ?"], 0, None, 'fullbottom', 'big', refresh=False)
            self.update_screen()

            new_buttons['EXTENDED_GPIO'] = self.dropdown(self.res['x'] / 8 * 3, self.res['y'] / 8 * 3, [('1', 'yes'), ('0', 'no')])

            if new_buttons['EXTENDED_GPIO'] == '0':
                j = 0
                while j < totalButtons:
                    if list(self.config.buttons)[j] == 'EXTENDED_GPIO':
                        j += 1
                        continue

                    key = list(self.config.buttons)[j]
                    txt = f"{self.lang.translate('conf-fillin')} {key}"
                    self.message([txt], 0, None, 'fullbottom', 'big')
                    if j == 0:
                        subtxt = "Merci d'indiquer si vous avez une carte d'extension. Echap pour quitter, Entrée pour valider."
                    else:
                        subtxt = f"Merci d'indiquer sur quel pin est connecté le bouton {key.replace('PIN_', '')}.Echap pour revenir en arrière, Entrée pour valider ou passer."

                    self.menu_header("Configuration du Raspberry", key)
                    self.update_screen()

                    tmp = self.input_value_item('pins', '', 1, 27, align = 'Center')
                    if tmp in ('', 'space'):
                        j = totalButtons
                    elif tmp == 'escape':
                        j -= 1
                        used_pins.pop()
                        if j < 1:
                            return False
                    elif tmp in used_pins:
                        self.message([self.lang.translate('config-already')], 2000, None, 'fullbottom', 'big')
                    else:
                        new_buttons[key] = tmp
                        used_pins.append(tmp)
                        j += 1

            self.rpi.init_gpio(new_inputs, 'IN')
            self.rpi.init_gpio(new_outputs, 'OUT')

        # Leds conf
        new_leds = {}
        totalLeds = len(self.config.leds)

        j = 0
        while j < totalLeds:
            self.display_background()    # display basic screen

            key = list(self.config.leds)[j]
            if j == 0:
                esc_text = self.lang.translate('conf-esc1')
            else:
                esc_text = self.lang.translate('conf-esc2')

            if key.startswith('PIN_'):
                subtxt = self.lang.translate('conf-pin1').format(self.lang.translate(key), esc_text)
            else:
                subtxt = self.lang.translate('conf-pin2').format(self.lang.translate(key), esc_text)

            self.menu_header(self.lang.translate('conf-leds'))
            self.message([f"{self.lang.translate('conf-fillin')} {self.lang.translate(key)}"], 0, None, 'fullbottom', 'big', refresh=False)
            self.update_screen()

            if key in ('PIN_STRIPLED', 'PIN_TARGETLED'):
                tmp = self.input_value_item('pins', '', 1, 27, align = 'Center')
            elif key in ('BRI_STRIPLED', 'BRI_TARGETLED'):
                tmp = self.input_value_item('number', '', 1, 100, align = 'Center')
            elif key == 'NBR_STRIPLED':
                tmp = self.input_value_item('number', '', 1, 1000, align = 'Center')

            if tmp in ('', 'space'):
                new_leds[key] = '0'
                if key == 'PIN_STRIPLED':
                    j += 3
                    new_leds['NBR_STRIPLED'] = 0
                    new_leds['BRI_STRIPLED'] = 0
                elif key == 'PIN_TARGETLED':
                    j += 2
                    new_leds['BRI_TARGETLED'] = 0
                elif key.startswith('BRI') or key == 'NBR_STRIPLED':
                    if key in ('NBR_STRIPLED', 'BRI_TARGETLED'):
                        used_pins.pop()
                    j -= 1
                else:
                    tmp = 'escape'
            elif tmp == 'escape':
                j -= 1
                if j < 0:
                    return False
            elif key in ('PIN_STRIPLED', 'PIN_TARGETLED') and tmp in used_pins:
                self.message([self.lang.translate('config-already')], 2000, None, 'fullbottom', 'big')
            else:
                new_leds[key] = tmp
                if key.startswith('PIN'):
                    used_pins.append(tmp)
                j += 1

        self.rpi.set_leds_conf(new_leds)

        if card == 'Au':
            # Parametrage de la cible
            j = 0
            UsedKeys = []

            self.display_background()    # display basic screen
            while j < 62:
                key = list(self.config.keys)[j]
                i = 0
                txt = self.lang.translate('press-on').format(key)
                self.message([txt], 0, None, 'fullbottom', 'big', refresh=False)    # Print background first
                for key2 in list(self.config.keys):
                    # Get type
                    multiplier = key2[:1]
                    # Define colors
                    if i % 2 == 0 and multiplier in ('D', 'T'):
                        part_color = self.colorset['menu-ok']
                    elif multiplier in ('D', 'T'):
                        part_color = self.colorset['menu-ko']
                    else:
                        part_color = None
                    if key2 == key: part_color = self.colorset['menu-shortcut']
                    # Draw the right thing
                    if key2[1:] != 'B' and len(key2) <= 3:
                        score = int(key2[1:])
                    elif key2[1:] == 'B':
                        score = 'B'
                    if multiplier == 'S' and score != 'B':
                        self.draw_exterior_simple(self.targets[score], part_color)
                        self.draw_interior_simple(self.targets[score], part_color)
                    elif multiplier == 'D' and score != 'B':
                        self.draw_double(self.targets[score], part_color)
                    elif multiplier == 'T' and score != 'B':
                        self.draw_triple(self.targets[score], part_color)
                    elif multiplier == 'S' and score == 'B':
                        self.draw_bull(True, False, part_color)
                    elif multiplier == 'D' and score == 'B':
                        self.draw_bull(False, True, part_color)
                    if key2 != 'D5':    # On T20 we switch color order
                        i += 1
                    if key2 == key or len(key2) > 3: break    # If key2 is not yet configurer or if it is buttons

                subtxt = f"{self.lang.translate('press-on-parts')} - {self.lang.translate('left')} : {total - i}"
                self.menu_header(self.lang.translate('board-calibration'), subtxt)

                self.update_screen()

                key_pressed = self.rpi.listen_inputs([], ['escape', 'enter', 'TOGGLEFULLSCREEN'], context = 'wizard')

                if key_pressed == 'escape':
                    if j > 0:
                        self.display_background()    # display basic screen
                        j -= 2
                        if UsedKeys:
                            UsedKeys.pop(-1)
                    else:
                        self.rpi.gpio_flush()
                        sys.exit(0)
                elif key_pressed not in UsedKeys and key_pressed not in ('enter', ''):
                    new_keys[key] = key_pressed
                    UsedKeys.append(key_pressed)
                    self.play_sound('Blaster')

                else:
                    # Cancel next step because of the key is the same than the previous or unauthorized
                    i -= 1
                    j -= 1

                i += 1
                j += 1

            for l in [1, 2, 3, 4]:
                new_keys[self.config.keys[j]] = ''
                j += 1

            if new_buttons['EXTENDED_GPIO'] == '1':
                from include import cgpio_extender

                for k in self.config.buttons:
                    if k != 'EXTENDED_GPIO':
                        new_buttons[k] = cgpio_extender.DEFAULTS[k]

            self.rpi.set_inputs_conf(new_inputs)
            self.rpi.set_outputs_conf(new_outputs)
            self.rpi.set_buttons_conf(new_buttons)
            self.rpi.set_keys_conf(new_keys)
        else:
            used_pins = []
            for p in self.rpi.inputs:
                pin = elf.raspberry.inputs[p]
                if pin != '':
                    used_pins.append(int(pin))

            for p in self.rpi.outputs:
                pin = self.rpi.outputs[p]
                if pin != '':
                    used_pins.append(int(pin))

        if leds_ji == 'yes':
            self.config.set_ji_leds_config()

        self.display_background()    # display basic screen
        self.menu_header("config-buttons_choice", "config-buttons_question")
        self.update_screen()
        yesno_dd = [['yes', 'yes'], ['no', 'no']]
        go_conf = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, yesno_dd)

        if go_conf == 'yes':
            extended_io = self.setup_io_extender()
            if extended_io is not None:
                self.config.set_config('Raspberry', extended_io)

        # Write config file
        self.config.write_file()

        self.message([f"{self.lang.translate('config-restart')}"], 2500, None, 'middle', 'big')
        return True

    def setup_io_extender(self):

        try:
            from . import cgpio_extender
            gpio = cgpio_extender.Gpio_extender('')

            pins = []
            for pin in range(0, 16):
                pins.append(gpio.mcp.get_pin(pin))
                pins[pin].pull = gpio.pull_up

            outputs = []
            value = hex(gpio.mcp.gpio)
            for button in range(0, 16):
                if not int(value, 16) & 2**button:
                    outputs.append("{}".format(chr(65 + int(button / 8)) + chr(48 + button % 8)))    # Compute A0..B7

            if len(outputs) > 0:
                self.message([f"{self.lang.translate('config-toysfound')} {'/'.join(outputs)}"], 2500, None, 'middle', 'big')

            buttons_list = []
            toys_list = []
            done = []
            buttons_conf = {}
            toys_conf = {}

            for key in gpio.get_defaults():
                if key == 'PIN_DEMOLED':
                    pass
                if key.startswith('PIN_'):
                    buttons_list.append(key)
                if key.startswith('LIGHT_'):
                    toys_list.append(key)

            for pin in gpio.all_io:
                if not pin in outputs:
                    self.display_background()
                    self.menu_header(f"{self.lang.translate('config-pin')} {pin}", f"{self.lang.translate('config-pin-sub')}")
                    self.update_screen()
                    buttons_dd = [(button, f"{self.lang.translate(button)}") for button in buttons_list] + [('None', 'Aucun')]
                    button = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, buttons_dd)
                    if button != 'None':
                        buttons_list.remove(button)
                        buttons_conf[button] = pin

            for pin in outputs:
                self.display_background()
                self.menu_header(f"{self.lang.translate('config-toy')} {pin}", f"{self.lang.translate('config-toy-sub')}")
                self.update_screen()
                toys_dd = [(toy, f"{self.lang.translate(toy)}") for toy in toys_list] + [('None', 'Aucun')]
                toy = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, toys_dd)
                if toy != 'None':
                    toys_list.remove(toy)
                    toys_conf[toy] = pin

            config = {}
            for key in gpio.get_defaults():
                if key == 'PIN_DEMOLED':
                    value = ''
                elif key == 'EXTENDED_GPIO':
                    if buttons_conf is not None:
                        value = 1
                    else:
                        value = 0
                elif key.startswith('PIN_'):
                    if buttons_conf is not None:
                        value = buttons_conf.get(key, '')
                    else:
                        value = ''
                elif key.startswith('LIGHT_'):
                    if buttons_conf is not None:
                        value = toys_conf.get(key, '')
                    else:
                        value = ''
                config[key] = value

            return config
        except:
            self.message([self.lang.translate('config-noMCP')], 3000, None, 'middle', 'big', bg_color='menu-ko')
            return None

    def starting(self, NetClient, NetStatus, local_players, netgamename, game):
        '''
        Display Players engaged in a network game menu
        '''
        self.display_background()    # display basic screen
        # Init empty values
        Rdy = {'REQUEST': None, 'PLAYERSNAMES': None}
        players = []
        # This loop will ends when the game will be launched
        click_zones = {}
        selected = 1
        nb_boutons = 1
        nb_players = len(local_players)
        nb_local_players = nb_players
        old_nb_players = nb_players
        Rdy = NetClient.send_local_players(local_players)    # Send name of local players, and wait for game to be launched
        while True:
            # Listen for keyboard
            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'],
                            ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                            'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'],
                            timeout=1000)

            # Analyse mouse
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            selected = self.navigate(selected, key_pressed, 0, nb_boutons, nb_boutons)

            # Analyse key
            # If the Master player pressed tab
            if nb_players > nb_local_players and NetStatus == 'YOUAREMASTER' and ((key_pressed in ENTER_KEYS and selected == 2) or key_pressed in TAB_KEYS):
                self.play_sound('shakeitbaby')
                # Request the server to shuffle player names
                data = {'REQUEST': 'SHUFFLE', 'GAMENAME': NetClient.gamename}
                NetClient.send(data)    # Send message
                # Display refreshing from server
                #self.message([self.lang.translate('net-client-randomizing')], 500)

            elif (key_pressed in ENTER_KEYS and selected == 1) or key_pressed in ESCAPE_KEYS:
                if NetStatus == 'YOUARESLAVE':
                    return -1    # Return -1 means yourself, as a slave client left the game
                return []    # Return -1 means yourself, as a slave client left the game

            # If the Master pressed enter
            if nb_players > nb_local_players and NetStatus == 'YOUAREMASTER' and ((key_pressed in ENTER_KEYS and selected == 3) or key_pressed in CONTINUE_KEYS):
                self.message([self.lang.translate('Ready to kick ass ?')], 0, None, 'middle', 'big')
                # He is ok to launch the game. Tell it to server
                data = {'REQUEST': 'LAUNCH', 'GAMENAME': NetClient.gamename}
                NetClient.send(data)    # Send message

            Rdy = NetClient.send_local_players(local_players)    # Send name of local players, and wait for game to be launched
            # refresh player list if provided by server
            if 'PLAYERSNAMES' in Rdy:
                players = Rdy['PLAYERSNAMES']
            # Display page title
            if NetStatus == 'YOUAREMASTER':
                txt = self.lang.translate('players-ready-masterplayer')
            else:
                txt = self.lang.translate('players-ready-slaveplayer')

            # Display screen
            self.display_background()
            txt2 = f"{self.lang.translate('game-type')} : {game.replace('_', ' ')} - {self.lang.translate('game-name')} : {netgamename}"
            self.menu_header(txt, txt2)

            nb_players = 0
            for player in players:
                nb_players += 1
                self.menu_item((nb_players, len(players), 0), ('', player, BTN_CHOICE, None), collapsed=True)

            if NetStatus == 'YOUAREMASTER' and nb_players > nb_local_players:
                if key_pressed is False and old_nb_players != nb_players:
                    selected = 3
                click_zones['shake'] = self.display_button(2 == selected, 'shake', special='refresh')
                click_zones['continue'] = self.display_button(3 == selected, 'continue', special='return')
                nb_boutons = 3
            else:
                nb_boutons = 1
                selected = 1

            click_zones['escape'] = self.display_button(1 == selected, 'back', special='escape')

            self.update_screen()
            # If we received the order to LAUNCH or to ABORT game
            if Rdy['REQUEST'] in ('LAUNCH', 'ABORT'):
                # Return Player list to main game
                return players
            old_nb_players = nb_players

    def pnj_name(self, playerName):
        '''
        Compute PNJ name
        '''

        if '[' not in playerName:
            return '[NoOb]' + playerName
            # Noob

        if '[NoOb]' in playerName:
            return playerName.replace('[NoOb]', '[BegiN]')
             # Beginner

        if '[BegiN]' in playerName:
            return playerName.replace('[BegiN]', '[InTeR]')
            # Interdemdiate

        if '[InTeR]' in playerName:
            return playerName.replace('[InTeR]', '[PrO]')
            # Pro

        if '[PrO]' in playerName:
            return playerName.replace('[PrO]', '[ExperT]')
            # Expert

        return playerName.replace('[ExperT]', '')

    def next_key(self, character, context=None):
        '''
        In case of using buttons instead of keyboard
        return the next character
        '''

        if context == 'number':
            next_key = {'9':'0'}
        elif context == 'leds':
            next_key = {
                '9':', ',
                ', ':'0'
                }
        elif context == 'server':
            next_key = {
                'z':'0',
                '9':'.',
                '.':':',
                ':':'_',
                '_':'-',
                '-':'a'
                }
        else:
            next_key = {
                    'e': 'é',
                    'é': 'è',
                    'è': 'ë',
                    'ë': 'f',
                    'o': 'ô',
                    'ô': 'p',
                    'z': 'a'
                }

        return next_key.get(character, chr(ord(character) + 1))

    def previous_key(self, character, context=None):
        '''
        In case of using buttons instead of keyboard
        return the previous character
        '''

        if context == 'number':
            previous_key = {'0':'9'}
        elif context == 'leds':
            previous_key = {
                ', ':'9',
                '0':', '
                }
        elif context == 'server':
            previous_key = {
                 'a':'_',
                 '_':'-',
                 '-':':',
                 ':':'.',
                 '.':'9',
                 '0':'z'
                 }
        else:
            previous_key = {
                    'a': 'z',
                    'p': 'ô',
                    'ô': 'o',
                    'f': 'ë',
                    'ë': 'è',
                    'è': 'é',
                    'é': 'e',
                    }

        return previous_key.get(character, chr(ord(character)-1))

    def no_doubles(self, edit, players, selected):
        '''
        Check if player name is already in list of players
        '''
        index = 1
        for player in players:
            if edit.upper() == player.upper() and index != selected:
                return False
            index += 1
        return True

    def navigate(self, selected, key, nb_elements, add, defaultTopBottom, sound=True, item_per_line=1, left_right=False, zero=1):
        '''
        Common navigation menu
        '''
        grid_max = math.ceil(nb_elements/item_per_line) * item_per_line
        v_min = zero

        if key in DOWN_KEYS:
            if item_per_line > 1:
                if selected > nb_elements:
                    selected = 1
                else:
                    selected += item_per_line
                    if selected > nb_elements and add > 0:
                        selected = nb_elements + 1
                    elif selected > nb_elements:
                        selected = selected-grid_max
                    if selected < v_min:
                        selected += item_per_line
            elif selected < nb_elements:
                selected += 1
            elif selected == nb_elements and defaultTopBottom > 0:
                selected = nb_elements + defaultTopBottom
            else:
                selected = v_min

        elif key in UP_KEYS:
            if item_per_line > 1:
                if selected > nb_elements:
                    selected -= 1
                else:
                    selected -= item_per_line
                    if selected < v_min and add > 0:
                        selected = nb_elements + 1
                    elif selected < v_min:
                        selected = grid_max + selected
                        if selected > nb_elements:
                            selected -= item_per_line
            elif selected == v_min:
                selected = nb_elements + defaultTopBottom
            elif selected <= nb_elements:
                selected -= 1
            elif nb_elements == 0:
                selected = defaultTopBottom
            else:
                selected = nb_elements

        elif key in LEFT_KEYS:
            if selected > nb_elements or left_right:
                selected -= 1
            if selected < v_min:
                selected = nb_elements + add
        elif key in RIGHT_KEYS:
            if selected > nb_elements or left_right:
                selected += 1
            if selected > nb_elements + add:
                selected = v_min
        elif key == 'resize':    # Resize screen
            self.create_screen(False, self.rpi.newresolution)
        elif key == 'TOGGLEFULLSCREEN':    # Toggle fullscreen
            self.create_screen(True, False)
        elif sound and key in VOLUME_UP_KEYS + VOLUME_DOWN_KEYS:
            self.adjust_volume(key, False)
        elif sound and key in VOLUME_MUTE:
            self.adjust_volume(key, False)

        return selected

    def players_menu(self, favorites, context='game', bank=[], sets=None, competition_mode=False):
        '''
        Player Names menu
        '''
        players = []
        nb_players = 0

        if context == 'pref':
            self.dmd.send_text(self.lang.translate('dmd-player-favorites'), tempo = 1)
        elif context == 'bank':
            self.dmd.send_text(self.lang.translate('dmd-player-bank'), tempo = 1)
        else:
            self.dmd.send_text(self.lang.translate('dmd-player-choice'), tempo = 1)

        for player in favorites:
            if len(player) > 0:
                players.append(player)
        if context in ('game', 'netcreate', 'netjoin'):
            random.shuffle(players)

        if len(players) == 0:
            players.append(f"{self.lang.translate('Player')} 1")

        if context in ('netcreate', 'netjoin'):
            btn_random = False
            selected = 1
        elif len(players) > 1:
            btn_random = True
            selected = len(players) + 3
        else:
            btn_random = False
            selected = len(players) + 2

        # Init enabled F keys
        key_pressed = ''

        while True:
            nb_elements = len(players)
            shortcuts = []
            click_zones = {}
            clic = ''
            # Draw background
            self.display_background()
            # Draw Text
            self.menu_header(self.lang.translate('players-names'), self.lang.translate('players-names-subtitle'))

            i = 1
            if len(players) == 1:
                special = 'first'
            elif len(players) == 16:
                special = 'last'
            else:
                special = None

            for player in players:
                shortcut = f'F{i}'
                # Display player name
                tmp = self.player_item((i, nb_elements, selected), shortcut, player, special=special)

                # Add clickable zones
                for (e, f) in tmp:
                    click_zones[e] = f

                # Construct available F keys list
                shortcuts.append(shortcut)

                i += 1

            if nb_players != len(players):
                # Show message on Raspydarts DMD
                self.dmd.send_text(f"{len(players)} joueur" + ('', 's')[bool(len(players) > 1)])
                nb_players = len(players)

            # go back and next
            click_zones['escape'] = self.display_button(i == selected, 'back', special='escape')
            if context in ('game', 'netcreate', 'netjoin'):
                if btn_random:
                    click_zones['shake'] = self.display_button(i + 1 == selected, 'shake', special='refresh')
                    click_zones['continue'] = self.display_button(i + 2 == selected, 'continue', special='return')
                else:
                    click_zones['continue'] = self.display_button(i + 1 == selected, 'continue', special='return')
            else:
                if btn_random:
                    click_zones['shake'] = self.display_button(i + 1 == selected, 'shake', special='refresh')
                    click_zones['save'] = self.display_button(i + 2 == selected, 'save', special='return')
                else:
                    click_zones['save'] = self.display_button(i + 1 == selected, 'save', special='return')

            zero = False
            if sets is not None:
                rect = pygame.Rect(self.res_x_16, 3 * self.res_y_16, 2 * self.res_x_16, self.res_x_16)
                self.new_blit_rect2(rect, self.colorset['menu-alternate'], corners='Top')
                self.blit_text2("sets", rect, color=self.colorset['menu-text'])

                rect2 = pygame.Rect(self.res_x_16, 3 * self.res_y_16 + self.res_x_16, 2 * self.res_x_16, self.res_x_16)
                if (selected == 0 and context != 'game') or selected == -1:
                    self.new_blit_rect2(rect2, self.colorset['menu-selected'], padding=self.colorset['padding'] \
                            , border_size=self.colorset['border-size'], border_color=self.colorset['menu-border'], corners='Bottom')
                else:
                    self.new_blit_rect2(rect2, self.colorset['menu-header'], alpha=166, corners='Bottom')
                self.blit_text2(sets, rect2, color=self.colorset['menu-text'])


                if context == 'game':
                    click_zones['F-1'] = rect2
                    shortcuts.append('F-1')

                    zero = True
                    rect = pygame.Rect(self.res_x_16, 7 * self.res_y_16, 2 * self.res_x_16, self.res_x_16)
                    self.new_blit_rect2(rect, self.colorset['menu-alternate'], corners='Top')
                    self.blit_text2("mode", rect, color=self.colorset['menu-text'])

                    rect2 = pygame.Rect(self.res_x_16, 7 * self.res_y_16 + self.res_x_16, 2 * self.res_x_16, self.res_x_16)
                    if selected == 0:
                        self.new_blit_rect2(rect2, self.colorset['menu-selected'], padding=self.colorset['padding'] \
                                , border_size=self.colorset['border-size'], border_color=self.colorset['menu-border'], corners='Bottom')
                    else:
                        self.new_blit_rect2(rect2, self.colorset['menu-header'], alpha=166, corners='Bottom')
                    if competition_mode:
                        mode = "competition"
                    else:
                        mode = "leisure"
                    self.blit_text2(mode, rect2, color=self.colorset['menu-text'])

                click_zones['F0'] = rect2
                shortcuts.append('F0')

            self.update_screen()

            # Read input
            key_pressed = self.rpi.listen_inputs(
                    ['alpha', 'num', 'fx', 'math', 'arrows'],
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'],
                    events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Compare all Players names zone to clicked zone
            clicked = self.is_clicked(click_zones, key_pressed)

            # Return:
            #   +|F1    Add player
            #   -|F1    Del 1st player
            #   /|F1    Player 1 PNJ
            #   1|F1    Select player 1

            if clicked:
                if "|" in clicked:
                    splitted = clicked.split("|")
                    clic = splitted[0]
                    selected = int(splitted[1][1::])    # 1 from +|F1

                    if clic in PLUS_KEYS + MINUS_KEYS + ['/']:
                        key_pressed = clic
                    else:
                        key_pressed = "enter"
                else:
                    key_pressed = clicked

            # Navigation in menu
            if sets is not None:
                zero = -1
            else:
                zero = 1
            if btn_random:
                selected = self.navigate(selected, key_pressed, nb_elements, 3, 3, sound=False, zero=zero)
            else:
                selected = self.navigate(selected, key_pressed, nb_elements, 2, 2, sound=False, zero=zero)

            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            # Key analysis
            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                if context in ('pref', 'bank'):
                    return sets, 'escape'
                return sets, 'escape', competition_mode

            if key_pressed in TAB_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2 and btn_random):
                # Randomize players
                self.play_sound('shakeitbaby')
                random.shuffle(players)

            elif key_pressed in EXTRA_KEYS and selected <= nb_elements:
                # Set player as computer
                players[selected - 1] = self.pnj_name(players[selected - 1])

            elif key_pressed in PLUS_KEYS and (context == 'pref' or nb_elements < 16):
                # Add a player
                i = nb_elements + 1
                while True:
                    new_player = f"{self.lang.translate('Player')} {i}"
                    if new_player not in players:
                        break
                    i += 1

                if bank is None or bank == [''] :
                    missing_players = [(f'{new_player}', f'{new_player}')]
                else:
                    missing_players = [(f'{player}', f'{player}') for player in bank if player not in players] + [(new_player, new_player)]

                if len(missing_players) > 1:
                    new_player = self.dropdown(int(6.5 * self.res_x_16 ), int(2.5 * self.res_y_16), missing_players)

                if new_player != 'escape':
                    players.append(f'{new_player}')

                selected = i
                btn_random = True

            elif key_pressed in MINUS_KEYS and nb_elements > 1 and selected <= nb_elements:
                # Remove player
                players.pop(selected - 1)
                selected -= 1
                selected = max(selected, 1)
                if len(players) < 2:
                    btn_random = False

            elif key_pressed in ENTER_KEYS and ((selected == 0 and context != 'game') or selected == -1):
                sets_bank = [(x, x) for x in (1, 2, 3, 5, 10)]
                tmp = self.dropdown(self.res_x_16, 3 * self.res_y_16 + self.res_x_16, sets_bank, width=2 * self.res_x_16)
                if tmp != 'escape':
                    sets = int(tmp)

            elif key_pressed in ENTER_KEYS and selected == -1 and context == 'game':
                if competition_mode:
                    competition_mode = False
                else:
                    competition_mode = True

            elif key_pressed in ENTER_KEYS and selected == 0 and context == 'game':
                if competition_mode:
                    competition_mode = False
                else:
                    competition_mode = True

            elif key_pressed in SAVE_KEYS or (key_pressed in CONTINUE_KEYS and ( key_pressed != 'BTN_NEXTPLAYER' or selected > nb_elements))\
                    or (key_pressed in ENTER_KEYS and selected == nb_elements + 2 and not btn_random) \
                    or (key_pressed in ENTER_KEYS and selected == nb_elements + 3 and btn_random):
                new_players = []
                nb_elements = 0
                for player in players:
                    if len(player) > 0:
                        nb_elements += 1
                        new_players.append(player)
                # Next Screen !
                self.define_constants(nb_elements)
                if context in ('pref', 'bank'):
                    return sets, sorted(new_players)
                elif context in ('netcreate', 'netjoin'):
                    return sets, new_players, True
                return sets, new_players, competition_mode

            elif key_pressed in ENTER_KEYS + CONTINUE_KEYS:
                # Edit player name
                if players[selected - 1].startswith(self.lang.translate('Player')):
                    tmp = self.input_value_item('string', '', 1, 12, text='player-name')
                else:
                    tmp = self.input_value_item('string', players[selected - 1], 1, 12, text='player-name')

                if tmp != '' and tmp != 'escape':
                    players[selected - 1] = tmp[0].upper() + tmp[1::]


    def blit_border(self, rect, border_color, border_size, corners, border_radius=None, alpha=None):

        if border_color is not None:
            if border_radius is None:
                if self.colorset['border-radius'] == 'max':
                    border_radius = int(rect.height / 2)
                else:
                    border_radius = int(self.colorset['border-radius'])

            if alpha is None:
                alpha = self.alpha
            border_color = (border_color[0], border_color[1], border_color[2], alpha)

            top_left = 0
            top_right = 0
            bottom_left = 0
            bottom_right = 0

            if corners in ('Top', 'TopLeft', 'Left', 'All', 'NotTopRight', 'NotBottomLeft', 'NotBottomRight'):
                top_left = border_radius

            if corners in ('Top', 'TopRight', 'Right', 'All', 'NotTopLeft', 'NotBottomLeft', 'NotBottomRight'):
                top_right = border_radius

            if corners in ('Bottom', 'BottomLeft', 'Left', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomRight'):
                bottom_left = border_radius

            if corners in ('Bottom', 'BottomRight', 'Right', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomLeft'):
                bottom_right = border_radius

            surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            self.rect(surface, border_color, surface.get_rect(), border_size, top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)
            self.blit(surface, rect)

    #@debug
    def new_blit_rect2(self, rectangle, background_color, padding=0, border_color=None, border_size=0, alpha=None, corners=None, border_radius=None, selected=False):
        '''
        Blit rect using rectangle
        '''

        if background_color is None:
            return
        else:
            if selected:
                border_color = self.colorset['menu-border']
                border_size = self.colorset['border-size']
                padding = self.colorset['padding']
                background_color = self.colorset['menu-selected']
            if alpha is None:
                alpha = self.alpha
            color = (background_color[0], background_color[1], background_color[2], alpha)

        top_left = 0
        top_right = 0
        bottom_left = 0
        bottom_right = 0

        if border_radius is None:
            if self.colorset['border-radius'] == 'max':
                border_radius = int(rectangle.height / 2)
            else:
                border_radius = int(self.colorset['border-radius'])

        if corners in ('Top', 'TopLeft', 'Left', 'All', 'NotTopRight', 'NotBottomLeft', 'NotBottomRight'):
            top_left = border_radius

        if corners in ('Top', 'TopRight', 'Right', 'All', 'NotTopLeft', 'NotBottomLeft', 'NotBottomRight'):
            top_right = border_radius

        if corners in ('Bottom', 'BottomLeft', 'Left', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomRight'):
            bottom_left = border_radius

        if corners in ('Bottom', 'BottomRight', 'Right', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomLeft'):
            bottom_right = border_radius

        if padding == 'max' and border_color is not None:
            surface = pygame.Surface((rectangle.width, rectangle.height), pygame.SRCALPHA)
            self.rect(surface, border_color, surface.get_rect(), border_size, top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)
            self.blit(surface, rectangle)

        elif padding + border_size > 0:
            if border_color is not None:
                # Draw border
                surface = pygame.Surface((rectangle.width, rectangle.height), pygame.SRCALPHA)
                self.rect(surface, border_color, surface.get_rect(), border_size, top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)
                self.blit(surface, rectangle)
            # Draw rectangle
            inside_rectangle = rectangle.copy()
            inside_rectangle.x += border_size + padding
            inside_rectangle.y += border_size + padding
            inside_rectangle.width -= 2 * (border_size + padding)
            inside_rectangle.height -= 2 * (border_size + padding)

            surface = pygame.Surface((inside_rectangle.width, inside_rectangle.height), pygame.SRCALPHA)

            self.rect(surface, color, surface.get_rect(), 0, top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)
            self.blit(surface, inside_rectangle)

        else:
            surface = pygame.Surface((abs(rectangle.width), abs(rectangle.height)), pygame.SRCALPHA)
            self.rect(surface, color, surface.get_rect(), border_size, top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)
            self.blit(surface, rectangle)


    def rect(self, surface, color, rect, border_size=0, top_left=None, top_right=None, bottom_left=None, bottom_right=None):
        if str(pygame.version.ver) == '2.0.0':
            pygame.draw.rect(surface
                , color
                , rect
                , width=border_size
                , border_top_left_radius=top_left
                , border_top_right_radius=top_right
                , border_bottom_left_radius=bottom_left
                , border_bottom_right_radius=bottom_right)
        else:
            pygame.draw.rect(surface, color, rect, border_size)

            
    def new_blit_rect(self, pos_x, pos_y, width, height, background_color, border_color=None, Alpha=None, corners=None, border_radius=None, border_size=3):
        '''
        New blit_rect method, usefull for pygame 2.0
        It could display rounded corners
        '''
        if background_color is None:
            return
        if Alpha is None:
            Alpha = 225    # Half transparency
        if border_radius is None:
            if self.colorset['border-radius'] == 'max':
                border_radius = int(height / 2)
            else:
                border_radius = int(self.colorset['border-radius'])

        top_left = 0
        top_right = 0
        bottom_left = 0
        bottom_right = 0

        if corners in ('Top', 'TopLeft', 'Left', 'All'):
            top_left = border_radius

        if corners in ('Top', 'TopRight', 'Right', 'All'):
            top_right = border_radius

        if corners in ('Bottom', 'BottomLeft', 'Left', 'All'):
            bottom_left = border_radius

        if corners in ('Bottom', 'BottomRight', 'Right', 'All'):
            bottom_right = border_radius
        
        if border_color is not None:
            shape_surf = pygame.Surface((width - border_size * 4, height - border_size * 4), pygame.SRCALPHA)

            self.rect(shape_surf
                    , (background_color[0], background_color[1], background_color[2], Alpha)
                    , shape_surf.get_rect()
                    , top_left = top_left - border_size
                    , top_right = top_right - border_size
                    , bottom_left = bottom_left - border_size
                    , bottom_right = bottom_right - border_size
                )
            self.screen.blit(shape_surf, (pos_x + border_size * 2, pos_y + border_size * 2, width + border_size * 2, height + border_size * 2))

            shape_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect(shape_surf
                , (border_color[0], border_color[1], border_color[2])
                , shape_surf.get_rect()
                , border_size
                , top_left = top_left
                , top_right = top_right
                , bottom_left = bottom_left
                , bottom_right = bottom_right
            )
            self.screen.blit(shape_surf, (pos_x, pos_y, width, height))

        else:
            shape_surf = pygame.Surface((width, height), pygame.SRCALPHA)

            self.rect(shape_surf
                    , (background_color[0], background_color[1], background_color[2], Alpha)
                    , shape_surf.get_rect()
                    , top_left = top_left
                    , top_right = top_right
                    , bottom_left = bottom_left
                    , bottom_right = bottom_right
                )
            self.screen.blit(shape_surf, (pos_x, pos_y, width, height))


    def div_color(self, component, div):
        '''
        Divide component of color
        Maximum is 255
        '''
        return int(min(255, component * div))

    def menu_color(self, color, div=1.5, index=None):
        '''
        Return color
        '''
        if index is None or index % 2 == 1:
            return (self.div_color(color[0], div)
                    , self.div_color(color[1], div)
                    , self.div_color(color[2], div)
                    )
        return color

    def invert_color(self, color):
        '''
        Return inverted color
        '''

        return (255 - int(color[0]), 255 - color[1], 255 - color[2])

    def slider(self, title, value, minimum, maximum, step=1, diviser=1, bar_color=None, dot_color=None, text_color=None):
        '''
        Display a slider
        '''
        if bar_color is None:
            bar_color = self.colorset['menu-buttons']
        if dot_color is None:
            dot_color = self.colorset['menu-shortcut']
        if text_color is None:
            text_color = self.colorset['menu-text-black']
        border_color = self.colorset['menu-border']

        pos_x = int(self.res_x / 4)
        pos_y = int(self.res_y / 16 * 6)
        width = int(self.res_x / 2)
        height = int(self.res_y / 4)
        border_size = 10
        margin = int(self.res_x / 64)

        border_radius = int(height / 8)

        border_rect = pygame.Rect(pos_x, pos_y, width, height)
        title_rect = pygame.Rect(pos_x, pos_y, width, height / 4 + 2 * border_size)
        value_rect = pygame.Rect(pos_x, title_rect.bottom - 2 * border_size, width, height - title_rect.height + 2 * border_size)
        bar = pygame.Rect(value_rect.x + margin, value_rect.y + int(value_rect.height * 4 / 6), value_rect.width - 2 * margin, margin)

        border_radius -= border_size

        self.new_blit_rect2(title_rect, self.colorset['menu-buttons'], corners='Top', border_radius=border_radius, border_size=border_size, alpha=255)
        self.new_blit_rect2(value_rect, self.colorset['menu-selected'], corners='Bottom', border_radius=border_radius, border_size=border_size, alpha=255)

        if border_color is not None:
            # Blit border
            border_radius += border_size
            self.blit_border(border_rect, border_color, border_size, corners='All', border_radius=border_radius, alpha=255)
        self.blit_text2(title, title_rect, color=self.colorset['menu-text-black'])

        pygame.draw.rect(self.screen, bar_color, bar)
        pygame.draw.circle(self.screen, bar_color , (bar.x, bar.y + int(bar.height / 2)), int(bar.height / 2))
        pygame.draw.circle(self.screen, bar_color, (bar.x + bar.width, bar.y + int(bar.height / 2)), int(bar.height / 2))

        if (minimum / diviser) % 1:
            self.blit_text(f'{(minimum / diviser):.1f}', bar.x, bar.y - self.res_y_8, self.res_y_8, self.res_y_8, text_color, align='Left')
        else:
            self.blit_text(f'{int(minimum / diviser)}', bar.x, bar.y - self.res_y_8, self.res_y_8, self.res_y_8, text_color, align='Left')
        self.blit_text(str(int(maximum / diviser)), bar.x + bar.width - self.res_y_8, bar.y - self.res_y_8, self.res_y_8, self.res_y_8, text_color, align='Right')

        rect = pygame.Rect((pos_x - border_size, pos_y - border_size, width + 2 * border_size \
                    , height + 2 * border_size))

        sub = self.screen.subsurface(rect)
        screenshot = pygame.Surface((rect.width, rect.height))
        screenshot.blit(sub, (0, 0))

        click_zones = {}
        width = int(bar.w / (1 + ((maximum - minimum) / step)))
        for segment in range(minimum, maximum + step, step):
            value_offset = 100 * ((segment - minimum) / (maximum - minimum))
            dot_x = bar.x + int(bar.width / 100 * value_offset)
            click_zones[f'S{segment}'] = (dot_x - int(width / 2), bar.y, width, bar.height)

        while True:
            self.blit(screenshot, (rect.x, rect.y))
            value_offset = 100 * ((value - minimum) / (maximum - minimum))
            dot_x = bar.x + int(bar.width / 100 * value_offset)
            dot_y = bar.y + int(bar.height / 2)

            pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y), margin)

            self.blit_text(f"{(value / diviser):.1f}".replace('.0', ''), bar.centerx - self.res_y_16, bar.top - self.res_y_8, self.res_y_8, self.res_y_8, text_color)

            self.update_screen((rect))
            # Read input
            key_pressed = self.rpi.listen_inputs(['arrows'], ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON', 'VOLUME-UP', 'VOLUME-DOWN', 'escape', 'enter', 'space', 'single-click'], context='editing')

            clicked = self.is_clicked(click_zones, key_pressed)

            if key_pressed in LEFT_KEYS:
                value = max(minimum, int(value - step))
            elif key_pressed in RIGHT_KEYS:
                value = min(maximum, int(value + step))
            elif key_pressed in ENTER_KEYS:
                return value
            elif key_pressed in ESCAPE_KEYS:
                return 'escape'
            elif clicked and clicked.startswith('S'):
                value = int(clicked[1::])

    def dropdown(self, pos_x, pos_y, values, special=None, navigate=None, width=None):
        '''
        Display a dropdown
        '''

        selected = 1
        max_items = 9
        moy = int((max_items + 1) / 2)
        border_size = 3
        nb_elements = len(values)
        if width is None:
            width = int(3 * self.res_x_16)
        else:
            width = int(width)
        height = self.res_y_16

        if nb_elements > max_items:
            add_arrows = True
        else:
            add_arrows = False

        index = 0
        if special == 'dmdColor':
            index = 0
            for color in values:
                index += 1
                if color == navigate:
                    selected = index
                    break
        else:
            for value in values:
                index += 1
                if navigate == value[0]:
                    selected = index
                    break

        border_radius = self.get_radius(int(height / 2))
        while True:
            key_pressed = ''
            click_zones = {}
            if selected > nb_elements:
                selected = 1
            elif selected < 1:
                selected = nb_elements

            offset = 0
            if add_arrows:
                offset = 1

            rect = pygame.Rect(pos_x - border_size, pos_y - border_size, width + 2 * border_size, height * ( 2 * offset + min(nb_elements, max_items)) + 2 * border_size)
            self.new_blit_rect2(rect, self.colorset['menu-text-black'], alpha=255, corners='All', border_radius=border_radius)

            i_rect = pygame.Rect(rect.x + border_size, rect.y + border_size, rect.w - 2 * border_size, height)
            if add_arrows:
                click_zones['scrollup'] = self.dropdown_item(i_rect, True, "^", special='arrowFirst')
                i_rect.y = i_rect.bottom

            i = 0

            for value in values:
                i += 1
                if nb_elements <= max_items:
                    Go = True
                else:
                    if selected - moy <= 0:
                        if i <= max_items:
                            Go = True
                        else:
                            Go = False
                    elif selected + moy > nb_elements:
                        if i >= nb_elements + 1 - max_items:
                            Go = True
                        else:
                            Go = False
                    elif selected - moy + 1 <= i <= selected + moy - 1:
                        Go = True
                    else:
                        Go = False

                if Go:
                    if offset == 0 and i == 1:
                        FirstLast = 'First'
                    elif offset == 0 and i == nb_elements:
                        FirstLast = 'Last'
                    else:
                        FirstLast = None

                    if special == 'font':
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[1], special='font', FirstLast=FirstLast)
                    elif special == 'pattern':
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[1], special='pattern', FirstLast=FirstLast)
                    elif special == 'dmdColor':
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value, FirstLast=FirstLast)
                    else:
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[1], FirstLast=FirstLast)
                    i_rect.y = i_rect.bottom


            if add_arrows:
                click_zones['scrolldown'] = self.dropdown_item(i_rect, True, "v", special='arrowLast')

            #self.update_screen(rect=(rect.x, rect.y, rect.w, rect.h))
            self.update_screen()

            # Read input
            key_pressed = self.rpi.listen_inputs(['arrows'], ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON', 'VOLUME-UP', 'VOLUME-DOWN', 'escape', 'enter', 'space', 'single-click'], context='editing')

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, 0, 0)

            if clicked:
                if clicked == 'scrolldown':
                    selected += 1
                elif clicked == 'scrollup':
                    selected -= 1
                else:
                    selected = int(clicked)
                    if special == 'dmdColor':
                        return values[selected - 1]

                    return values[selected - 1][0]
            elif key_pressed in ENTER_KEYS:
                if special == 'dmdColor':
                    return values[selected - 1]

                return values[selected - 1][0]
            elif key_pressed in ESCAPE_KEYS:
                return 'escape'

    def dropdown_item(self, rect, selected, value, special=False, FirstLast=None):
        '''
        Display drop down item
        '''
        if special == 'arrowFirst':
            color = self.colorset['menu-alternate']
            FirstLast = 'First'
        elif special == 'arrowLast':
            color = self.colorset['menu-alternate']
            FirstLast = 'Last'
        elif selected:
            color = self.colorset['menu-selected']
        else:
            color = self.colorset['menu-buttons']

        if FirstLast == 'First':
            corners = 'Top'
        elif FirstLast == 'Last':
            corners = 'Bottom'
        else:
            corners = 'None'

        self.new_blit_rect2(rect, color, corners=corners)

        if selected:
            text_color = self.colorset['menu-text-white']
        else:
            text_color = self.colorset['menu-text-black']

        if special == 'font':
            minus = int(rect.height * 0.1)
            rect2 = rect.copy()
            rect2.y += minus
            rect2.height -= 2 * minus
            self.blit_text2(value, rect2, text_color, font=f'{value}')
        elif special == 'pattern':
            self.blit_text2(value, rect, text_color, image=f'patterns/{value}')
        else:
            self.blit_text2(value, rect, text_color)
        return (rect.x, rect.y, rect.w, rect.h)

    def display_button(self, selected, text, special):
        '''
        Display buttons at bottom of menus : escape, save, continue, ...
        '''

        width = int(self.res['x'] / 8)

        if special == 'escape':
            pos_x = int(self.res['x'] / 8)
        elif special == 'refresh':
            pos_x = int(self.res['x'] / 2 - width / 2)
        #elif special == 'return':
        else:
            pos_x = int(self.res['x'] * 7 / 8 - width)

        pos_y = int(self.res['y'] / 32 * 29)
        height = self.res_y_16

        rect = pygame.Rect(pos_x, pos_y, width, height)

        if selected:
            background_color = self.colorset['menu-selected']
            text_color = self.colorset['menu-text-white']
            border_color = self.colorset['menu-border']
            border_size = self.colorset['border-size']
            padding = self.colorset['padding']
        else:
            background_color = self.colorset['menu-buttons']
            text_color = self.colorset['menu-text-black']
            border_color = None
            border_size = 0
            padding = 0

        if self.colorset['button-radius'] == 'max':
            border_radius = int(height / 2)
        else:
            border_radius = min(int(height / 2), int(self.colorset['button-radius']))

        self.new_blit_rect2(rect, background_color, padding, border_color, border_size, corners='All', border_radius=border_radius)
        self.blit_text2(text, rect, color=text_color)

        return (rect[0], rect[1], rect[2], rect[3])

    def get_radius(self, value):
        if self.colorset['border-radius'] == 'max':
            return int(value)
        elif int(self.colorset['border-radius']) > int(value):
            return int(value)
        else:
            return int(self.colorset['border-radius'])

    def compute_corners(self, item_id, total, selected, collapsed, alternate=False):
        if alternate:
            offset = 2
        else:
            offset = 1

        if collapsed:
            if item_id == selected - offset:
                corners = 'Bottom'
                if item_id <= offset:
                    corners = 'All'
            elif item_id == selected + offset:
                corners = 'Top'
                if item_id > total - offset:
                    corners = 'All'
            elif item_id <= offset:
                corners = 'Top'
            elif item_id > total - offset:
                corners = 'Bottom'
            else:
                corners = 'None'
            return corners
        else:
            return 'All'


    def adapt_corners(self, corners, operation, operation2=None):
        if operation == 'AddRight':
            if corners == 'All' and operation2 == 'NotLeft':
                return 'Right'
            elif corners == 'All' and operation2 == 'NotRight':
                return 'Left'
            elif corners == 'All':
                return corners
            elif corners == 'Top':
                if operation2 == 'NotLeft':
                    return 'Right'
                else:
                    return 'NotBottomLeft'
            elif corners == 'Bottom':
                if operation2 == 'NotLeft':
                    return 'Right'
                else:
                    return 'NotTopLeft'
            elif corners == 'None':
                return 'Right'
            else:
                return corners
        elif operation == 'NotRight':
            if corners == 'Bottom':
                return 'BottomLeft'
            elif corners == 'Top':
                return 'TopLeft'
            elif corners == 'All':
                return 'Left'
            else:
                return corners
        elif operation == 'NotLeft':
            if corners == 'Bottom':
                return 'BottomRight'
            elif corners == 'Top':
                return 'TopRight'
            elif corners == 'All':
                return 'Right'
            else:
                return corners
        else:
            return corners

    def pouet(self):
        self.update_screen()
        self.wait_touch()

    #@debug
    def st_item(self, shortcut, text, rect, padding=0, border_size=0, border_color=None, alpha=None, divider=None, corners=None):
        '''
        Display one line : Shortcut | Text
        Shortcut and text must be :
            (background_color, text_value, text_color)
        '''

        s_rect = rect.copy()
        s_rect.width = s_rect.height

        t_rect = pygame.Rect(s_rect.right, s_rect.y, rect.w - s_rect.w, s_rect.h)

        if border_size + padding > 0:
            minus = border_size + padding
            if self.colorset['border-radius'] == 'max':
                border_radius = int(rect.h / 2) - minus
            else:
                border_radius = int(self.colorset['border-radius']) - minus

            border_radius = max(border_radius, 0)

            if border_color is not None:
                # Blit border
                self.blit_border(rect, border_color, border_size, corners=corners)

            inside_rect = pygame.Rect(rect.x + minus, rect.y + minus, rect.w - 2 * minus, rect.h - 2 * minus)
            self.new_blit_rect2(inside_rect, text[0], alpha=alpha, corners=corners, border_radius=border_radius)

            # Compute missing values
            if shortcut[1] is not None:

                inside_rect.width = inside_rect.height + minus
                # Display shortcut
                self.new_blit_rect2(inside_rect, shortcut[0], alpha=alpha, corners=self.adapt_corners(corners, 'AddRight'), border_radius=border_radius)
                self.blit_text2(shortcut[1], s_rect, color=shortcut[2])
                self.blit_text2(text[1], t_rect, color=text[2], align='Left', divider=divider)
            else:
                self.blit_text2(text[1], rect, color=text[2], align='Center', divider=divider)

        elif shortcut[1] is None:
            # Display text
            self.new_blit_rect2(rect, text[0], alpha=alpha, corners=corners)
            self.blit_text2(text[1], rect, color=text[2], align='Center', divider=divider)
        else:
            # Display text
            self.new_blit_rect2(rect, text[0], alpha=alpha, corners=self.adapt_corners(corners, 'All'))
            self.blit_text2(text[1], t_rect, color=text[2], align='Left', divider=divider)

            # Display shortcut
            self.new_blit_rect2(s_rect, shortcut[0], alpha=alpha, corners='All')
            self.blit_text2(shortcut[1], s_rect, color=shortcut[2], divider=divider)


    #@debug
    def svt_item(self, shortcut, value, text, rect, padding=0, border_size=0, border_color=None, alpha=None, ratio=0.2):
        '''
        Display one line : Shortcut | Value | Text
        Shortcut, value and text must be :
            (background_color, text_value, text_color)
        '''

        s_rect = rect.copy()
        s_rect.width = s_rect.height

        v_rect = pygame.Rect(s_rect.right, s_rect.y, int(rect.w * ratio), s_rect.h)
        t_rect = pygame.Rect(v_rect.right, s_rect.y, rect.w - v_rect.w - s_rect.w, s_rect.h)

        if border_size + padding > 0:
            minus = border_size + padding
            if border_color is not None:
                # Blit border
                self.blit_border(rect, border_color, border_size, corners='All')
            if self.colorset['border-radius'] == 'max':
                border_radius = int(rect.h / 2) - minus
            else:
                border_radius = int(self.colorset['border-radius']) - minus

            border_radius = max(border_radius, 0)

            inside_rect = pygame.Rect(rect.x + minus, s_rect.y + minus, rect.w - 2 * minus, s_rect.h - 2 * minus)

            # Display text
            self.new_blit_rect2(inside_rect, text[0], alpha=alpha, corners='All', border_radius=border_radius)
            self.blit_text2(text[1], t_rect, color=text[2], align='Left')

            # Display value
            inside_rect = pygame.Rect(s_rect.x + minus, v_rect.y + minus, v_rect.w + s_rect.w - minus, inside_rect.h)
            self.new_blit_rect2(inside_rect, value[0], alpha=alpha, border_radius=border_radius, corners='All')
            self.blit_text2(value[1], v_rect, color=value[2])

            # Display shortcut
            inside_rect = pygame.Rect(s_rect.x + minus, s_rect.y + minus, s_rect.w - minus, s_rect.h - 2 * minus)
            self.new_blit_rect2(inside_rect, shortcut[0], alpha=alpha, corners='All', border_radius=border_radius)
            self.blit_text2(shortcut[1], s_rect, color=shortcut[2])
        else:
            # Display text
            self.new_blit_rect2(rect, text[0], alpha=alpha, corners='All')
            self.blit_text2(text[1], t_rect, color=text[2], align='Left')

            # Display value
            v_rect.x -= s_rect.w
            v_rect.w += s_rect.w
            self.new_blit_rect2(v_rect, value[0], alpha=alpha, corners='All')
            v_rect.x += s_rect.w
            v_rect.w -= s_rect.w
            self.blit_text2(value[1], v_rect, color=value[2], align='Center')

            # Display shortcut
            self.new_blit_rect2(s_rect, shortcut[0], alpha=alpha, corners='All')
            self.blit_text2(shortcut[1], s_rect, color=shortcut[2])

    def game_item(self, item, favorite):
        '''
        Special item for favorite games
        2 columns

        item is : (item_id, total, selected)
        favorite is Shortcut / Game name / value=True/False
        '''

        width = 2 * self.res_x_16
        height = int(22 * self.res_y_16 / item[1])

        pos_y = 3 * self.res_y_16 + height * ((item[0] - 1) % (item[1] / 2))

        if item[0] % 2 == 1:
            pos_x = self.mid_x - self.res_x_16 - width
        else:
            pos_x = self.mid_x + self.res_x_16

        pos_y = 3 * self.res_y_16 + height * (int((item[0] + 1) / 2) - 1)
    

        if item[0] == item[2]:
            value_bg_color = self.menu_color(self.colorset['menu-selected'])
        else:
            value_bg_color = self.menu_color(self.colorset['menu-buttons'], index=(item[0] + 1) // 2 + 1)

        radius = self.get_radius(height / 2)

        if item[0] == item[2]:
            minus = self.colorset['border-size'] + self.colorset['padding']
            # Selected item
            if favorite[2]:
                shortcut_bg_color = self.colorset['menu-ok']
            else:
                shortcut_bg_color = self.colorset['menu-ko']
            value_bg_color = self.menu_color(self.colorset['menu-selected'])
            shortcut_text_color = self.colorset['menu-text-white']
            value_text_color = self.colorset['menu-text-white']

            if self.colorset['border-radius'] == 'max':
                border_radius = int(height / 2) - minus
            else:
                border_radius = int(self.colorset['border-radius']) - minus

            border_radius = max(border_radius, 0)

            # Display border
            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.blit_border(rect, self.colorset['menu-border'] , self.colorset['border-size'], corners='All')

            # Display value
            rect = pygame.Rect(pos_x + minus
                    , pos_y + minus
                    , width - 2 * minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, value_bg_color, corners='All', border_radius=border_radius)
            # To keep same text size
            rect2 = pygame.Rect(pos_x + height, pos_y, width - height, height)
            self.blit_text2(favorite[1], rect2, color=value_text_color)

            # Display shortcut
            rect = pygame.Rect(pos_x + minus
                    , pos_y + minus
                    , height - minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, shortcut_bg_color, corners='All', border_radius=border_radius)
            # To keep same text size
            rect2 = pygame.Rect(pos_x, pos_y, height, height)
            self.blit_text2(favorite[0], rect2, color=shortcut_text_color)

        else:
            corners = self.compute_corners(item[0], item[1], item[2], True, alternate=True)
            # Change color according to index
            if favorite[2]:
                shortcut_bg_color = self.colorset['menu-ok']
            else:
                shortcut_bg_color = self.colorset['menu-ko']
            shortcut_text_color = self.colorset['menu-text-black']
            value_text_color = self.colorset['menu-text-black']

            # Display value
            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.new_blit_rect2(rect, value_bg_color, corners=corners, border_radius=radius)
            self.blit_text2(favorite[1], rect, color=value_text_color)

            # Display shortcut
            rect.width = rect.h
            self.new_blit_rect2(rect, shortcut_bg_color, corners=self.adapt_corners(corners, 'AddRight'), border_radius=radius)
            self.blit_text2(favorite[0], rect, color=shortcut_text_color)

        return (pos_x, pos_y, width, height)

    def button_item(self, item, value, text, alpha):
        '''
        Special item for buttons
        Text and value have same width
        2 columns

        item is : (item_id, total, selected)
        '''

        if alpha is None:
            alpha = self.alpha

        width = self.mid_x - 2 * self.res_x_16
        height = int(22 * self.res_y_16 / item[1])

        if item[0] > int(item[1] / 2):
            pos_x = self.res_x_16 + self.mid_x
        else:
            pos_x = self.res_x_16

        pos_y = 3 * self.res_y_16 + height * ((item[0] - 1) % (item[1] / 2))

        if item[0] % 2 == 1:
            pos_x = self.res_x_16
        else:
            pos_x = self.res_x_16 + self.mid_x

        pos_y = 3 * self.res_y_16 + height * (int((item[0] + 1) / 2) - 1)
    

        if item[0] == item[2]:
            minus = self.colorset['border-size'] + self.colorset['padding']
            # Selected item
            item_bg_color = self.menu_color(self.colorset['menu-selected'])
            value_bg_color = self.menu_color(self.colorset['menu-selected'])
            item_text_color = self.colorset['menu-text-white']
            value_text_color = self.colorset['menu-text-white']

            # Display border
            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.blit_border(rect, self.colorset['menu-border'] , self.colorset['border-size'], corners='All')

            # Display text
            rect = pygame.Rect(pos_x + minus
                    , pos_y + minus
                    , int(width / 2) - minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, item_bg_color, alpha=alpha, corners='Left')
            # To keep same text size
            rect2 = pygame.Rect(pos_x, pos_y, int(width / 2), height)
            self.blit_text2(text, rect2, color=value_text_color)

            # Display value
            rect = pygame.Rect(pos_x + int(width / 2)
                    , pos_y + minus
                    , int(width / 2) - minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, value_bg_color, alpha=alpha, corners='Right')
            # To keep same text size
            rect2 = pygame.Rect(pos_x + int(width / 2), pos_y, int(width / 2), height)
            self.blit_text2(value, rect2, color=item_text_color)
        else:
            corners = self.compute_corners(item[0], item[1], item[2], collapsed=True, alternate=True)

            # Change color according to index
            item_bg_color = self.menu_color(self.colorset['menu-buttons'], index=item[0] + 1)
            value_bg_color = self.menu_color(self.colorset['menu-shortcut'], index=item[0] + 1)
            item_text_color = self.colorset['menu-text-black']
            value_text_color = self.colorset['menu-text-black']

            # Display text
            rect = pygame.Rect(pos_x, pos_y, int(width / 2), height)
            self.new_blit_rect2(rect, item_bg_color, alpha=alpha, corners=self.adapt_corners(corners, 'NotRight'))
            self.blit_text2(text, rect, color=value_text_color)

            # Display value
            rect = pygame.Rect(pos_x + int(width / 2), pos_y, int(width / 2), height)
            self.new_blit_rect2(rect, value_bg_color, alpha=alpha, corners=self.adapt_corners(corners, 'NotLeft'))
            self.blit_text2(value, rect, color=item_text_color)

        return (pos_x, pos_y, width, height)

    def player_item(self, item, shortcut, name, special, alpha=None):
        '''
        Display Players' menu items
        item is : (item_id, total, selected)
        '''

        if alpha is None:
            alpha = self.alpha

        click_zones = []

        min_y = 3 * self.res_y_16
        max_y = 13 * self.res_y_16

        pos_x = 4 * self.res_x_16
        width = self.res_x - 2 * pos_x

        height = min(int(self.res['y'] / 14), int((max_y - min_y) / item[1]))
        pos_y = min_y + height * (item[0] - 1)

        minus = self.colorset['border-size'] + self.colorset['padding']

        shortcut_bg_color = self.colorset['menu-shortcut']

        if special == 'first':
            minus_bg_color = self.colorset['menu-inactive']
        else:
            minus_bg_color = self.colorset['menu-ko']
        
        if special == 'last':
            plus_bg_color = self.colorset['menu-inactive']
        else:
            plus_bg_color = self.colorset['menu-ok']


        radius = self.get_radius(height / 2)

        if item[0] == item[2]:
            shortcut_text_color = self.colorset['menu-text-black']
            text_color = self.colorset['menu-text-white']

            inside_y = pos_y + minus
            inside_h = height - 2 * minus

            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.blit_border(rect, self.colorset['menu-border'], self.colorset['border-size'], corners='All')

            # Display Firstname
            firstname_x = pos_x + minus
            rect = pygame.Rect(firstname_x, inside_y, width - 3 * height - minus, inside_h)
            self.new_blit_rect2(rect, self.colorset['menu-selected'], alpha=alpha, corners='Left')

            pnj_x = rect.x + rect.width
            rect.x += height
            rect.width -= height
            self.blit_text2(name, rect, color=text_color, align='Left')

            # Display Shortcut
            shortcut_x = pos_x + minus
            rect = pygame.Rect(shortcut_x, inside_y, height - minus, inside_h)
            self.new_blit_rect2(rect, shortcut_bg_color, alpha=alpha, corners='All')
            self.blit_text2(shortcut, rect, color=shortcut_text_color)

            # Pnj box
            rect = pygame.Rect(pnj_x, inside_y, height, inside_h)
            self.new_blit_rect2(rect, shortcut_bg_color, alpha=alpha)
            self.blit_text2('PNJ', rect, color=text_color)

            # Plus box
            plus_x = pnj_x + height
            rect = pygame.Rect(plus_x, inside_y, height, inside_h)
            self.new_blit_rect2(rect, plus_bg_color, alpha=alpha)
            self.blit_text2('+', rect, color=text_color)

            # Minus box
            minus_x = plus_x + height
            rect = pygame.Rect(minus_x, inside_y, height - minus, inside_h)
            self.new_blit_rect2(rect, minus_bg_color, alpha=alpha, corners='Right')
            self.blit_text2('-', rect, color=text_color)

        else:
            corners = self.compute_corners(item[0], item[1], item[2], collapsed=True)
            shortcut_text_color = self.colorset['menu-text-white']
            text_color = self.colorset['menu-text-black']
            shortcut_color = self.menu_color(shortcut_bg_color, index=item[0] + 1)
            plus_color = self.menu_color(plus_bg_color, index=item[0] + 1)
            minus_color = self.menu_color(minus_bg_color, index=item[0] + 1)
            player_color = self.menu_color(self.colorset['menu-buttons'], index=item[0] + 1)

            # Display Firstname
            firstname_x = pos_x + height
            rect = pygame.Rect(firstname_x - height, pos_y, width - 3 * height, height)
            self.new_blit_rect2(rect, player_color, alpha=alpha, corners='Left', border_radius=radius)
            rect = pygame.Rect(firstname_x, pos_y, width - 4 * height, height)
            self.blit_text2(name, rect, color=text_color, align='Left')

            # Display Shortcut
            rect = pygame.Rect(pos_x, pos_y, height, height)
            self.new_blit_rect2(rect, shortcut_color, alpha=alpha, corners='All', border_radius=radius)
            self.blit_text2(shortcut, rect, color=shortcut_text_color)

            # Pnj box
            pnj_x = firstname_x + width - 4 * height
            rect = pygame.Rect(pnj_x, pos_y, height, height)
            self.new_blit_rect2(rect, shortcut_color, alpha=alpha)
            self.blit_text2('PNJ', rect, color=text_color)

            # Plus box
            plus_x = pnj_x + height
            rect = pygame.Rect(plus_x, pos_y, height, height)
            self.new_blit_rect2(rect, plus_color, alpha=alpha)
            self.blit_text2('+', rect, color=text_color)

            # Minus box
            minus_x = plus_x + height
            rect = pygame.Rect(minus_x, pos_y, height, height)
            self.new_blit_rect2(rect, minus_color, alpha=alpha, corners='Right', border_radius=radius)
            self.blit_text2('-', rect, color=text_color)

        if special != 'first':
            click_zones.append(('-|' + shortcut, (minus_x, pos_y, height, height)))
        if special != 'last':
            click_zones.append(('+|' + shortcut, (plus_x, pos_y, height, height)))

        click_zones.append(('/|' + shortcut, (pnj_x, pos_y, height, height)))
        click_zones.append((shortcut, (firstname_x, pos_y, width - 4 * height, height)))


        return click_zones

    def logo_item(self, item, logo, item_per_line, align, limit_height=None, Alpha=None, menu=False, border_radius=50):
        '''
        Print games' logo
        '''

        if align == 'Left':
            pos_x = int(self.res_x_16 / 2)
            max_x = 8 * self.res_x_16 - pos_x
        else:
            pos_x = 3 * self.res_x_16
            max_x = 13 * self.res_x_16
        max_w = max_x - pos_x

        pos_y = 3 * self.res_y_16
        max_y = 13 * self.res_y_16
        max_h = max_y - pos_y

        item_per_col = (item[1] // item_per_line) + 1

        # Max size of logo
        height = min(max_w // item_per_line, max_h // item_per_col)

        # To center logo on available surface
        pos_x += (max_w - item_per_line * height) / 2
        if menu:
            pos_y = (self.res_y - height) / 2
        else:
            pos_y += (max_h - item_per_col * height) / 2

        # Position of the logo
        pos_y += ((item[0] - 1) // item_per_line) * height
        pos_x += ((item[0] - 1) % item_per_line) * height

        selected_color = self.colorset['menu-selected']
        inactive_color = self.colorset['menu-inactive']
        border_color = self.colorset['menu-border']

        rect = pygame.Rect(pos_x, pos_y, height, height)
        if item[0] == item[2]:
            # Selected logo
            if self.colorset['border-size'] + self.colorset['padding'] > 0:
                minus = self.colorset['border-size'] + self.colorset['padding']
                if border_color is not None:
                    # Blit border
                    self.blit_border(rect, border_color, int(self.colorset['border-size']), border_radius=border_radius, corners='All')
                rect2 = pygame.Rect(pos_x + minus, pos_y + minus, height - 2 * minus, height - 2 * minus)
                border_radius -= self.colorset['padding']
                border_radius -= self.colorset['border-size']

            else:
                rect2 = rect
            self.new_blit_rect2(rect2, selected_color, alpha=Alpha, border_radius=border_radius, corners='All')
        else:
            # Not selected
            self.new_blit_rect2(rect, inactive_color, alpha=20, border_radius=border_radius, corners='All')

        self.display_image(self.file_class.get_full_filename(f'logos_menu/{logo}', 'images'), pos_x, pos_y, height, height, True, False, False)

        return (pos_x, pos_y, height, height)

    def menu_item(self, item, value, space=0, align=None, collapsed=False, exit=True, special=None, border_color=None, valid=None, item_per_line=None, limit_height=None, divider=None):
        '''
        Display menu's item (new version)

        item is : (item_id, total, selected)
        value is : (shortcut, text, button_type, value)
        '''

        padding = self.margin
        vertical_margin = 0 # Margin between 2 lines

        # ItemType:
        #   BTN_CHECK    (1) : Check Box
        #   BTN_CHOICE   (2) : Text (not editable)
        #   BTN_VALUE    (3) : Text (editable)
        #   BTN_LOGO     (4) : img
        #   BTN_DROPDOWN (5) : Drop down

        # Base display
        min_x = self.res_x_16
        if item[1] > 8:
            min_y = 2 * self.res_y_16
        else:
            min_y = 3 * self.res_y_16
        max_x = 14 * self.res_x_16

        if exit:
            max_y = 12 * self.res_y_16      # 3 / 16 reserved for title and 3 / 16 for other buttons
        else:
            max_y = 13 * self.res_y_16      # Only 3 / 16 reserved for title

        if item[1] >= 10:                   # No blank between items if > 9 items
            collapsed = True
        else:
            vertical_margin = int(max_y / 144) * 2

        height = min(self.res_y_15, int(max_y / item[1]))

        if align in ('Full', 'Values'):
            pos_x = int(3 * self.res_x_16)
            width = int(self.res['x'] - pos_x - height - pos_x)
        elif align == 'Left':
            pos_x = int(self.res['x'] * 1 / 16)
            width = int(self.res['x'] * 7 / 16 - min_x - height)
        elif align == 'Half':
            pos_x = int(self.res['x'] * 6 / 16)
            width = int(self.res['x'] * 4 / 16 - height)
        else:
            pos_x = int(self.res['x'] * 4 / 16)
            width = int(self.res['x'] / 2 - min_x - height)

        pos_y = min_y + (vertical_margin + height) * (item[0] + space - 1)

        if item[0] == item[2]:
            #shortcut_bg_color = self.menu_color(self.colorset['menu-selected'])
            shortcut_bg_color = self.colorset['menu-selected']
            shortcut_text_color = self.colorset['menu-text-black']
            value_bg_color = self.colorset['menu-selected']
            value_text_color = self.colorset['menu-text-white']
            text_bg_color = self.colorset['menu-selected']
            text_text_color = self.colorset['menu-text-black']
            border_color = self.colorset['menu-border']
            border_size = int(self.colorset['border-size'])
            padding = int(self.colorset['padding'])
            corners = 'All'
        else:
            shortcut_bg_color = self.colorset['menu-shortcut']
            shortcut_text_color = self.colorset['menu-text-black']
            text_bg_color = self.menu_color(self.colorset['menu-buttons'])
            text_text_color = self.colorset['menu-text-black']
            if collapsed:
                text_bg_color = self.menu_color(self.colorset['menu-buttons'], index=item[0] + 1, div=0.5)
                value_bg_color = self.menu_color(self.colorset['menu-shortcut'], index=item[0] + 1)
                value_text_color = self.menu_color(self.colorset['menu-text-black'], index=item[0] + 1)
            else:
                value_bg_color = self.colorset['menu-shortcut']
                value_text_color = self.colorset['menu-text-black']

            border_color = None
            border_size = 0
            padding = 0
            corners = self.compute_corners(item[0], item[1], item[2], collapsed)

        if value[2] == BTN_CHECK and value[3]:
            shortcut_bg_color = self.colorset['menu-ok']
        elif value[2] == BTN_CHECK:
            shortcut_bg_color = self.colorset['menu-ko']
        elif value[2] in (BTN_VALUE, BTN_DROPDOWN):
            shortcut_bg_color = self.colorset['menu-alternate']

        shortcut = (shortcut_bg_color, value[0], shortcut_text_color)
        text = (text_bg_color, value[1], value_text_color)
        rect = pygame.Rect(pos_x, pos_y, width, height)
        if value[2] == BTN_CHOICE:
            # Background_value, text_value, text_color
            self.st_item(shortcut, text, rect, padding, border_size, border_color, divider=divider, corners=corners)
        else:
            text = (text_bg_color, value[1], text_text_color)
            value = (value_bg_color, value[3], value_text_color)
            self.svt_item(shortcut, value, text, rect, padding, border_size, border_color)

        return (pos_x, pos_y, width, height)

    def favorites_servers_menu(self, favorites):
        '''
        Favorites servers
        '''
        selected = 1
        servers = []
        self.dmd.send_text(self.lang.translate('dmd-server-favorites'), tempo = 1)

        for f in favorites.split(', '):
            servers.append(f)

        while True:
            nb_elements = len(servers)
            index = 0

            shortcuts = []
            click_zones = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('favorites-servers', 'enter-valid-url')

            for server in servers:
                index += 1
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), ('', f"Serveur {index}", BTN_VALUE, server), align='Values')
                shortcuts.append(f'F{index}')

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['add'] = self.display_button(nb_elements + 2 == selected, 'add', special='refresh')
            click_zones['save'] = self.display_button(nb_elements + 3 == selected, 'save', special='return')

            self.update_screen()

            # Read input
            key_pressed = self.rpi.listen_inputs(
                    ['alpha', 'num', 'fx', 'math', 'arrows'],
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'])

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, 3, 3)

            #Shortcuts
            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key_pressed in SAVE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 3):
                return ', '.join(servers)

            if key_pressed in PLUS_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2):
                if len(servers) < 8:
                    servers.append('')
                    selected = len(servers)

            elif key_pressed in MINUS_KEYS:
                if len(servers) > 0:
                    servers.pop(selected - 1)

            elif key_pressed in ENTER_KEYS:    # Edition mode
                tmp = self.input_value_item('string', '', 1, 64)
                if tmp != 'escape':
                    servers[selected - 1] = tmp

    def favorites_games_menu(self, favorites):
        '''
        Favorite games
        '''
        selected = 1

        self.dmd.send_text(self.lang.translate('dmd-game-favorites'), tempo = 1)

        game_list = self.get_games_list() + self.get_games_list(category='fun') + self.get_games_list(category='sport')
        nb_elements = len(game_list)
        prefered = []
        for game in favorites.split(', '):
            if game != '':
                prefered.append(game)

        game_list.sort()

        old_selection = None
        refresh = True
        while True:
            index = 0

            shortcuts = []
            games = []
            click_zones = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('favorites-games')

            for game in game_list:
                index += 1
                games.append(game)
                if game in prefered:
                    value = True
                else:
                    value = False
                click_zones[f'F{index}'] = self.game_item((index, nb_elements, selected) \
                        , (f'F{index}', game, value))
                shortcuts.append(f'F{index}')

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            print(f"game_list={game_list}")
            print(f"click_zones={click_zones}")
            if selected <= nb_elements:
                selection = [click_zones[f'F{selected}']]
                if selected > 1:
                    selection.append(click_zones[f'F{selected - 1}'])
                if selected > 2:
                    selection.append(click_zones[f'F{selected - 2}'])
                if selected < nb_elements:
                    selection.append(click_zones[f'F{selected + 1}'])
                if selected < nb_elements - 1:
                    selection.append(click_zones[f'F{selected + 2}'])
            elif nb_elements + 1 == selected:
                selection = [click_zones['escape']]
            elif nb_elements + 2 == selected:
                selection = [click_zones['save']]
            else:
                selection = None

            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=old_selection)
                self.update_screen(rect_array=selection)

            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, 2, 2, item_per_line=2 , left_right=True)

            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key_pressed in SAVE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2):
                return ', '.join(prefered)

            # Keyboard cases
            if (key_pressed in ENTER_KEYS) and selected <= nb_elements:
                if games[selected - 1] in prefered:
                    prefered.remove(games[selected - 1])
                else:
                    prefered.append(games[selected - 1])

            old_selection = selection

    def display_changelog(self, version):
        '''
        Display Changelog
        '''

        try:
            with open(f'{self.config.changelogFile}.{version}', 'r') as changelog:
                text = changelog.readlines()
            action = "move"
            changelog.close()

        except:
            try:
                with open(f'{self.config.changelogFile}.{version}.1', 'r') as changelog:
                    text = changelog.readlines()
                action = "delete"
                changelog.close()

            except:
                return

        self.dmd.send_text(self.lang.translate('news'))

        # Draw bg
        self.display_background()

        # Titles
        self.menu_header('news')
        self.update_screen()

        width = 14 * self.res_x_16
        height = 12 * self.res_y_16
        pos_x = self.res_x_16
        pos_y = 2 * self.res_y_16
        marge_x = int(self.res['x'] / 64)
        marge_y = int(self.res['y'] / 64)

        # New surface
        Surface = pygame.Surface((width, height))
        Surface.set_alpha(192)
        Surface.fill(self.colorset['menu-item-black'])
        self.new_blit_rect(pos_x, pos_y, width, height, self.colorset['menu-buttons'], corners='All', border_radius=50, Alpha=228)

        font_file = self.file_class.get_full_filename('FreeSansBold', 'fonts')
        # Add description
        nb_lines = len(text)
        font = pygame.font.Font(font_file, 50)

        index = 0
        maxsize = 0
        # Find correct font size
        for line in text:
            font_size = font.size(line)
            if font_size[0] > maxsize:
                maxsize = font_size[0]
                longest = index
            index += 1

        scaled_text = self.scale_text(text[longest], width - 2 * marge_x, (height - 2 * marge_y) / nb_lines, divider=1.5, step=0.05, dafont=font_file )
        font_size = scaled_text[0]
        font = pygame.font.Font(font_file, font_size + self.margin)

        if nb_lines > 1:
            interline = (height - nb_lines * font_size - 2 * marge_y) / (nb_lines - 1)
        else:
            interline = 0

        index = 0
        for line in text:
            text = font.render(line.replace('\n', ''), True, self.colorset['menu-text-black'])
            #self.blit(text, [pos_x + marge_x, pos_y + I * (i-1) + marge_y])
            self.blit(text, [pos_x + marge_x, pos_y + marge_y])
            index += 1
            pos_y += font_size + interline

        ################
        # Update screen
        self.update_screen()
        self.wait_touch()

        if action == 'move':
            os.system(f"mv {self.config.changelogFile}.{version} {self.config.changelogFile}.{version}.1")
        elif action == 'delete':
            os.system(f"mv {self.config.changelogFile}.{version}.1 {self.config.changelogFile}.{version}.read")

    def backup_menu(self):
        '''
        Backups menu
        '''
        selected = 1
        self.dmd.send_text(self.lang.translate('dmd-backup-menu'), tempo = 1)

        while True:
            files_list = self.get_backups_list()
            if files_list is None:
                files_list = []

            nb_elements = len(files_list)

            index = 0

            click_zones = {}
            shortcuts = []
            backups = []

            if nb_elements > 3:
                addClean = True
                add = 3
            else:
                addClean = False
                add = 2

            click_zones = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('backups')

            for backup in files_list:
                index += 1
                if index <= 12:
                    if backup[0].startswith('backup/raspydarts'):
                        file_type = 'Full'
                    elif backup[0].startswith('backup/update'):
                        file_type = 'Update'
                    else:
                        index -= 1
                        continue

                    backup_text = f"Version {backup[1]} du {backup[2][6::]}/{backup[2][4:6]}/{backup[2][0:4]} ({backup[3][0:2]}h{backup[3][2::].split('.')[0]} - {file_type})"
                    backups.append((backup[0], backup_text))
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', backup_text, BTN_CHOICE, None))
                    shortcuts.append(f'F{index}')

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            if addClean:
                click_zones['clean'] = self.display_button(nb_elements + 2 == selected, 'clean', special='refresh')
            click_zones['backup'] = self.display_button(nb_elements + add == selected, 'backup', special='return')

            ################
            # Update screen
            self.update_screen()

            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'], events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, add, add)

            # Shotcuts
            if key_pressed in shortcuts:
                selected = int(key_pressed[1::])
                key_pressed = 'enter'

            # Key analysis
            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1) :    # Previous menu
                return 'escape'

            if key_pressed in BACKUP_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + add) : # Make a backup
                self.message(['backing-up'], wait = 100)
                os.system(f"{self.backupscript} b")
                self.message(['backup-done'], wait = 2000)

            elif nb_elements > 3 and (key_pressed in CLEAN_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2)): # Clean backups
                response = self.wait_validation('backup-clean')
                if response:
                    self.message(['cleaning'])
                    pygame.time.wait(1000)
                    os.system(f"{self.backupscript} c")
                    self.message(['clean-done'], wait = 2000)

            elif key_pressed in ENTER_KEYS and 0 < selected <= nb_elements:
                restore = backups[selected - 1][0]
                msg= f"{self.lang.translate('backup-choice')} {backups[selected - 1][1]}"
                response = self.wait_validation(msg)
                if response:
                    response = self.wait_validation("are-you-sure")
                    if response:
                        # Ici
                        self.message(['restoring'])
                        os.system(f"{self.backupscript} r {restore}")
                        self.message(['restore-done'], wait = 2000)
                        response = self.wait_validation(self.lang.translate('need-restart'))
                        if response:
                            return 'restart'

    def input_value_item(self, v_type, value, v_min, v_max, character=None, align='Center', text=None, zero=False):
        '''
        Input value item

        v_type : string, number , numeric(=number + . + , )
        v_min : Min length or min value
        v_max : Maw length or max value
        special : Authorized keys (if string)
        '''
        authorized = ['alpha', 'num', 'arrows']
        limited = None

        if v_type == 'number':
            authorized = ['num', 'arrows', 'math']
            limited = None
        elif v_type == 'pins':
            authorized = ['num', 'arrows']
            limited = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'backspace', 'enter', 'escape']
        elif v_type == 'leds':
            authorized = ['num', 'alpha', 'math', 'arrows']
            limited = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '.', 'backspace', 'enter', 'escape']
        elif v_type == 'string':
            limited = None
        else:
            self.logs.log("ERROR", f"Line 2786 : Unauthorized type: {v_type}")
            return False

        self.save_background()

        value = str(value)
        if character is None:
            if value == '':
                character = ''
            else:
                character = value[-1]

        border_size = 5 * self.colorset['border-size']
        minus = self.colorset['padding'] + border_size
        minus = border_size

        if text is not None:
            rect = pygame.Rect(self.res_x_16 * 6, self.res_y_16 * 6, self.res_x_16 * 4, self.res_y_16 * 4)
            t_rect = pygame.Rect(rect.x + minus, rect.y + minus, rect.w - 2 * minus, self.res_y_16 * 2 - minus)
            v_rect = pygame.Rect(rect.x + minus, t_rect.bottom, rect.w - 2 * minus, self.res_y_16 * 2 - minus)
        else:
            rect = pygame.Rect(self.res_x_16 * 6, self.res_y_16 * 6.5, self.res_x_16 * 4, self.res_y_16 * 3)
            v_rect = pygame.Rect(rect.x + minus, rect.y + minus, rect.w - 2 * minus, self.res_y_16 * 3 - 2 * minus)


        if self.colorset['border-radius'] == 'max':
            border_radius = int(v_rect.h / 2)
        else:
            border_radius = int(self.colorset['border-radius'])

        key = ''
        while True:
            self.blit_border(rect, self.colorset['menu-border'], border_size, corners='All', border_radius=border_radius, alpha=255)
            inside_border_radius = border_radius - border_size
            if text is not None:
                self.new_blit_rect2(t_rect, self.colorset['menu-buttons'], corners='Top', border_radius=inside_border_radius, alpha=255)
                self.blit_text2(self.lang.translate(text), t_rect, self.colorset['menu-text-black'])
                self.new_blit_rect2(v_rect, self.colorset['menu-selected'], corners='Bottom', border_radius=inside_border_radius, alpha=255)
            else:
                self.new_blit_rect2(v_rect, self.colorset['menu-selected'], corners='All', border_radius=inside_border_radius, alpha=255)

            self.blit_text2(value, v_rect, self.colorset['menu-text-black'], align=align)

            self.update_screen(rect)

            # Read input
            key = self.rpi.listen_inputs(authorized,
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'], wait_for=limited, context='editing')

            if key in ENTER_KEYS :    # Valid and quit
                if v_type == 'leds' and len(value) > 0:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'pins':
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'string' and len(value) >= v_min and len(value) <= v_max:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number' and value == str(v_min):
                    # For solo option which accept -1
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number' and value != '' and value.isnumeric() and int(value) >= v_min and int(value) <= v_max:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number' and value != '' and value.isnumeric() and int(value) == 0 and zero:
                    self.restore_background()
                    self.reset_background()
                    return value
            elif key in ESCAPE_KEYS:
                self.restore_background()
                self.reset_background()
                return 'escape'
            elif key in RIGHT_KEYS : # Add char
                if v_type == 'string' and len(value) < v_max:
                    character = 'a'
                elif (v_type in ('number', 'pins') and int(f"{value}0") <= v_max) or (v_type == 'leds' and len(value) < v_max):
                    if len(value)== 0:
                        character = '1'
                    else:
                        character = '0'
                else:
                    character = ''
                value = f"{value}{character}"

            elif key in BACK_KEYS + LEFT_KEYS :     # Del char
                if len(value) > 0:
                    character = value[-1]
                    value = value[:-1]

            elif key in UP_KEYS + DOWN_KEYS :    # Change char
                if character == '':
                    if v_type in ('leds', 'number', 'pins'):
                        new_char = '0'
                    else:
                        new_char = 'a'
                elif key in UP_KEYS:
                    new_char = self.next_key(character, context=v_type)
                else:
                    new_char = self.previous_key(character, context=v_type)

                if len(value) > 0:
                    value = (f"{value[:-1]}{new_char}")
                else:
                    value = new_char
                character = new_char
            elif len(str(key)) == 1:
                if (v_type == 'string' and len(value) < v_max) \
                or (v_type == 'leds' and len(value) < v_max) \
                or (v_type == 'pins' and int(f"{value}0") <= v_max) \
                or (v_type == 'number' and int(f"{value}0") <= v_max):
                    if v_type != 'string' and value == '0' and str(key) != '0':
                        value = key
                    elif not(v_type == 'number' and value == '' and str(key) == '0') or zero:
                        value = f"{value}{key}"
                    character = str(key)

    def reverse_leds(self, leds):
        '''
        Reverse led's values
        '''
        return ",".join(leds.split(',')[::-1])

    def clean_led(self, leds):
        '''
        Clean leds
        '''
        prev = True
        new = ''
        leds = leds.replace('.', ',')
        for led in leds:
            if led != ',':
                new = f'{new}{led}'
                prev = False
            if led == ',' and not prev :
                prev = True
                new = f'{new}{led}'
        if len(leds)> 0 and leds[-1] == ',':
            return new[0:-1:1]
        return new

    def valid_led(self, leds):
        '''
        Check if there is no doubles
        '''
        tab = []
        for led in leds.split(','):
            if led in tab:
                return False
            else:
                tab.append(led)
        return True

    def valid_leds(self, mult, led, leds):
        '''
        Check if there is no doubles
        '''
        tab = []

        # leds = {'S': '128, 129', 'D': '129', 'T': '130'}
        # mult = S
        # led = '128, 129'

        for multiplier in leds:
            if multiplier != mult:
                for led in leds[multiplier].split(','):
                    tab.append(led)

        for led in led.split(','):
            if led in tab:
                return False
        return True

    def valid_all_leds(self, leds, key):
        '''
        Check is data are correct
        '''

        if key not in ('TB', 'EB'):
            for led in leds[key].split(','):
                for o in leds:
                    if o != key and leds[o] != '' and led in leds[o].split(','):
                        return False
        return True

    def setup_pinsleds_menu(self, config, used_pins):
        '''
        Setup pins and brightness of leds
        '''
        selected = 1
        nb_elements = 5
        new = {}

        links = {}
        for key in config:
            new[key] = config[key]

        while True:
            click_zones = {}
            shortcuts = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-pinsleds')

            index = 1
            for key in new:
                shortcut = f'F{index}'
                click_zones[shortcut] = self.menu_item((index, nb_elements, selected), (shortcut, self.lang.translate(f"menu-{key}"), BTN_VALUE, new[key]), exit=False)
                links[shortcut] = key
                shortcuts[shortcut] = index

                index += 1

            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            self.update_screen()

            key = self.rpi.listen_inputs(['arrows'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 2, 2)

            # Shortcuts
            if key in shortcuts:
                selected = shortcuts[key]
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            #if key in EXTRA_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
            #    return Defaults

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                if int(new['PIN_STRIPLED']) != int(new['PIN_TARGETLED']) \
                        or new['PIN_STRIPLED'] == '' or new['PIN_TARGETLED'] == '':
                    return new
                else:
                    self.message(['menu-leds-conflict'], 1000, self.colorset['menu-text-black'], 'middle', 'big')

            if key in ('F1', 'F3') or (selected in (1, 3) and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.input_value_item('pins', new[links[key]], 10, 21)
                if tmp == 'escape' :
                    pass
                elif int(tmp) in used_pins:
                    self.message(['menu-config-already'], 1000, self.colorset['menu-text-black'], 'middle', 'big', bg_color='menu-ko')
                elif tmp != 'escape':
                    new[links[key]] = tmp

            if key in ('F2', 'F5') or (selected in (2, 5) and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.input_value_item('number', new[links[key]], 1, 100)
                if tmp != 'escape':
                    new[links[key]] = tmp

            if key == 'F4' or (selected == 4 and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.input_value_item('number', new[links[key]], 1, 1000)
                if tmp != 'escape':
                    new[links[key]] = tmp

    def setup_led_menu(self, number, s_value, d_value, t_value, e_value, bull=False):
        '''
        Setup leds menu
        '''

        pos_x = 3 * self.res_x_16
        pos_y = int(self.res['y'] / 8)
        W = 10 * self.res_x_16
        H = int(self.res['y'] * 3 / 4)

        w = int(W / 10)
        h = int(H / 8)

        texts = {'S': 'simple', 'D': 'double', 'T': 'triple', 'E': 'tire'}
        values = {'S': s_value, 'D': d_value, 'T': t_value, 'E': e_value}
        selected = [1, 2]
        while True:
            click_zones = {}
            shortcuts = {}
            cursor = {}

            self.new_blit_rect(pos_x, pos_y, W, H, self.colorset['menu-buttons'], border_color=self.colorset['menu-border'], border_size=10, border_radius=30, Alpha=255, corners='All', )
            self.blit_text(f"{self.lang.translate('paramled_text1')} {number}", pos_x + int(W / 4), pos_y, int(W / 2), h, self.colorset['menu-text'], align='Center')
            self.blit_text(f"{self.lang.translate('paramled_text2')}", pos_x + int(W / 4), pos_y + int(h * 3 / 4), int(W / 2), int(h / 2), self.colorset['menu-text'], align='Center')
            self.blit_text(f"{self.lang.translate('paramled_text3')}", pos_x + int(W / 4), pos_y + int(h * 9 / 8), int(W / 2), int(h / 2), self.colorset['menu-text'], align='Center')
            self.blit_text(f"{self.lang.translate('paramled_text4')}", pos_x + int(W / 4), pos_y + int(h * 3 / 2), int(W / 2), int(h / 2), self.colorset['menu-text'], align='Center')

            index = 0
            if bull:
                keys = ['S', 'D']
                nb_elements = 2
            else:
                keys = ['S', 'D', 'T', 'E']
                nb_elements = 4

            for key in keys:
                index += 1
                if index % 2 == 0:
                    Alpha = self.alpha2
                else:
                    Alpha = self.alpha
                x_ = pos_x + w
                for column in range(1, 5):
                    y_ = pos_y + (1 + index) * h
                    w_ = w
                    align = 'Left'

                    if column == 1:
                        text = texts[key]
                        background_color = 'menu-item-black'
                        textColor = 'menu-text-white'
                        index_click_zone = None
                    elif column == 2:
                        text = values[key]
                        if values[key] == '':
                            background_color = 'menu-buttons'
                        elif self.valid_leds(key, values[key], values) is False:
                            background_color = 'menu-ko'
                        elif self.valid_led(values[key]) is False:
                            background_color = 'menu-warning'
                        else:
                            background_color = 'menu-ok'
                        textColor = 'menu-text-black'
                        index_click_zone = key
                        w_ = 5 * w
                    elif column == 3:
                        text = 'reverse'
                        background_color = 'menu-alternate'
                        textColor = 'menu-text-white'
                        index_click_zone = f'I-{key}'
                    else:
                        text = 'test'
                        background_color = 'menu-shortcut'
                        textColor = 'menu-text-black'
                        index_click_zone = f'T-{key}'
                        align = 'Center'


                    self.new_blit_rect(x_, y_, w_, h, self.colorset[background_color], Alpha=Alpha, border_color=self.border_color(selected, column, index))
                    self.blit_text(text, x_, y_, w_, h, self.colorset[textColor], align = align)
                    if index_click_zone != None:
                        click_zones[index_click_zone] = (x_, y_, w_, h)
                        shortcuts[index_click_zone] = [index, column]
                        cursor[f"{index}-{column}"] = index_click_zone

                    x_ += w_

            if selected[0] == nb_elements + 1:
                self.new_blit_rect(pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-ok'], corners = 'All', border_radius = 10,
                        border_color = self.colorset['menu-text-white'])
            else:
                self.new_blit_rect(pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-item-black'], corners = 'All', border_radius = 10)
            click_zones['escape'] = (pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2))
            self.blit_text('back', pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2),
                   self.colorset['menu-text-white'])

            if selected[0] == nb_elements + 2:
                self.new_blit_rect(pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-ok'], corners = 'All', border_radius = 10,
                        border_color = self.colorset['menu-text-white'])
            else:
                self.new_blit_rect(pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-item-black'], corners = 'All', border_radius = 10)
            self.blit_text('save', pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2),
                    self.colorset['menu-text-white'])
            click_zones['save'] = (pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2))

            self.update_screen(rect=(pos_x, pos_y, W, H))

            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            if key in shortcuts:
                selected =[shortcuts[key][0], shortcuts[key][1]]
                key = 'enter'

            # Navigation
            selected =[self.navigate(selected[0], key, nb_elements, 2, 2), selected[1]]

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 1):
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 2):
                return values['S'], values['D'], values['T'], values['E']

            if key == 'space':
                if selected == 1:
                    values['S'] = ''
                elif selected == 2:
                    values['D'] = ''
                elif selected == 3:
                    values['T'] = ''
                else:
                    values['E'] = ''
            elif key in ENTER_KEYS :
                C = cursor[f"{selected[0]}-{selected[1]}"]
                if len(C) == 1:
                    tmp = self.clean_led(self.input_value_item('leds', values[C], 0, 43))
                    if tmp != 'escape':
                        values[C] = tmp
                elif C[0:2:1] == 'I-':
                    # Reverse
                    values[C[2]] = self.reverse_leds(values[C[2]])
                elif C[0:2:1] == 'T-':
                    # Try this
                    C = cursor[f"{selected[0]}-{selected[1]}"]
                    ret = 'try|'
                    if selected[0] == 1:
                        ret += f"-S:{values['S']}"
                    elif selected[0] == 2:
                        ret += f"-D:{values['D']}"
                    elif selected[0] == 3:
                        ret += f"-T:{values['T']}"
                    elif selected[0] == 4:
                        ret += f"-E:{values['E']}"
                    return ret

            elif key in RIGHT_KEYS:
                if selected[1] == 4:
                    selected = [selected[0], 2]
                else:
                    selected = [selected[0], selected[1] + 1]

            elif key in LEFT_KEYS:
                if selected[1] == 2:
                    selected = [selected[0], 4]
                else:
                    selected = [selected[0], selected[1] - 1]

    def setup_leds_menu(self, leds, sel_y, sel_x, Nmoy):
        '''
        Leds setup menu
        '''
        selected = [sel_y, sel_x]

        if '|' in leds :    # Submenu
            if sel_x == 5:
                sub = ''
            else:
                sub = leds.split('|')[0]
            leds = leds.split('|')[1]
        else:
            sub = ''

        if leds != '':
            leds = ast.literal_eval(leds)
        else:
            leds = {}

        List = {}
        for number in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 'B']:
            for multiplier in ['S', 'D', 'T', 'E']:
                if number == 'B' and multiplier in ('T', 'E'):
                    continue
                index = f"{multiplier}{number}"
                try:
                    List[index] = leds[index]
                except:
                    List[index] = ''

        numbers = ['20', '1', '18', '4', '13', '6', '10', '15', '2', '17', '3', '19', '7', '16', '8', '11', '14', '9', '12', '5', 'B']

        H = self.res_y_16
        N = 1
        S = 6
        D = 2
        T = 2
        E = 2

        nb_elements = 1
        key = ''
        while True:
            if selected[0] <= 5:
                Nmoy = 6
            elif selected[0] > 4 and selected[0] < 18:
                if key in UP_KEYS:
                    Nmoy -= 1
                elif key in DOWN_KEYS:
                    Nmoy += 1
            else:
                Nmoy = 18

            click_zones = {}
            shortcuts = {}
            cursor = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-leds')

            pos_x = min_x = self.res_x_16
            W = self.res_x_16

            pos_y = 3*H
            self.new_blit_rect(pos_x, pos_y, N*W, H, self.colorset['menu-item-black'])
            self.new_blit_rect(pos_x + N*W, pos_y, S*W, H, self.colorset['menu-item-black'])
            self.blit_text("simple", pos_x + N*W, pos_y, S*W, H, self.colorset['menu-text-white'], align = 'Left')
            self.new_blit_rect(pos_x + W*(N + S), pos_y, D*W, H, self.colorset['menu-item-black'])
            self.blit_text("double", pos_x + W+S*W, pos_y, D*W, H, self.colorset['menu-text-white'], align = 'Left')
            self.new_blit_rect(pos_x + W*(N + S+D), pos_y, T*W, H, self.colorset['menu-item-black'])
            self.blit_text("triple", pos_x + W+S*W + D*W, pos_y, T*W, H, self.colorset['menu-text-white'], align = 'Left')
            self.new_blit_rect(pos_x + W*(N + S+D + T), pos_y, E*W, H, self.colorset['menu-item-black'])
            self.blit_text("tire", pos_x + W*(N + S+D + T), pos_y, E*W, H, self.colorset['menu-text-white'])
            self.new_blit_rect(pos_x + W*(N + S+D + T+E), pos_y, W, H, self.colorset['menu-item-black'])
            self.blit_text("test", pos_x + W*(N + S+D + T+E), pos_y, W, H, self.colorset['menu-text-white'])
            pos_y += H
            nb_elements = 0

            index = 0
            for n in numbers:
                pos_x = min_x
                index += 1
                if Nmoy - 5 <= index < Nmoy + 4:
                    if index % 2 == 0:
                        Alpha = self.alpha2
                    else:
                        Alpha = self.alpha
                    if selected[0] == index:
                        background_color = self.colorset['menu-ok']
                    else:
                        background_color = self.colorset['menu-buttons']

                    self.new_blit_rect(pos_x, pos_y, N*W, H, background_color, Alpha=Alpha)
                    self.blit_text(n, pos_x, pos_y, N*W, H, self.colorset['menu-text-black'])
                    pos_x += N * W

                    j = 0
                    for (k, w) in [('S', S), ('D', D), ('T', T), ('E', E), ('A', 1)]:
                        j += 1
                        key = f"{k}{n}"
                        if k == 'A':
                            background_color = self.colorset['menu-shortcut']
                        else:
                            valid = self.valid_all_leds(List, key)
                            if selected[0] == index:
                                if valid:
                                    background_color = self.colorset['menu-ok']
                                else:
                                    background_color = self.colorset['menu-shortcut']
                            elif valid:
                                background_color = self.colorset['menu-buttons']
                            else:
                                background_color = self.colorset['menu-ko']

                        if k == 'A' and selected[1] == 5 and selected[0] == index:
                            borderColor = self.colorset['menu-text-white']
                        elif k != 'A' and selected[1] != 5 and selected[0] == index:
                            borderColor = self.colorset['menu-text-white']
                        else:
                            borderColor = None
                        self.new_blit_rect(pos_x, pos_y, w * W, H, background_color, border_color=borderColor, Alpha=Alpha)
                        if k != 'A' and key not in ('TB', 'EB'):
                            self.blit_text(List[key], pos_x, pos_y, w * W, H, self.colorset['menu-text-black'], align='Left')
                        elif k == 'A':
                            self.blit_text('X', pos_x, pos_y, w * W, H, self.colorset['menu-text-black'], align='Center')
                        click_zones[key] = (pos_x, pos_y, w * W, H)
                        cursor[f'{index}-{j}'] = key
                        shortcuts[key] = [index, j]
                        pos_x += w*W

                    pos_y += H
                nb_elements += 1

            click_zones['escape'] = self.display_button(nb_elements + 1 == selected[0], 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected[0], 'save', special='return')

            if sub == '':
                self.update_screen()
                key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])
            else:
                selected = shortcuts[f'S{sub}']
                key = 'enter'

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            if key in shortcuts:
                selected = [shortcuts[key][0], shortcuts[key][1]]
                key = 'enter'

            # Navigation
            selected = [self.navigate(selected[0], key, nb_elements, 2, 2), selected[1]]

            if key in RIGHT_KEYS:
                if selected[1] == 5:
                    selected = [selected[0], 1]
                else:
                    selected = [selected[0], 5]
            elif key in LEFT_KEYS:
                if selected[1] == 1:
                    selected = [selected[0], 5]
                else:
                    selected = [selected[0], 1]

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 1) :    # Previous menu
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 2):
                return List

            if key in ENTER_KEYS :
                n = cursor[f'{selected[0]}-{selected[1]}'][1::]
                if selected[1] == 5:
                    # Try
                    C = cursor[f"{selected[0]}-{selected[1]}"][1:3:1]
                    ret = 'try|'
                    if List[f'S{C}'] != '':
                        ret += '-S:{}'.format(List[f'S{C}'])
                    if List['D{}'.format(C)] != '':
                        ret += '-D:{}'.format(List[f'D{C}'])
                    if C != 'B' and List['T{}'.format(C)] != '':
                        ret += '-T:{}'.format(List[f'T{C}'])
                    if C != 'B' and List['E{}'.format(C)] != '':
                        ret += '-E:{}'.format(List[f'E{C}'])
                    ret += f'|{List}|{n}|{selected[0]}|{selected[1]}|{Nmoy}'
                    return ret

                if n != 'B':
                    tmp = self.setup_led_menu(str(n), List[f'S{n}'], List[f'D{n}'], List[f'T{n}'], List[f'E{n}'])
                else:
                    tmp = self.setup_led_menu(str(n), List[f'S{n}'], List[f'D{n}'], '', '', bull=True)

                if tmp[0:3:1] == 'try':
                    if tmp[5:6] == 'S':
                        List[f'S{n}'] = tmp.split(':')[1]
                    if tmp[5:6] == 'D':
                        List[f'D{n}'] = tmp.split(':')[1]
                    if tmp[5:6] == 'T':
                        List[f'T{n}'] = tmp.split(':')[1]
                    if tmp[5:6] == 'E':
                        List[f'E{n}'] = tmp.split(':')[1]

                    return f"{tmp}|{List}|{n}|{selected[0]}|{1}|{Nmoy}"

                if tmp != 'escape':
                    List[f'S{n}'] = tmp[0]
                    List[f'D{n}'] = tmp[1]
                    List[f'T{n}'] = tmp[2]
                    List[f'E{n}'] = tmp[3]
                    sub = ''
                else:
                    sub = ''

    def test_target_menu(self):
        '''
        Test target menu
        '''
        self.display_background()
        self.menu_header('test-target', subtxt = 'test-target-msg')
        self.update_screen()

        while True:
            stroke = self.rpi.listen_inputs([],
                 ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON', 'EXTRABUTTON',
                  'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISSDART',
                  'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'single-click', 'escape', 'space', 'special'],
                  context='test', timeout=10000)

            if stroke is False:
                self.message(['timeout'], 1000, self.colorset['menu-item-black'], 'middle', 'big')
                return

            if stroke == 'escape':
                return

            if stroke and not isinstance(stroke, tuple):
                code = stroke[0]
                message = stroke[1]

                if code == 0:
                    self.play_sound(stroke[1])
                    self.message([message], 200, self.colorset['menu-ok'], 'middle', 'big')
                else:
                    self.message([message], 5000, self.colorset['menu-ko'], 'middle', 'big')

                self.display_background()
                self.menu_header('test-target', subtxt = 'test-target-msg')
                self.update_screen()

    def test_buttons_menu(self):
        '''
        Test buttons menu
        '''
        self.display_background()
        self.menu_header('test-buttons', subtxt = 'test-button-msg')
        self.update_screen()

        while True:

            key_pressed = self.rpi.test_buttons()

            if key_pressed == 'nogpio':
                self.message([self.lang.translate('nogpio')], 2000, self.colorset['menu-item-black'], 'middle', 'big')
                return

            if key_pressed is False:
                self.message(['timeout'], 1000, self.colorset['menu-item-black'], 'middle', 'big')
                return

            if key_pressed == 'escape':
                return

            if isinstance(key_pressed, list) and len(key_pressed) > 0:
                self.message([' / '.join(key_pressed)], 100, self.colorset['menu-item-black'], 'middle', 'big')
                if len(key_pressed) >= 3:
                    return

                self.display_background()
                self.menu_header('test-buttons', subtxt = 'Appuyer sur escape, sur 3 boutons en même temps ou attendez 10 secondes pour quitter.')
                self.update_screen()

    def setup_buttons_menu(self, buttons, Defaults):
        '''
        Buttons setup menu
        '''
        selected = 1

        ButtonsList = [('', 'notattributed')]

        for letter in ('A', 'B'):
            for number in (0, 1, 2, 3, 4, 5, 6, 7):
                ButtonsList.append((f'{letter}{number}', f'{letter}{number}'))

        if buttons['EXTENDED_GPIO'] == '1':
            index = 0
            for button in buttons:
                if button != 'EXTENDED_GPIO':
                    index += 1
                    if buttons[button] != '0':
                        break
            if index == 16 :    # Tous les boutons à 0
                buttons = Defaults.copy()

        refresh = True
        while True:
            click_zones = {}
            shortcuts = {}
            cursor = {}
            index = 0

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-buttons')

            if buttons['EXTENDED_GPIO'] == '1':
                nb_elements = len(buttons)
            else:
                nb_elements = 1

            click_zones['btn-extended'] = self.button_item((1, nb_elements, selected), self.lang.translate(buttons['EXTENDED_GPIO']), 'extended', self.alpha2)
            shortcuts['btn-extended'] = 1
            cursor[1] = 'btn-extended'

            if buttons['EXTENDED_GPIO'] == '1':
                index = 1
                for button in buttons:
                    if button != 'EXTENDED_GPIO':
                        index += 1
                        if (index // 2) % 2 == 0:
                            Alpha = self.alpha
                        else:
                            Alpha = self.alpha2
                        if buttons[button] == '':
                            val = 'notattributed'
                        else:
                            val = buttons[button]
                        click_zones[f'btn-{button}'] = self.button_item((index, nb_elements, selected), val, button.replace('pin_', ''), Alpha)

                        shortcuts[f'btn-{button}'] = index
                        cursor[index] = f'btn-{button}'

            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['reset'] = self.display_button(nb_elements + 2 == selected, 'reset', special='refresh')
            click_zones['save'] = self.display_button(nb_elements + 3 == selected, 'save', special='return')

            # Update screen
            #if refresh:
            if True:
                self.update_screen()
                refresh = False
            else:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])


            key = self.rpi.listen_inputs(['arrows'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 3, 3, item_per_line=2 , left_right=True)

            # Shortcuts
            if key in shortcuts:
                selected =shortcuts[key]
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in EXTRA_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                return Defaults

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 3):
                return buttons

            # Key analysis
            if key == 'btn-extended' or (key in ENTER_KEYS and selected == 1):
                tmp = self.dropdown(self.res['x'] / 8*3, self.res['y'] / 4, [('1', 'yes'), ('0', 'no')], navigate=buttons['EXTENDED_GPIO'])
                buttons['EXTENDED_GPIO'] = str(tmp)
                if tmp == '1':
                    buttons = Defaults.copy()
                else:
                    for button in buttons:
                        buttons[button] = '0'

            elif key in ENTER_KEYS :
                key = cursor[selected]

                old = buttons[key.replace('btn-', '')]    # A2 par ex
                t = self.dropdown(self.res['x'] / 8*3, self.res['y'] / 4, ButtonsList, navigate = buttons[key.replace('btn-', '')])
                if t != 'escape':
                    for button in buttons:
                        if buttons[button] == t and t != '':
                            buttons[button] = old
                            break
                    buttons[key.replace('btn-', '')] = t

    '''
    Test toys menu
    '''
    def test_toys_menu(self):
        selected = 1
        nb_elements = 0
        toys = []

        for toy in self.rpi.buttons:
            if toy.startswith('LIGHT_') and self.rpi.buttons[toy] != '':
                toys.append((self.rpi.buttons[toy], toy))
                nb_elements += 1

        self.rpi.light_buttons(toys, state=False)

        while True:
            click_zones = {}
            shortcuts = []

            # Draw bg
            self.display_background()
            self.menu_header('test-toys')

            index = 1
            for toy in toys:
                if toy[0] != '0':
                    Fx = f'F{index}'
                    click_zones[Fx] = self.menu_item((index, nb_elements, selected)
                            , (Fx, f'{toy[0]}  --  {self.lang.translate(toy[1])}', BTN_CHOICE, None)
                            , exit=False)
                    shortcuts.append(Fx)
                    index += 1

            if index == 1:
                self.message([self.lang.translate('notoyset')], 2000, None, 'middle', 'big', bg_color='menu-ko')
                return

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            ################
            # Update screen
            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 1)

            # Keyboard cases
            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'

            # Key analysis
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS :
                toy = toys[selected - 1][1]
                self.rpi.gpio.strobe_buttons([toy], delay=1200, delay_off=400)


    def setup_menu(self):
        '''
        Main setup menu
        '''
        selected = self.selected_menu.get('setup', 1)

        nb_elements = 7

        refresh = True
        old_selection = None
        while True:
            click_zones = {}
            shortcuts = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup')

            # Button's setup
            click_zones['F1'] = self.menu_item((1, nb_elements, selected), ("F1", "setup-buttons", BTN_CHOICE, None), exit=False)
            shortcuts.append('F1')
            # Led's pins setup
            click_zones['F2'] = self.menu_item((2, nb_elements, selected), ("F2", "setup-pinsleds", BTN_CHOICE, None), exit=False)
            shortcuts.append('F2')
            # Led's setup
            click_zones['F3'] = self.menu_item((3, nb_elements, selected), ("F3", "setup-leds", BTN_CHOICE, None), exit=False)
            shortcuts.append('F3')
            # Test buttons
            click_zones['F4'] = self.menu_item((4, nb_elements, selected), ("F4", "test-buttons", BTN_CHOICE, None), exit=False)
            shortcuts.append('F4')
            # Test target
            click_zones['F5'] = self.menu_item((5, nb_elements, selected), ("F5", "test-target", BTN_CHOICE, None), exit=False)
            shortcuts.append('F5')
            # Test toys
            click_zones['F6'] = self.menu_item((6, nb_elements, selected), ("F6", "test-toys", BTN_CHOICE, None), exit=False)
            shortcuts.append('F6')
            # Test toys
            click_zones['F7'] = self.menu_item((7, nb_elements, selected), ("F7", "reset", BTN_CHOICE, None), exit=False)
            shortcuts.append('F7')
            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            if selected <= nb_elements:
                selection = click_zones[f'F{selected}']
            elif nb_elements + 1 == selected:
                selection = click_zones['escape']
            elif nb_elements + 2 == selected:
                selection = click_zones['save']
            else:
                selection = None

            # Refresh screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None or True:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=[old_selection, selection])

            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'], events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 1)

            # Keyboard cases
            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'

            # Key analysis
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS :
                self.selected_menu['setup'] = selected
                if selected == 1:
                    return 'setup-buttons'

                if selected == 2:
                    return 'setup-pinleds'

                if selected == 3:
                    return 'setup-leds'

                if selected == 4:
                    return 'test-buttons'

                if selected == 5:
                    return 'test-target'

                if selected == 6:
                    return 'test-toys'

                if selected == 7:
                    return 'reset'

                if selected == nb_elements + 1:
                    return 'escape'

            old_selection = selection

    def miscellaneous(self):
        '''
        Miscellaneous
        '''
        nb_elements = 8
        selected = self.selected_menu.get('miscellaneous', 1)

        self.dmd.send_text(f"{self.lang.translate('parameters')}")

        old_selection = None
        refresh = True
        while True:

            click_zones = {}
            shortcuts = {}

            # Draw bg
            self.display_background()
            # Titles
            self.menu_header(f"{self.lang.translate('parameters')}")
            # Ip address
            self.display_ips()
            # Version of rpi
            self.display_rpi_version()
            # Pydarts' version
            self.display_version()

            # Menu
            click_zones['F1'] = self.menu_item((1, nb_elements, selected), ("F1", "favorites-players", BTN_CHOICE, None), exit=False)
            shortcuts['F1'] = 'firstnames'

            click_zones['F2'] = self.menu_item((2, nb_elements, selected), ("F2", "favorites-games", BTN_CHOICE, None), exit=False)
            shortcuts['F2'] = 'games'

            click_zones['F3'] = self.menu_item((3, nb_elements, selected), ("F3", "favorites-servers", BTN_CHOICE, None), exit=False)
            shortcuts['F3'] = 'servers'

            click_zones['F4'] = self.menu_item((4, nb_elements, selected), ("F4", "customization", BTN_CHOICE, None), exit=False)
            shortcuts['F4'] = 'customization'

            click_zones['F5'] = self.menu_item((5, nb_elements, selected), ("F5", "animations", BTN_CHOICE, None), exit=False)
            shortcuts['F5'] = 'animations'

            click_zones['F6'] = self.menu_item((6, nb_elements, selected), ("F6", "players-bank", BTN_CHOICE, None), exit=False)
            shortcuts['F6'] = 'firstname-bank'

            click_zones['F7'] = self.menu_item((7, nb_elements, selected), ("F7", "setup", BTN_CHOICE, None), exit=False)
            shortcuts['F7'] = 'setup'

            click_zones['F8'] = self.menu_item((8, nb_elements, selected), ("F8", "backups", BTN_CHOICE, None), exit=False)
            shortcuts['F8'] = 'backups'

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            if selected <= nb_elements:
                selection = click_zones[f'F{selected}']
            elif nb_elements + 1 == selected:
                selection = click_zones['escape']
            elif nb_elements + 2 == selected:
                selection = click_zones['save']
            else:
                selection = None

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None:
                self.update_screen(rect_array=[old_selection, selection])
            else:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])

            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 1)

            # Shortcuts
            if key in shortcuts:
                selected = int(key.replace('F', ''))
                self.selected_menu['miscellaneous'] = selected
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS :
                self.selected_menu['miscellaneous'] = selected
                return shortcuts[f'F{selected}']

            old_selection = selection

    def border_color(self, selected, pos_x, pos_y):
        '''
        Return border's color according selected item or not
        '''
        if selected[0] == pos_y and selected[1] == pos_x:
            return self.colorset['menu-border']

        return None

    def event_menu(self, event_name, S_Animations, T_Animations, Colors, Event):
        '''
        Event <> animation link menu
        '''
        empty_animation = ',1,random,10'
        empty_element = ['', 1, 'random', 10]
        if Event is None:
            #if event_name not in ('touch', 'SB', 'DB'):
            if event_name not in ('touch'):
                Event = {'TARGET':[empty_animation], 'STRIP':[empty_animation], 'DMD':[empty_animation], 'MATRIX':[empty_animation], 'OTHER':[',,,']}
            else:
                Event = {'STRIP':[empty_animation], 'DMD':[empty_animation], 'MATRIX':[empty_animation], 'OTHER':[',,,']}
        # Adding missing devices
        for device in ['STRIP', 'TARGET', 'DMD', 'MATRIX', 'OTHER']:
            if device not in Event:
                Event[device] = [empty_animation]
            #elif len(Event[device]) == 0 and device in ['STRIP', 'TARGET'] and event_name not in ('touch', 'SB', 'DB'):
            elif len(Event[device]) == 0 and device in ['STRIP', 'TARGET'] and event_name not in ('touch'):
                Event[device] = ['']

        if self.selected is None:
            self.selected = [1, 1]

        S_Animations_DD = []
        for a in S_Animations:
            S_Animations_DD.append([a, a])

        T_Animations_DD = []
        for a in T_Animations:
            T_Animations_DD.append([a, a])

        count_dropdown = []
        for index in [1, 2, 3, 4, 5, 10, 15, 20, 50, 100]:
            count_dropdown.append([str(index), str(index)])

        colors_dropdown = []
        for color in Colors:
            colors_dropdown.append([color, color])

        delay_dropdown = []
        for delay in [1, 2, 5, 10, 20, 50, 100, 200, 500]:
            delay_dropdown.append([str(delay), str(delay)])

        #if event_name not in ('touch', 'SB', 'DB'):
        if event_name not in ('touch'):
            deviceList = ['TARGET', 'STRIP']
        else:
            deviceList = ['STRIP']

        title = self.lang.translate('menu-event') + ' "' + self.lang.translate(f"event-{event_name}") + '"'
        key = ''
        act = ''
        refresh = True
        selection = None

        while True:
            nb_elements = 0
            for element in Event:
                if element in deviceList:
                    nb_elements += len(Event[element])
            i = 0
            k = 0
            if self.selected[0] > nb_elements + 3:
                self.selected = [1, 1]
            elif self.selected[0] < 1:
                self.selected = [nb_elements + 3, 1]

            click_zones = {}
            shortcuts = {}
            cursor = {}
            left = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header(title, subtxt = '5 animations maxi par évènement')

            # + STRIP  | Ring   | blue   | 2
            # +        | Strobe | red    | 2
            # +-------- + -------- + -------- + ---
            # + TARGET | Ring   | yellow | 3
            # +-------- + -------- + -------- + ---
            # + DMD    | yes/no
            # +-------- + -------- + -------- + ---
            # + MATRIX | yes/no

            nb_animations = 0
            for element in Event:
                if element not in deviceList:
                    continue
                nb_animations += len(Event[element])
            pos_y = 3 * self.res_y_16
            for element in Event:
                if element not in deviceList:
                    continue
                i += 1

                if i % 2 == 0:
                    background_color = self.colorset['menu-text-white']
                else:
                    background_color = self.colorset['menu-shortcut']
                device = Event[element]

                pos_x = int(self.res['x'] * 2.5 / 16)
                nb = len(Event[element])
                if nb_animations <= 9:
                    H = self.res_y_16
                else:
                    H = int(10 * self.res_y_16 / nb_animations)

                # 1st : Animation device
                w = int(self.res['x'] * 2 / 16)
                rect = pygame.Rect(pos_x, pos_y, w, H)
                if nb == 1:
                    self.new_blit_rect2(rect, background_color, corners='Left')
                else:
                    self.new_blit_rect2(rect, background_color, corners='TopLeft')

                self.blit_text2(element, rect, self.colorset['menu-text-black'])

                j = 0
                for e in Event[element]:
                    if j % 2 == 0:
                        Alpha = self.alpha
                    else:
                        Alpha = self.alpha2
                    if j > 0:
                        i += 1
                    j += 1
                    if j == 2:
                        pos_x = int(self.res['x'] * 2.5 / 16)
                        rect = pygame.Rect(pos_x, pos_y, w, H)
                        border_color = self.border_color(self.selected, 0, i)
                        self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='BottomLeft', alpha=Alpha, border_color=border_color)
                        self.blit_text2('try', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-0-try'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-0-try'] = (element, 10, 'try', i, 0)
                        cursor[f'{k + 1}-0'] = f'{element}-0-try'
                        left.append(i)

                    pos_x = int(self.res['x'] * 2.5 / 16 + w)
                    W = self.res_x_16

                    if element in deviceList:
                        selected = False
                        k += 1
                        if e.count(',') < 3:
                            elts = empty_element
                            Event[element] = [empty_animation]
                        else:
                            elts = e.split(',')

                        rect = pygame.Rect(pos_x, pos_y, 3 * W, H)
                        border_color = self.border_color(self.selected, 1, k)
                        selected = [k, 1] == self.selected

                        if j <= 2 or j != nb:
                            self.new_blit_rect2(rect, self.colorset['menu-buttons'], alpha=Alpha, border_color=border_color, selected=selected)
                        else:
                            self.new_blit_rect2(rect, self.colorset['menu-buttons'], alpha=Alpha, corners='BottomLeft', border_color=border_color, selected=selected)

                        self.blit_text2(elts[0], rect, self.colorset['menu-text-white'])
                        click_zones[f'{element}-{j}-anim'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-anim'] = (element, j, 'anim', i, 1)
                        cursor[f'{k}-1'] = f'{element}-{j}-anim'

                        rect.x = rect.right
                        rect.width = W

                        border_color = self.border_color(self.selected, 2, k)
                        selected = [k, 2] == self.selected

                        self.new_blit_rect2(rect, self.menu_color(self.colorset['menu-ok']), alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2(elts[1], rect, self.colorset['menu-text-white'])
                        click_zones[f'{element}-{j}-count'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-count'] = (element, j, 'count', i, 2)
                        cursor[f'{k}-2'] = f'{element}-{j}-count'

                        rect.x = rect.right
                        rect.width = 2 * W

                        border_color = self.border_color(self.selected, 3, k)
                        selected = [k, 3] == self.selected

                        self.new_blit_rect2(rect, self.colorset['menu-ok'], alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2(elts[2], rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-color'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-color'] = (element, j, 'color', i, 3)
                        cursor[f'{k}-3'] = f'{element}-{j}-color'

                        # Color
                        rect.x = rect.right
                        rect.width = rect.height

                        border_color = self.border_color(self.selected, 4, k)
                        selected = [k, 4] == self.selected

                        self.new_blit_rect2(rect, self.colorset['menu-shortcut'], alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2(elts[3], rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-delay'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-delay'] = (element, j, 'delay', i, 4)
                        cursor[f'{k}-4'] = f'{element}-{j}-delay'

                        # Up
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 4, k)
                        selected = [k, 5] == self.selected

                        if nb > 1:
                            updown_color = self.colorset['menu-alternate']
                        else:
                            updown_color = self.menu_color(self.colorset['menu-inactive'])

                        self.new_blit_rect2(rect, self.menu_color(updown_color), alpha=Alpha, border_color=border_color, selected=selected)
                        if j > 1:
                            self.blit_text2('^', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-moveup'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-moveup'] = (element, j, 'moveup', i, 5)
                        cursor[f'{k}-5'] = f'{element}-{j}-moveup'

                        # Down
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 4, k)
                        selected = [k, 6] == self.selected

                        self.new_blit_rect2(rect, updown_color, alpha=Alpha, border_color=border_color, selected=selected)
                        if j < nb:
                            self.blit_text2('v', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-movedown'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-movedown'] = (element, j, 'movedown', i, 6)
                        cursor[f'{k}-6'] = f'{element}-{j}-movedown'

                        if nb < 5:
                            plus_color = self.menu_color(self.colorset['menu-ok'])
                        else:
                            plus_color = self.menu_color(self.colorset['menu-inactive'])

                        # Plus
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 7, k)
                        selected = [k, 7] == self.selected

                        self.new_blit_rect2(rect, plus_color, alpha=Alpha, border_color=border_color, selected=selected)

                        click_zones[f'{element}-{j}-plus'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-plus'] = (element, j, 'plus', i, 7)
                        cursor[f'{k}-7'] = f'{element}-{j}-plus'
                        if nb < 5:
                            self.blit_text2('+', rect, self.colorset['menu-text-black'])

                        # Minus
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 8, k)
                        selected = [k, 8] == self.selected

                        minus_color = self.colorset['menu-ok']
                        self.new_blit_rect2(rect, minus_color, alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2('-', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-minus'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-minus'] = (element, j, 'minus', i, 8)
                        cursor[f'{k}-8'] = f'{element}-{j}-minus'

                        # Try
                        rect.x = rect.right
                        rect.width *= 2
                        border_color = self.border_color(self.selected, 9, k)
                        selected = [k, 9] == self.selected

                        if nb == 1:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='Right', alpha=Alpha, border_color=border_color, selected=selected)
                        elif j == 1:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='TopRight', alpha=Alpha, border_color=border_color, selected=selected)
                        elif j == nb:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='BottomRight', alpha=Alpha, border_color=border_color, selected=selected)
                        else:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], alpha=Alpha, border_color=border_color, selected=selected)

                        self.blit_text2('try', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-try'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-try'] = (element, j, 'try', i, 9)
                        cursor[f'{k}-9'] = f'{element}-{j}-try'

                    pos_y += H
                pos_y += H

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == self.selected[0], 'back', special='escape')
            click_zones['try'] = self.display_button(nb_elements + 2 == self.selected[0], 'try', special='refresh')
            click_zones['save'] = self.display_button(nb_elements + 3 == self.selected[0], 'save', special='return')
            shortcuts['try'] = ('event', 0, 'try', nb_elements + 2, 0)

            if self.selected[0] <= nb_elements:
                selection = click_zones[cursor[f"{self.selected[0]}-{self.selected[1]}"]]
            elif nb_elements + 1 == self.selected[0]:
                selection = click_zones['escape']
            elif nb_elements + 2 == self.selected[0]:
                selection = click_zones['try']
            elif nb_elements + 3 == self.selected[0]:
                selection = click_zones['save']
            else:
                selection = None

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is not None and selection is not None:
                self.update_screen(rect_array=[old_selection, selection])
            else:
                self.update_screen(rect_array=[click_zones[click_zone] for click_zone in click_zones])

            key = self.rpi.listen_inputs(['math', 'arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space', 'backspace'])

            act = ''
            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in PLUS_KEYS:
                key = cursor[f"{self.selected[0]}-7"]
            elif key in MINUS_KEYS:
                key = cursor[f"{self.selected[0]}-8"]

            if key not in ['escape', 'BACKUPBUTTON', 'BTN_GAMEBUTTON', 'enter', 'save'] + DIRECTION_KEYS:
                try:
                    T = shortcuts[key]
                    dev = T[0]
                    index = int(T[1])-1
                    act = T[2]
                    y = int(T[3])
                    x = T[4]
                    self.selected = [y, x]

                    if act == 'try':
                        if index == -1:
                            act = 'tryE'            # try whole event
                        elif index == 9:
                            act = 'tryD'            # try device animation
                        else:
                            act = 'tryA'            # try only this animation
                except:
                    act = key
            else:
                act = key

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and self.selected[0] == nb_elements + 1):
                return 'escape'

            if key in EXTRA_KEYS or (key in ENTER_KEYS and self.selected[0] == nb_elements + 2):
                act = 'tryE'
            elif key in SAVE_KEYS or (key in ENTER_KEYS and self.selected[0] == nb_elements + 3):
                # Clean empty animations
                for device in Event:
                    devices = []
                    for anim in Event[device]:
                        if anim == empty_animation:
                            anim = ''
                        else:
                            devices.append(anim)
                    Event[device] = devices
                return str(Event)

            elif key in ENTER_KEYS:
                try:
                    T = shortcuts[cursor[f"{self.selected[0]}-{self.selected[1]}"]]
                    dev = T[0]
                    index = int(T[1])-1
                    act = T[2]
                    if act == 'try':
                        if index == -1:
                            act = 'tryE'            # try whole event
                        elif index == 9:
                            act = 'tryD'             # try device animation
                        else:
                            act = 'tryA'            # try only this animation
                except:
                    act = act
                refresh = True
            elif key in LEFT_KEYS and self.selected[0] > nb_elements + 1:
                self.selected = [self.selected[0] - 1, self.selected[1]]
            elif key in LEFT_KEYS and self.selected[0] <= nb_elements:
                if self.selected[1] == 1 and self.selected[0] in left:
                    self.selected = [self.selected[0], 0]
                elif self.selected[1] in (0, 1):
                    self.selected = [self.selected[0], 9]
                else:
                    self.selected =[self.selected[0], self.selected[1]-1]
            elif key in RIGHT_KEYS and self.selected[0] > nb_elements and self.selected[0] < nb_elements + 3:
                self.selected = [self.selected[0] + 1, self.selected[1]]
            elif key in RIGHT_KEYS and self.selected[0] <= nb_elements:
                if self.selected[1] == 9 and self.selected[0] in left:
                    self.selected = [self.selected[0], 0]
                elif self.selected[1] == 9:
                    self.selected = [self.selected[0], 1]
                else:
                    self.selected = [self.selected[0], self.selected[1] + 1]
            elif key in UP_KEYS:
                if self.selected[0] == 1:
                    self.selected = [nb_elements + 2, 1]
                elif self.selected[0] in left and self.selected[1] == 0:
                    self.selected = [self.selected[0] - 1, 1]
                elif self.selected[0] > nb_elements:
                    self.selected = [nb_elements, 1]
                else:
                    self.selected = [self.selected[0] - 1, self.selected[1]]
            elif key in DOWN_KEYS:
                if self.selected[0] == nb_elements:
                    self.selected = [nb_elements + 2, 1]
                elif self.selected[0] > nb_elements:
                    self.selected = [1, 1]
                elif self.selected[0] in left and self.selected[1] == 0:
                    self.selected = [self.selected[0] + 1, 1]
                else:
                    self.selected = [self.selected[0] + 1, self.selected[1]]
            elif key == 'resize':    # Resize screen
                self.create_screen(False, self.rpi.newresolution)
                refresh = True
            elif key == 'TOGGLEFULLSCREEN':    # Toggle fullscreen
                self.create_screen(True, False)
                refresh = True

            if act == 'anim':
                if dev == 'STRIP':
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, S_Animations_DD, navigate=Event[dev][index].split(',')[0])
                else:
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, T_Animations_DD, navigate=Event[dev][index].split(',')[0])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{tmp},{it},{co},{de}"
                refresh = True
            elif act == 'count':
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, count_dropdown, navigate=Event[dev][index].split(',')[1])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{an},{tmp},{co},{de}"
                refresh = True
            elif act == 'color':
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, colors_dropdown, navigate=Event[dev][index].split(',')[2])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{an},{it},{tmp},{de}"
                refresh = True
            elif act == 'delay':
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, delay_dropdown, navigate=Event[dev][index].split(',')[3])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{an},{it},{co},{tmp}"
                refresh = True
            elif act in PLUS_KEYS:
                if len(Event[dev]) < 5:
                    Event[dev].append(empty_animation)
                    refresh = True
            elif act in MINUS_KEYS:
                del Event[dev][index]
                if len(Event[dev]) == 0:
                    Event[dev].append(empty_animation)
                refresh = True

            elif act == 'movedown' and index + 1 < len(Event[dev]):
                tmp = Event[dev][index + 1]
                Event[dev][index + 1] = Event[dev][index]
                Event[dev][index] = tmp
                refresh = True
            elif act == 'moveup' and index > 0:
                tmp = Event[dev][index]
                Event[dev][index] = Event[dev][index - 1]
                Event[dev][index - 1] = tmp
                refresh = True

            elif act == 'tryE':
                # Try event (all animations, on all devices)
                ret = 'tryE'
                ret += f'|{Event}|'
                for d in Event:
                    ret += f"-{d}:{';'.join(Event[d])}"
                return ret.replace('|+', '|')
            elif act == 'tryD':
                # Try animation of specific device (ex TARGET)
                ret = f"tryD|{Event}|{dev}:{';'.join(Event[dev])}"
                return ret

            elif act == 'tryA':
                # Try specific animation on specific device
                ret = f"tryA|{Event}|{dev}:{Event[dev][index]}"
                return ret
            old_selection = selection

    def animations_menu(self, events, selected_event=None):
        '''
        Leds animations menu
        '''
        selected = 1
        index = 0
        for event in events:
            index += 1
            if selected_event == event:
                selected = index

        nb_elements = len(events)
        self.dmd.send_text(f"{self.lang.translate('animations')}", tempo=2)

        refresh = True

        while True:
            click_zones = {}
            shortcuts = []
            cursor = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('animations-menu')

            index = 0
            for event in events:
                index += 1
                click_zones[event] = self.menu_item((index, nb_elements, selected), (None, f"event-{event}", BTN_CHOICE, None), align = 'Half')
                shortcuts.append(event)
                cursor[event] = index

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            else:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])

            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space', 'backspace'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 1)
            if selected <= nb_elements:
                text = f"event-{shortcuts[selected - 1]}"
            else:
                text = 'back'
            self.dmd.send_text(f"{self.lang.translate(text)}")

            # Shortcuts
            if key in shortcuts:
                selected = int(cursor[key])
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS or key in RIGHT_KEYS:
                return shortcuts[selected - 1]

    def customization_menu(self, customization):
        '''
        Customization menu
        '''
        selected = 1
        Cust = []
        avoid = []

        try:
            themes = [os.path.basename(f.path) for f in os.scandir(self.config.themes_dir) if f.is_dir() ]
        except:
            themes = []

        nb_elements = 0
        for option in customization:
            min_value = 1
            max_value = 10000
            zero = False
            if option in ('startpercent', 'nbcol', 'resx', 'resy', 'fullscreen', 'masterserver', 'endgamestats', 'videosound_multiplier', 'pnj_time'):
                avoid.append([option, customization[option], '', 0, []])
                continue

            if option in ('endgamestats', 'bypass-stats', 'onscreenbuttons', 'fullscreen', \
                    'keeporder', 'play_firstname', 'print_dartstroke', 'light_target', 'light_strip', \
                    'competition_mode', 'exhibition_mode', 'illumination_mode'): #by Manu script.
                option_type = 'check'
                option_values = []
                if customization[option] == 'False' or customization[option] is False:
                    customization[option] = False
                else:
                    customization[option] = True
            elif option in ('sound_multiplier'):
                option_type = 'slider'
                min_value = 0
                max_value = 100
                option_values = 5
                zero = 1
            elif option in ('soundvolume'):
                option_type = 'slider'
                min_value = 0
                max_value = 100
                option_values = 10
                zero = 1
            elif option in ('pnj_time', 'blinktime', 'releasedartstime', 'waitevent_time', 'nextplayer_sound_duration'):
                option_type = 'slider'
                min_value = 500
                max_value = 5000
                zero = 1000         # Divisé par
                option_values = 500 # Pas
                if option == 'waitevent_time':
                    min_value = 15000
                    max_value = 180000
                    option_values = 3000
                if option == 'nextplayer_sound_duration':
                    min_value = 3000
                    max_value = 30000
                if option == 'releasedartstime':
                    min_value = 0
                    max_value = 30000
            elif option in ('solo', 'resx', 'resy', 'nbcol'):
                option_type = 'number'
                option_values = []
                if option == 'solo':
                    min_value = -1
                    zero = True
                elif option in ('resx', 'resy'):
                    min_value = 200
                    if option == 'resx':
                        max_value = 1920
                    else:
                        max_value = 1080
                elif option == 'nbcol':
                    min_value = 6
                    max_value = 6
            elif option == 'locale':
                option_type = 'dropdown'
                option_values = []
                for l in [name for name in os.listdir('locales') if os.path.isdir(os.path.join('locales', name)) ]:
                    option_values.append((l, self.lang.translate(l)))
            elif option == 'font':
                option_type = 'dropdown'
                option_values = []
                for element in [name for name in os.listdir('fonts') if name.endswith('.ttf') ]:
                    option_values.append((element, element.replace('.ttf', '')))
                if os.path.isdir(f'{self.config.user_dir}/fonts'):
                    for element in [name for name in os.listdir(f'{self.config.user_dir}/fonts') if name.endswith('.ttf') ]:
                        option_values.append((element, element.replace('.ttf', '')))

                option_values.sort()
            elif option == 'colorset':
                option_type = 'dropdown'
                option_values = [('clear', 'clear'), ('dark', 'dark'), ('purple', 'purple')]
                for theme in themes:
                    option_values.append((theme, theme))
            elif option == 'debuglevel':
                option_type = 'dropdown'
                option_values = [('0', 'Debug'), ('1', 'Warnings'), ('2', 'Errors'), ('3', 'Fatal errors'), ('4', 'Infos'), ('5', 'No logs')]
            elif option == 'videos':
                option_type = 'dropdown'
                option_values = [('0', 'videos-none'), ('1', 'videos-special'), ('2', 'videos-all')]
            elif option == 'preferedcategory':
                option_type = 'dropdown'
                option_values = [('classic', 'classic'), ('fun', 'fun'), ('sport', 'sport')]
            else:
                option_type = 'string'
                option_values = []
                min_value = 1
                if option == 'netgamecreator':
                    max_value = 12
                else:
                    max_value = 64
            Cust.append([option, customization[option], option_type, max_value, option_values, min_value, zero])
            nb_elements += 1

        old_selection = None
        while True:
            click_zones = {}
            shortcuts = []
            cursor = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('customization')

            index = 0
            for option in Cust:
                index += 1

                if option[2] == 'check' and not option[1]:
                    value = False
                    Cbtn = BTN_CHECK
                elif option[2] == 'check' and option[1]:
                    value = True
                    Cbtn = BTN_CHECK
                elif option[2] == 'dropdown':
                    value = ''
                    for element in option[4]:
                        if element[0] == option[1] or element[1] == option[1]:
                            value = element[1]
                    Cbtn = BTN_DROPDOWN
                else:
                    value = option[1]
                    Cbtn = BTN_VALUE

                if option[2] == 'slider':
                    number = float(value)

                    if (number / option[6]) % 1 == 0:
                        value = int(int(value) / option[6])
                    else:
                        value = int(value) / option[6]
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', option[0], Cbtn, value), align='Full')
                else:
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', option[0], Cbtn, value), align='Full')
                shortcuts.append(f'F{index}')
                cursor.append(click_zones[f'F{index}'])

            if selected <= nb_elements:
                if Cust[selected - 1][2] == 'numeric':
                    allowed = ['arrows', 'fx', 'num', 'math']
                elif Cust[selected - 1][2] == 'Alpha':
                    allowed = ['arrows', 'fx', 'num', 'math', 'alpha']
                else:
                    allowed = ['arrows', 'fx']
            else:
                allowed = ['arrows', 'fx']

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            if selected <= nb_elements:
                selection = click_zones[f'F{selected}']
            elif nb_elements + 1 == selected:
                selection = click_zones['escape']
            elif nb_elements + 2 == selected:
                selection = click_zones['save']
            else:
                selection = None

            ################
            # Update screen
            if old_selection is None:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=[old_selection, selection])

            key = self.rpi.listen_inputs(allowed, ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space', 'backspace'], events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation in menu
            selected = self.navigate(selected, key, nb_elements, 2, 2)

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                customization = {}
                for option in Cust:
                    customization[option[0]] = option[1]
                for option in avoid:
                    customization[option[0]] = option[1]

                return customization

            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'
            elif key in RIGHT_KEYS and selected <= nb_elements:
                key = 'enter'
            elif key in LEFT_KEYS and selected <= nb_elements and Cust[selected - 1][2] == 'check':
                key = 'enter'
            elif len(key) == 1 and selected <= nb_elements and Cust[selected - 1][2] == 'Alpha':
                key = 'enter'

            if key in ENTER_KEYS:
                if Cust[selected - 1][2] == 'check':
                    if Cust[selected - 1][1]:
                        Cust[selected - 1][1] = False
                    else:
                        Cust[selected - 1][1] = True
                elif Cust[selected - 1][2] == 'slider':
                    act_value = float(Cust[selected - 1][1])
                    min_value = Cust[selected - 1][5]
                    max_value = Cust[selected - 1][3]
                    step = Cust[selected - 1][4]
                    title = Cust[selected - 1][0]
                    diviser = Cust[selected - 1][6]

                    tmp = self.slider(title, act_value, min_value, max_value, step=step, diviser=diviser)
                    if tmp != 'escape':
                        Cust[selected - 1][1] = str(tmp)
                    # Force refresh off screen
                    selection = None
                elif Cust[selected - 1][2] == 'dropdown':
                    if Cust[selected - 1][0] == 'font':
                        tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, Cust[selected - 1][4], special='font', navigate=Cust[selected - 1][1])
                    else:
                        tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, Cust[selected - 1][4], navigate=Cust[selected - 1][1])
                    if tmp != 'escape':
                        Cust[selected - 1][1] = tmp
                    # Force refresh off screen
                    selection = None
                else:
                    click_zone = cursor[selected - 1]
                    tmp = self.input_value_item(Cust[selected - 1][2], \
                            Cust[selected - 1][1], \
                            Cust[selected - 1][5], \
                            Cust[selected - 1][3], \
                            text=Cust[selected - 1][0], \
                            zero=Cust[selected - 1][6])
                    if tmp != 'escape':
                        if Cust[selected - 1][2] == 'number':
                            Cust[selected - 1][1] = int(tmp)
                        else:
                            Cust[selected - 1][1] = tmp
            old_selection = selection

    def server_menu(self, NetClient, ServerList):
        '''
        Server Menu : Choice server before create/join network games
        '''
        nb_elements = len(ServerList)
        if nb_elements == 0 :    # No prefered servers
            return 'noserver'

        if nb_elements == 1 : #Only one, no choice, skip the screen
            return ServerList[0]

        # Draw bg
        self.display_background()

        # Titles
        self.menu_header('server-menu')

        self.message(['check-server'], wait = 0)

        self.update_screen()
        List = []

        for server in ServerList:
            txt = server.split('.')[0]
            if NetClient.test_host(server) == True:
                Valid = True
            else:
                Valid = False
                txt += " ({self.lang.translate('server-unreachable')})"
            List.append((server, Valid, txt))

        else :    # You have to make a choice
            selected =1

            while True:
                # Round the selected clock ;)
                if selected > nb_elements + 2:
                    selected = 1
                if selected == 0:
                    selected = nb_elements + 2

                click_zones = {}

                # Draw bg
                self.display_background()

                # Titles
                self.menu_header('server-menu')

                shortcuts = []
                index = 0
                for s in List:
                    index += 1
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f"F{index}", s[2], BTN_CHOICE, None), valid=s[1])
                    shortcuts.append(f'F{index}')

                # go back and next
                click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

                ################
                # Update screen
                self.update_screen()

                key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

                # Click cases
                clicked = self.is_clicked(click_zones, key)
                if clicked:
                    key = clicked

                # Navigation menu
                selected = self.navigate(selected, key, nb_elements, 1, 1)

                #Shortcuts
                if key in shortcuts:
                    key = 'enter'
                    selected = int(clicked.replace('F', ''))

                # Keyboard cases
                if key in ENTER_KEYS or key in RIGHT_KEYS:
                    if selected == nb_elements + 1:
                        key = 'escape'
                    elif selected == nb_elements + 2:
                        key = 'enter'
                    elif List[selected - 1][1]:
                        return List[selected - 1][0]

                elif key in ESCAPE_KEYS :    # Previous menu
                    return 'escape'

    def infos_menu(self, Conf):
        '''
        Infos menu
        '''
        import shutil
        import psutil

        ratio = 1 / 3

        while True:
            total, used, free = shutil.disk_usage("/")

            # Draw bg
            self.display_background()

            # Rpi version:
            # cat /proc/device-tree/model

            # Titles
            self.menu_header(self.lang.translate('technical-informations'))

            self.display_row(1, 2, 1, [("Hardware", 1 / 2), ('Version', 1 / 2)], ratio, offset=-2)
            self.display_row(2, 2, 0, [("Raspberry", 1 / 2), (Conf.rpi_version, 1 / 2)], ratio, offset=-2)

            self.display_row(1, 4, 1, [("Software", 1 / 2), ('Version', 1 / 2)], ratio, 1)
            self.display_row(2, 4, 0, [("Raspydarts", 1 / 2), (Conf.pyDartsFullVersion, 1 / 2)], ratio, 1)

            self.display_row(3, 4, 0, [("Python", 1 / 2), (sys.version.split(' ')[0], 1 / 2)], ratio, 1)
            self.display_row(4, 4, 0, [("Pygame", 1 / 2), (str(pygame.version.ver), 1 / 2)], ratio, 1)

            if len(self.ips) > 0:
                self.display_row(1, 1 + len(self.ips), 1, [("Interface", 1 / 2), ("Adresse IP", 1 / 2)], ratio, 6)

            index = 1
            for ip in self.ips:
                index += 1
                self.display_row(index, 1 + len(self.ips), 0, [(ip[0], 1 / 2), (ip[1], 1 / 2)], ratio, 6)

            cpu_freq = f"{psutil.cpu_freq().current:.0f} ({psutil.cpu_freq().min:.0f} - {psutil.cpu_freq().max:.0f})"

            self.display_row(1, 6, 1, [("Information", 1 / 2), ("Value", 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(2, 6, 0, [("Résolution", 1 / 2), (f"{self.res_x} x {self.res_y}", 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(3, 6, 0, [("Disk occupation", 1 / 2), ("{} %".format(round(100 * used / total, 1)), 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(4, 6, 0, [("RAM occupation", 1 / 2), ("{} %".format(psutil.virtual_memory()[2]), 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(5, 6, 0, [("CPU usage", 1 / 2), ("{} %".format(psutil.cpu_percent()), 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(6, 6, 0, [("CPU frequency", 1 / 2), (cpu_freq, 1 / 2)], ratio, 8 + len(self.ips))

            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx', 'alpha', 'math'],
                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                        'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'], \
                        timeout = 2000)
            if key is not False:
                break

    def main_menu(self):
        '''
        Choose Game Type : Local - Network
        '''
        selected = 1
        if bool(self.config.get_value('SectionGlobals', 'exhibition_mode')):
            nb_elements = 3
        else:
            nb_elements = 6

        #self.dmd.send_text(self.lang.translate('Welcome') + "!")
        self.dmd.send_text('Raspydarts')
        refresh = True
        while True:

            click_zones = {}

            # Draw bg
            self.display_background(display_version=True)

            # Titles
            self.menu_header(self.lang.translate('game-type-menu'))

            # Local game type
            click_zones['F1'] = self.menu_item((1, nb_elements, selected), ("F1", "game-type-local", \
                    BTN_CHOICE, None), exit=False)

            # Join network game
            click_zones['F2'] = self.menu_item((2, nb_elements, selected), ("F2", "game-type-master", \
                    BTN_CHOICE, None), exit=False)

            # Create network game
            click_zones['F3'] = self.menu_item((3, nb_elements, selected), ("F3", "game-type-manual", \
                    BTN_CHOICE, None), exit=False)

            # Preferences menu
            if not bool(self.config.get_value('SectionGlobals', 'exhibition_mode')):
                click_zones['F4'] = self.menu_item((4, nb_elements, selected), ("F4", "miscellaneous", \
                        BTN_CHOICE, None), exit=False)

            # Restart game
            #click_zones['F11'] = self.menu_item((5, nb_elements, selected), ("F11", "menu-restart", \
            #        BTN_CHOICE, None), space = 0.5, exit=False)

            if not bool(self.config.get_value('SectionGlobals', 'exhibition_mode')):
                # Back to desktop
                click_zones['F12'] = self.menu_item((5, nb_elements, selected), ("F12", "back-to-desktop", BTN_CHOICE, None), space=1.5, exit=False)

                # Exit
                click_zones['escape'] = self.menu_item((6, nb_elements, selected), ("ESC", "exit", BTN_CHOICE, None), space=2, exit=False)

            ################
            # Update screen
            if refresh or True:
                self.update_screen()
                refresh = False
            else:
                self.update_screen(rect_array=[click_zones[click_zone] for click_zone in click_zones])

            key = self.rpi.listen_inputs(['arrows', 'fx', 'alpha', 'math'],
                 ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'],
                 events=[(self.wait_event_time, 'EVENT', 'wait')])
                 #events=[(3000, 'EVENT', 'wait'), (500, 'LIGHT', ['LIGHT_NAVIGATE'])])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            selected = self.navigate(selected, key, nb_elements, 0, 0)

            # Keyboard cases
            if key in ENTER_KEYS :    # First position please, because eventually construct F1, F2 or F3
                #if selected == 5:
                #    key = 'F11'
                if selected == 5:
                    key = 'F12'
                elif selected == 6:
                    key = 'escape'
                else:
                    key = f'F{selected}'

            if key == 'F1':
                return 'local'

            if key == 'F2':
                return 'netjoin'    # netmaster

            if key == 'F3':
                return 'netcreate'    # netmanual

            if key == 'F4':
                return 'miscellaneous'

            if key == 'F9':
                return 'infos'

            if key == 'F11':
                return 'restart'

            if key == 'F12':
                return 'quit'

            if key == 'escape':
                # Properly shutdown Rpi
                response = self.wait_validation(self.lang.translate('realy-stop'))
                if response:
                    return 'shutdown'

    def extract_version(self, file_name):
        '''
        Return version of file, included in his name
        '''
        version = re.search(r'^.*V([0-9._]*)\..*$', file_name)

        return version.group(1)

    def get_backups_list(self):
        '''
        Get list and infos from availables backup files
        '''
        file_list = []
        tmp_list = []

        if len(glob.glob('backup')) > 0:
            for backup in glob.glob('backup/raspydarts*tgz') + glob.glob('backup/update*tgz'):
                tmp_list.append(backup)

            tmp_list.sort(key = self.extract_version, reverse=True)

            for backup in tmp_list:
                data = backup.split('_')
                file_list.append((backup, data[1], data[2], data[3]))

            return file_list
        return None

    def get_games_list(self, category='classic'):
        '''
        Get Game List from local game folder
        '''
        fileiter = (os.path.join(root, f)
                    for root, _, files in os.walk(f'games/{category}')
                    for f in files)
        fileiter = sorted(fileiter)
        menu_data = [self.lang.translate('game-list')]
        games = []
        for foundfiles in fileiter:
            name, extension = os.path.splitext(foundfiles)
            if extension == '.py' and os.path.basename(name) != '__init__':
                games.append(os.path.basename(name).replace('_', ' '))
                menu_data.append(os.path.basename(name).replace('_', ' '))
        # Display all games names
        self.logs.log("DEBUG", f"Found these games : {'/'.join(menu_data[1:])}")
        return games

    def get_description(self, game):
        '''
        Get Game description (from language file)
        '''
        description = []
        try:
            description = self.lang.translate(f"Description-{game.replace(' ', '_')}")
        except:
            description.append(self.lang.translate('game-no-desc'))
            self.logs.log("WARNING", f"Unable to get a description for game {game}")
        return description

    def game_category_menu(self, category=None):
        '''
        Menu which display a table to choose the category of the game
        '''
        categories = ['classic', 'fun', 'sport']
        if category is None:
            selected = 1
        else:
            selected = 1 + categories.index(category)

        shortcuts = []
        shortcuts.append('F1')
        shortcuts.append('F2')
        shortcuts.append('F3')
        nb_elements = 3

        refresh = True

        while True:
            if selected == 1:
                self.dmd.send_text(self.lang.translate('dmd-game-classic'))
            elif selected == 2:
                self.dmd.send_text(self.lang.translate('dmd-game-fun'))
            else:
                self.dmd.send_text(self.lang.translate('dmd-game-sport'))
            click_zones = {}
            # Draw background
            self.display_background()

            # Screen Titles
            self.menu_header(self.lang.translate('game-cat'))

            click_zones['F1'] = self.logo_item((1, nb_elements, selected), 'menu_classic', 3, 'Center', limit_height=self.res['y'] / 3, menu=True)
            click_zones['F2'] = self.logo_item((2, nb_elements, selected), 'menu_fun', 3, 'Center', limit_height=self.res['y'] / 3, menu=True)
            click_zones['F3'] = self.logo_item((3, nb_elements, selected), 'menu_sport', 3, 'Center', limit_height=self.res['y'] / 3, menu=True)

            # Arrow to go back and next
            click_zones['escape'] = self.display_button(4 == selected, 'back', special='escape')

            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            else:
                self.update_screen(rect_array=[click_zones[click_zone] for click_zone in click_zones])


            key = self.rpi.listen_inputs(
                    ['arrows', 'fx', 'alpha', 'math'],
                    ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                    'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN',
                    'enter', 'space'],
                    events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                if clicked in shortcuts:
                    selected = int(clicked[1::])
                    key = 'enter'
                else:
                    key = clicked

            # Navigation menu
            selected = self.navigate(selected, key, nb_elements, 1, 1, left_right=True)

            # Keyboard cases
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS + SAVE_KEYS:
                return categories[selected - 1]

    def game_menu(self, games_list, favorites, selected_game=None):
        '''
        Menu which display a table to choose the game
        '''
        selected = 1

        self.dmd.send_text(self.lang.translate('dmd-game-choice'), tempo=1)

        games = []

        index = 1
        # Favorites first
        for game in games_list:
            if game in favorites:
                games.append(game)
                if selected_game is not None and selected_game == game:
                    selected = index
                index += 1

        # and others
        for game in games_list:
            if game not in favorites:
                games.append(game)
                if selected_game is not None and selected_game == game:
                    selected = index
                index += 1

        nb_elements = len(games)
        if nb_elements > 16:
            nb_column = 5
        else:
            nb_column = 4

        refresh = True
        old_selection = None

        while True:
            click_zones = {}
            shortcuts = []
            # Draw background
            self.display_background()

            # Screen Titles
            self.menu_header(self.lang.translate('game-list'))

            index = 1
            for game in games:     # Display Game menu
                if index == selected:
                    game_desc_rect = self.game_description(game, False)
                    game_desc_rect = [(game_desc_rect[0], game_desc_rect[1], game_desc_rect[2], game_desc_rect[3])]

                shortcut = f'F{index}'
                click_zones[shortcut] = self.logo_item((index, len(games), selected), game.replace(' ', '_'), nb_column, 'Left', border_radius=25)
                shortcuts.append(shortcut)
                index += 1

            # Arrow to go back and next
            click_zones['escape'] = self.display_button(index == selected, 'back', special='escape')

            if selected <= nb_elements:
                selection = click_zones[f'F{selected}']
            elif nb_elements == selected:
                selection = click_zones['escape']
            else:
                selection = None

            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None:
                self.update_screen(rect_array=[click_zones[click_zone] for click_zone in click_zones] + game_desc_rect)
            else:
                self.update_screen(rect_array=[old_selection, selection] + game_desc_rect)

            key = self.rpi.listen_inputs(
                    ['arrows', 'fx', 'alpha', 'math'],
                    ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                    'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN',
                    'enter', 'space'],
                    events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                if clicked in shortcuts:
                    selected = int(clicked[1::])
                    key = 'enter'
                else:
                    key = clicked

            # Navigation menu
            selected = self.navigate(selected, key, nb_elements, 1, 1, \
                    item_per_line=nb_column, left_right=True)

            if selected <= nb_elements:
                self.dmd.send_text(games[selected - 1].replace('_', ' '))
            else:
                self.dmd.send_text(self.lang.translate('back'))
            # Keyboard cases
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS + SAVE_KEYS + CONTINUE_KEYS:
                self.selectedgame = games[selected - 1]
                return self.selectedgame

            old_selection = selection

    def display_row(self, item_id, total, selected, columns, ratio=1, offset=0, center=True, align=None):
        '''
        Menu to display a row (to display an array)
        '''

        # Columns = [("Title1", pct1), ("Title2", pct2), ... ]

        # 1st cell position
        if center:
            min_x = self.res_x_16
        elif align == 'right':
            min_x = int(self.res['x'] * 3 / 4)
        else:
            min_x = int(self.res['x'] / 2)
        min_y = 4 * self.res_y_16

        # Line size
        if center:
            row_width = int(self.res['x'] * 14 / 16)
        elif align == 'right':
            row_width = int(self.res['x'] * 7 / 32)
        else:
            row_width = int(self.res['x'] * 7 / 16)
        row_height = int((self.res['y'] * 10 / 16) / (max(15, total)))

        # Apply ratio
        if ratio < 1:
            row_width = int(row_width * ratio)
            if center:
                min_x = int((self.res['x'] - row_width) / 2)

        cell_x = min_x
        cell_y = min_y + row_height * (item_id - 1 + offset)

        index = 0
        for column in columns:
            index += 1
            # Cell size
            cell_width = int(row_width * column[1])

            # Cell value
            value = column[0]

            # Cell color
            if item_id == selected:
                cell_color = self.colorset['menu-selected']
                cell_text_color = self.colorset['menu-text-black']
            elif item_id == 1:
                cell_color = self.colorset['menu-item-white']
                cell_text_color = self.colorset['menu-text-black']
            elif item_id % 2 == 0:
                cell_color = self.colorset['menu-item-black']
                cell_text_color = self.colorset['menu-text-white']
            else:
                cell_color = self.menu_color(self.colorset['menu-buttons'])
                cell_text_color = self.colorset['menu-text-black']

            if item_id == 1 and index == 1:
                corners = 'TopLeft'
            elif item_id == 1 and index == len(columns):
                corners = 'TopRight'
            elif item_id == total and index == 1:
                corners = 'BottomLeft'
            elif item_id == total and index == len(columns):
                corners = 'BottomRight'
            else:
                corners = 'None'

            self.new_blit_rect(cell_x, cell_y, cell_width, row_height, cell_color, corners=corners)
            self.blit_text(value, cell_x, cell_y, cell_width, row_height, cell_text_color, \
                    align='Center')

            cell_x += cell_width

        return (min_x, cell_y, row_width, row_height)

    def display_big_row(self, item_id, total, selected, columns, offset=0):
        '''
        Menu to display a big row (to display an array)
        '''
        # Columns = [("Title1", pct1), ("Title2", pct2), ... ]

        row_width = int(self.res['x'] * 14 / 16)
        row_height = int((self.res['y'] * 10 / 16) / (max(5, total)))

        cell_x = self.res_x_16
        cell_y = 3 * self.res_y_16 + row_height * (item_id - 1 + offset)

        for column in columns:
            # Cell size
            cell_width = int(row_width * column[1])

            # Cell value
            text = column[0]

            # Cell color
            if item_id == 1:
                cell_color = self.colorset['menu-item-black']
                cell_text_color = self.colorset['menu-text-white']
            elif item_id == selected:
                cell_color = self.colorset['menu-selected']
                cell_text_color = self.colorset['menu-text-white']
            elif item_id % 2 == 1:
                cell_color = self.colorset['menu-buttons']
                cell_text_color = self.colorset['menu-text-black']
            else:
                cell_color = self.menu_color(self.colorset['menu-buttons'])
                cell_text_color = self.colorset['menu-text-black']

            self.new_blit_rect(cell_x, cell_y, cell_width, row_height, cell_color)
            self.blit_text(text, cell_x, cell_y, cell_width, row_height, cell_text_color, \
                    align='Center')

            cell_x += cell_width

        return (self.res_x_16, cell_y, row_width, row_height)

    def net_game_list(self, master_client, number_of_players, host, port):
        '''
        Menu which display a table to choose net game (MasterServer Client)
        '''
        self.rpi.shift = False    # Reinit Kbd Shift status
        # Display "Pending connexion..."
        self.display_background()
        self.message([self.lang.translate('master-client-connecting')], wait = 0)
        masterclientpolltime = int(self.config.get_value('SectionAdvanced', 'masterclientpolltime'))
        selected = 1

        while True:
            try:
                self.logs.log("DEBUG", f"Try to connect to {host}:{port}")
                master_client.connect_master(host, port)
                self.logs.log("DEBUG", f"Connected")
            except:
                self.logs.log("ERROR", f"Unable to reach Master Server : {host}:{port}")
                self.display_background()
                self.message([self.lang.translate('master-client-no-connection')])
                return 'escape'    # Tels master loop to turn back to previous menu

            game_list = master_client.wait_list(number_of_players)    # get and clean server list
            self.logs.log("DEBUG", f"game_list={game_list}")
            master_client.close_connection()
            self.logs.log("DEBUG", f"Disconnected")

            # In case of network issue
            if game_list is False:
                # Tell the user there is a network error
                msg = self.lang.translate('network-error')
                # Display error msg
                self.message([msg], 1000)
                # Simulate an escape key (back to menu)
                return 'escape'

            if game_list == 0:
                game_list = {}
            # In case of a list containing something (or not)
            self.logs.log("DEBUG", f"Received a list with {len(game_list)} games")
            nb_elements = len(game_list) + 1    # Add first line

            while True:
                # Display basis
                self.display_background()
                self.menu_header(self.lang.translate('master-client-title'), \
                        self.lang.translate('master-client-refresh'))

                click_zones = {}
                self.display_row(0, nb_elements, False, [('game-name', 4 / 16), \
                        ('game-type', 4 / 16), ('creator', 6 / 16), \
                        ('players', 2 / 16)], 3 / 4)

                index = 0
                for game in game_list:
                    click_zones[f'select|{index}'] = self.display_row(1 + index, nb_elements, \
                            selected, [(game['GAMENAME'], 4 / 16), \
                            (game['GAMETYPE'].replace('_', ' '), 4 / 16), \
                            (game['GAMECREATOR'], 6 / 16), (str(game['PLAYERS']), 2 / 16)], 3 / 4)
                    index += 1

                click_zones['escape'] = self.display_button(index + 2 == selected, 'back', special='escape')
                #click_zones['escape'] = self.display_button(index + 3 == selected, 'refresh', special='refresh')

                self.update_screen()    # refresh screen

                # Listen for any input
                key = self.rpi.listen_inputs(['arrows', 'alpha'], ['enter', 'escape', 'space', \
                        'TOGGLEFULLSCREEN', 'single-click'], \
                        timeout=max(1000, masterclientpolltime))

                if not key:
                    # Refresh screen
                    break

                # Mouse
                clicked = self.is_clicked(click_zones, key)
                if clicked:
                    if "select|" in clicked:
                        selected = int(clicked.split('|')[1]) + 1
                        key = 'enter'
                    else:
                        key = clicked

                # Navigation menu
                # Avoid 1st line => titles
                selected = max(self.navigate(selected, key, nb_elements, 2, 2), 2)

                # Keyboard
                if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                    return 'escape'

                if key in ENTER_KEYS and selected <= nb_elements:
                    return game_list[selected-2]['GAMENAME']    # Header not counted

    def game_description(self, game, full=False):
        '''
        Display game's description
        '''

        # Marges
        marge_x = int(self.res['x'] / 64)
        marge_y = int(self.res['y'] / 64)

        # Main box
        box_pos_x = int(self.res['x'] / 2)
        box_width = int(self.res['x'] / 2 - marge_x)
        box_pos_y = 3 * self.res_y_16
        box_height = 11 * self.res_y_16

        # Image box
        logo_pos_x = box_pos_x
        logo_pos_y = box_pos_y
        logo_width = box_width
        logo_height = int(box_height / 3)

        # Description box
        text_pos_x = box_pos_x
        text_pos_y = box_pos_y + marge_y
        text_width = box_width
        text_height = box_height - marge_y

        if not full:
            text_pos_y += logo_pos_y
            text_height -= logo_height

        # Game description
        description = self.get_description(game)

        # cut description for not full mode
        if not full:
            description = description.split("-----\n")[0]
        else:
            if "-----\n" in description:
                description = description.split("-----\n")[1]

        color = self.colorset['description-bg']
        if color is not None:
            # New surface
            #Surface = pygame.Surface((box_width, box_height))
            #Surface.set_alpha(192)
            #Surface.fill(self.colorset['description-bg'])
            self.new_blit_rect(box_pos_x, box_pos_y, box_width, box_height, color, corners='All', \
                    border_radius=50, Alpha=192)

        # Add Image if not full desc
        if not full:
            image = self.file_class.get_full_filename(f"logos_menu/{game.replace(' ', '_')}", 'images')
            self.display_image(image, logo_pos_x, logo_pos_y, logo_width, logo_height, False, True, True)

        # Add description
        description = description.splitlines()
        nb_lines = len(description)
        font = pygame.font.Font(self.defaultfontpath, 50)

        index = 0
        maxsize = 0
        for line in description:
            font_size = font.size(line)
            if font_size[0] > maxsize:
                maxsize = font_size[0]
                longest = index
            index += 1

        scaled_text = self.scale_text(description[longest], text_width - 2 * marge_x, \
                (text_height - 2 * marge_y) / nb_lines)
        font_size = scaled_text[0]
        height = text_height / (2 * max (8, index))    # Pour eviter des intervalles trop grand entre les lignes.

        font = pygame.font.Font(self.defaultfontpath, font_size)

        index = 0
        for line in description:
            index += 2
            if index == 2 and not full:
                font_title = pygame.font.Font(self.defaultfontpath, 50)
                text = font_title.render(line, True, self.colorset['description-game'])
                self.blit(text, [text_pos_x + text_width / 2 - font_title.size(line)[0] / 2, \
                        text_pos_y + height * (index - 1) + marge_y / 2])
            else:
                text = font.render(line, True, self.colorset['description-text'])
                self.blit(text, [text_pos_x + marge_x, text_pos_y + height * (index - 2) + marge_y / 2])

        return pygame.Rect(box_pos_x, box_pos_y, box_width, box_height)

    def options_menu(self, game_options, game, number_of_players):
        '''
        Game options menu
        '''

        self.logs.log("DEBUG", "Waiting for game options")

        # Show message on Raspydarts DMD
        self.dmd.send_text(self.lang.translate('game-options'), tempo=1)
        self.dmd.send_text(game.upper().replace('_', ' '))

        # List avaiables themes
        try:
            themes = [os.path.basename(f.path) for f in os.scandir(self.config.themes_dir) if f.is_dir() ]
        except:
            themes = []
        themes.append('default')

        teaming = False
        if number_of_players % 2 == 0:
            teaming = True

        nb_elements = 0
        selected = 3
        for option_name, option_value in game_options.items():
            if (option_name.endswith('Teaming') or option_name.endswith('optionteamscore')) \
                    and not teaming:
                continue
            if option_name == 'theme' and len(themes) == 0:
                continue
            nb_elements += 1

        selected += nb_elements

        refresh = True
        old_selection = None
        while True:
            # Display Background
            self.display_background()

            # Display menu header
            self.menu_header(f"{self.lang.translate('game-options')} {game.replace('_', ' ')}")

            #Display game description and game options
            game_desc_rect = self.game_description(game, True)

            click_zones = {}
            shortcuts = []
            cursor = {}
            options = {}
            values = []

            index = 1
            for option_name, option_value in game_options.items():

                text = f'{game}-{option_name}'
                if (option_name.endswith('Teaming') or \
                        option_name.endswith('optionteamscore')) and not teaming:
                    continue
                if option_name == 'theme' and len(themes) == 0:
                    continue

                if isinstance(option_value, bool):
                    option_type = BTN_CHECK    # Boolean
                    value = False
                    if option_value is True:
                        value = True
                elif option_name == 'theme':
                    text = 'colorset'
                    option_type = BTN_DROPDOWN
                    values = [(theme, theme) for theme in themes]
                    value = option_value
                else:
                    option_type = BTN_VALUE    # free entry (Alphanum)
                    value = option_value

                shortcut = f'F{index}'
                options[index] = [value, option_type, option_name]

                click_zones[shortcut] = self.menu_item((index, nb_elements, selected)
                        , (shortcut, f'{text}', option_type, value), align='Left')
                shortcuts.append(shortcut)
                cursor[index] = shortcut
                index += 1

            # Arrow to go back and next
            click_zones['escape'] = self.display_button(index == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(index + 1 == selected, 'save', special='refresh')
            click_zones['continue'] = self.display_button(index + 2 == selected, 'continue', special='return')

            if selected < nb_elements:
                selection = click_zones[f'F{selected}']
            elif index == selected:
                selection = click_zones['escape']
            elif index + 1 == selected:
                selection = click_zones['save']
            elif index + 2 == selected:
                selection = click_zones['continue']
            else:
                selection = None

            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None or True:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=[old_selection, selection])

            key = self.rpi.listen_inputs(['num', 'fx', 'arrows'], \
                 ['BACKUPBUTTON', 'EXTRABUTTON', 'BTN_NEXTPLAYER', 'PLAYERBUTTON', 'GAMEBUTTON', 'return', \
                 'enter', 'escape', 'TOGGLEFULLSCREEN', 'single-click', 'space', 'backspace'],
                 events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Input - mouse
            clicked = self.is_clicked(click_zones, key)

            if clicked:
                key = clicked
            else:
                key = str(key)

            # Navigation in menu
            selected = self.navigate(selected, key, nb_elements, 3, 3)

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                self.config.set_game_config(game, game_options)
                self.config.write_file()
                self.message(['options-saved'], None, self.colorset['menu-text-black'], 'middle', 'big')
                refresh = True
                continue

            #if key in SAVE_KEYS + CONTINUE_KEYS or key == 'BTN_NEXTPLAYER' \
            if key in CONTINUE_KEYS and key != 'BTN_NEXTPLAYER' \
                    or (key in ENTER_KEYS and selected == nb_elements + 3):
                self.game_options = game_options
                return game_options

            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'

            if key in ENTER_KEYS or key == 'BTN_NEXTPLAYER':
                # Toggle on edit mode with Fx keys
                if options[selected][1] == BTN_CHECK:
                    if options[selected][0]:
                        game_options[options[selected][2]] = False
                    else:
                        game_options[options[selected][2]] = True
                elif options[selected][1] == BTN_DROPDOWN:
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, values)
                    if tmp != 'escape':
                        game_options[options[selected][2]] = tmp
                    refresh = True

                else:
                    click_zone = click_zones[f'F{selected}']
                    if options[selected][2] == 'max_round':
                        min_value = 2
                        max_value = 99
                    elif options[selected][2] == 'Time':
                        min_value = 500
                        max_value = 10000
                    elif options[selected][2] == 'startingat':
                        min_value = 181
                        max_value = 10000
                    else:
                        min_value = 0
                        max_value = 500

                    tmp = self.input_value_item('number', '', min_value, max_value, text=f'{game}-{options[selected][2]}')
                    if tmp != 'escape':
                        game_options[options[selected][2]] = tmp
            elif key in LEFT_KEYS + RIGHT_KEYS and selected <= nb_elements and \
                    options[selected][1] == BTN_CHECK:
                if options[selected][0]:
                    game_options[options[selected][2]] = False
                else:
                    game_options[options[selected][2]] = True

        old_selection = selection

    def display_version(self):
        self.blit_text(self.config.pyDartsFullVersion, self.margin, \
            self.res['y'] * 1.05 / 30, self.res['x'] * 1.9 / 16, \
            self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], align='Left', margin=False)

    def display_rpi_version(self):
        '''
        Display version of raspydarts on top
        '''
        self.blit_text(self.config.rpi_version, self.res['x'] * 3 / 4, \
                self.res['y'] * 1.05 / 30, self.res['x'] / 4 - self.margin, \
                self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], align='Right', margin=False)

    def display_ips(self, big=False):
        '''
        Display ip address on top
        '''
        index = 0
        if big:
            for ip in self.ips:
                self.blit_text(ip[1], self.res['x'] * 12 / 16, self.res['y'] * (13 + index) / 16, \
                        self.res['x'] / 8, self.res_y_16, self.colorset['menu-text-white'], margin=False)
                index += 1
        else:
            ips = [ip[1] for ip in self.ips]
            self.blit_text(' / '.join(ips), self.res['x'] * 3 / 4, self.res['y'] * 2.05 / 30, \
                    self.res['x'] / 4 - self.margin, self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], \
                    align='Right', margin=False)
            self.blit_text(' / '.join(ips), 0, self.res['y'] * 2.05 / 30, \
                    self.res['x'] / 4 - self.margin, self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], \
                    align='Left', margin=False)

    def display_volume(self, backup):
        self.save_background()

        if self.sound_volume > 90:
            color = self.colorset['menu-ko']
        elif self.sound_volume > 70:
            color = self.colorset['menu-warning']
        else:
            color = self.colorset['menu-ok']

        rect = pygame.Rect(self.res_x / 4, self.res_y / 4, self.res_x / 2, self.res_y / 2)
        self.new_blit_rect2(rect, self.colorset['message-bg'])
        if self.sound_volume == 0:
            self.blit_text2('Mute', rect, color=color)
        else:
            self.blit_text2(self.sound_volume, rect, color=color)
        self.update_screen(rect=rect)

        pygame.time.wait(200)

        self.restore_background()
        self.reset_background()

    def display_records(self, data, record, game, options, current=False):
        '''
        Dsiplay records
        '''
        self.logs.log("DEBUG", f"Displaying Hi score table for {game}, options : {options}")

        ratio = 1 / 2

        # Store number of columns to display
        rows = len(data)

        selected = 2

        while True:

            # Init
            click_zones = {}
            self.display_background()

            # Array title
            if current:
                txt = self.lang.translate('this-game-stats')
            else:
                txt = self.lang.translate('local-db-stats')

            self.display_row(1, 2 + rows, False, [(txt, 1)], ratio)
            self.display_row(2, 2 + rows, False, [(self.lang.translate('ranking'), 1 / 4), \
                    (self.lang.translate('Date'), 1 / 4), \
                    (self.lang.translate('Player'), 1 / 4), \
                    (self.lang.translate(record), 1 / 4)], ratio)

            index = 0
            for row in data:
                index += 1
                self.display_row(2 + index, 2 + rows, False, [(str(index), 1 / 4), \
                        (row[1], 1 / 4), (row[2], 1 / 4), ('%.2f' % (row[3]), 1 / 4)], ratio)

            # back to desktop and next
            click_zones['escape'] = self.display_button(1 == selected, 'back-to-menu', special='escape')
            click_zones['continue'] = self.display_button(2 == selected, 'continue', special='refresh')
            #click_zones['restart'] = self.display_button(3 == selected, 'restart', special='return')

            self.update_screen()
            # Wait for an input
            key_pressed = self.rpi.listen_inputs(['fx', 'arrows'], ['escape', 'enter', \
                    'TOGGLEFULLSCREEN', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click'])

            selected = self.navigate(selected, key_pressed, 0, 2, 2)
            # Analyse input (Mouse, keyboard and buttons)
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == 1):
                return 'menu'

            #if key_pressed == 'restart' or (key_pressed in ENTER_KEYS and selected == 3):
            #    return 'startagain'

            if key_pressed in ENTER_KEYS + CONTINUE_KEYS and selected == 2:
                return 'continue'

    def new_player_line(self, pos_y, player_id, actual_player, nb_players, p_color=None, b_color=None, alive=True):
        '''
        This method fill background squares
        '''
        # Please comment to explain
        teaming_size = self.pn_size / 5
        score_size = self.box_width * 2
        # Player names' box
        if b_color is None:
            if player_id == actual_player:
                background_color = self.colorset['menu-alternate']
            else:
                background_color = self.colorset['menu-item-white']
        else:
            background_color = b_color

        if p_color is None:
            p_color = b_color

        if not alive:
            background_color = self.colorset['game-dead']
            box_background_color = self.colorset['game-dead']
        else:
            box_background_color = self.colorset['game-dead']

        # If teaming is enabled, display a colored square beside the player name
        if nb_players >= 10:
            color_line_height = self.margin
        else:
            color_line_height = int(self.margin * (1 + (10 - nb_players) * 0.5))
        firstname_height = self.line_height - color_line_height - self.margin - 2

        rect = pygame.Rect(self.margin, pos_y, self.pn_size - self.margin, color_line_height)
        self.new_blit_rect2(rect, p_color)

        rect.y += color_line_height + 2
        rect.height = firstname_height
        self.new_blit_rect2(rect, background_color)

        # All other boxes
        rect = pygame.Rect(self.margin + self.pn_size, pos_y, self.box_width - self.margin, self.line_height - self.margin)

        for index in range(0, int(self.config.get_value('SectionGlobals', 'nbcol')) + 1):
            rect.x = self.margin + self.pn_size + self.box_width * index
            self.new_blit_rect2(rect, box_background_color)

        # Score box
        rect = pygame.Rect(self.margin + self.pn_size + self.box_width * (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1), pos_y, score_size - self.margin, self.line_height - self.margin)
        self.new_blit_rect2(rect, box_background_color)

    def new_headers(self, headers):
        '''
        This method display column headers
        '''
        y = self.position[0] - self.line_height - self.margin

        for index in range(0, int(self.config.get_value('SectionGlobals', 'nbcol')) + 1):
            rect = pygame.Rect(self.margin + self.pn_size + self.box_width * index, y, self.box_width - self.margin, self.line_height)

            self.new_blit_rect2(rect, self.colorset['game-table'], alpha=self.alpha + 10)
            self.blit_text2(str(headers[index][:5]), rect, self.colorset['game-headers'])


    def headers(self, headers):
        '''
        This method display column headers
        '''
        y = self.position[0] - self.line_height - self.margin

        for index in range(0, int(self.config.get_value('SectionGlobals', 'nbcol')) + 1):
            # Limit header to 3 char
            txt = str(headers[index][:3])
            scaled_text = self.scale_text(txt, self.box_width, self.line_height)
            font = pygame.font.Font(self.defaultfontpath, scaled_text[0])
            # Render text
            text = font.render(txt, True, self.colorset['menu-text-black'])
            # Calculate place of text
            pos_x = int(self.margin + self.pn_size + self.box_width * index + scaled_text[1])
            pos_y = int(y + scaled_text[2])
            # Create BG rect
            self.blit_rect(self.margin + self.pn_size + self.box_width * index, y, self.box_width - self.margin, self.line_height, self.colorset['game-table'], False, False, self.alpha + 10)
            # Display text
            self.blit(text, [pos_x, pos_y])

    def end_of_set(self, data):
        '''
        End of set's screen
        '''
        pos_y = self.top_space
        height = (self.box_height - self.line_height - self.top_space - self.margin) / 2
        pos_y += height - self.margin

        # Display text container - if a color is set in colorset
        self.blit_rect(0, pos_y, self.res['x'], height, self.colorset['menu-ko'])
        self.blit_text(f"{self.lang.translate('end-of-set')} {data[0]}", 0, pos_y, self.res['x'], height, self.colorset['menu-text-black'])

    def end_of_game_text(self):
        '''
        Display "End of game"
        '''
        height = (self.box_height - self.line_height - self.top_space - self.margin) / 2

        pos_y = self.res_y_16
        height = 2 * pos_y

        # Display text container - if a color is set in colorset
        self.blit_rect(0, pos_y, self.res['x'], height, self.colorset['menu-ko'])
        self.blit_text('end-of-game', 0, pos_y, self.res['x'], height, self.colorset['menu-text-black'])

    def is_true(self, var):
        '''
        Return true or false
        '''
        if var is True or var == 'True' or var == 1 or var == '1':
            return True
        return False

    
    def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, text_on_logo=False, wait=False, onscreen_buttons=None, showScores=True, end_of_game=False, end_of_set=None, set_number=None, max_set=None):

        return self.new_refresh_game_screen(players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, text_on_logo, wait, onscreen_buttons, showScores, end_of_game, end_of_set, set_number, max_set)

    def on_event(self, display, t_event, rect_array):
        count = 0
        online = []
        for index in range(1,6):
            online.append(self.file_class.get_full_filename(f'online{index}', 'images'))

        self.display = display
        index = 0
        while True:
            if t_event.is_set():
                for rect in rect_array:
                    self.blit(rect[0], (rect[1][0], rect[1][1]))
                    if index != 3:
                        self.display_image(online[index], rect[1][0], rect[1][1], width=rect[1][2], height=rect[1][3], UseCache=True)
                    self.update_screen(rect[1])

                if index >= 3:
                    index = 0
                else:
                    index += 1
                t_event.clear()
            else:
                pygame.time.wait(25)

    def create_thread(self, rect_array=None):
        if self.thread is None and rect_array is not None and len(rect_array) > 0:
            index = 0
            for rect in rect_array:
                sub = self.screen.subsurface(rect)
                screenshot = pygame.Surface((rect[2], rect[3]))
                screenshot.blit(sub, (0, 0))

                self.rects.append((screenshot, rect))  # (x, y, w, h, data)
            self.thread = Thread(target=self.on_event, args=(self.display, self.t_event, self.rects))
            self.thread.setDaemon(True)
            self.thread.start()

    def refresh_scores(self, players, actual_player, refresh=True):
        # Get number of players
        nb_players = len(players)

        # Display headers

        if refresh:
            self.display_background()
        index = 0
        for player in players:
            if player.position is None:
                # Classical display
                position = self.position[index]
            else:
                # 1st dead at last position (Sudden death of High Score)
                position = self.position[player.position - 1]

            # Display all other info on the player line
            if index == actual_player:
                self.new_player_line(position, index, actual_player, nb_players, p_color=player.color, b_color=player.color, alive=player.alive)
                self.new_display_score(position, player.score, player.color)
            else:
                self.new_player_line(position, index, actual_player, nb_players, p_color=player.color, b_color=self.colorset['game-inactive'], alive=player.alive)
                self.new_display_score(position, player.score, self.colorset['menu-text-white'])

            # Display player's score
            # Displayer player name box
            self.display_player_name(position, index, actual_player, player.name)
            index += 1

        # Display Table Content
        rect = self.new_display_table_content(players, actual_player)
        if refresh:
            self.update_screen(rect)
            self.save_background()

    def new_refresh_game_screen(self, players, actual_round, max_round, remaining, nb_darts, logo, headers, actual_player, text_on_logo=False, wait=False, onscreen_buttons=None, showScores=True, end_of_game=False, end_of_set=None, set_number=None, max_set=None):

        '''
        Refresh in game screen
        '''
        # Get number of players
        nb_players = len(players)

        # Recalculate line height
        self.define_constants(nb_players)

        # Init click_zones
        click = None

        self.reset_background()

        game_background = f"background_{logo.replace(' ', '_').split('.')[0]}"
        game_background = self.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display_background(image=game_background)
        else:
            self.display_background()

        if self.colorset['game-bg'] is not None:
            self.blit_rect(0, 0, self.res_x, self.res_y, self.colorset['game-bg'])
        if self.game_type == 'online' and self.t_event is not None:
            self.create_thread(rect_array=[(int(self.res_x / 2 - 110), self.margin + int(self.res_y / 5), int(self.res_y / 36), int(self.res_y / 36))])

        self.new_display_round(players[actual_player], actual_round, max_round, set_number, max_set)
        self.new_display_logo(logo)

        if not end_of_game and end_of_set is None:
            # Game options
            #
            # If some options are displayed, use compact mode for remaining darts
            OptDisplayed = self.new_display_game_options()
            #if OptDisplayed:
            # Rem Darts compact display
            self.display_darts(remaining, nb_darts, players[actual_player].color)

            game_h = int(self.res_y / 12)
            game_w = game_h
            game_x = int(self.res_x - 3 * (game_w + self.margin))
            game_y = self.margin + game_h

            # Display on-screen clickable buttons if requested
            if onscreen_buttons is True or self.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
                click = self.onscreen_buttons()
        #
        # All players line by line
        #
        if showScores:
            self.new_headers(headers)
            self.refresh_scores(players, actual_player, refresh=False)

        self.save_background()
        self.update_screen()

        # manage end game menu
        if end_of_game:
            click = self.end_of_game_menu(logo)
        # Wait if requested
        elif wait:
            pygame.time.wait(wait)

        # Return Click
        return click


    def old_refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, text_on_logo=False, wait=False, onscreen_buttons=None, showScores=True, end_of_game=False, end_of_set=None, set_number=None, max_set=None):
        '''
        refresh In-game screen
        '''
        # Get number of players
        nb_players = len(players)

        # Recalculate line height
        self.define_constants(nb_players)

        # Init click_zones
        click = None

        # Clear
        #self.screen.fill(self.colorset['menu-item-white']

        # Background image
        self.display_background()

        if not end_of_game and end_of_set is None:
            # Game Logo (or optionnaly "Text On Logo")
            if not text_on_logo:
                self.display_logo(logo)
            else:
                self.text_on_logo(str(text_on_logo))
            #
            # Game options
            #
            # If some options are displayed, use compact mode for remaining darts
            OptDisplayed = self.display_game_options()
            #if OptDisplayed:
                # Rem Darts compact display
            self.display_rem_darts_compact(RemDarts, nb_darts)
            #else:
                # Rem Darts normal :)
            #    self.display_rem_darts(RemDarts, nb_darts)

            # Display on-screen clickable buttons if requested
            if onscreen_buttons is True or self.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
                click = self.onscreen_buttons()
        #
        # Rounds
        #
        self.display_round(actual_round, max_round, set_number, max_set)

        #
        # All players line by line
        #
        if showScores:
            save = self.config.get_value('SectionGlobals', 'onscreenbuttons')
            if end_of_game:
                # Force onscreenbuttons for available space to print buttons
                self.config.set_value('SectionGlobals', 'onscreenbuttons', True)
                self.define_constants(nb_players)

            index = 0
            for player in players:
                # Displayer player name box
                self.display_player_name(self.position[index], index, actual_player, player.name)
                # Display all other info on the player line
                if index == actual_player:
                    self.player_line(self.position[index], index, actual_player, nb_players, color=player.color, alive=player.alive)
                else:
                    self.player_line(self.position[index], index, actual_player, nb_players, color=self.colorset['game-inactive'], alive=player.alive)
                # Display player's score
                self.display_score(self.position[index], player.score)
                index += 1
            # Display headers
            self.headers(headers)
            # Display Table Content
            self.display_table_content(players)

            # Restore onscreenbuttons
            self.config.set_value('SectionGlobals', 'onscreenbuttons', save)

        # refresh !
        self.update_screen()

        # manage end game menu
        if end_of_game:
            click = self.end_of_game_menu(logo)
        # Wait if requested
        elif wait:
            pygame.time.wait(wait)
        # Return Click
        return [click]

    def end_of_game_menu(self, logo=None, stat_button=True):
        '''
        Manage End game menu
        '''
        if logo is not None:
            self.display_logo(logo)
        self.end_of_game_text()

        selected = 2
        while True:
            click_zones = {}
            if stat_button:
                stats = 1
                click_zones['stats'] = self.display_button(selected == 1, 'statistics', special='escape')
            else:
                stats = 0

            click_zones['continue'] = self.display_button(selected == 1 + stats, 'back-to-menu', special='refresh')
            if self.game_type != 'online':
                online = 1
                click_zones['restart'] = self.display_button(selected == 2 + stats, 'restart', special='return')
            else:
                online = 0


            self.update_screen()

            key_pressed = self.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'TOGGLEFULLSCREEN', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click'])

            selected = self.navigate(selected, key_pressed, 0, 1 + online + stats, 2)

            # Analyse input (Mouse, keyboard and buttons)
            clicked = self.is_clicked(click_zones, key_pressed)

            if clicked:
                key_pressed = clicked

            if key_pressed == 'stats' or (key_pressed in ENTER_KEYS and selected == 1 and stat_button):
                return 'stats'

            if key_pressed in CONTINUE_KEYS + ESCAPE_KEYS + BACK_KEYS or (key_pressed in ENTER_KEYS and selected == 1 + stats):
                return 'continue'

            if key_pressed == 'restart' or (key_pressed in ENTER_KEYS and selected == 2 + stats):
                return 'startagain'

            if key_pressed in DIRECTION_KEYS:
                self.update_screen(rect_array = click_zones.values())
        # Return Clickable zones
        return click_zones

    def new_display_logo(self, logo=False):
        '''
        Display an image on the middle top of the screen
        '''
        pos_x = int(self.res_x / 2 - self.res_x / 6)
        pos_y = self.margin
        height = int(self.res_y / 5)
        width = int(self.res_x / 3)

        #self.display_image(self.file_class.get_full_filename(f'logos_menu/{logo}', 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True)
        name = logo.replace('_', ' ').split('.')[0]
        self.blit_text(name, pos_x, pos_y, width, height, self.colorset['game-title1'], margin=False)
        self.blit_text(name, pos_x, pos_y, width, height, self.colorset['game-title2'])
        
        gt_height = int(self.res_y / 36)

        if self.colorset['game-type'] is not None:
            if self.game_type == 'online':
                self.display_image(self.online_icon, self.res_x / 2 - 110, pos_y + height, width=gt_height, height=gt_height, UseCache=True)
            self.blit_text(f"{self.game_type} game", pos_x, pos_y + height, width, gt_height, color=self.colorset['game-type'], dafont='Impact', align='Center', valign='top', margin=False)

    def new_display_players(self, players, actual_player, end_of_game=False):
        
        player_height = int(self.res_y / 8)
        player_width = int(self.res_x / max(2 * len(players), 6))
        players_x = int(self.res_x / 4 + (self.res_x / 2 - player_width * len(players)) / 2)
        if end_of_game:
            player_y = self.res_y - 2 * player_height - self.margin
        else:
            player_y = self.res_y - player_height - self.margin
        heading_height = int(self.res_y / 24)

        heading_color = self.colorset['game-headers']
        player_color = self.colorset['game-alt-headers']

        index = 0
        for player in players:
            color = player.color
            name = player.name
            score = player.score
            player_x = players_x + index * player_width

            if index != actual_player:
                if index < actual_player:
                    player_x -= int(player_width / 2)
                else:
                    player_x += int(player_width / 2)

                self.blit_rect(player_x, player_y, player_width, heading_height, heading_color)
                self.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, player_color)

                if self.colorset['game-bg'] is not None:
                    pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
                    pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height - 1), 2)
                    pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)

                if index < actual_player:
                    align = 'Left'
                    icon_align = 'Right'
                else:
                    icon_align = 'Left'
                    align = 'Right'
                skull_icon = self.file_class.get_full_filename('killer_skull', 'images')
                pygame.draw.line(self.screen, color, (player_x, player_y), (player_x + player_width, player_y), self.margin * 2)
                self.blit_text(name, player_x, player_y - self.margin * 2, player_width, heading_height + self.margin * 2, color=player_color, dafont='Impact', align=align, valign='Bottom')
                self.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=heading_color, dafont='Impact', align=align)
                if not player.alive:
                    if index < actual_player:
                        self.display_image(skull_icon, player_x + player_width - (player_height - heading_height), player_y + heading_height, player_width, player_height - heading_height, UseCache=True)
                    else:
                        self.display_image(skull_icon, player_x, player_y + heading_height, player_width, player_height - heading_height, UseCache=True)
            else:
                # For actual player's infos
                actual_color = color
                actual_x = player_x - int(player_width / 2)
                actual_name = name
                actual_score = score
            index += 1

        # Actual player and his score
        player_x = int(self.res_x / 4 + (self.res_x / 2 - player_width * len(players)) / 2) + actual_player * player_width - (player_width / 2)
        player_y -= self.margin
        player_height += self.margin * 2
        player_width *= 2
        dart_icon_size = player_height - heading_height - self.margin * 2
        dart_icon = self.file_class.get_full_filename('dart_icon', 'images')
        self.blit_rect(player_x, player_y, player_width, heading_height, actual_color)
        self.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, actual_color)
        if self.colorset['game-bg'] is not None:
            pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
            pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
            pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)
        self.display_image(dart_icon, player_x + self.margin, player_y + heading_height + self.margin, width=dart_icon_size, height=dart_icon_size, UseCache=True)
        if self.colorset['game-bg'] is not None:
            self.blit_text(actual_name, player_x, player_y - self.margin, player_width, heading_height + self.margin * 2, color=self.colorset['game-bg'], dafont='Impact', align='Center')
        else:
            self.blit_text(actual_name, player_x, player_y - self.margin, player_width, heading_height + self.margin * 2, color=(0, 0, 0), dafont='Impact', align='Center')

        self.blit_text(actual_score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=self.colorset['game-score'], dafont='Impact', align='Right')

    def display_logo(self, logoimage=False):
        '''
        Display an image on the middle top of the screen
        '''
        # Local Constants
        pos_x = self.pn_size + self.margin
        pos_y = self.top_space
        width = self.box_width * (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) - self.margin
        height = self.box_height - self.line_height - self.top_space - self.margin
        # Display rect container - if a color is set in colorset
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-LOGO'])
        # Display LOGO
        self.display_image(self.file_class.get_full_filename(f'logos_menu/{logoimage}', 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True)

    def text_on_logo(self, txt, wait=False, update=False):
        '''
        Display text instead of game LOGO
        '''
        # Local Constants
        pos_x = self.pn_size + self.margin
        pos_y = self.top_space
        width = self.box_width * (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) - self.margin
        height = self.box_height - self.line_height - self.top_space - self.margin
        border_color = self.colorset['menu-border']
        border_size = int(self.box_width / 20)
        text_color = self.colorset['menu-text-black']
        scaled_text = self.scale_text(txt, width, height)
        font = pygame.font.Font(self.defaultfontpath, scaled_text[0])
        # Display rect container
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-LOGO'], border_size, border_color)
        # Render text
        text = font.render(txt, True, text_color)
        # Text location
        text_x = pos_x + scaled_text[1]
        text_y = pos_y + scaled_text[2]
        # Blit text
        self.blit(text, [text_x, text_y])
        if update:
            self.update_screen()    # refresh screen if requested
        if wait:
            pygame.time.wait(wait)    # Wait if requested

    def display_background(self, image=None, rect=None, display_version=False):
        '''
        Display background
        '''
        if image is True:
            image = self.background
        elif image is not None:
            image = self.file_class.get_full_filename(image, 'images')

        if self.colorset['bg-global']:
            self.screen.fill(self.colorset['bg-global'])
        # If there is no background color in used colorset, try to use image
        if self.game_background is not None and image is None:
            self.restore_background()

        elif not self.colorset['bg-global'] and (self.background is not None or image is not None):
            if image is None:
                image = self.background

            if rect is None:
                self.display_image(image, 0, 0, self.res['x'], self.res['y'], Scale=True)
            else:
                self.display_image(image, 0, 0, self.res['x'], self.res['y'], Scale=True, rect=rect)

            if display_version :
                width = self.res_x_16
                height = self.res_y_16
                pos_x = self.res['x'] - width
                pos_y = int(self.res['y'] * 3 / 4) - height
                version = f"V{self.config.pyDartsVersion[0:3]}"

                self.blit_text(version, pos_x , pos_y, width, height, self.colorset['menu-text-white'], \
                        dafont=self.file_class.get_full_filename('Impact', 'fonts'))

    def scale_image(self, image, scale=True, width=0, height=0):
        '''
        Method to scale an image to fit on given size
        '''
        image_size = image.get_rect().size
        image_prop = float(image_size[0]) / float(image_size[1])

        if width > 0 and height > 0 and scale:
            # Force to given size
            image_width = width
            image_height = height

        elif not scale and int(width / image_prop) <= height:
            # Else, try first to fit into width
            image_width = width
            image_height = int(width / image_prop)

        elif not scale:
            # If it doesnt fit, fit to height
            image_width = int(height * image_prop)
            image_height = height

        # Scale to correct size
        return (pygame.transform.scale(image, (image_width, image_height)), (image_width, image_height))

    #@debug
    def display_image(self, imagepath, pos_x, pos_y, width=0, height=0, Scale=False, center_x=False, center_y=False, rect=None, Screen=None, UseCache=True, change_colors=None):
        '''
        Scale and display an image
        '''
        if imagepath is None:
            return

        # Cache is cleaned when resolution changed
        # Store in cache for Scate True/False and width/height (surface size to blit
        if change_colors is None:
            image_cache = f'{imagepath}-{Scale}-{width}-{height}'
        else:
            image_cache = f'{imagepath}-{Scale}-{width}-{height}-{change_colors}'

        if UseCache:
            if image_cache not in self.imagecache:
                try:
                    self.logs.log("DEBUG", f"Inserting image into cache {imagepath} ({image_cache})")
                    # Load
                    loaded_image = pygame.image.load(imagepath).convert_alpha()
                    if change_colors is not None:
                        image_pixel_array = pygame.PixelArray(loaded_image)
                        for change in change_colors:
                            image_pixel_array.replace(change[0], change[1])
            
                    # Scale
                    scaled = self.scale_image(loaded_image, scale=Scale, width=int(width), height=int(height))
                    # then store image + size
                    self.imagecache[image_cache] = scaled

                except Exception as e:
                    self.logs.log("WARNING", f"Unable to load image {imagepath}. Error was {e}.")
                    return False

                self.logs.log("DEBUG", f"{len(self.imagecache)} elements in cache")
            scaled_image = self.imagecache[image_cache][0]
            scaled_width = self.imagecache[image_cache][1][0]
            scaled_height = self.imagecache[image_cache][1][1]
        else:
            # Load
            loaded_image = pygame.image.load(imagepath).convert_alpha()
            if change_colors is not None:
                image_pixel_array = pygame.PixelArray(loaded_image)
                for change in change_colors:
                    image_pixel_array.replace(change[0], change[1])

            # Scale
            scaled = self.scale_image(loaded_image, scale=Scale, width=int(width), height=int(height))
            scaled_image = scaled[0]
            scaled_width = scaled[1][0]
            scaled_height = scaled[1][1]

        # Compute posiion
        if center_x:
            pos_x = int(pos_x + (width - scaled_width) / 2)
        else:
            pos_x = pos_x
        if center_y:
            pos_y = int(pos_y + (height - scaled_height) / 2)
        else:
            pos_y = pos_y

        if Screen is None:
            self.blit(scaled_image, (pos_x, pos_y), area=rect)
        else:
            self.blit_screen(scaled_image, (pos_x, pos_y), area=rect)

        return (scaled_width, scaled_height)

    def define_constants(self, nb_players=None, Font=None):
        '''
        Define and eventually refresh some constants (most of them depends of user resolution)
        '''
        # Basic space
        self.margin = int(self.res['y'] / 200)
        # space at the top side of the screen
        self.top_space = self.margin
        # Define bottom space
        if self.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
            self.bottomspace = self.margin*32
        else:
            self.bottomspace = self.margin
        # Space on left side of the screen
        self.leftspace = int(self.res['x'] / 8)
        # Header for in-game screen boxes
        self.box_headers = int(self.res['y'] / 25)
        self.box_height = int(self.res['y'] / 2.5)
        # Nb col + 1 bull + 4 unit for player name and score
        self.box_width = int(self.res['x'] / (int(self.config.get_value('SectionGlobals', 'nbcol')) + 5))
        # Transparency
        self.alpha = 210
        self.alpha2 = 168
        # Default font path
        if Font is None:
            try :    # Already define
                self.defaultfontpath = self.defaultfontpath
            except :    # 1st define
                self.defaultfontpath = self.file_class.get_full_filename('MaPolice', 'fonts')
        else:
            self.defaultfontpath = self.file_class.get_full_filename(f'{Font}', 'fonts')

        # Animation time (in ms)
        self.animation = 5
        ###### HEIGHT
        # All this sh** depends of the nb of players
        if nb_players:
            # The size of the top and bottom part of the screen
            self.screen_top = self.box_height - self.box_headers - self.top_space
            self.screen_bottom = self.res['y'] - self.screen_top - self.bottomspace
            # Max line_height is restrained to the space when 3 players plays (+ 1 header)
            max_line_height = int(self.screen_bottom / 4)
            # Calculate line_height
            # Screen size minus the header size, divided by number of players + 1 header
            self.line_height = min(int(self.screen_bottom / (nb_players + 1)), max_line_height)
            # Define Y position of each line for each player
            self.position = []
            for p in range(0, nb_players):
                positemp = int(self.res['y'] - self.bottomspace - ((nb_players - p) * (self.line_height)))
                self.position.append(positemp)

        ###### WIDTH (X Axis)
        # Player name box width
        self.pn_size = self.box_width * 2
        # Width of an in-game column
        self.colwidth = self.box_width

        ###### SCREEN PROPORTIONS
        # Proportion between screen Height and Width
        self.screen_proportions = float(float(self.res['x']) / float(self.res['y']))
        # Limit of proportion before considering the screen as vertical display
        self.prop_limit = 1

    def display_player_name(self, pos_y, ident, actual_player, playername=None):
        '''
        Display name of the player if given, Player X otherwise
        '''
        if playername is None:
            playername = 'Player ' + str(ident)
        if actual_player == ident:
            txtcolor = self.colorset['menu-text-white']
        else:
            txtcolor = self.colorset['menu-text-black']
        #  Player name size depends of player name number of char (dynamic size)
        scaled_text = self.scale_text(playername, self.pn_size - 2 * self.margin, self.line_height)
        font = pygame.font.Font(self.defaultfontpath, scaled_text[0])
        # Render the text. "True" means anti-aliased text.
        pos_x = self.margin * 2 + scaled_text[1]
        pos_y = pos_y + scaled_text[2]
        text = font.render(playername, True, txtcolor)
        self.blit(text, [pos_x, pos_y])

    def new_display_table_content(self, players, actual_player):
        '''
        Fill-in table With DISPLAY-LEDS func
        '''
        index = 0
        min_x = self.res['x']
        min_y = self.res['y']
        max_x = 0
        max_y = 0

        for player in players:
            if player.position is None:
                # Classical display
                position = self.position[index]
            else:
                # 1st dead at last position (Sudden death of High Score)
                position = self.position[player.position - 1]

            if index == actual_player:
                color = player.color
            elif player.alive:
                color = self.colorset['game-table']
            else:
                color = self.colorset['game-dead']

            for column, value in enumerate(player.columns):
                pos_x = min_x
                pos_y = min_y
                width = max_x
                height = max_y
                if len(value) == 3 and value[2] is not None:
                    color = self.colorset[value[2]]

                if value[1] == 'image' and value[0] is not None:    # Maybe you want to put images in the table?
                    pos_x, pos_y, width, height = self.display_leds_image(position, value[0], column)
                elif value[1] == 'leds':    # Or you want to display leds style?
                    pos_x, pos_y, width, height = self.led_box2(position, int(value[0]), column, player.color)
                elif value[1] == 'int' and value[0] != '':
                    if value[0] != '' and int(value[0]) > 100:
                        pos_x, pos_y, width, height = self.new_text_box(position, str(int(value[0])), column, color)
                    else:
                        pos_x, pos_y, width, height = self.new_text_box(position, str(value[0]).replace('.0', ''), column, color)
                elif value[1] == 'str' and value[0] != '':
                    pos_x, pos_y, width, height = self.new_text_box(position, value[0], column, color)
                elif value[0] is not None and value[0] != '':    # Or fallback to default, it displays a string or int
                    pos_x, pos_y, width, height = self.new_text_box(position, value[0], column, color)

                if pos_x < min_x:
                    min_x = pos_x
                    max_x = pos_x + width
                if pos_y < min_y :
                    min_y = pos_y
                    max_y = pos_y + height
            index += 1

        return (min_x, min_y, max_x, max_y)

    def display_table_content(self, players, wait=False):
        '''
        Fill-in table With DISPLAY-LEDS func
        '''
        index = 0
        for player in players:
            for column, value in enumerate(player.columns):
                if len(value) == 3:
                    color = value[2]
                else:
                    color = None
                if value[1] == 'image':    # Maybe you want to put images in the table?
                    self.display_leds_image(self.position[index], value[0], column)
                elif value[1] == 'leds':    # Or you want to display leds style?
                    self.led_box2(self.position[index], int(value[0]), column, list(self.colorset)[player.ident])
                elif value[1] == 'int' and value[0] != '':
                    if value[0] != '' and int(value[0]) > 100:
                        self.text_box(self.position[index], str(int(value[0])), column, color)
                    else:
                        self.text_box(self.position[index], str(value[0]).replace('.0', ''), column, color)
                elif value[1] == 'str' and value[0] != '':
                    self.text_box(self.position[index], value[0], column, color)
                elif value[0] != '' :    # Or fallback to default, it displays a string or int
                    self.text_box(self.position[index], value[0], column, color)
                if wait:
                    pygame.time.wait(self.animation)
            index += 1

    def led_box(self, pos_y, nb_leds, column, color=None):
        '''
        Graphical representation of a number in the box, from 0 to 3
        '''
        # 3 leds max
        #
        pos_x = int(column * self.box_width + self.pn_size + self.margin)
        end_x = int(column * self.box_width + self.box_width + self.pn_size - self.margin / 4)
        end_y = int(pos_y + self.line_height - self.margin * 2)
        if color is None:
            color = self.colorset['menu-text-black']
        else:
            color = self.colorset[color]
        BB = int(self.res['y'] / 130)
        if nb_leds == 1:
            pygame.draw.line(self.screen, color, [pos_x, pos_y + self.margin], [end_x, end_y], BB)
        elif nb_leds == 2:
            pygame.draw.line(self.screen, color, [pos_x, pos_y + self.margin], [end_x, end_y], BB)
            pygame.draw.line(self.screen, color, [pos_x, end_y], [end_x, pos_y + self.margin], BB)
        elif nb_leds == 3:
            self.blit_rect(self.margin + self.pn_size + self.box_width * column, pos_y, self.box_width - self.margin,
                          self.line_height - self.margin, color)

    def led_box2(self, pos_y, nb_leds, column, color=None):
        '''
        graphical representation of a number in the box, from 0 to 3
        '''
        # 3 leds max
        #
        if color is None:
            color = self.colorset['menu-ok']
        elif type(color) is not tuple:
            color = self.colorset[color]

        height = int((self.line_height - self.margin) * nb_leds / 3) + 1
        if nb_leds > 0:
            self.blit_rect(self.margin + self.pn_size + self.box_width * column
                , pos_y + self.line_height - self.margin - height
                , self.box_width - self.margin, height
                , color)

        return self.margin + self.pn_size + self.box_width * column \
            , pos_y + self.line_height - self.margin - height \
            , self.box_width - self.margin, height

    def led_box3(self, pos_y, nb_leds, column, color=None):
        '''
        graphical representation of a number in the box, from 0 to 3
        '''
        color = self.colorset['menu-item-black']
        height = int((self.line_height - self.margin) * nb_leds / 3) + 1
        if nb_leds > 0:
            self.blit_rect(self.margin + self.pn_size + self.box_width * column
                , pos_y + self.line_height - self.margin - height
                , self.box_width - self.margin, height
                , color, Alpha=255)

    def new_text_box(self, pos_y, text, column, color=None):
        '''
        Display text or integer in the given column
        '''
        # keep max 4 char
        # text = str(text[:4])
        if text.endswith('.'):
            text = str(text[:-1])

        # Asign default color if required
        if color is None: color = self.colorset['game-text']

        pos_x = column * self.box_width + self.pn_size
        # Write text in box
        self.blit_text(text, pos_x, pos_y, self.box_width, self.line_height, color)

        return pos_x, pos_y, self.box_width, self.line_height

    def text_box(self, pos_y, text, column, color=None):
        '''
        Display text or integer in the given column
        '''
        # keep max 4 char
        text = str(text[:4])
        if text.endswith('.'):
            text = str(text[:3])

        # Asign default color if required
        if color is None: color = 'menu-text-black'

        # Write text in box
        scaled_text = self.scale_text(text, self.box_width - self.margin * 2, self.line_height - self.margin * 2)
        font = pygame.font.Font(self.defaultfontpath, scaled_text[0])
        text = font.render(text, True, self.colorset[color])
        pos_x = column * self.box_width + self.pn_size + self.margin * 2 + scaled_text[1]

        self.blit(text, [pos_x, pos_y + scaled_text[2]])

    def display_leds_image(self, pos_y, image, column):
        '''
        Display an image in a specified column of a given player
        '''
        #
        height = int(self.line_height - self.margin * 3)
        width = int(min(self.box_width - self.margin * 3, height))
        #
        pos_x = int(column * self.box_width + self.pn_size + self.margin + (self.box_width - width) / 2)
        pos_y = int(pos_y + self.margin)
        #
        imagefile = self.file_class.get_full_filename(f'{image}', 'images')
        self.display_image(imagefile, pos_x, pos_y, width, height, False, True, True)

        return pos_x, pos_y, width, height

    def new_display_score(self, pos_y, txt, color):
        '''
        Display score for given player
        '''
        txt = str(txt).replace('.0', '')
        pos_x = int(self.pn_size + (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) * self.box_width)
        score_size = int(self.res['x'] / 5)

        self.blit_text(txt, pos_x, pos_y, score_size, self.line_height, color)


    def display_score(self, pos_y, txt):
        '''
        Display score for given player
        '''
        txt = str(txt).replace('.0','')
        score_size = int(self.res['x'] / 5)
        # self.box_width = int(self.res['x'] / 11.7)
        #
        pos_x = int(self.pn_size + (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) * self.box_width)
        scaled_text = self.scale_text(txt, score_size - self.margin * 2, self.line_height - self.margin * 2)
        font = pygame.font.Font(self.defaultfontpath, scaled_text[0])
        text = font.render(txt, True, self.colorset['menu-text-black'])
        self.blit(text, [pos_x + self.margin * 2 + scaled_text[1], pos_y + scaled_text[2]])

    def display_darts(self, remaining, nb_darts, color, image='dart_icon'):
        '''
        Display remaining darts
        '''
        pos_y = self.margin + int(self.res_y / 96)
        height = int(self.res_y / 12)
        width = height
        pos_x = int(self.res_x - nb_darts * (width + 2 * self.margin)) #by Manu script.

        for dart in range(1, nb_darts + 1):
            if dart <= remaining:
                self.display_image(self.file_class.get_full_filename(image, 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True, change_colors=[((0, 0, 0), color)])
            elif self.colorset['game-darts'] is not None:
                self.display_image(self.file_class.get_full_filename(image, 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True, change_colors=[((0, 0, 0), self.colorset['game-darts'])])
            pos_x += width + 2 * self.margin

    def new_display_game_options(self):
        '''
        Display game's options
        '''
        pos_y = self.margin + int(self.res_y / 48) + int(self.res_y / 12)
        height = int(self.res_y / 36)
        width = int(self.res_y / 6)
        width = int(self.res_y / 2)

        pos_x = self.res_x - width - self.margin
        game = self.selectedgame.replace(' ', '_')

        if self.colorset['game-option'] is not None:
            # Display options one by one
            for option, value in self.game_options.items():
                if option == 'theme':
                    continue
                if option == 'Time' and value == 0:
                    continue
                txt_option = self.lang.translate(f'{game}-{option}')
                if value is True:
                    self.blit_text(f'{txt_option}', pos_x, pos_y, width, height, color=self.colorset['game-option'], dafont='Impact', align='Right', margin=False)
                elif value is False:
                    continue
                    #self.blit_text(f'{txt_option}', pos_x, pos_y, width, height, color=self.colorset['menu-ko'], dafont='Impact', align='Right', margin=False)
                else:
                    if value != '0':
                        self.blit_text(f'{txt_option} : {value}', pos_x, pos_y, width, height, color=self.colorset['game-option'], dafont='Impact', align='Right', margin=False)
                    else:
                        continue
                pos_y += height + self.margin


    def display_rem_darts(self, remaining, nb_darts, dartimage='target'):
        '''
        Display how many darts remain (only if game has no option so more room space available)
        '''
        #
        pos_x = int(self.margin + self.pn_size + (self.box_width * 7))
        pos_y = self.top_space
        #
        width = int(self.res['x'] - pos_x - self.margin)
        height = self.box_height
        #
        title_height = self.box_headers    # Basic title height
        #
        height = min(int((height - title_height) / nb_darts), width)
        width = height
        #
        image_x = pos_x + ((width - width) / 2)
        image_y = pos_y + title_height
        #
        imagefile = self.file_class.get_full_filename(dartimage, 'images')
        #
        scaled_text= self.scale_text(self.lang.translate('remaining-darts'), width, title_height)
        font_size = scaled_text[0]
        font = pygame.font.Font(self.defaultfontpath, font_size)
        text_x = int(pos_x + scaled_text[1])
        text_y = int(pos_y + scaled_text[2])
        text = font.render(self.lang.translate('remaining-darts'), True, self.colorset['menu-text-black'])
        # Display
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-darts-nb'])
        self.blit_rect(pos_x, pos_y, width, title_height, self.colorset['bg-darts-nb-header'])
        self.blit(text, [text_x, text_y])
        for dart in range(0, remaining):
            self.display_image(imagefile, image_x, image_y + (dart * width), width, height)

    def display_rem_darts_compact(self, nb_remaining, nb_darts, dartimage='target'):
        '''
        Compact version (when options are set in game)
        '''
        #
        pos_x = int(self.margin + self.pn_size + (self.box_width * 7))
        pos_y = self.top_space
        #
        width = int(self.res['x'] - pos_x - self.margin)
        height = int(self.res['y'] / 12)
        # Title height
        title_height = self.box_headers    # Basic title height
        #
        image_height = min(int(width / nb_darts), height)
        image_width = image_height
        #
        image_x = int(pos_x + ((width - image_width * nb_darts) / 2))
        image_y = int(pos_y + title_height + ((height - image_height) / 2))
        #
        imagefile = self.file_class.get_full_filename(dartimage, 'images')
        #
        scaled_text= self.scale_text(self.lang.translate('remaining-darts'), width, title_height)
        font_size = scaled_text[0]
        font = pygame.font.Font(self.defaultfontpath, font_size)
        text_x = int(pos_x + scaled_text[1])
        text_y = int(pos_y + scaled_text[2])
        text = font.render(self.lang.translate('remaining-darts'), True, self.colorset['menu-text-black'])
        # Display
        self.blit_rect(pos_x, pos_y + title_height, width, height, self.colorset['bg-darts-nb'])
        self.blit_rect(pos_x, pos_y, width, title_height, self.colorset['bg-darts-nb-header'])
        self.blit(text, [text_x, text_y])

        for x in range(0, nb_remaining):
            self.display_image(imagefile, image_x + (x * image_width), image_y, \
                    image_width, image_height)

    def display_game_options(self):
        '''
        Display game options during gameplay
        '''
        # Define options to be hidden on game screen
        hide_options = {'totalround': False, 'max_round': False}
        # Remove them from dict
        display_game_options = {key: value for key, value in self.game_options.items() \
                if key not in hide_options}    # Hide arbitrary options
        # Remove options when value is False
        display_game_options = {key: value for key, value in display_game_options.items()
                if value not in ('False', '0')}    # Remove false options
        # Get number of options
        nb_options = len(display_game_options)
        # Stop here if there is no otion to display
        if nb_options == 0: return False
        #
        pos_x = int(self.margin + self.pn_size + (self.box_width * 7))
        pos_y = self.top_space + int(self.res['y'] / 12) + int(self.res['y'] / 25) + self.margin
        #
        width = int(self.res['x'] - pos_x - self.margin)
        title_height = self.box_headers    # Basic title height
        max_y = int(self.screen_top - int(self.res['y'] / 12) - title_height - self.top_space - self.margin)
        height = min(title_height, int(max_y / nb_options))
        # Display header
        self.blit_rect(pos_x, pos_y, width, title_height, self.colorset['bg-optionslist-header'])
        scaled_text= self.scale_text(self.lang.translate('game-options'), width, height)
        font = pygame.font.Font(self.defaultfontpath, scaled_text[0])
        text_x = int(pos_x + scaled_text[1])
        text_y = int(pos_y + scaled_text[2])
        text = font.render(self.lang.translate('game-options'), True, self.colorset['menu-text-black'])
        self.blit(text, [text_x, text_y])
        pos_y += height
        # Display options one by one
        for option, value in display_game_options.items():
            if value != 'True':
                txt = self.lang.translate(f"{self.selectedgame.replace(' ', '_')}-{option}") + ' : ' + str(value)
            else:
                txt = self.lang.translate(f"{self.selectedgame.replace(' ', '_')}-{option}")
            scaled_text= self.scale_text(txt, width, height)
            font_size = scaled_text[0]
            font = pygame.font.Font(self.defaultfontpath, font_size)
            self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-optionslist'])
            text = font.render(txt, True, self.colorset['menu-text-black'])
            self.blit(text, [pos_x + scaled_text[1], pos_y + scaled_text[2]])
            pos_y += height
        # Return True if some options are displayed
        return True

    def display_sets(self, sets, end_of_game=False, wait=True):
        '''
        Sets winner's screen
        '''

        nb_sets = len(sets)
        self.reset_background()
        self.display_background()
        if end_of_game:
            self.end_of_game_text()

        self.display_big_row(1, nb_sets, 0, [(self.lang.translate("set"), 3 / 32), \
                (self.lang.translate('winner'), 3 / 8), \
                (self.lang.translate('duration'), 2 / 8), \
                (self.lang.translate('rounds'), 1 / 8), \
                (self.lang.translate('darts'), 5 / 32)] )

        index = 2
        for se_t in sets:
            data = str(se_t[2] - se_t[1]).split('.')[0]
            if data.startswith('0:0'):
                data = data[3::]
            elif data.startswith('0:'):
                data = data[2::]

            if isinstance(se_t[3], int) and se_t[3] == -1:
                w = self.lang.translate('none')
            else:
                w = se_t[3]

            self.display_big_row(index, nb_sets, 0, [(str(se_t[0]), 3 / 32), (w, 3 / 8), \
                    (data, 2 / 8), (str(se_t[4]), 1 / 8), (str(se_t[5]), 5 / 32)])
            index += 1

        # manage end game menu
        if end_of_game:
            click_zones = self.end_of_game_menu()
        elif wait:
            self.display_button(True, 'continue', special='return')

        self.update_screen()

        if end_of_game:
            return click_zones
        elif wait:
            self.wait_touch()

        return None

    def new_display_round(self, player, actual_round, max_round, set_number=None, max_set=None, history='scores', end_of_game=False):
        '''
        Display round
        '''

        left_x = self.margin
        left_y = self.margin
        left_w = int(self.res_x / 6 - 2 * self.margin)
        left_h = int(self.res_y / 4 - 2 * self.margin)
        text_h = int(left_h / 5)

        if set_number is not None and max_set is not None and max_set > 1:
            self.blit_text(f"Set", left_x, left_y, int(left_w / 3), text_h, color=self.colorset['game-round'], align='Left', valign='top', margin=False)
            self.blit_text(f"{set_number} / {max_set}", left_x + int(left_w / 2), 0, left_x + left_w - int(left_w / 2), text_h * 2, color=self.colorset['game-round'], align='Right', valign='top', margin=False)
            left_y += text_h * 2

        self.blit_text(f"Round", left_x, left_y, int(left_w / 3), text_h, color=self.colorset['game-round'], align='Left', valign='top', margin=False)
        self.blit_text(f"{actual_round} / {max_round}", left_x + int(left_w / 2), left_y - self.margin, left_x + left_w - int(left_w / 2), text_h * 2, color=self.colorset['game-round'], align='Right', valign='top', margin=False)
        left_y += text_h * 2

        if history == 'scores':
            try:
                for index in range(3):
                    if end_of_game:
                        continue
                    if actual_round - index > 0:
                        text1 = f'R{actual_round - index}'
                        score = player.scores[actual_round - 1 - index][3]
                        #text2 = f'{sum(scores[actual_round - index - 1] if scores[actual_round - index - 1] is not None else 0)}'
                        text2 = score
                        self.blit_text(text1, left_x, left_y, int(left_w / 2), text_h, color=self.colorset['menu-text-white'], dafont='Impact', align='Left')
                        self.blit_text(text2, left_x, left_y, int(left_w / 2), text_h, color=player.color, dafont='Impact', align='Right', margin=False)
                    left_y += text_h
            except:
                self.logs.log("ERROR", f"No score historized for this game")

    def display_round(self, actual_round, max_round, set_number=None, max_set=None):
        '''
        Display Round
        '''
        #
        pos_x = self.margin
        pos_y = self.top_space
        # Title Y size
        height = 2 * self.box_headers    # Basic title height
        #
        title_width = int(self.pn_size - self.margin)
        title_height = int(min(self.position[0], self.res['y'] / 2) / 2 - height - self.margin) / 2

        if set_number is None or max_set is None or max_set < 2:
            title1 = 'round'
            title2 = 'over'
            text1 = f'{round}'
            text2 = f'{max_round}'
        else:
            title1 = 'set'
            title2 = 'round'
            text1 = f'{set_number+1}'
            text2 = f'{round} / {max_round}'

        self.blit_rect(pos_x, pos_y, title_width, title_height, self.colorset['bg-round-nb-header'])
        self.blit_text(title1, pos_x, pos_y, title_width, title_height, self.colorset['menu-text-black'])

        self.blit_rect(pos_x, pos_y + title_height, title_width, height, \
                self.colorset['bg-round-nb'])
        self.blit_text(text1, pos_x, pos_y + title_height, title_width, height, \
                self.colorset['menu-text-black'])

        self.blit_rect(pos_x, pos_y + title_height + height, title_width, height, \
                self.colorset['bg-round-nb-header'])
        self.blit_text(title2, pos_x, pos_y + title_height + height, title_width, height, \
                self.colorset['menu-text-black'])

        self.blit_rect(pos_x, pos_y + title_height  + 2 * height, title_width, height, \
                self.colorset['bg-round-nb'])
        self.blit_text(text2, pos_x, pos_y + title_height + 2 * height, title_width, height, \
                self.colorset['menu-text-black'])

    def onscreen_buttons(self):
        '''
        On screen buttons
        '''
        # Init
        click_zones = {}

        # GAME BUTTON
        width = (self.res['x'] - self.margin * 6) / 4
        height = self.margin * 30
        pos_x = self.margin
        pos_y = self.res['y'] - height - self.margin * 2

        # Blit Background rect
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['menu-alternate'], 2, self.colorset['menu-buttons'], self.alpha)
        click_zones['GAMEBUTTON'] = (pos_x, pos_y, width, height)

        # Blit button
        self.blit_text('Exit', pos_x, pos_y, width, height, self.colorset['menu-text-white'])

        # BACKUP BUTTON
        pos_x = pos_x + self.margin + width + width / 2

        # Blit Background rect
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['menu-shortcut'], 2, self.colorset['menu-buttons'], self.alpha)
        click_zones['BACKUPBUTTON'] = (pos_x, pos_y, width, height)

        # Blit button
        self.blit_text('Backup', pos_x, pos_y, width, height, self.colorset['menu-text-white'])

        # MISS BUTTON
        pos_x = pos_x + self.margin + width + width / 2

        # Blit Background rect
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['menu-ok'], 2, self.colorset['menu-buttons'], self.alpha)
        click_zones['PLAYERBUTTON'] = (pos_x, pos_y, width, height)

        # Blit button
        self.blit_text('Next Player', pos_x, pos_y, width, height, self.colorset['menu-text-white'])

        # Return Dict of tuples representing clickage values
        return [click_zones]


    def press_player(self, txt='Press Player button', color='menu-ko'):
        '''
        Show the player icon on the top right of the screen
        '''
        height = int(self.res['y'] / 10)
        width = int(self.res['x'])
        pos_x = 0
        pos_y = int((self.res['y'] / 2) - (height / 2))
        pygame.draw.rect(self.screen, self.colorset[color], (pos_x, pos_y, width, height), 0)

        self.blit_text(txt, pos_x, pos_y, width, height)

        self.update_screen()

    def update_screen(self, rect=None, rect_array=None):
        '''
        Simply update the screen (after multiple updates for example)
        '''
        if rect_array is not None:
            #self.display.update(rect_array)
            for rect in rect_array:
                self.display.update(rect)
        elif rect is not None:
            self.display.update(rect)
        else:
            self.display.flip()

    def speech(self, text, speed=None):
        '''
        Espeak vocal synthetiser (untested on windows)
        '''
        try:
            volume = self.sound_volume
            if speed is not None:
                pass
            elif self.random_speed:
                speed = random.randint(80, 180)
            else:
                speed = 150
            subprocess.run(f'espeak -a {volume} -s {speed} -v mb-fr1 "{text}" --stdout |aplay 2> /dev/null', shell=True)
            self.logs.log("INFO", f'espeak -a {volume} -s {speed} -v mb-fr1 "{text}"')
            return True
        except Exception as e:
            self.logs.log("WARNING", f"Problem trying to use espeak : {e}")
            return False

    def fade_out(self, sound, duration, fade_time):
        '''
        Crop and fadeout the sound
        '''
        if duration > fade_time:
            pygame.time.wait(duration - fade_time)
            sound.fadeout(fade_time)
        else:
            sound.fadeout(duration)

    def play_sound(self, filename='beep1', wait_finish=False, duration=0):
        '''
        Play given sound. Search first in the home folder, then play default sound, or beep1 if not found.
        '''
        sound_file = self.file_class.get_full_filename(filename, 'sounds')
        if sound_file is not None:
            try:
                pygame.mixer.init(22050, -16, 2)
                sound = pygame.mixer.Sound(sound_file)
                # Play only if sound is set
                if sound:
                    # Set volume to defined setting and play
                    volume = round((int(self.sound_volume) * self.sound_multiplier / 100), 1)
                    sound.set_volume(volume)
                    self.logs.log("INFO", f"Play {sound_file} at volume {volume}")
                    play_sound = sound.play()

                    # if crop duration is requested, new thread to fadeout the sound
                    if duration > 0:
                        pygame.time.wait(100)
                        x = threading.Thread(target = self.fade_out, args = (sound, duration, 2000))
                        x.start()

                    # if requested, we block the process until the sound is running
                    if wait_finish:
                        self.wait_end_sound(play_sound)
                    else:
                        return play_sound
            except Exception as e:
                self.logs.log("WARNING", f"Unable to load audio while trying to play file : {sound_file}\n{e}")
        else:
            self.logs.log("WARNING", f"Unable to load this audio file : {filename}")

    def wait_end_sound(self, played_sound):
        '''
        '''
        while played_sound.get_busy():
             pygame.time.wait(100)
            
    def adjust_volume(self, key, backup=True):
        '''
        Set sound volume
        '''
        if key in VOLUME_DOWN_KEYS:
            diff = -10
            if self.sound_volume == 0:
                diff = 0
        elif key in VOLUME_UP_KEYS:
            diff = 10
            if self.sound_volume == 100:
                diff = 0
        elif key in VOLUME_MUTE:
            if self.sound_volume == 0:
                self.sound_volume = self.old_volume
            else:
                self.old_volume = self.sound_volume
                self.sound_volume = 0
            diff = 0
        else:
            diff = 0

        if diff != 0:
            self.sound_volume += diff
            self.sound_volume = max(0, self.sound_volume)
            self.sound_volume = min(100, self.sound_volume)

            self.logs.log("DEBUG", f"Volume level is now {self.sound_volume}")
            if diff > 0:
                self.play_sound('vol+', wait_finish=False)
            else:
                self.play_sound('vol-', wait_finish=False)
            self.video_player.set_volume(self.sound_volume)
        self.display_volume(backup)

    def sound_start_round(self, player, play_firstname=True):
        '''
        Play player name at the begining of a round (priority : personnal sound / speech / beep)
        '''
        # Try to play User Sound (user.ogg in the .pydarts directory)
        user_sound = self.play_sound(player, False)
        # If it fail, try to generate sound with text-to-speech
        if not user_sound and play_firstname:
            user_speech = self.speech(str(player))
            if not user_speech:
                self.play_sound()

    def sound_end_game(self, player, delay=None, duration=0):
        '''
        Play Winner at the end of the Game (priority : personnal sound / speech / "you")
        '''
        if self.file_class.is_dir('winneris', 'sounds'):
            self.play_sound('winneris', wait_finish=False, duration=duration)
            return
        else:
            self.play_sound('winneris', wait_finish=True, duration=duration)

        if delay is not None:
            pygame.time.wait(delay)
        user_sound = self.play_sound(player, False)
        if not user_sound:
            user_speech = self.speech(player)
            if not user_speech:
                self.play_sound('you', False)
        if duration > 0:
            self.play_sound('set_victory', wait_finish=True, duration=duration)
        else:
            self.play_sound('victory', wait_finish=True, duration=duration)

    def sound_for_touch(self, touch):
        '''
        Method to play sound for double, triple and bullseye
        '''
        if touch == "DB":
            self.play_sound('doublebullseye')
        elif touch == "SB":
            self.play_sound('bullseye')
        else:
            self.play_sound(touch)

    def nice_shot(self, msg='Nice Shot !', wait_time=3000, sens='DG'):
        '''
        Nice hit animation
        '''

        # Image size
        width = int(self.res['x'] / 3)
        height = int(self.res['y'] / 8)

        # Image movement step
        if self.config.rpi_model in ('0', '3A+', '3B+'):
            nb_steps = 20
        else:
            nb_steps = 45
        step = int(self.res['x'] / nb_steps)

        # Placement
        pos_y = int(self.res['y'] / 2.4)
        self.play_sound('niceshot')

        self.display_background()
        self.update_screen()

        if sens == 'GD' :    # Gauche à Droite
            sens = 1
            min_x = -width
            max_x = int(self.res['x'])
        else:
            sens = -1
            min_x = int(self.res['x'])
            max_x = -width

        image1 = self.file_class.get_full_filename('dart1', 'images')
        image2 = self.file_class.get_full_filename('dart2', 'images')

        alternate = 0
        for pos_x in range(min_x, max_x, step * sens):
            rect = (pos_x - step, pos_y , width + 4 * step, height)

            if alternate % 10 < 5:
                image = image1
            else:
                image = image2

            self.display_background(rect=rect)
            self.display_image(image, pos_x, pos_y, width, height)
            self.update_screen(rect=rect)
            alternate += 1

        self.message([msg], wait_time, self.colorset['menu-text-black'], 'middle', 'big')

    def version_check(self, serverversion):
        '''
        Display message for network version mismatch (only for major versions : exemple 1.0.1
        and 1.0.9 are supposed to be compatibles)
        '''
        if serverversion[:3] != self.config.pyDartsVersion[:3]:
            self.logs.log('ERROR',
                        f'Version of client ({self.config.pyDartsVersion}) and server \
                                ({serverversion}) do not match. This is strongly \
                                discouraged ! Please upgrade !')
            self.message([self.lang.translate('version-mismatch')], 200, None, 'middle', 'big', bg_color='menu-ko')
        else:
            self.logs.log('DEBUG', f'Version of client ({self.config.pyDartsVersion}) \
                    and server ({serverversion}) are supposed to be compatible. Continuing...')

    def draw_triple(self, angle_index, color=None, center=True):
        '''
        Draw triples
        '''
        color = self.colorset['menu-ok'] if color is None else color
        radius_triple_out = int(min(self.res['y'], self.res['x']) / 5.3)
        width_triple = min(int(self.res['y'] / 38), int(self.res['x'] / 38))

        if center:
            div = 2
        else:
            div = 4

        arc_rect = (self.res['x'] / div - radius_triple_out, self.res['y'] / 2 - radius_triple_out,
                radius_triple_out * 2, radius_triple_out * 2)

        pygame.draw.arc(self.screen, color, arc_rect, math.radians(18 * 6.5 - 18 * (angle_index + 1)),
                    math.radians(18 * 6.5 - 18 * angle_index), width_triple)

    def draw_missed(self, color=None, center=True):
        '''
        Draw missed
        '''
        color = self.colorset['menu-item-black'] if color is None else color
        radius_missed_out = int(min(self.res['y'], self.res['x']) / 3)
        width_missed = int(min(self.res['y'], self.res['x'] / 60))
        if center:
            div = 2
        else:
            div = 4

        arc_rect = (self.res['x'] / div - radius_missed_out, self.res['y'] / 2 - radius_missed_out,
                radius_missed_out * 2, radius_missed_out * 2)

        pygame.draw.arc(self.screen, color, arc_rect, math.radians(0), math.radians(361), width_missed)

    def draw_double(self, angle_index, color=None, center=True):
        '''
        draw_double
        '''
        if color is None:
            color = self.colorset['menu-alternate']

        radius_double_out = int(min(self.res['y'], self.res['x']) / 3.3)
        width_double = min(int(self.res['y'] / 35), int(self.res['x'] / 35))
        if center:
            div = 2
        else:
            div = 4

        arc_rect = (self.res['x'] / div - radius_double_out, self.res['y'] / 2 - radius_double_out,
                radius_double_out * 2, radius_double_out * 2)

        pygame.draw.arc(self.screen, color, arc_rect, math.radians(18 * 6.5 - 18 * (angle_index + 1)),
                        math.radians(18 * 6.5 - 18 * angle_index), width_double)

    def draw_exterior_simple(self, angle_index, color=None, center=True):
        '''
        Draw external simple
        '''
        if color is None:
            color = self.colorset['menu-item-white']

        radius_double_in = int(min(self.res['y'], self.res['x']) / 3.65)
        width_simple1 = min(int(self.res['y'] / 12), int(self.res['x'] / 12))

        if center:
            div = 2
        else:
            div = 4

        arc_rect1 = (self.res['x'] / div - radius_double_in, self.res['y'] / 2 - radius_double_in,
                    radius_double_in * 2, radius_double_in * 2)

        pygame.draw.arc(self.screen, color, arc_rect1, math.radians(18 * 6.5 - 18 * (angle_index + 1)),
                        math.radians(18 * 6.5 - 18 * angle_index), width_simple1)

    def draw_interior_simple(self, angle_index, color=None, center=True):
        '''
        Draw internal simple
        '''
        if color is None:
            color = self.colorset['menu-item-white']

        radius_triple_in = int(min(self.res['y'], self.res['x']) / 6.2)
        width_simple2 = min(int(self.res['y'] / 8.7), int(self.res['x'] / 8.7))

        if center:
            div = 2
        else:
            div = 4

        arc_rect2 = (self.res['x'] / div - radius_triple_in , self.res['y'] / 2 - radius_triple_in,
                    radius_triple_in * 2, radius_triple_in * 2)

        pygame.draw.arc(self.screen, color, arc_rect2, math.radians(18 * 6.5 - 18 * (angle_index + 1)),
                        math.radians(18 * 6.5 - 18 * angle_index), width_simple2)

    def draw_bull(self, simple=False, double=False, color=None, center=True):
        '''
        Draw bullseye and double bullseye
        '''
        if color is None:
            if double:
                color = self.colorset['target-db']
            elif simple:
                color = self.colorset['target-sb']

        width_simple = min(int(self.res['y'] / 32), int(self.res['x'] / 32))
        width_double = min(int(self.res['y'] / 64), int(self.res['x'] / 64))

        radius_center_out = int(min(self.res['y'], self.res['x']) / 22)
        radius_center_in = int(min(self.res['y'], self.res['x']) / 52)

        if center:
            center_x = int(self.res['x'] / 2)
        else:
            center_x = int(self.res['x'] / 4)

        if simple:
            pygame.draw.circle(self.screen, color, (center_x, int(self.res['y'] / 2)), \
                    radius_center_out, width_simple)
        if double:
            pygame.draw.circle(self.screen, color, (center_x, int(self.res['y'] / 2)), \
                    radius_center_in, width_double)

    def draw_background(self, center=True):
        '''
        Draw background. Call it before anything else
        '''

        width = min(int(self.res['y'] / 3), int(self.res['x'] / 3))
        radius_center = int(min(self.res['y'], self.res['x']) / 3)
        if center:
            center_x = int(self.res['x'] / 2)
        else:
            center_x = int(self.res['x'] / 4)
        pygame.draw.circle(self.screen, self.colorset['color-black'], \
                (center_x, int(self.res['y'] / 2)), radius_center, width)

    def heat_map(self, name, stats, color=None):
        '''
        Display heat map
        '''

        self.display_background()
        self.menu_header(name)
        self.draw_background(center=False)

        item_id = 2
        total = stats[1]
        max_darts = min(total, 15)

        self.display_row(1, 5, 1, [(self.lang.translate("stats-multiplier"), 1 / 3), (self.lang.translate('stats-touch'), 1 / 3), (self.lang.translate('stats-percent'), 1/3)], center=False, align='right')
        self.display_row(2, 5, 1, [(self.lang.translate("Simple"), 1 / 3), (str(stats[2][0]), 1 / 3), (str(stats[2][1]), 1/3)], center=False, align='right')
        self.display_row(3, 5, 0, [(self.lang.translate("Double"), 1 / 3), (str(stats[3][0]), 1 / 3), (str(stats[3][1]), 1/3)], center=False, align='right')
        self.display_row(4, 5, 1, [(self.lang.translate("Triple"), 1 / 3), (str(stats[4][0]), 1 / 3), (str(stats[4][1]), 1/3)], center=False, align='right')
        self.display_row(5, 5, 0, [(self.lang.translate("Missed"), 1 / 3), (str(stats[5][0]), 1 / 3), (str(stats[5][1]), 1/3)], center=False, align='right')

        self.display_row(1, max_darts + 1, 1, [("Segment", 1 / 3), ('Touches', 1 / 3), ('Pourcentage', 1/3)], 1/2, center=False)

        # Print 10 first more occurences
        for stat in stats[0]:
            if item_id > max_darts or stats[0][stat][0] == 0:
                break
            self.display_row(item_id, max_darts, item_id % 2 == 0, [(stat, 1/3), (str(stats[0][stat][0]), 1/3), (str(stats[0][stat][1]), 1/3)], 1/2, 0, False)
            item_id += 1

        ref = 30

        interior = self.config.get_value('SectionAdvanced', 'interior')
        if interior:
            multipliers = ['s', 'S', 'D', 'T']
        else:
            multipliers = ['S', 'D', 'T']
        for hit in [f'{mult}{num}' for mult in multipliers for num in range(1, 21)] + ['SB', 'DB', 'MISS']:
            # Get type
            multiplier = hit[:1]
            pos = stats[0][hit][3]

            # Define colors
            if stats[0][hit][0] == 0:
                green = ref
                red = ref
                blue = ref
                part_color = (ref, ref, ref)
            elif color == 'green':
                green = 255 - ( pos / total ) * 192
                part_color = (0, green, 0)
            else:
                red = 255 - ( pos / total ) * 255
                blue = 255 - red
                green = 0
                part_color = (max(ref, int(red)), max(ref, int(green)), max(ref, int(blue)))
                part_color = (red, green, blue)

            # Draw the right thing
            if hit[1:] == 'B':
                score = 'B'
            elif hit == 'MISS':
                score = None
            else:
                score = int(hit[1:])

            if score == 'B' :
                if multiplier == 'S':
                    self.draw_bull(True, False, part_color, center=False)
                else:
                    self.draw_bull(False, True, part_color, center=False)
            elif multiplier == 'S':
                self.draw_exterior_simple(self.targets[score], part_color, center=False)
                if not interior:
                    self.draw_interior_simple(self.targets[score], part_color, center=False)
            elif multiplier == 's':
                self.draw_interior_simple(self.targets[score], part_color, center=False)
            elif multiplier == 'D':
                self.draw_double(self.targets[score], part_color, center=False)
            elif multiplier == 'M':
                self.draw_missed(part_color, center=False)
            else:
                self.draw_triple(self.targets[score], part_color, center=False)

        self.update_screen()
        self.display_button(True, 'continue', special='return')

        self.wait_touch()

    def sort_players(self, player):
        return player[1]

