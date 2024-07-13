#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
awesome electronic darts' game
"""

################
# Import pyDarts internal classes and load essentials
################

import sys
import datetime
from time import sleep
import os, os.path
from copy import deepcopy
import random
from subprocess import Popen

from threading import Event

try:
    from include import cconfig
    from include import clogs
    from include import cevent

    # Starts logger system, it will filter on a config basis
    logs = clogs.Logs()
    # Load config file
    Config = cconfig.Config(logs)
    # Check local config file existance and create if necessary
    Config.check_config_file()
    # Read config file for main configuration and store it in object data storage
    Config.read_file("SectionGlobals")
    # Read hidden default values
    Config.read_file("SectionAdvanced")
    # Read Config file for keys combination : rpi send a key=>it correspond to a hit
    ConfigKeys = Config.read_file("SectionKeys")
    # Read Config file for rpi configuration
    Config_rpi = Config.read_file("Raspberry")
    # Read Config file for rpi Dart Board Pins configuration
    config_leds = Config.read_file("Raspberry_Leds")
    # Read Config file for LED Target configuration
    config_target_leds = Config.read_file("LEDTarget")
    # Read Config file for Favorites
    config_favorites = Config.read_file("Favorites", none='')
    # Read Config file for events
    config_events = Config.read_file("Events")
    # Read Config file for global options
    config_globals = Config.read_file("SectionGlobals")
    # Read Config file for advanced
    config_advanced = Config.read_file("SectionAdvanced")
    # Read inputs
    config_input = Config.read_file("Raspberry_BoardPinsIns")
    # Read outputs
    config_output = Config.read_file("Raspberry_BoardPinsOuts")

    # Games' options
    for game in config_advanced['game-options-list'].split(','):
        Config.read_file(f"game-{game.replace(' ', '_')}")

    # Update logs system with loglevel set in config
    logs.set_level(Config.get_value('SectionGlobals', 'debuglevel', 0))

    # dispatcher dispatcher
    subsribers = []
    if config_leds['PIN_STRIPLED'] in ('10', '12', '18', '21'):
        subsribers.append('StripLeds')
    if config_leds['PIN_TARGETLED'] in ('10', '12', '18', '21'):
        subsribers.append('TargetLeds')
    if Config.get_value('SectionAdvanced', 'use-dmd'):
        subsribers.append('Dmd')
    if Config.get_value('SectionAdvanced', 'use-matrix'):
        subsribers.append('Matrix')
    if Config.get_value('SectionAdvanced', 'use-other') or Config.get_value('SectionAdvanced', 'use-hue'):
        subsribers.append('Other')

    mqtt_broker = Config.get_value('SectionAdvanced', 'mqtt-broker')
    logs.log("DEBUG", f"use-dmd option is set to : {Config.get_value('SectionAdvanced', 'use-dmd')}")
    logs.log("DEBUG", f"use-matrix option is set to : {Config.get_value('SectionAdvanced', 'use-matrix')}")
    logs.log("DEBUG", f"use-other option is set to : {Config.get_value('SectionAdvanced', 'use-other')}")
    logs.log("DEBUG", f"mqtt-broker option is set to : {Config.get_value('SectionAdvanced', 'mqtt-broker')}")

    dispatcher = cevent.Event(logs, config_events, subscribers=subsribers, broker=mqtt_broker)

    # For old versions +> write new config file
    logs.log("DEBUG", f"target-bgcolor1 option is set to : {Config.get_value('SectionAdvanced', 'target-bgcolor1')}")
    logs.log("DEBUG", f"target-bgcolor2 option is set to : {Config.get_value('SectionAdvanced', 'target-bgcolor2')}")
    logs.log("DEBUG", f"target-bgcolor3 option is set to : {Config.get_value('SectionAdvanced', 'target-bgcolor3')}")
    logs.log("DEBUG", f"target-bgbrightness option is set to : {Config.get_value('SectionAdvanced', 'target-bgbrightness')}")

except Exception as exception:
    print("[FATAL] Unable to load internal first level dependancies or to create basic instances. Your download seems corrupted. Please download raspydarts again.")
    print(f"[FATAL] Error was {exception}")
    exit(1)

#################
# Start Leds servers
#################

if Config.file_exists and config_leds['PIN_STRIPLED'] in ('10', '12', '18', '21'):
    logs.log("DEBUG", "Starting Strip Leds Server")
    strip_log = open('logs/StripLeds.log', "w", 1)
    cmd = ['sudo', 'python3', '/pydarts/addons/StripLeds_Server.py'
            , f'-host={mqtt_broker}'
            , '9'
            , f"{dispatcher.strip_topic}"
            , f"{config_leds['PIN_STRIPLED']}"
            , f"{config_leds['NBR_STRIPLED']}"
            , f"{config_leds['BRI_STRIPLED']}"]
    p_strip = Popen(cmd, stdout=strip_log)
    dispatcher.strip_leds = True
    logs.log("DEBUG", f"Launched {' '.join(cmd)}")
    sleep(0.5)
else:
    dispatcher.strip_leds = False
    p_strip = None

if Config.file_exists and config_leds['PIN_TARGETLED'] in ('10' , '12', '18', '21'):
    logs.log("DEBUG", "Starting Target Leds Server")
    logs.log("DEBUG", f"Using this configuration : {config_target_leds}")
    target_log = open('logs/TargetLeds.log', "w", 1)
    cmd = ['sudo', 'python3', '/pydarts/addons/TargetLeds_Server.py'
            , f'-host={mqtt_broker}'
            , '-bgcolors={},{},{}'.format(Config.get_value('SectionAdvanced', 'target-bgcolor1')
                , Config.get_value('SectionAdvanced', 'target-bgcolor2')
                , Config.get_value('SectionAdvanced', 'target-bgcolor3'))
            , f"-bgbrightness={Config.get_value('SectionAdvanced', 'target-bgbrightness')}"
            , '10'
            , f'{dispatcher.target_topic}'
            , f'{config_target_leds}'
            , f"{config_leds['PIN_TARGETLED']}"
            , f"{config_leds['BRI_TARGETLED']}"]
    p_target = Popen(cmd, stdout=target_log)
    dispatcher.target_leds = True
    logs.log("DEBUG", f"Launched {' '.join(cmd)}")
    sleep(0.5)
else:
    dispatcher.target_leds = False
    p_target = None

if Config.file_exists and Config.get_value('SectionAdvanced', 'use-hue'):
    logs.log("DEBUG", "Starting Hue Server")
    hue_log = open('logs/Hue.log', "w", 1)
    cmd = ['python3', '/pydarts/addons/Hue_Server.py'
            , f'-host={mqtt_broker}'
            , f'{dispatcher.other_topic}']
    p_hue = Popen(cmd, stdout=hue_log)
    dispatcher.other = True
    logs.log("DEBUG", f"Launched {' '.join(cmd)}")
elif Config.get_value('SectionAdvanced', 'use-other'):
    dispatcher.other = True
else:
    dispatcher.other = False


logs.log("DEBUG", f"dispatcher.strip_leds is set to {dispatcher.strip_leds}")
logs.log("DEBUG", f"dispatcher.target_leds is set to {dispatcher.target_leds}")
logs.log("DEBUG", f"subsribers is set to {subsribers}")

#################
# Welcome
#################
print("############### Welcome to RaspyDarts ########################")
print("#      A Free, Open-Source and Open-Hardware Darts Game      #")
print("#             Please check the website to know more          #")
print("#               {}               #".format(Config.officialwebsite))
print("#                     or check the Wiki                      #")
print("#         {}         #".format(Config.wiki))
print("#            or use --help for available options             #")
print("##############################################################")

########################
# Create various instances of second layer internal classes
########################
# from include import CBluetooth
from include import craspberry
from include import cdmd
from include import cvideos
from include import cupdate
#from include import cplayer
from include import cscreen
from include import clocale
from include import cclient
from include import cscores
from include import cfiles

# Create locale instance
Lang = clocale.Locale(logs, Config)
# Manage display
font = Config.get_value('SectionGlobals', 'font', False)  # Local players
releasedartstime = int(Config.get_value('SectionGlobals', 'releasedartstime'))# Relase darts delay
wait_event_time = int(Config.get_value('SectionGlobals', 'waitevent_time', False))
t_event = Event()

# Manage raspberry gpio
try:
    rpi = craspberry.Craspberry(logs, Config, config_target_leds, dispatcher, t_event=t_event)
    rpi_error = None
except Exception as exception:
    print(f"[ERROR] {exception}")

    rpi_error = exception
    Config_rpi['EXTENDED_GPIO'] = 0
    try:
        rpi = craspberry.Craspberry(logs, Config, config_target_leds, dispatcher, t_event=t_event)
    except Exception as exception:
        print(f"[ERROR] {exception}")

        rpi_error = exception

# For random files
File = cfiles.Cfile(Config, logs, theme=Config.get_value('SectionGlobals', 'colorset'))
logs.log("INFO", f"Theme dir is {File.theme_dir}")
logs.log("INFO", f"Personnal dir is {Config.user_dir}")
logs.log("INFO", f"Root dir is {Config.root_dir}")

# Manage Raspydarts dmd
dmd = cdmd.Cdmd(logs, dispatcher, File)

# Manage Raspydarts Video Player
video_level = int(Config.get_value('SectionGlobals', 'videos'))
volume = int(Config.get_value('SectionGlobals', 'soundvolume'))
try:
    videosound_multiplier = int(Config.get_value('SectionGlobals', 'videosound_multiplier'))
    if videosound_multiplier < 1 or videosound_multiplier > 5:
        raise('not valid multiplier')
    logs.log("INFO", f"Video sound multiplier is set to {videosound_multiplier}")
except:
    videosound_multiplier = 1
    logs.log("ERROR", f"{Config.get_value('SectionGlobals', 'videosound_multiplier')} is not a valid videosound_multiplier(1-5). Back to 1")

try:
    sound_multiplier = float(Config.get_value('SectionGlobals', 'sound_multiplier'))
    if sound_multiplier < 10 or sound_multiplier > 100:
        raise('not valid multiplier')
    logs.log("INFO", f"Sound multiplier is set to {sound_multiplier}")
except:
    sound_multiplier = 100
    logs.log("ERROR", f"{Config.get_value('SectionGlobals', 'sound_multiplier')} is not a valid sound_multiplier(10-100. ex : 75). Back to 100")

video_player = cvideos.Videos(logs, File, level=video_level, volume=volume, multiplier=videosound_multiplier)

#display = cscreen.Screen(Config, logs, File, Lang, rpi, dmd, video_player, Font=font, wait_event_time=wait_event_time, t_event=t_event)
display = cscreen.Screen(Config, logs, File, Lang, rpi, dmd, video_player, Font=font, wait_event_time=wait_event_time)
display.set_soundmultiplier(sound_multiplier)

rpi.set_play_sound(display.play_sound)
rpi.set_send_insult(dmd.send_insult)

if rpi_error is not None:
    display.mcp_error(rpi_error)

# Client of Master Server
NetMasterClient = cclient.MasterClient(logs)
# v1.2 SQlite score storage
scores = cscores.Scores(Config, logs)

#####################
# Update librairies #
#####################

if not Config.file_exists:
    logs.log("INFO", "================================================================")
    logs.log("INFO", "Updating librairies\n")
    display.message(['Updating_librairies'], 0, None, 'middle')
    cmd = '/pydarts/scripts/update_tool.sh'
    os.system(cmd)
    logs.log("INFO", "================================================================")

##############
# AUTO UPDATE
##############
game_type = None

display.init_colorset()

version = cupdate.get_version(logs)
try:
    display.message(['update-check'], 0, None, 'middle')
    last, new_version, size = cupdate.get_last(logs, \
            config_favorites['servers'].split(',')[0].split(':')[0], '5000', version)

    if last is not None:
        display.message(['update-download'], 0, None, 'middle')
        last, size = cupdate.download_update(logs, \
                config_favorites['servers'].split(',')[0].split(':')[0], '5000', last, size)

        if last is None:
            display.message(['update-failed'], 0, None, 'middle')
        else:
            response = display.wait_validation("update-available")
            if response:
                display.message(['updating'], 0, None, 'middle')
                cupdate.apply_update(logs, last, new_version)
                display.message([f'Version {new_version} installée', 'restarting'], \
                        1000,  'middle', bg_color='menu-ok')
                version = new_version

                game_type = 'restart'
except Exception as exception:
    print("[WARNING] Unable to check/get updates.")
    print(f"[WARNING] Error was {exception}")
    print(f"version is {version}")

##############
# INIT
##############

# Give translations to object rpi
rpi.Lang = Lang

dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])
dispatcher.publish('launch', limit=['TARGET', 'STRIP', 'OTHER'])

# Beautiful intro screen
if game_type != 'restart' and rpi_error is None:
    if bool(config_advanced['launch-game-celebration']):
        rpi.light_buttons(['LIGHT_CELEBRATION'])
    dmd.send_text(Lang.translate('Welcome'))
    #display.nice_shot(Lang.translate('Welcome'))
    rpi.light_buttons(['LIGHT_CELEBRATION'], False)

# If exists, display version's changelog
display.display_changelog(version)

# Sound volume
if volume:
    display.sound_volume = volume

# Sys requirements check
if sys.version[:3] not in Config.supported_python_versions:
    logs.log("WARNING", f"Your version of python {sys.version[:3]} is not known as raspydarts compatible.")
    logs.log("WARNING", f"Please execute raspydarts with one of this version of python : {Config.supported_python_versions}.")

# Verbosity
debuglevel = int(Config.get_value('SectionGlobals', 'debuglevel'))
if debuglevel >= 1 and debuglevel <= 4:
    logs.update_facility(debuglevel)

####################
# Calibration Wizard
####################

rpi.gpio_connect()

print(f"Config.file_exists={Config.file_exists}")

if not Config.file_exists:
    logs.log("DEBUG", "Launching raspberry input wizard")

    config_done = False
    cancel = 0
    while not config_done:
        if cancel > 2:
            logs.log("DEBUG", "Configuration canceled by user")
            sys.exit(0)

        cancel += 1
        # Display first use wizard
        config_done = display.get_rpi_config()

    p_target = False
    p_strip = False
    game_type = 'restart'

#####################
# Init some vars
#####################
match_qty = 0  # Count number of matches

# Init vars according to Customization, config else
#solo = int(Config.get_value('SectionGlobals', 'solo'))
play_firstname = bool(Config.get_value('SectionGlobals', 'play_firstname'))
print_dartstroke = bool(Config.get_value('SectionGlobals', 'print_dartstroke'))
light_target = bool(Config.get_value('SectionGlobals', 'light_target'))
light_strip = bool(Config.get_value('SectionGlobals', 'light_strip'))
illumination_mode = bool(Config.get_value('SectionGlobals', 'illumination_mode')) #by Manu scripts.
illumination_color = Config.get_value('SectionGlobals', 'illumination_color') #by Manu scripts.
pnj_time = int(Config.get_value('SectionGlobals', 'pnj_time'))
sound_duration = int(Config.get_value('SectionGlobals', 'nextplayer_sound_duration'))
try:
    competition_mode = bool(Config.get_value('SectionGlobals', 'competition_mode'))
except:
    competition_mode = False

#logs.log("DEBUG", f"Solo option is set to : {solo}s")
logs.log("DEBUG", f"play_firstname option is set to : {play_firstname}")
logs.log("DEBUG", f"print_dartstroke option is set to : {print_dartstroke}")
logs.log("DEBUG", f"light_target option is set to : {light_target}")
logs.log("DEBUG", f"light_strip option is set to : {light_strip}")
logs.log("DEBUG", f"illumination_mode option is set to : {illumination_mode}") #by Manu script.
logs.log("DEBUG", f"illumination color option is set to : {illumination_color}") #by Manu script.
logs.log("DEBUG", f"pnj_time option is set to : {pnj_time}ms")
logs.log("DEBUG", f"nextplayer_sound_duration option is set to : {sound_duration}ms")
logs.log("DEBUG", f"wait_event_time option is set to : {wait_event_time}ms")

stats_screen = False  # Return value of Stats Screen (start again a new game with same parameters)
direct_play = None  # Direct play functionnlity (play without having to use menus)
netgamename = Config.get_value('SectionAdvanced', 'netgamename', False)  # Game Name

if game_type != 'restart':
    game_type = 'local'
players_bank = Config.get_value('SectionAdvanced', 'localplayers', False).split(',')  # Local players
selected_game = Config.get_value('SectionAdvanced', 'selected_game', False)            # Selected game
pref_fun_game = Config.get_value('SectionAdvanced', 'preferedfungame', False, None)
pref_classic_game = Config.get_value('SectionAdvanced', 'preferedclassicgame', False, None)
pref_sport_game = Config.get_value('SectionAdvanced', 'preferedsportgame', False, None)
pref_category = Config.get_value('SectionAdvanced', 'preferedcategory', False, None)
nb_sets = int(Config.get_value('SectionAdvanced', 'nb_sets', False, None))

if pref_category is None:
    category = 'classic'
else:
    category = pref_category

favorites_players = Config.get_value('Favorites', 'firstnames', False).split(',')
local_players = Config.get_value('Favorites', 'firstnames', False).split(',')

logs.log("DEBUG", f"localplayers option is set to : {players_bank}")
logs.log("DEBUG", f"local_players option is set to : {local_players}")
logs.log("DEBUG", f"pref_fun_game option is set to : {pref_fun_game}")
logs.log("DEBUG", f"pref_sport_game option is set to : {pref_sport_game}")
logs.log("DEBUG", f"pref_classic_game option is set to : {pref_classic_game}")
logs.log("DEBUG", f"pref_category option is set to : {pref_category}")

wait_finish = not File.is_dir('next_player', 'sounds')
######################
######## SOFTWARE LOOP
######################

selected_game = None
try:
    while game_type not in ('restart', 'quit', 'shutdown'):

        # Init (or reset) network status
        net_status = None  # Master or slave

        # To restore special bg
        display.reset_background()
        #############################
        # NEW MENUS SEQUENCE
        #############################

        ######
        # START AGAIN (possibility to start a new game straight away without using menus again)
        ######

        if stats_screen == 'startagain':
            if game_type == 'local':
                menu = True
                if config_globals['keeporder']:
                    for player in players:
                        player.reset()
                else:
                    # Try to order players depending of game
                    try:
                        local_players = game.next_game_order(players)
                        all_players = local_players
                        players_count = len(local_players)
                    except Exception as exception:
                        logs.log("ERROR", "Unable to order players from previous results.")
                        logs.log("ERROR", f"Error was {exception}")
            elif game_type in ('netjoin', 'netcreate'):
                players_count = len(local_players)
                menu = 'connect'

        ###
        ### DIRECT PLAY MODE (possibility to launch a game without passing thru menus).
        ### Only available if it hasen't be disabled by any process
        elif game_type == 'local' and local_players and selected_game and direct_play:
            try:
                Game = selected_game.replace(' ', '_')
                menu = True
                all_players = local_players
                players_count = len(local_players)
                choosed_game = __import__("games.{Game}", fromlist=["games"])
                    
                # Merge config file options and default game options
                default_game_options = choosed_game.OPTIONS
                # Take config file Game options if they exists
                config_game_options = Config.read_file(Game)
                if not config_game_options: config_game_options = {}  # Default to empty dict
                game_options = default_game_options.copy()
                game_options.update(config_game_options)
                display.game_options = game_options
                display.selected_game = Game
                # Enable Direct Play mode
                direct_play = True
            except Exception as exception:
                logs.log("ERROR", f"Unable launch Direct Play mode. Error was {exception}")
                menu = 'gametype'
        else:
            menu = 'gametype'

        #######################
        # Menus loop
        #######################
        while menu is not True:

            ########
            # MAIN MENU - GAME TYPE (LOCAL, NETWORK, NETWORK MANUAL)
            ########
            if menu == 'gametype':
                rpi.light_buttons(['LIGHT_NAVIGATE', 'LIGHT_VALIDATE'])
                rpi.light_buttons(['LIGHT_BACK'], False) #by Manu script.
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                game_type = display.main_menu()
                if game_type in ('restart', 'quit', 'shutdown'):
                    rpi.light_buttons(['LIGHT_VALIDATE'], False) #by Manu script.
                    break
                elif game_type == 'infos':
                    display.infos_menu(Config)
                elif game_type != 'miscellaneous':
                    menu = 'players'

            ########
            # PLAYERS NAMES
            ########
            if menu == 'players':
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                rpi.light_buttons(['LIGHT_PLAYERS'])
                rpi.light_buttons(['LIGHT_BACK']) #by Manu script.
                # Display menu anyway
                nb_sets = int(Config.get_value('SectionAdvanced', 'nb_sets', False, None))
                #if game_type == 'netcreate':
                #    nb_sets, players_list, competition_mode = \
                #            display.players_menu(local_players, bank=players_bank, sets=nb_sets, context=game_type)
                #elif game_type == 'netjoin':
                if game_type in ('netjoin', 'netcreate'):
                    nb_sets, players_list, competition_mode = \
                            display.players_menu(local_players, bank=players_bank, sets=None, context=game_type)
                    nb_sets = 1
                else:
                    nb_sets, players_list, competition_mode = \
                            display.players_menu(local_players, bank=players_bank, sets=nb_sets, competition_mode=competition_mode)

                if players_list == 'escape':
                    menu = 'gametype'
                else:
                    local_players = players_list[::]
                    players_count = len(local_players)  # players_count = Number of players

                    if game_type in ('netjoin', 'netcreate'):
                        menu = 'serverlist'
                    elif game_type == 'local':
                        menu = 'gamecategory'
                rpi.light_buttons(['LIGHT_PLAYERS'], False)

                if competition_mode:
                    video_player.set_level(0)
                    #solo = -1
                    releasedartstime = 1
                    display.set_blinktime(500)
                else:
                    display.reset_mode()
                    #solo = int(Config.get_value('SectionGlobals', 'solo'))
                    releasedartstime = int(Config.get_value('SectionGlobals', 'releasedartstime'))# Relase darts delay
                    display.set_blinktime(int(Config.get_value('SectionGlobals', 'blinktime')))

                    video_player.set_level(video_level)
                logs.log("DEBUG", f"Competition mode : {competition_mode}")
                logs.log("DEBUG", f"Video : {video_player.level}")
                logs.log("DEBUG", f"releasedartstime  : {releasedartstime}")

            ########
            # NETWORK USING MASTER SERVER
            ########
            if menu == 'serverlist':  # Choice server (when several)
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                if config_favorites['servers'] == '':
                    display.message(["Aucun server paramétré."], wait=5, refresh=True)
                    menu = 'servers'
                    game_type = 'miscellaneous'
                else:
                    net_client = cclient.Client(logs)
                    # No interaction if only one server on favorites
                    Server = display.server_menu(net_client, config_favorites['servers'].split(','))
                    servername = Server.split(':')[0]
                    serverport = 25005
                    masterserverport = 25006 #int(Server.split(':')[1])
                    serveralias = Server.split('.')[0]
                    logs.log("DEBUG", f"Using {servername}:{masterserverport}")
                    if Server == 'escape':
                        # Back to home
                        menu = 'gametype'
                    else:
                        menu = 'createorjoin'


            if menu == 'createorjoin':
                menu = 'connect'
                if game_type == 'netjoin':
                    logs.log("DEBUG", f"Get remote game list on {servername}:{masterserverport}")
                    netgamename = display.net_game_list(NetMasterClient, players_count, servername, masterserverport)
                    if netgamename == 'escape':
                        menu = 'gametype'
                else:
                    netgamename = f'game{random.randint(10000, 99999)}'

            ########
            # NET CONNECTION
            ########
            # If network, connect to server
            if game_type in ('netjoin', 'netcreate') and menu == 'connect':
                logs.log("DEBUG", "Net game requested.")
                releasedartstime = 0 # In case of online game, force the SOLO MODE OFF from config (players must push PLAYERBUTTON every rounds, mandatory)
                try:
                    display.display_background()
                    display.message([Lang.translate('game-client-connecting')], wait=500)
                    net_client.connect_host(servername, serverport)    #int(serverport))
                    menu = 'net1'
                except Exception as exception:
                    logs.log("ERROR", f"Unable to reach server : {servername}:{serverport}. Error is {exception}")
                    display.display_background()
                    display.message([Lang.translate('game-client-no-connection')])
                    menu = 'gametype'

            if game_type in ('netjoin', 'netcreate') and menu == 'net1':
                # Check client/server version compatibility
                logs.log("DEBUG", "Join {} remote game".format(netgamename))
                serverversion = net_client.get_server_version(netgamename)
                display.version_check(serverversion)
                net_status = net_client.join2(netgamename)
                logs.log("DEBUG", "net_status = {}".format(net_status))
                # If you are master go to the game selector
                if net_status == 'YOUAREMASTER' and stats_screen != 'startagain':
                    menu = 'gamecategory'
                # If you are master and asked to start again, so... go to starting page
                elif net_status in ['YOUAREMASTER', 'YOUARESLAVE']:
                    menu = 'net3'

            if game_type == 'miscellaneous':
                # PREFERENCES
                rpi.light_buttons(['LIGHT_BACK']) #by Manu script.
                if menu != 'servers':
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    Misc = display.miscellaneous()

                    if Misc == 'escape':
                        menu = 'gametype'
                    else:
                        menu = Misc

                if menu == 'firstnames':
                    # FAVORITE PLAYERS
                    rpi.light_buttons(['LIGHT_PLAYERS'])
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    useless, firstnames = display.players_menu(favorites_players, context='pref', bank=players_bank)
                    if firstnames != 'escape':
                        config_favorites['firstnames'] = ','.join(firstnames)
                        favorites_players = firstnames[::]
                        local_players = firstnames[::]
                        Config.write_file()
                    rpi.light_buttons(['LIGHT_PLAYERS'], False)

                elif menu == 'games':
                    # FAVORITE GAMES
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    games = display.favorites_games_menu(config_favorites['games'])
                    if games != 'escape':
                        config_favorites['games'] = games
                        Config.write_file()

                elif menu == 'servers':
                    # SERVERS MENU
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    servers = display.favorites_servers_menu(config_favorites['servers'])
                    if servers != 'escape':
                        config_favorites['servers'] = servers
                        Config.write_file()
                    menu = ''

                elif menu == 'setup':
                    # SETUP MENU
                    setup = display.setup_menu()

                    while setup != 'escape':
                        if setup == 'test-buttons':
                            display.test_buttons_menu()

                        elif setup == 'test-target':
                            display.test_target_menu()

                        elif setup == 'test-toys':
                            display.test_toys_menu()

                        elif setup == 'reset':
                            response = display.wait_validation("reinit-question")
                            if response:
                                display.message(['reseting'], 0, None, 'middle')
                                os.rename(Config.configFile, f"{Config.configFile}.back")
                                game_type = 'restart'
                                break

                        elif setup == 'setup-buttons':
                            try:
                                DefButtons = rpi.gpio.get_defaults()
                            except:
                                DefButtons = rpi.get_defaults()
                            setupbuttons = display.setup_buttons_menu(Config_rpi, DefButtons)
                            if setupbuttons != 'escape':
                                Config_rpi = setupbuttons
                                if not rpi.set_buttons(setupbuttons):
                                    display.message([config-noMCP], None, 'red', 'middle', 'big')
                                else:
                                    rpi.config.set_config('Raspberry', setupbuttons)
                                    Config.write_file()

                        elif setup == 'setup-leds':
                            setupleds = ''
                            selY = 1
                            selX = 1
                            Nmoy = 6
                            work = str(config_target_leds)
                            while setupleds != 'escape':
                                if isinstance(setupleds, dict):
                                    config_target_leds = setupleds
                                    rpi.config.set_config('LEDTarget', setupleds)
                                    Config.write_file()
                                    break
                                elif setupleds[0:3:1] == 'try':
                                    # try
                                    leds = setupleds.split('|')[1]
                                    work = setupleds.split('|')[2]
                                    work = f"{setupleds.split('|')[3]}|{work}"
                                    selY = int(setupleds.split('|')[4])
                                    selX = int(setupleds.split('|')[5])
                                    Nmoy = int(setupleds.split('|')[6])
                                    dispatcher.publish('leds', leds, limit=['TARGET', 'STRIP', 'OTHER'])
                                    if setupleds.count('|') != 6:
                                        work = str(config_target_leds)
                                setupleds = display.setup_leds_menu(work, selY, selX, Nmoy)

                        elif setup == 'setup-pinleds':
                            used_pins = []
                            for key in config_input:
                                try:
                                    used_pins.append(int(config_input[key]))
                                except:
                                    pass
                            for key in config_output:
                                try:
                                    used_pins.append(int(config_output[key]))
                                except:
                                    pass

                            tmp = display.setup_pinsleds_menu(config_leds, used_pins)
                            if tmp != 'escape':
                                config_leds = tmp
                                rpi.config.set_config('Raspberry_Leds', config_leds)
                                Config.write_file()

                        setup = display.setup_menu()

                elif menu == 'firstname-bank':
                    # Firstnames bank menu
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    rpi.light_buttons(['LIGHT_PLAYERS'])
                    useless, bank = display.players_menu(players_bank, context='bank')
                    if bank != 'escape':
                        config_advanced['localplayers'] = ','.join(bank)
                        Config.write_file()
                        players_bank = bank[::]
                    rpi.light_buttons(['LIGHT_PLAYERS'], False)

                elif menu == 'backups':
                    # BACKUP MENU
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    b = display.backup_menu()
                    if b == 'restart':
                        game_type = 'restart'
                        break

                elif menu == 'customization':
                    # CUSTOMIZATION
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    cust = display.customization_menu(Config.config['SectionGlobals'])
                    if cust != 'escape':
                        Config.config['SectionGlobals'] = cust
                        Config.write_file()
                        config_globals = Config.read_file("SectionGlobals")
                        video_level = int(Config.get_value('SectionGlobals', 'videos'))
                        video_player.set_level(video_level)
                        video_player.set_volume(int(Config.get_value('SectionGlobals', 'soundvolume')))
                        display.sound_volume = int(Config.get_value('SectionGlobals', 'soundvolume'))
                        #solo = int(Config.get_value('SectionGlobals', 'solo'))
                        releasedartstime = int(Config.get_value('SectionGlobals', 'releasedartstime'))
                        play_firstname = bool(Config.get_value('SectionGlobals', 'play_firstname'))
                        print_dartstroke = bool(Config.get_value('SectionGlobals', 'print_dartstroke'))
                        light_target = bool(Config.get_value('SectionGlobals', 'light_target'))
                        light_strip = bool(Config.get_value('SectionGlobals', 'light_strip'))
                        competition_mode = bool(Config.get_value('SectionGlobals', 'competition_mode'))
                        illumination_mode = bool(Config.get_value('SectionGlobals', 'illumination_mode')) #by Manu script.
                        illumination_color = Config.get_value('SectionGlobals', 'illumination_color') #by Manu script.

                        logs.update_facility(int(Config.get_value('SectionGlobals', 'debuglevel')))
                        display.wait_event_time = int(Config.get_value('SectionGlobals', 'waitevent_time'))
                        display.file_class.reset_theme(Config.get_value('SectionGlobals', 'colorset'))
                        display.init_colorset()
                        display.define_constants(True, Font=cust['font'])

                elif menu == 'animations':
                    # LEDS ANIMATIONS
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    event = display.animations_menu(dispatcher.get_events())
                    work = ''
                    while event != 'escape':
                        if work != '':
                            animation = dispatcher.string_to_pref(work)
                        else:
                            try:
                                animation = config_events[event].copy()
                            except:
                                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                                animation = None

                        anim = display.event_menu(event, dispatcher.get_strip(), dispatcher.get_target(), dispatcher.get_colors(), animation)

                        if anim[0:3:1] == 'try':
                            work = anim.split('|')[1]
                            for a in anim.split('|')[2::]:
                                dispatcher.publish('special', a, limit=['TARGET', 'STRIP', 'OTHER'])
                        elif anim == 'escape':
                            dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                            event = display.animations_menu(dispatcher.get_events(), selected_event=event)
                            work = ''
                        else:
                            # save
                            config_events[event] = dispatcher.string_to_pref(anim)
                            Config.write_file()
                            dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                            event = display.animations_menu(dispatcher.get_events(), selected_event=event)
                            work = ''
                if game_type != 'restart':
                    game_type = 'miscellaneous'
                else:
                    break

            if (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gamecategory':
                # GAME CATEGORY SELECTION
                # Display game category
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])

                response = display.game_category_menu(category=category)
                if response == 'escape':
                    rpi.gpio_flush()
                    menu = 'players'
                    if net_status is not None:
                        net_client.leave_game(netgamename, local_players, net_status)
                        net_client.close_host()
                        net_status = None  # reset Network status if you leave network game
                else:
                    category = response
                    if selected_game is None:
                        if category == 'fun':
                            selected_game = f"{pref_fun_game}"
                        elif category == 'classic':
                            selected_game = f"{pref_classic_game}"
                        elif category == 'sport':
                            selected_game = f"{pref_sport_game}"
                    menu = 'gamelist'

            if (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gamelist':
                # GAME SELECTION
                # Display game choice and option only for game creators (local and netcreate)
                games = display.get_games_list(category)
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                display.update_screen(display.message(["Loading"], wait=0, refresh=False))
                Game = display.game_menu(games, config_favorites['games'], selected_game=selected_game)

                if Game == 'escape':
                    menu = 'gamecategory'
                else:
                    choosed_game = __import__(f"games.{category}.{Game.replace(' ', '_')}", fromlist=["games"])
                    try:
                        if not choosed_game.check_players_allowed(players_count):
                            display.message([f"{Lang.translate('bad-numberofplayers')}"], 2500, 'menu-ko', 'middle', 'big')
                        else:
                            logs.log("DEBUG", f"Ok, {players_count} players allowed")
                            selected_game = Game
                            menu = 'gameoptions'
                    except:
                        logs.log("DEBUG", f"KO, cannot check if {players_count} players allowed")
                        selected_game = Game
                        menu = 'gameoptions'

            if (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gameoptions':
                # GAME OPTIONS
                # Display game choice and option only for game creators (local and netcreate)
                default_game_options = choosed_game.OPTIONS
                config_game_options = Config.read_file(f"game-{Game.replace(' ', '_')}")  # Take config file Game options if they exists
                if not config_game_options: config_game_options = {}  # Default to empty dict

                game_options = default_game_options.copy()
                game_options.update(config_game_options)

                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                game_options = display.options_menu(game_options, Game.replace(' ', '_'), players_count)
                if game_options == 'escape':
                    menu = 'gamelist'
                elif net_status is None:
                    menu = True
                else:
                    menu = 'net3'

    
            if net_status == 'YOUAREMASTER' and menu == 'net3':
                # MasterPlayer send game info to server
                # Send Game info (gamename and selected options - can be merged)
                net_client.send_game(Game.replace(' ', '_'))
                net_client.send_options(game_options, choosed_game.NB_DARTS, nb_sets)
                menu = 'starting'
                try:  # Check if it is the right place
                    logs.log("DEBUG", f"Sending game info to master server {servername}:{masterserverport}")
                    NetMasterClient.connect_master(servername, masterserverport)
                    NetMasterClient.send_game_info(servername, serveralias, serverport, netgamename, Game.replace(' ', '_'), config_globals['netgamecreator'], players_count, nb_sets)
                    NetMasterClient.close_connection()
                except Exception as exception:
                    logs.log("WARNING", f"Unable to reach Master Server {servername} on port {masterserverport}. Error was : {exception}")

            """
            Notice Master server that we joined and add local players to game on
            master server
            """
            if net_status == 'YOUARESLAVE' and menu == 'net3':
                try:
                    NetMasterClient.connect_master(servername, masterserverport)
                    NetMasterClient.join_game(netgamename, len(local_players))
                    NetMasterClient.close_connection()
                    menu = 'starting'
                except:
                    logs.log("WARNING", "Unable to add local players to Master Server")

            if menu == 'starting':
                """
                Network game menu - Starting - If network enabled, all_players (All players names)
                list is updated via network
                """
                # Wait for the choosed game from server
                if net_status == 'YOUARESLAVE':
                    Game = net_client.get_game()
                # Display starting page with a few game info
                all_players = display.starting(net_client, net_status, local_players, netgamename, Game.replace(' ', '_'))
                menu = True  # Means that goes on...
                if all_players == [] or all_players == -1:  # Empty network Player List or -1 signal
                    net_client.leave_game(netgamename, local_players, net_status)
                    net_client.close_host()
                    # For Slave players, display the message and wait for Enter to be pressed
                    if not all_players:
                        display.message([Lang.translate('master-player-has-left')], None, None, 'middle')
                        NetMasterClient.connect_master(servername, masterserverport)
                        NetMasterClient.cancel_game(netgamename)
                        NetMasterClient.close_connection()
                        rpi.listen_inputs(['arrows'], ['escape', 'enter'])
                    elif all_players == -1:  # Notice Master server that someone is leaving
                        NetMasterClient.connect_master(servername, masterserverport)
                        NetMasterClient.leave_game(netgamename, len(local_players))
                        NetMasterClient.close_connection()
                    menu = 'gametype'
                    net_status = None  # reset Network status if you leave network game
                else:
                    menu = 'net4'
            # If network disabled - local games
            else:
                all_players = local_players  #  In local games, all players are local players
                players_count = len(all_players)  # Refresh count of number of players again

            if net_status == 'YOUARESLAVE' and menu == 'net4':
                """ Display message while it download info from server """
                players_count = len(all_players)  # Refresh count of number of players again
                display.message([Lang.translate('getting-info-from-server')], 0, None, 'middle')
                try:
                    choosed_game = __import__("games.classic.{}".format(Game.replace(' ', '_')), fromlist=["games"])
                except:
                    try:
                        choosed_game = __import__("games.fun.{}".format(Game.replace(' ', '_')), fromlist=["games"])
                    except:
                        choosed_game = __import__("games.sport.{}".format(Game.replace(' ', '_')), fromlist=["games"])
                game_options, nb_sets = net_client.get_options()
                display.game_options = game_options
                display.selected_game = Game.replace(' ', '_')
                logs.log("DEBUG", "Starting a network game of {} (with options {} with {} players : {}".format(Game.replace(' ', '_'), game_options, players_count, all_players))
                menu = True

            if net_status == "YOUAREMASTER" and menu == 'net4':
                """ players are ready - game will be launch so we can delete game from master server """
                players_count = len(all_players)  # Refresh count of number of players again
                menu = True
                try:
                    NetMasterClient.connect_master(servername, masterserverport)
                    NetMasterClient.launch_game(netgamename)
                    NetMasterClient.close_connection()
                except Exception as e:
                    logs.log("WARNING", f"Unable to reach Master Server {servername} on port {masterserverport} in order to remove game")

        """ END OF MENU LOOP """
        if game_type not in ('restart' ,'quit' ,'shutdown'):
            if stats_screen != 'startagain' or not config_globals['keeporder']:
                if stats_screen == 'startagain':
                    old_players = players[:]

                # Now create players objects
                players = []
                nbcol = int(Config.get_value('SectionGlobals','nbcol'))

                for ident in range(0, players_count):
                    # Get Player color
                    #if light_strip:
                    player_color = display.colorset[f'player{ident + 1}']
                    #else:
                    #    player_color = list(display.colorset.values())[ident]
                    # Create Player object
                    try:
                        players.append(choosed_game.CPlayerExtended(ident, nbcol, interior=Config.get_value('SectionAdvanced','interior')))
                    except:
                        players.append(choosed_game.CPlayerExtended(ident, nbcol))

                    players[ident].init_color(player_color)
                    players[ident].name = all_players[ident]

                    if all_players[ident].find("]") != -1:
                        players[ident].computer = True
                        if all_players[ident].find('[NoOb]') != -1:
                            players[ident].level = 1
                            players[ident].name = players[ident].name.replace('[NoOb]','')
                        elif all_players[ident].find('[BegiN]') != -1:
                            players[ident].level = 2
                            players[ident].name = players[ident].name.replace('[BegiN]','')
                        elif all_players[ident].find('[InTeR]') != -1:
                            players[ident].level = 3
                            players[ident].name = players[ident].name.replace('[InTeR]','')
                        elif all_players[ident].find('[PrO]') != -1:
                            players[ident].level = 4
                            players[ident].name = players[ident].name.replace('[PrO]','')
                        else:
                            players[ident].level = 5
                            players[ident].name = players[ident].name.replace('[ExperT]','')

                if stats_screen == 'startagain':
                    for ident in range(0, players_count):
                        for other in range(0, players_count):
                            if players[ident].name == old_players[other].name:
                                players[ident].level = old_players[other].level
                                if players[ident].level > 0:
                                    players[ident].computer = True
                                continue
                    del old_players

            stats_screen = False

            ################
            # MATCH Loop
            ################

            # Match loop ends if match_done is true
            match_done = False
            set_done = False
            set_winner = None
            Set = 0
            Sets = []
            # StartTime / EndTime / winner
            Sets.append([Set + 1, datetime.datetime.now(), None, -1, 0, 0])
            interrupted = False
            # Round init
            actual_round = 1
            # Player Launch Init
            player_launch = 1
            # Actual Player Init
            actual_player = 0
            # Create Game objects and init var
            display.teaming = False
            game = choosed_game.Game(display, Game.replace(' ', '_'), players_count, game_options, Config, logs, rpi, dmd, video_player)
            game_is_ok_for_color = game.game_is_ok_for_color #by Manu script.
            for ident in range(0, players_count):
                if display.teaming and ident >= int(players_count / 2):
                    players[ident].init_color(players[ident - int(players_count / 2)].color)
                else:
                    players[ident].init_color(display.colorset[f'player{ident + 1}'])

            try:
                game_theme = game_options['theme']
                if game_theme != 'default':
                    display.file_class.reset_theme(game_theme)
                    display.init_colorset()
            except:
                logs.log("ERROR", f"No personnalisable theme for {game}")
            display.define_constants(players_count, Font=config_globals['font'])

            game.dispatcher = dispatcher
            try:
                light_segment = game.light_segment
            except:
                light_segment = True
            try:
                if game_type in ('netjoin', 'netcreate'):
                    display.game_type = 'online'
                else:
                    display.game_type = 'local'
            except:
                pass
            # Dart Stroke Init
            dart_stroke = None
            # Increment the number of Match done
            match_qty += 1
            # Backup of the Hit for a usage in following round
            prev_dart_stroke = None
            back_count = 0
            # Used to store Cheats
            magickey = ""
            handler = game.init_handler()

            # Run handicap
            try:
                game.check_handicap(players)
            except Exception as exception:
                logs.log("ERROR", f"Handicap failed : {exception}")

            # Store game properties in local DB
            data = {'game_options': ""}
            for opts in game_options:
                data['game_options'] += f"{opts}={game_options[opts]}|"
            data['game_name'] = Game.replace(' ', '_')
            data['nb_players'] = players_count
            game_id = scores.add_game(data)
            logs.log("DEBUG", f"Local game id is : {game_id}")
            # Reinit leds
            dispatcher.publish('newgame', limit=['TARGET', 'STRIP', 'OTHER'])
            rpi.target_leds = ''
            rpi.target_leds_blink = ''
            logs.log("DEBUG", "###### NEW GAME #########")
            # Disable videos during online game
            if net_status in ('YOUARESLAVE', 'YOUAREMASTER') or competition_mode:
                video_player.set_level(0)
            else:
                game.play_intro()

        else:
            match_done = True
            set_done = True

        # Main loop (every input runs a loop - a dart, a button or a click)
        while not match_done:
            while not set_done:
                post_round_handler = game.init_handler()
                rpi.light_buttons(['LIGHT_NAVIGATE', 'LIGHT_VALIDATE', 'LIGHT_PLAYERS'], False)
                rpi.light_buttons(['LIGHT_NEXTPLAYER'])

                if player_launch == 1 :
                    rpi.light_buttons(['LIGHT_BACK'], False)
                else:
                    rpi.light_buttons(['LIGHT_BACK'], True)

                if players[actual_player].computer:
                    rpi.light_buttons(['LIGHT_LASER'], False)
                else:
                    rpi.light_buttons(['LIGHT_LIGHT'])
                    rpi.light_buttons(['LIGHT_LASER'])

                ##############
                # Step 1 : The player plays
                ##############
                pre_dart = -1
                post_dart = -1
                post_round = -2
                early_player_button = -1
                missed_dart = -1

                # Display debug every round
                logs.log("DEBUG", "###### NEW ROUND #########")
                logs.log("DEBUG",
                         f"Game Round {actual_round}. Round of player {players[actual_player].name}.\
                                 Dart {player_launch}.")

                # Backup round
                try :
                    game.backup_round(players, player_launch)
                except:
                    logs.log("ERROR", "Cannot backup round")
                    pass

                # Pre Play Checks
                if net_status == 'YOUARESLAVE':
                    try:
                        randomval = net_client.get_random(actual_round, actual_player, player_launch)
                        game.set_random(players, actual_round, actual_player, player_launch, randomval)
                    except Exception as exception:
                        logs.log("ERROR", f"Problem getting and setting random value from master client : {exception}")
                        # On eteint la cible si besoin
                        dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

                ##############
                # pre_dart - Is a game method that prepares game before each dart
                ##############
                pre_dart = game.pre_dart_check(players, actual_round, actual_player, player_launch)

                if player_launch == 1 and len(magickey) == 0 and pre_dart != 4:
                    dmd.send_text(players[actual_player].name)
                    logs.log("DEBUG", f"Display {players[actual_player].name}")
                    if handler['announcement'] is None:
                        display.message([players[actual_player].name], 0, None, 'middle', 'big')
                    # Play sound for first dart (playername otherwise default)
                    display.sound_start_round(players[actual_player].name, play_firstname=play_firstname)

                ##############
                #
                if net_status == 'YOUAREMASTER':
                    try:
                        randomval = game.get_random(players, actual_round, actual_player, player_launch)
                        net_client.send_random(randomval, actual_round, actual_player, player_launch)
                    except Exception as exception:
                        logs.log("ERROR", f"Problem sending random value to slave clients : {exception}")
                        # On eteint la cible si besoin
                        dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

                # If the player is allowed to play
                if pre_dart != 4 and player_launch <= game.nb_darts:

                    try :
                        # For Simon game
                        logs.log("DEBUG", "POSTPRE")
                        for element in game.post_pre_dart_check(players, actual_round, actual_player, player_launch):
                            logs.log("DEBUG", f"POSTPRE : {element}")
                            if element == 'PRESSURE':
                                dispatcher.publish('pressure', limit=['TARGET', 'STRIP', 'OTHER'])
                            if element == 'NOPRESSURE':
                                dispatcher.publish('nopressure', limit=['TARGET', 'STRIP', 'OTHER'])

                    except:
                        pass

                    # Display board
                    ClickZones = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                                        game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                        Set=Set, MaxSet=nb_sets
                                        )

                    # On illumine si besoin
                    if light_target and game_is_ok_for_color: #by Manu script.
                        dispatcher.publish('Background', limit=['TARGET', 'STRIP', 'OTHER'])
                    if illumination_mode: #by Manu script.
                        dispatcher.publish('special', f'STRIP:Light, 0.3,{illumination_color}', limit=['TARGET', 'STRIP', 'OTHER']) #by Manu script.
                    elif light_strip:
                        dispatcher.publish('special', f'STRIP:Light, 0.3,{players[actual_player].color}', limit=['TARGET', 'STRIP', 'OTHER'])

                    if rpi.target_leds != '':
                        dispatcher.publish('goal', rpi.target_leds, limit=['TARGET', 'STRIP', 'OTHER'])
                    if rpi.target_leds_blink != '':
                        dispatcher.publish('blink', rpi.target_leds_blink, limit=['TARGET', 'STRIP', 'OTHER'])

                    # The player plays !
                    if net_status is None or players[actual_player].name in local_players:
                        # If its a local game or our turn to play in a net game : We read inputs.

                        while True:

                            if dart_stroke is not None and isinstance(dart_stroke, str):
                                # Backup this dart_stroke for next round
                                prev_dart_stroke = dart_stroke.upper()
                            else:
                                prev_dart_stroke = dart_stroke

                            # If there is cheating in progress
                            if len(magickey) > 0:
                                ktype = ['num', 'alpha']
                            else:
                                ktype = []

                            ##### INPUT #######
                            if players[actual_player].computer:
                                # PNJ
                                dart_stroke = rpi.listen_inputs(ktype,
                                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISSDART',
                                      'VOLUME-UP', 'VOLUME-DOWN', 'VOLUME-MUTE', 'enter', 'single-click', 'escape', 'space'],
                                      context='game', timeout=pnj_time)
                                if dart_stroke is False :    # Time out reached : PNJ has to play
                                    PnJ = game.pnj_score(players, actual_player, players[actual_player].level, player_launch)
                                    if PnJ == 'PNE' or PnJ == 'TB' :    # Simplier to treate TB here than on each game, considered as MISSDART
                                        dart_stroke = 'MISSDART'
                                    else:
                                        dart_stroke = PnJ
                            elif game.time > 0:
                                dart_stroke = rpi.listen_inputs(ktype,
                                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISSDART',
                                      'VOLUME-UP', 'VOLUME-DOWN', 'VOLUME-MUTE', 'enter', 'single-click', 'escape', 'space', 'special'],
                                      context='game', timeout=game.time)

                                if dart_stroke is False:
                                    logs.log("DEBUG", f"Timeout {game.time}")
                                    pre_dart = game.pre_dart_check(players, actual_round, actual_player, player_launch)
                                    ClickZones = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                                                game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                                Set=Set, MaxSet=nb_sets)
                                    if light_target and game_is_ok_for_color: #by Manu script.
                                        dispatcher.publish('Background', limit=['TARGET', 'STRIP', 'OTHER'])
                                    else:
                                        dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

                                    if rpi.target_leds != '':
                                        dispatcher.publish('goal', rpi.target_leds, limit=['TARGET', 'STRIP', 'OTHER'])
                                    if rpi.target_leds_blink != '':
                                        dispatcher.publish('blink', rpi.target_leds_blink, limit=['TARGET', 'STRIP', 'OTHER'])

                                    continue
                            else:
                                # Human
                                dart_stroke = rpi.listen_inputs(ktype,
                                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISSDART',
                                      'VOLUME-UP', 'VOLUME-DOWN', 'VOLUME-MUTE', 'enter', 'single-click', 'escape', 'space', 'special'],
                                      context='game',
                                      events=[(wait_event_time, 'LIGHT', ['LIGHT_NEXTPLAYER']), \
                                              (wait_event_time * 2, 'SOUND', 'snoring'), \
                                              (wait_event_time * 2, 'DMD', 'insults')],
                                      firstname=players[actual_player].name)

                                # Unexpected button pressed
                                if dart_stroke in ('BTN_LEFT', 'BTN_RIGHT', 'BTN_UP', 'BTN_DOWN', 'BTN_CPTPLAYER', 'BTN_DEMOLED'):
                                    rpi.strobe_buttons(['LIGHT_NAVIGATE', 'LIGHT_VALIDATE'], iterations=2)
                                    continue
                                if dart_stroke == 'BTN_VALIDATE':
                                    dart_stroke = 'MISSDART'

                            ##### INPUT #######

                            # Check Mouse input first
                            if ClickZones:
                                Clicked = display.is_clicked(ClickZones[0], dart_stroke)
                                if Clicked:
                                    dart_stroke = Clicked

                            # If at this stage dart_stroke is still a tuple, we loop again (clicked on screen)
                            if isinstance(dart_stroke, tuple):
                                logs.log("DEBUG", "Stop clicking nowhere !")
                                continue

                            # Backup turn on first round => NO !!
                            #if dart_stroke in ['BTN_BACK', 'BACKUPBUTTON'] and actual_player == 0 and actual_round == 1 and player_launch == 1:
                            #    logs.log("WARNING", "Backup Turn is disabled on first round of first player ! Naughty you !")
                            #    continue

                            # Toggle full-screen or resize
                            elif dart_stroke in ['TOGGLEFULLSCREEN', 'resize']:
                                if dart_stroke == 'TOGGLEFULLSCREEN':
                                    display.create_screen(True, Font=config_globals['font'])
                                else:
                                    display.create_screen(False, rpi.newresolution)
                                ClickZones = game.refresh_game_screen(players, actual_round, game.max_round,
                                                game.nb_darts - player_launch + 1, game.nb_darts,
                                                game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                                Set=Set, MaxSet=nb_sets)

                            # Adjust volume
                            elif dart_stroke in ['BTN_PLUS', 'VOLUME-UP', 'VOLUME-MUTE', 'BTN_VOLUME_UP', 'BTN_MINUS', 'VOLUME-DOWN', 'BTN_VOLUME_DOWN', 'BTN_VOLUME_MUTE']:
                                display.adjust_volume(dart_stroke)

                            # If you hit on keyboard a value, like T20, it is stored in a variable "magickey".
                            # This is great for debugging pyDarts. Or cheating !
                            elif dart_stroke == 'CHEAT':
                                magickey = 'MAGIC!'
                            elif magickey == 'MAGIC!' and dart_stroke in ['S', 'D', 'T', 'R', 's', 'd', 't', 'r' ]:
                                magickey = str(dart_stroke)
                            # Try to override backup button when trying to press a bullseye
                            elif magickey and magickey != 'MAGIC!' and dart_stroke in ['BTN_BACK', 'BACKUPBUTTON', 'BTN_CANCEL']:
                                magickey += 'B'
                            elif magickey and magickey != 'MAGIC!' and str(dart_stroke) in ['b', 'B', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                                magickey += str(dart_stroke)
                            else:
                                # S18, D20... BTN_*
                                break

                        # If magickey is set and you hit enter - it's validated - similar to JOKER but without random
                        if dart_stroke == 'enter' and len(magickey) > 0:
                            # If you hit R21, it jump directly to round 21, for instance
                            if magickey[:1] in ['r', 'R']:
                                actual_round = int(magickey[1:])
                                logs.log("DEBUG", f"Jumping to round : {actual_round}")
                                magickey = ''
                                continue
                            # Otherwise we keep what you pressed as a valid hit (cheating)
                            dart_stroke = magickey.upper()
                            logs.log("DEBUG", f"Not fair to cheat nasty boy ! Get this : {dart_stroke}")
                            magickey = ''

                        # Rewrite by a random hit (when pressing 'r' Joker key)
                        if dart_stroke == 'JOKER':
                            # Transfer ConfigKeys to new list
                            RandList = list(ConfigKeys)
                            # remove buttons from list to prevent missing dart, going back a turn,
                            # skipping a turn or closing game (pop with None arg remove only if exists)
                            if 'playerbutton' in RandList:RandList.remove('playerbutton')
                            if 'gamebutton' in RandList:RandList.remove('gamebutton')
                            if 'backupbutton' in RandList:RandList.remove('backupbutton')
                            if 'extrabutton' in RandList:RandList.remove('extrabutton')
                            # Try to choose random value from ConfigKeys
                            try:
                                dart_stroke = random.choice(list(RandList)).upper()
                                logs.log("DEBUG", f"Looking up for a random hit... Lucky guy ! {dart_stroke}")
                            except Exception as e:
                                dart_stroke = 'S20'
                                logs.log("WARNING", f"Unable to get a random hit. Your board is probably not calibrated ! I give you a {dart_stroke}.")
                                logs.log("DEBUG", f"Looking up for a random hit... Lucky guy ! {dart_stroke}")

                        # What did we play ?
                        logs.log("DEBUG", f"Input restrained is : {dart_stroke}")

                        # Send dart_stroke to server if player has played
                        if net_status is not None:
                            ret = net_client.play(actual_round, actual_player, player_launch, dart_stroke)
                            if ret is not None:
                                dart_stroke = 'TIMEOUT'

                    else:
                        # Else its a net game and it's our turn to wait from network !
                        logs.log("DEBUG", "Waiting for remote player (Player {} and Round {})...".format(actual_player, actual_round))
                        dart_stroke = str(net_client.wait_someone_play(actual_round, actual_player, player_launch))
                        while dart_stroke is False:
                            sleep(0.2)
                            dart_stroke = net_client.wait_someone_play(actual_round, actual_player, player_launch)

                        if dart_stroke == 'FINALPLAYERBUTTON':
                            dart_stroke = 'PLAYERBUTTON'
                        elif light_segment:
                            dispatcher.publish('stroke', dart_stroke.upper(), limit=['TARGET', 'STRIP', 'OTHER'])

                    if dart_stroke in ['BTN_BACK', 'BACKUPBUTTON'] and back_count < 3:
                        # Simulate BTN_CANCEL or BTN_GAMEBUTTON
                        # 2 x BTN_BACK = BTN_CANCEL
                        # 3 x BTN_BACK = BTN_GAMEBUTTON
                        if actual_round == 1 and actual_player == 0 and player_launch == 1:
                            back_count = 3
                        else:
                            back_count += 1
                        dart_stroke = f"BTN_BACK{back_count}"

                    # GAMEBUTTON button pressed : game interrupted
                    if dart_stroke in ['escape', 'GAMEBUTTON', 'BTN_GAMEBUTTON', 'BTN_BACK3', 'BTN_CANCEL2', 'TIMEOUT']:
                        if dart_stroke == 'TIMEOUT':
                            logs.log("DEBUG", f"Timeout from player {actual_player}")
                            # Dispacth messages
                            dispatcher.publish('timeout', limit=['TARGET', 'STRIP', 'OTHER'])
                            dmd.send_text(Lang.translate('timeout'))

                            display.message([Lang.translate('timeout')], None, 'menu-ko', 'middle', 'big')
                        else:
                            logs.log("DEBUG", "Who has pushed the Game Button ?")

                            # Dispacth messages
                            dispatcher.publish('interrupt', limit=['TARGET', 'STRIP', 'OTHER'])
                            dmd.send_text(Lang.translate('Game interrupted'))

                            display.message([Lang.translate('Game interrupted')], None, 'menu-white', 'middle', 'big', bg_color='menu-warning')

                        # Terminate match
                        match_done = True
                        set_done = True
                        interrupted = True
                        last_game_screen = None
                        continue

                    # CANCEL button ppressed : back to 1st dart of same player
                    if dart_stroke in ['BTN_CANCEL', 'BTN_BACK2']:
                        logs.log("DEBUG", "Who has pushed the Cancel Button ?")

                        # Dispacth messages
                        dispatcher.publish('round_cancel', limit=['TARGET', 'STRIP', 'OTHER'])
                        dmd.send_text(Lang.translate('Backup Turn !'))
                        display.message([Lang.translate('Backup Turn !')], None, None, 'middle', 'big')

                        try :
                            RestoreSession = game.restore_round(1)
                        except:
                            RestoreSession = None

                        if RestoreSession is not None:
                            players = deepcopy(RestoreSession)
                            game.refresh_stats(players, actual_round)

                        player_launch = 1
                        continue

                    # BACK button ppressed : back to previous dart
                    if dart_stroke in ['BTN_BACK1']:
                        logs.log("DEBUG", "Who has pushed the Back Button ?")
                        # Impossible cases
                        if player_launch == 1 and actual_round == 1 and actual_player == 0:
                            pass

                        try:
                            RestoreSession = game.restore_round(1 + (player_launch + 1) % 3)
                            if RestoreSession is not None:
                                players = deepcopy(RestoreSession)
                                game.refresh_stats(players, actual_round)

                                # Dispacth messages
                                dispatcher.publish('bounce_out', limit=['TARGET', 'STRIP', 'OTHER'])
                                dmd.send_text(Lang.translate('Bounce out !'))
                                display.message([Lang.translate('Bounce out !')], None, None, 'middle', 'big')

                                logs.log("DEBUG", "restore_round {}, player_launch={}, actual_player={}, actual_round={}".format(1 + (actual_round + 1) % 3,player_launch,actual_player,actual_round))
                                if player_launch == 1:
                                    # Back to last round of previous player
                                    player_launch = 3
                                    if actual_player == 0:
                                        # Back to previous round
                                        actual_round -= 1
                                        actual_player = players_count - 1
                                    else:
                                        actual_player -= 1
                                else :
                                    player_launch -= 1

                                del RestoreSession
                        except:
                            dmd.send_text(Lang.translate('Not available !'))
                            display.message([Lang.translate('Not available !')], None, None, 'middle', 'big')
                            logs.log("ERROR", "restore_round unavailable for this game !")
                        continue

                    # INFO : From here the dart_stroke should be something included in config file keys, or it loop again.
                    # Print error and loop again if key has not been found in config file
                    if dart_stroke not in ConfigKeys and dart_stroke not in ('MISSDART', 'PLAYERBUTTONFIRST', 'PLAYERBUTTON', 'BTN_NEXTPLAYER'):
                        logs.log("ERROR", f"Key \"{dart_stroke}\" must exists in your local config file and it has not been found. We recommand you to calibrate your board again.")
                        logs.log("DEBUG", "Jumping back to start of the loop.")
                        continue

                    # EARLY PLAYERBUTTON PRESSED
                    if dart_stroke in ['BTN_NEXTPLAYER', 'PLAYERBUTTON'] and player_launch <= game.nb_darts:
                        logs.log("DEBUG", "You pushed Playerbutton early... Hum !")
                        try:
                            early_player_button = game.early_player_button(players, actual_player, actual_round)
                        except Exception as error:
                            logs.log("ERROR", f"EARLYPLAYERBUTTON is not handled properly by this game. Error was {error}")
                            early_player_button = 1

                        for i in range(0, game.nb_darts - player_launch):
                            try :
                                game.backup_round(players, player_launch)
                            except:
                                pass

                        if early_player_button != 0 and post_dart != 3:
                            if releasedartstime == 0:
                                dart_stroke = 'PLAYERBUTTONFIRST'
                                dart_stroke = 'PLAYERBUTTON'

                    # Other button than BACKUP : reinit counter
                    back_count = 0

                    # Post Darts Checks
                    if dart_stroke in ConfigKeys:
                        logs.log("DEBUG", f"You pushed {dart_stroke}")
                        if light_segment:
                            dispatcher.publish('stroke', dart_stroke.upper(), limit=['TARGET', 'STRIP', 'OTHER'])

                        players[actual_player].add_histo(dart_stroke)
                        # POST DART CHECKS
                        #
                        # Return codes are:
                        #  1 - Jump to next player immediately
                        #  2 - Game is over
                        #  3 - There is a winner (self.winner must hold winner id)
                        #  4 - The player is not allowed to play (jump to next player)
                        logs.log("DEBUG", f"Key {dart_stroke} found in config file.")
                        #handler = {'return_code': 0, 'message': None, 'show': None, 'sound': None, 'lights': None, 'strobe': None, 'speech': None, 'speech_speed': None}
                        handler = game.post_dart_check(dart_stroke, players, actual_round, actual_player, player_launch)
                        logs.log("DEBUG", f"handler received : {handler}")

                        if not hasattr(game, "refresh_game_screen"):
                            display.refresh_scores(players, actual_player, refresh=True)

                        if type(handler) is int:
                            post_dart = handler
                            handler = game.init_handler()
                            handler['post_dart'] = post_dart
                        else:
                            post_dart = handler['return_code']

                        played_sound = None

                        if game.display_dmd():
                            if handler['dmd'] is not None:
                                logs.log("DEBUG", f"Send dmd : {handler['dmd']}")
                                dmd.send_text(handler['dmd'])
                            else:
                                logs.log("DEBUG", f"Send dmd : {player_launch},{dart_stroke}")
                                dmd.send_score(player_launch, dart_stroke)

                        if handler['strobe'] is not None or handler['light'] is not None or (post_dart in [0, 1, 2] and dart_stroke in ('SB', 'DB')):
                            # Turn OFF light to appreciate other celebrations
                            rpi.light_buttons(['LIGHT_LIGHT'], state=False)

                        if handler['strobe'] is not None:
                            logs.log("DEBUG", f"strobe_buttons({handler['strobe'][0]}, {handler['strobe'][1]}, {handler['strobe'][2]})")
                            rpi.strobe_buttons(handler['strobe'][0], handler['strobe'][1], handler['strobe'][2])
                        else:
                            # Default
                            if post_dart in [0, 1, 2] and dart_stroke == 'SB':
                                logs.log("DEBUG", f"rpi.strobe_buttons(['LIGHT_FLASH'])")
                                rpi.strobe_buttons(['LIGHT_FLASH'], iterations=3, delay=50)

                            if post_dart in [0, 1, 2] and dart_stroke == 'DB':
                                logs.log("DEBUG", f"rpi.light_buttons(['LIGHT_CELEBRATION']")
                                rpi.light_buttons(['LIGHT_CELEBRATION'], delay=int(config_advanced['db-celebration-delay']))

                        if handler['light'] is not None:
                            logs.log("DEBUG", f"rpi.light_buttons({handler['light'][0]}, {handler['light'][1]})")
                            rpi.light_buttons(handler['light'][0], handler['light'][1])
                        else:
                            #default
                            if post_dart in [0, 1, 2] and dart_stroke == 'DB':
                                rpi.strobe_buttons(['LIGHT_FLASH'], iterations=5)

                        if handler['video'] is not None and not competition_mode:
                            logs.log("DEBUG", f"video_player.play_video({handler['video']}")
                            video_player.play_video(File.get_full_filename(handler['video'], 'videos'), wait=True)

                        elif handler['show'] is not None and not competition_mode:
                            logs.log("DEBUG", f"video_player.play_show({handler['show'][0]}, {handler['show'][1]}, {handler['show'][2]})")
                            if not video_player.play_show(handler['show'][0], handler['show'][1], handler['show'][2]):
                                if handler['sound'] is not None:
                                    played_sound = display.play_sound(handler['sound'])
                        else:
                            if handler['message'] is not None and len(handler['message']) > 0:
                                display.message([handler['message']], 0, None, 'middle', 'big')

                            if handler['sound'] is not None:
                                logs.log("DEBUG", f"display.play_sound({handler['sound']})")
                                played_sound = display.play_sound(handler['sound'])
                            elif handler['speech'] is not None:
                                logs.log("DEBUG", f"speech {handler['speech']} ({handler['speech_speed']})")
                                if handler['speech_speed'] is not None:
                                    display.speech(handler['speech'], speed=handler['speech_speed'])
                                else:
                                    display.speech(handler['speech'])

                        if post_dart != 1:
                            rpi.strobe_buttons(['LIGHT_NEXTPLAYER', 'LIGHT_NAVIGATE', 'LIGHT_VALIDATE', 'LIGHT_BACK'])
                            # Winner
                            # Display score in differents ways depending on options
                            if hasattr(game, "display_hit") and callable(game.display_hit):
                                game.display_hit(ClickZones, players, actual_player, player_launch, dart_stroke)
                            else:
                                if player_launch == game.nb_darts:
                                    ClickZones = game.refresh_game_screen(players, actual_round, game.max_round,
                                                game.nb_darts - player_launch, game.nb_darts, game.logo,
                                                game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                                Set=Set, MaxSet=nb_sets)

                                # Useless if winner or not wanted for the game
                                if print_dartstroke and game.display_segment() and post_dart < 3:
                                    if os.path.isfile('{}/{}'.format(Config.dartsStrokeDir, dart_stroke)):
                                        display.message(' ', None, None, 'middle', 'huge', f'valeurs/{dart_stroke}.png')
                                    else:
                                        display.message([dart_stroke], None, None, 'middle', 'huge')

                    # MISSDART BUTTON PRESSED
                    # early_player_button for Golf
                    elif early_player_button != 4:
                        logs.log("DEBUG", f"Missed that dart : {early_player_button}!")
                        # Show message on Raspydarts dmd
                        dmd.send_text(Lang.translate('Missed !'))

                        try:
                            missed_dart = game.miss_button(players, actual_player, actual_round, player_launch)
                            if hasattr(game, "display_hit") and callable(game.display_hit):
                                game.display_hit(ClickZones, players, actual_player, player_launch, 'MISSDART')

                            if early_player_button > 0 and post_dart != 3:
                                for i in range(1, game.nb_darts - player_launch + 1):
                                    game.miss_button(players, actual_player, actual_round, player_launch + i)
                                    if hasattr(game, "display_hit") and callable(game.display_hit):
                                        game.display_hit(ClickZones, players, actual_player, player_launch, 'MISSDART')
                                player_launch = game.nb_darts
                        except Exception as e:
                            logs.log("ERROR", "MISSDART is not handled properly by this game. Error was {}".format(e))
                            # Show message on screen
                            display.message([Lang.translate('Missed !')], None, None, 'middle', 'big')
                    else:
                        # Go to next_player
                        player_launch = game.nb_darts

                    # DISPLAY RELEASE DARTS IF SOLO ENABLED
                    if  (releasedartstime > 0
                            and (player_launch == game.nb_darts or (dart_stroke in ('BTN_NEXTPLAYER', 'PLAYERBUTTON') and player_launch < game.nb_darts))
                            and post_dart not in (2,3)):
                        rpi.light_buttons(['LIGHT_LASER'], False)
                        dispatcher.publish('release', limit=['TARGET', 'STRIP', 'OTHER'])
                        if releasedartstime > 0:
                            dmd.send_text(Lang.translate("release-darts"))
                            display.message([Lang.translate('release-darts')], releasedartstime, None, 'middle', 'big')

                    """
                    Need a bit of clarification
                    """
                    # WAIT For Player Button... (MISSDART AND PLAYERBUTTON are voluntarily absent of this list)
                    if (
                          (net_status is None or players[actual_player].name in local_players)
                          and releasedartstime == 0
                          and (player_launch == game.nb_darts or post_dart == 1 or early_player_button == 1)
                          and post_dart != 2
                          and post_dart != 3
                          or dart_stroke == 'PLAYERBUTTONFIRST'
                       ):
                        dart_stroke = 'PLAYERBUTTONFIRST'
                        rpi.light_buttons(['LIGHT_NEXTPLAYER', 'LIGHT_BACK'], False)
                        ClickZones = game.refresh_game_screen(players, actual_round, game.max_round, 0, game.nb_darts, game.logo, game.headers,
                                    actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                    Set=Set, MaxSet=nb_sets)

                        if net_status is None:
                            display.press_player(Lang.translate('release-darts-and-press-player'))
                            dispatcher.publish('release', limit=['TARGET', 'STRIP', 'OTHER'])
                        rpi.light_buttons(['LIGHT_LASER'], False)

                        # Game context, wait for PLAYERBUTTON only...
                        while dart_stroke not in ('PLAYERBUTTON', 'BTN_NEXTPLAYER', 'BTN_VALIDATE') and net_status is None:
                            logs.log("DEBUG", "Waiting for player to push PLAYERBUTTON...")
                            if players[actual_player].computer:
                                logs.log("DEBUG", "Player is computer...")
                                dart_stroke = rpi.listen_inputs(['num', 'alpha', 'fx', 'arrows'],
                                            ['escape', 'GAMEBUTTON', 'PLAYERBUTTON', 'single-click'],
                                                context='game',
                                                timeout=pnj_time
                                            )
                                if dart_stroke is False:
                                    dart_stroke = 'PLAYERBUTTON'
                            else:
                                dart_stroke = rpi.listen_inputs(['num', 'alpha', 'fx', 'arrows'],
                                            ['PLAYERBUTTON', 'single-click'],
                                            context='game',
                                            events=[(350, 'STROBE', ['LIGHT_NEXTPLAYER']), (wait_event_time, 'EVENT', 'wait'), (wait_event_time * 2, 'SOUND', 'snoring')])

                            logs.log("DEBUG", f'dart_stroke = {dart_stroke}')
                            logs.log("DEBUG", f'ClickZones = {ClickZones}')
                            if ClickZones is not None:
                                Clicked = display.is_clicked(ClickZones[0], dart_stroke)
                                if Clicked:
                                    dart_stroke = Clicked

                            # L'utilisateur demande la fin de la partie sur le joueur ordinateur
                            if dart_stroke in ('BTN_GAMEBUTTON', 'GAMEBUTTON', 'BTN_CANCEL', 'TIMEOUT'):
                                break

                        if net_status is not None:
                            if net_client.play(actual_round, actual_player, player_launch, 'FINALPLAYERBUTTON') == 'TIMEOUT':
                                break

                    # OR Wait that the REMOTE player has pushed PLAYERBUTTON (Net game only) (MISSDART AND PLAYERBUTTON are voluntarily absent of this list)
                    elif (
                             net_status is not None
                             and players[actual_player].name not in local_players
                             and releasedartstime == 0
                             and (player_launch == game.nb_darts or post_dart == 1 or early_player_button == 1)
                             and post_dart != 2
                             and post_dart != 3
                             or dart_stroke == 'PLAYERBUTTONFIRST'
                          ):
                        #game.refresh_game_screen(players, actual_round, game.max_round, 0, game.nb_darts, game.logo, game.headers,
                        #        actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                        #        Set=Set, MaxSet=nb_sets)
                        display.press_player(Lang.translate('press-player-remote'), 'menu-alternate')
                        # Else its a net game and it's our turn to wait from network !
                        logs.log("DEBUG", "Waiting for remote player to push the FINALPLAYERBUTTON...")
                        # Wait to receive PLAYERBUTTON
                        #net_client.wait_someone_play(actual_round, actual_player, player_launch, 'FINALPLAYERBUTTON')
                        # If received, rewrite to PLAYERBUTTON for client
                        dart_stroke = 'PLAYERBUTTON'

                else:
                    # If not allowed to play (pre_dart = 4)
                    # Force BACKUPBUTTON again (double BACKUPTURN) if someone pressed BackupButton and that the previous player is not allowed to play neither
                    if prev_dart_stroke in ['BTN_BACK', 'BACKUPBUTTON']:
                        dart_stroke = prev_dart_stroke
                    else:
                        dart_stroke = 'PLAYERBUTTON'

                dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])
                #
                # Step 2 : All the differents possibilities
                #

                logs.log("DEBUG", f"At this stage, post_dart returns {post_dart}, early_player_button is {early_player_button}, and missed_dart is {missed_dart}")
                logs.log("DEBUG", "Memo: 0: nothing special, 1: jump to next player,  2: game over, 3: victory, 4: current player not allowed to play")

                # Is there a winner after this round ?
                if actual_player + 1 >= players_count and (player_launch >= game.nb_darts or pre_dart == 4):
                    # post_round_check return id of winner
                    post_round_handler = game.post_round_check(players, actual_round, actual_player)
                    if type(post_round_handler) is int:
                        post_round = post_round_handler
                        post_round_handler = game.init_handler()
                        post_round_handler['post_round'] = post_round
                    else:
                        post_round = post_round_handler['return_code']

                # Victory
                if post_round >= 0:
                    # Set win
                    players[actual_player].sets += 1
                    set_winner = post_round
                    set_done = True
                    Sets[Set][3] = game.get_player_name(players, set_winner)
                    Sets[Set][5] = game.get_darts_thrown(players, set_winner)

                elif post_dart == 3 or early_player_button == 3 or missed_dart == 3:
                    # Set win
                    players[actual_player].sets += 1
                    set_winner = game.winner
                    logs.log("DEBUG", "Set won by {}".format(set_winner))
                    set_done = True
                    Sets[Set][3] = game.get_player_name(players, set_winner)
                    Sets[Set][5] = game.get_darts_thrown(players, set_winner)

                # Game Over
                elif post_dart == 2 or early_player_button == 2 or missed_dart == 2 or post_round == -1:
                    logs.log("DEBUG", "Last round reached. No winner ...")

                    # Dispacth messages
                    dispatcher.publish('gameover', limit=['TARGET', 'STRIP', 'OTHER'])
                    dmd.send_text(Lang.translate('last-round-reached'))

                    display.play_sound('whatamess')
                    display.message([Lang.translate('last-round-reached')], None, None, 'middle', 'big')

                    # Terminate match
                    set_done = True
                elif post_round_handler['announcement'] is not None:
                    dmd.send_text(post_round_handler['announcement'])
                    display.message([post_round_handler['announcement']], 0, None, 'middle', 'big')
                    display.speech(post_round_handler['announcement'], speed=post_round_handler['speech_speed'])

                if not match_done and not set_done:
                    # Next hit, please !
                    player_launch += 1

                    # Next Player ?
                    if player_launch > game.nb_darts or post_dart in (1, 4) or dart_stroke == 'PLAYERBUTTON':
                        if played_sound is not None:
                            logs.log("DEBUG", f"Waif for end of sound")
                            display.wait_end_sound(played_sound)

                        if not players[actual_player].computer:
                            rpi.light_buttons(['LIGHT_LASER'])
                        # dont show/play next player if a player is not allowed to play
                        if pre_dart != 4:
                            dispatcher.publish('nextplayer', players[actual_player].name, limit=['TARGET', 'STRIP', 'OTHER'])
                            if handler['announcement'] is not None:
                                logs.log("DEBUG", f"announcement {handler['announcement']} ({handler['speech_speed']})")
                                dmd.send_text(handler['announcement'])
                                display.message([handler['announcement']], 0, None, 'middle', 'big')
                                display.speech(handler['announcement'], speed=handler['speech_speed'])
                            else:
                                display.play_sound('next_player', wait_finish=wait_finish, duration=sound_duration)

                        actual_player += 1
                        player_launch = 1

                    # Next Round ? - Only jump to next round if there is no victory, no match end (give more accurate stats)
                    if actual_player >= players_count:
                        actual_player = 0
                        actual_round += 1

                elif not interrupted:
                    rpi.gpio_flush()
                else:
                    last_game_screen = None

            # Set Done
            rpi.light_buttons(['LIGHT_LASER'], False)
            i = 0
            Sets[Set][2] = datetime.datetime.now()
            Sets[Set][4] = actual_round

            if nb_sets == 1:
                match_done = True
            else:
                for player in players:
                    if player.sets == nb_sets:
                        match_done = True
                        game.winner = player.ident
                    i += 1

            if not interrupted:
                if set_winner is not None:
                    Sets[Set][5] = game.get_darts_thrown(players, set_winner)
                    logs.log("DEBUG", "Set {} won by {}".format(Set, game.get_player_name(players, set_winner)))

                if match_done or nb_sets == 1:
                    if set_winner is not None:
                        logs.log("DEBUG", "And the winner is...")
                        txtwinner = "{} : {}".format(Lang.translate('winner'), game.get_player_name(players, set_winner))

                        display.message([txtwinner], 0, None, 'middle', 'big', bg_color='menu-ok')
                        dmd.send_text(txtwinner)
                        dispatcher.publish('winner', limit=['TARGET', 'STRIP', 'OTHER'])
                        rpi.light_buttons(['LIGHT_CELEBRATION'], delay=int(config_advanced['victory-celebration-delay']))
                        if nb_sets > 1:
                            display.sound_end_game(game.get_player_name(players, set_winner),duration=sound_duration)
                        else:
                            display.sound_end_game(game.get_player_name(players, set_winner))
                    else:
                        logs.log("DEBUG", "No winner")
                        txtwinner = Lang.translate('nowinner')
                        dmd.send_text(txtwinner)
                        display.message([txtwinner], None, None, 'middle', 'big', bg_color='menu-warning')

                    if nb_sets > 1:
                        last_game_screen = display.display_sets(Sets, end_of_game=match_done)
                    else:
                        last_game_screen = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                                game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'], end_of_game=True)
                    logs.log("DEBUG", f"You choosed {last_game_screen} nb_sets={nb_sets}")
                    if last_game_screen == 'startagain':
                        stats_screen = 'startagain'
                    else:
                        if net_status in ('YOUARESLAVE', 'YOUAREMASTER') or competition_mode:
                            video_player.set_level(Config.get_value('SectionGlobals', 'videos'))

                else:
                    if set_winner is not None:
                        # Set won by ...set_winner
                        txtwinner = f"{Lang.translate('setwinneris')} {game.get_player_name(players, set_winner)}"
                        logs.log("DEBUG", f"txtwinner = {txtwinner}")
                        dispatcher.publish('setwinner', limit=['TARGET', 'STRIP', 'OTHER'])
                        dmd.send_text(txtwinner)
                        rpi.light_buttons(['LIGHT_CELEBRATION'], delay=int(config_advanced['set-celebration-delay']))
                        display.message([txtwinner], None, None, 'middle', 'big', bg_color='menu-ok')
                        display.speech(txtwinner)

                        last_game_screen = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                            game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'], endOfSet=[Sets, players[set_winner].name],
                            Set=Set, MaxSet=nb_sets)
                    else:
                        last_game_screen = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                            game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'], Set=Set, MaxSet=nb_sets)

                    logs.log("DEBUG", f"You choosed {last_game_screen} nb_sets={nb_sets}")

                    if net_status == 'YOUAREMASTER':
                        display.display_sets(Sets, end_of_game=match_done)
                    elif net_status == 'YOUARESLAVE':
                        display.display_sets(Sets, end_of_game=match_done, wait=False)
                    else:
                        display.display_sets(Sets, end_of_game=match_done)


                    set_done = False
                    set_winner = None
                    interrupted = False
                    # Round init
                    actual_round = 1
                    # Player Launch Init
                    player_launch = 1
                    # Actual Player Init
                    actual_player = 0
                    # Shutown leds
                    rpi.target_leds = ''
                    rpi.target_leds_blink = ''
                    # Dart Stroke Init
                    dart_stroke = None
                    # Increment the number of Match done
                    match_qty += 1
                    # Backup of the Hit for a usage in following round
                    prev_dart_stroke = None
                    # Increase set
                    Set += 1
                    Sets.append([Set + 1, datetime.datetime.now(), None, -1, 0, 0])

                    logs.log("DEBUG", "config_globals['keeporder']={}".format(config_globals['keeporder']))
                    if not config_globals['keeporder'] or net_status is not None:
                        try:
                            game.next_set_order(players)
                        except Exception as exception:
                            logs.log("ERROR", "Unable to order players from previous results. Error was {exception}")

                    for player in players:
                        player.new_set()
                    if net_status == 'YOUAREMASTER':
                        net_client.next_set(",".join([player.name for player in players]))
                    elif net_status == 'YOUARESLAVE':
                        all_players = net_client.wait_next_set(Set)

            else:
                if net_status in ('YOUARESLAVE', 'YOUAREMASTER') or competition_mode:
                    video_player.set_level(Config.get_value('SectionGlobals', 'videos'))

        display.file_class.reset_theme(Config.get_value('SectionGlobals', 'colorset'))
        display.init_colorset()
        display.define_constants(True, Font=config_globals['font'])
        display.reset_background()
        # Match Done
        if game_type not in ('restart', 'quit', 'shutdown'):
            ###############
            # MATCH IS OVER
            ###############

            # Quit if it was a network game
            logs.log("DEBUG", "This game is over")
            if net_status is not None:
                net_client.close_host()

            # On eteint la cible si besoin
            dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])
            rpi.gpio_flush()

            # Grab stats from the game and write them in local DB
            if last_game_screen == 'stats':
                rpi.light_buttons(['LIGHT_NEXTPLAYER', 'LIGHT_BACK'], False)
                rpi.light_buttons(['LIGHT_NAVIGATE'])

                for player in players :
                    try:
                        display.heat_map(player.name, player.get_histo())
                    except Exception as e:
                        logs.log("ERROR", "Problem displaying stats")
                try:
                    game.game_stats(players, actual_round, scores)
                except Exception as e:
                    logs.log("ERROR", "Problem inserting stats")

                try:
                    first = True
                    for record in game.game_records:
                        # Get Stats for this game only
                        stats_data = scores.get_score_table(record, game.game_records[record], True)
                        # Display stats for this game
                        stats_screen = display.display_records(stats_data, record, scores.game_name, scores.game_options, True)
                        # Quit menu
                        if stats_screen in ('startagain', 'menu'):
                            break
                        # Get Stats for this type of game (with same options)
                        stats_data = scores.get_score_table(record, game.game_records[record])
                        # Display stats for this kind of game
                        stats_screen = display.display_records(stats_data, record, scores.game_name, scores.game_options)
                        # Quit menu
                        if stats_screen in ('startagain', 'menu'):
                            break
                except Exception as exception:
                    stats_screen = 'escape'
                    logs.log("ERROR", f"Problem displaying Stats table with screen.")
                    logs.log("ERROR", f"DisplayRecords method : {exception}")

            # Exiting if it was direct_play mode and that the user pressed escape
            if stats_screen == 'escape' and direct_play:
                logs.log("DEBUG", "Exiting game because of \"direct_play\" mode enabled. Bye !")
                sys.exit(0)

finally:
    # Quit or restart
    if dispatcher.target_leds and p_target.poll() is not None:
        dispatcher.target_leds = False

    if dispatcher.strip_leds and p_strip.poll() is not None:
        dispatcher.strip_leds = False

    rpi.light_buttons(['LIGHT_NEXTPLAYER', 'LIGHT_BACK', 'LIGHT_CELEBRATION', 'LIGHT_NAVIGATE'], \
            False)

    display.message(["Shutting down servers"], wait=0, refresh=True)

    logs.log("DEBUG", "Sending quit signal to external servers")
    if game_type == 'shutdown':
        # Volontary exit : play leds animation
        dispatcher.publish('quit', ack=True, limit=['TARGET', 'STRIP', 'DMD', 'OTHER'])
        sleep(1)

    #if display.thread is not None:
     #   display.thread.join()

    if game_type == 'quit':
        # added by Manu script.
        if display.fullscreen and debuglevel == 2:
             display.create_screen(True, False)
             display.display_background()
             display.update_screen()
             logs.log("DEBUG", "Actived by debuglevel == 2 : no FULLSCREEN when EXIT")
        dispatcher.publish('quit', ack=True, limit=['TARGET', 'STRIP'])
        sleep(1)
        logs.log("DEBUG", "Stop TARGETLEDS and STRIPLEDS when EXIT")
        # end added by Manu script.
        logs.log("DEBUG", "Exit")
    elif game_type == 'shutdown':
        import subprocess
        logs.log("DEBUG", "Shutdown")
        dmd.shutdown()
        subprocess.call(['poweroff'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif game_type == 'restart':
        try:
            f = open("restart", "w", encoding="utf-8")
            f.write("")
            f.close()
            logs.log("DEBUG", "Restart")
        except:
            logs.log("DEBUG", "Unable to create restart file")
