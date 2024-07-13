# -*- coding: utf-8 -*-
# Game by David !
# Option Variante : LaDite
######
from include import cplayer
from include import cgame
import random
import subprocess
import pygame

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'win_points': 3, 'master': False, 'variante': False}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Morpion.png' # background image
# Columns headers - Better as a string
HEADERS = ['#', 'PTS'] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}


#Extend the basic player
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
      self.segments = []
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record] = '0'

# Class of the real game
class Game(cgame.Game):
   def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
      super(Game, self).__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players
      self.options = options
      # GameRecords is the dictionnary of stats (see above)
      self.GameRecords = GAME_RECORDS

      self.max_round = 100
      self.winpoints = int(options['win_points'])
      self.master = options['master']
      self.variante = options['variante']
      
      self.segmentsLed = []
      self.grid = []
      self.bw = self.display.res['y'] * 5 / 6
      self.y = self.display.res['y'] / 12
      self.x = self.display.res['x'] / 2 - self.bw / 2
      case = self.bw / 3
      self.jw = self.bw / 3
      pad = (case - self.jw) / 2
      
      #print('')
      print('self.x - self.display.res["x"] / 2 - self.bw / 2')
      print(self.x)
      print('self.y - self.display.res["y"] / 12 ')
      print(self.y)
      print('self.bw - self.display.res["y"] * 5 / 6')
      print(self.bw)
      print('self.jw - self.bw / 3')
      print(self.jw)
      print('case - self.bw / 3')
      print(case)
      print('pad - (case - self.jw) / 2')
      print(pad)
      print('')

      self.pos = [
      (self.x + pad, self.y + pad ),
      (self.x + case + pad, self.y + pad),
      (self.x + case * 2 + pad, self.y + pad),
      (self.x + pad, self.y + case + pad),
      (self.x + case + pad, self.y + case + pad),
      (self.x + case * 2 + pad, self.y + case + pad),
      (self.x + pad, self.y + case * 2 + pad),
      (self.x + case + pad, self.y + case * 2 + pad),
      (self.x + case * 2 + pad, self.y + case * 2 + pad),
      ]

      # gestion de l'affichage du segment
      self.show_hit = True

   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.Log("ERROR","Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0

            #change background
            self.display.display_background('morpion/background.jpg')

            # define the first grid
            self.creategrid()

        # Each new player
        if player_launch == 1:
            players[actual_player].segments = ['__','__','__']
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,2):
                players[actual_player].columns.append(['','int'])

        # on allume les segments gagnants
        segments = {}
        g = self.grid
        colors = ['green','blue','red','yellow']
        tmp_players=[]
        for p in players :
            if p.ident != actual_player :
                tmp_players.append(p)
        tmp_players.append(players[actual_player])

#### Gestion des leds 
        for p in tmp_players :
           
            self.segmentsLed = []
            
            if not self.variante :
              self.checkLineToLed(g[0] , g[1] , g[2] , p.ident)
              self.checkLineToLed(g[0] , g[2] , g[1] , p.ident)
              self.checkLineToLed(g[0] , g[3] , g[6] , p.ident)
              self.checkLineToLed(g[0] , g[4] , g[8] , p.ident)
              self.checkLineToLed(g[0] , g[6] , g[3] , p.ident)
              self.checkLineToLed(g[0] , g[8] , g[4] , p.ident)
              self.checkLineToLed(g[1] , g[2] , g[0] , p.ident)
              self.checkLineToLed(g[1] , g[4] , g[7] , p.ident)
              self.checkLineToLed(g[1] , g[7] , g[4] , p.ident)
              self.checkLineToLed(g[2] , g[4] , g[6] , p.ident)
              self.checkLineToLed(g[2] , g[5] , g[8] , p.ident)
              self.checkLineToLed(g[2] , g[6] , g[4] , p.ident)
              self.checkLineToLed(g[2] , g[8] , g[5] , p.ident)
              self.checkLineToLed(g[3] , g[4] , g[5] , p.ident)
              self.checkLineToLed(g[3] , g[5] , g[4] , p.ident)
              self.checkLineToLed(g[3] , g[6] , g[0] , p.ident)
              self.checkLineToLed(g[4] , g[5] , g[3] , p.ident)
              self.checkLineToLed(g[4] , g[6] , g[2] , p.ident)
              self.checkLineToLed(g[4] , g[7] , g[1] , p.ident)
              self.checkLineToLed(g[4] , g[8] , g[0] , p.ident)
              self.checkLineToLed(g[5] , g[8] , g[2] , p.ident)
              self.checkLineToLed(g[6] , g[7] , g[8] , p.ident)
              self.checkLineToLed(g[6] , g[8] , g[7] , p.ident)
              self.checkLineToLed(g[7] , g[8] , g[6] , p.ident)

            ### Gestion des leds en variante 
            if self.variante :
              self.checkLineToLed_variante(g[0] , g[1] , g[2] , p.ident)
              self.checkLineToLed_variante(g[0] , g[1] , g[3] , p.ident)
              self.checkLineToLed_variante(g[0] , g[1] , g[4] , p.ident)
              self.checkLineToLed_variante(g[0] , g[2] , g[1] , p.ident)
              self.checkLineToLed_variante(g[0] , g[3] , g[1] , p.ident)
              self.checkLineToLed_variante(g[0] , g[3] , g[4] , p.ident)
              self.checkLineToLed_variante(g[0] , g[3] , g[6] , p.ident)
              self.checkLineToLed_variante(g[0] , g[4] , g[1] , p.ident)
              self.checkLineToLed_variante(g[0] , g[4] , g[3] , p.ident)
              self.checkLineToLed_variante(g[0] , g[4] , g[8] , p.ident)
              self.checkLineToLed_variante(g[0] , g[6] , g[3] , p.ident)
              self.checkLineToLed_variante(g[0] , g[8] , g[4] , p.ident)
              self.checkLineToLed_variante(g[1] , g[0] , g[2] , p.ident)
              self.checkLineToLed_variante(g[1] , g[0] , g[3] , p.ident)
              self.checkLineToLed_variante(g[1] , g[0] , g[4] , p.ident)
              self.checkLineToLed_variante(g[1] , g[2] , g[0] , p.ident)
              self.checkLineToLed_variante(g[1] , g[2] , g[4] , p.ident)
              self.checkLineToLed_variante(g[1] , g[2] , g[5] , p.ident)
              self.checkLineToLed_variante(g[1] , g[3] , g[0] , p.ident)
              self.checkLineToLed_variante(g[1] , g[3] , g[4] , p.ident)
              self.checkLineToLed_variante(g[1] , g[4] , g[0] , p.ident)
              self.checkLineToLed_variante(g[1] , g[4] , g[2] , p.ident)
              self.checkLineToLed_variante(g[1] , g[4] , g[3] , p.ident)
              self.checkLineToLed_variante(g[1] , g[4] , g[5] , p.ident)
              self.checkLineToLed_variante(g[1] , g[4] , g[7] , p.ident)
              self.checkLineToLed_variante(g[1] , g[5] , g[2] , p.ident)
              self.checkLineToLed_variante(g[1] , g[5] , g[4] , p.ident)
              self.checkLineToLed_variante(g[1] , g[7] , g[4] , p.ident)
              self.checkLineToLed_variante(g[2] , g[0] , g[1] , p.ident)
              self.checkLineToLed_variante(g[2] , g[1] , g[0] , p.ident)
              self.checkLineToLed_variante(g[2] , g[1] , g[4] , p.ident)
              self.checkLineToLed_variante(g[2] , g[1] , g[5] , p.ident)
              self.checkLineToLed_variante(g[2] , g[4] , g[1] , p.ident)
              self.checkLineToLed_variante(g[2] , g[4] , g[5] , p.ident)
              self.checkLineToLed_variante(g[2] , g[4] , g[6] , p.ident)
              self.checkLineToLed_variante(g[2] , g[5] , g[1] , p.ident)
              self.checkLineToLed_variante(g[2] , g[5] , g[4] , p.ident)
              self.checkLineToLed_variante(g[2] , g[5] , g[8] , p.ident)
              self.checkLineToLed_variante(g[2] , g[6] , g[4] , p.ident)
              self.checkLineToLed_variante(g[2] , g[8] , g[5] , p.ident)
              self.checkLineToLed_variante(g[3] , g[0] , g[1] , p.ident)
              self.checkLineToLed_variante(g[3] , g[0] , g[4] , p.ident)
              self.checkLineToLed_variante(g[3] , g[0] , g[6] , p.ident)
              self.checkLineToLed_variante(g[3] , g[1] , g[0] , p.ident)
              self.checkLineToLed_variante(g[3] , g[1] , g[4] , p.ident)
              self.checkLineToLed_variante(g[3] , g[4] , g[0] , p.ident)
              self.checkLineToLed_variante(g[3] , g[4] , g[1] , p.ident)
              self.checkLineToLed_variante(g[3] , g[4] , g[5] , p.ident)
              self.checkLineToLed_variante(g[3] , g[4] , g[6] , p.ident)
              self.checkLineToLed_variante(g[3] , g[4] , g[7] , p.ident)
              self.checkLineToLed_variante(g[3] , g[5] , g[4] , p.ident)
              self.checkLineToLed_variante(g[3] , g[6] , g[0] , p.ident)
              self.checkLineToLed_variante(g[3] , g[6] , g[4] , p.ident)
              self.checkLineToLed_variante(g[3] , g[6] , g[7] , p.ident)
              self.checkLineToLed_variante(g[3] , g[7] , g[4] , p.ident)
              self.checkLineToLed_variante(g[3] , g[7] , g[6] , p.ident)
              self.checkLineToLed_variante(g[4] , g[0] , g[1] , p.ident)
              self.checkLineToLed_variante(g[4] , g[0] , g[3] , p.ident)
              self.checkLineToLed_variante(g[4] , g[0] , g[8] , p.ident)
              self.checkLineToLed_variante(g[4] , g[1] , g[0] , p.ident)
              self.checkLineToLed_variante(g[4] , g[1] , g[2] , p.ident)
              self.checkLineToLed_variante(g[4] , g[1] , g[3] , p.ident)
              self.checkLineToLed_variante(g[4] , g[1] , g[5] , p.ident)
              self.checkLineToLed_variante(g[4] , g[1] , g[7] , p.ident)
              self.checkLineToLed_variante(g[4] , g[2] , g[1] , p.ident)
              self.checkLineToLed_variante(g[4] , g[2] , g[5] , p.ident)
              self.checkLineToLed_variante(g[4] , g[2] , g[6] , p.ident)
              self.checkLineToLed_variante(g[4] , g[3] , g[0] , p.ident)
              self.checkLineToLed_variante(g[4] , g[3] , g[1] , p.ident)
              self.checkLineToLed_variante(g[4] , g[3] , g[5] , p.ident)
              self.checkLineToLed_variante(g[4] , g[3] , g[6] , p.ident)
              self.checkLineToLed_variante(g[4] , g[3] , g[7] , p.ident)
              self.checkLineToLed_variante(g[4] , g[5] , g[1] , p.ident)
              self.checkLineToLed_variante(g[4] , g[5] , g[2] , p.ident)
              self.checkLineToLed_variante(g[4] , g[5] , g[3] , p.ident)
              self.checkLineToLed_variante(g[4] , g[5] , g[7] , p.ident)
              self.checkLineToLed_variante(g[4] , g[5] , g[8] , p.ident)
              self.checkLineToLed_variante(g[4] , g[6] , g[2] , p.ident)
              self.checkLineToLed_variante(g[4] , g[6] , g[3] , p.ident)
              self.checkLineToLed_variante(g[4] , g[6] , g[7] , p.ident)
              self.checkLineToLed_variante(g[4] , g[7] , g[1] , p.ident)
              self.checkLineToLed_variante(g[4] , g[7] , g[3] , p.ident)
              self.checkLineToLed_variante(g[4] , g[7] , g[5] , p.ident)
              self.checkLineToLed_variante(g[4] , g[7] , g[6] , p.ident)
              self.checkLineToLed_variante(g[4] , g[7] , g[8] , p.ident)
              self.checkLineToLed_variante(g[4] , g[8] , g[0] , p.ident)
              self.checkLineToLed_variante(g[4] , g[8] , g[5] , p.ident)
              self.checkLineToLed_variante(g[4] , g[8] , g[7] , p.ident)
              self.checkLineToLed_variante(g[5] , g[1] , g[2] , p.ident)
              self.checkLineToLed_variante(g[5] , g[1] , g[4] , p.ident)
              self.checkLineToLed_variante(g[5] , g[2] , g[1] , p.ident)
              self.checkLineToLed_variante(g[5] , g[2] , g[4] , p.ident)
              self.checkLineToLed_variante(g[5] , g[2] , g[8] , p.ident)
              self.checkLineToLed_variante(g[5] , g[3] , g[4] , p.ident)
              self.checkLineToLed_variante(g[5] , g[4] , g[1] , p.ident)
              self.checkLineToLed_variante(g[5] , g[4] , g[2] , p.ident)
              self.checkLineToLed_variante(g[5] , g[4] , g[3] , p.ident)
              self.checkLineToLed_variante(g[5] , g[4] , g[7] , p.ident)
              self.checkLineToLed_variante(g[5] , g[4] , g[8] , p.ident)
              self.checkLineToLed_variante(g[5] , g[7] , g[4] , p.ident)
              self.checkLineToLed_variante(g[5] , g[7] , g[8] , p.ident)
              self.checkLineToLed_variante(g[5] , g[8] , g[2] , p.ident)
              self.checkLineToLed_variante(g[5] , g[8] , g[4] , p.ident)
              self.checkLineToLed_variante(g[5] , g[8] , g[7] , p.ident)
              self.checkLineToLed_variante(g[6] , g[0] , g[3] , p.ident)
              self.checkLineToLed_variante(g[6] , g[2] , g[4] , p.ident)
              self.checkLineToLed_variante(g[6] , g[3] , g[0] , p.ident)
              self.checkLineToLed_variante(g[6] , g[3] , g[4] , p.ident)
              self.checkLineToLed_variante(g[6] , g[3] , g[7] , p.ident)
              self.checkLineToLed_variante(g[6] , g[4] , g[2] , p.ident)
              self.checkLineToLed_variante(g[6] , g[4] , g[3] , p.ident)
              self.checkLineToLed_variante(g[6] , g[4] , g[7] , p.ident)
              self.checkLineToLed_variante(g[6] , g[7] , g[3] , p.ident)
              self.checkLineToLed_variante(g[6] , g[7] , g[4] , p.ident)
              self.checkLineToLed_variante(g[6] , g[7] , g[8] , p.ident)
              self.checkLineToLed_variante(g[6] , g[8] , g[7] , p.ident)
              self.checkLineToLed_variante(g[7] , g[1] , g[4] , p.ident)
              self.checkLineToLed_variante(g[7] , g[3] , g[4] , p.ident)
              self.checkLineToLed_variante(g[7] , g[3] , g[6] , p.ident)
              self.checkLineToLed_variante(g[7] , g[4] , g[1] , p.ident)
              self.checkLineToLed_variante(g[7] , g[4] , g[3] , p.ident)
              self.checkLineToLed_variante(g[7] , g[4] , g[5] , p.ident)
              self.checkLineToLed_variante(g[7] , g[4] , g[6] , p.ident)
              self.checkLineToLed_variante(g[7] , g[4] , g[8] , p.ident)
              self.checkLineToLed_variante(g[7] , g[5] , g[4] , p.ident)
              self.checkLineToLed_variante(g[7] , g[5] , g[8] , p.ident)
              self.checkLineToLed_variante(g[7] , g[6] , g[3] , p.ident)
              self.checkLineToLed_variante(g[7] , g[6] , g[4] , p.ident)
              self.checkLineToLed_variante(g[7] , g[6] , g[8] , p.ident)
              self.checkLineToLed_variante(g[7] , g[8] , g[4] , p.ident)
              self.checkLineToLed_variante(g[7] , g[8] , g[5] , p.ident)
              self.checkLineToLed_variante(g[7] , g[8] , g[6] , p.ident)
              self.checkLineToLed_variante(g[8] , g[0] , g[4] , p.ident)
              self.checkLineToLed_variante(g[8] , g[2] , g[5] , p.ident)
              self.checkLineToLed_variante(g[8] , g[4] , g[0] , p.ident)
              self.checkLineToLed_variante(g[8] , g[4] , g[5] , p.ident)
              self.checkLineToLed_variante(g[8] , g[4] , g[7] , p.ident)
              self.checkLineToLed_variante(g[8] , g[5] , g[2] , p.ident)
              self.checkLineToLed_variante(g[8] , g[5] , g[4] , p.ident)
              self.checkLineToLed_variante(g[8] , g[5] , g[7] , p.ident)
              self.checkLineToLed_variante(g[8] , g[6] , g[7] , p.ident)
              self.checkLineToLed_variante(g[8] , g[7] , g[4] , p.ident)
              self.checkLineToLed_variante(g[8] , g[7] , g[5] , p.ident)
              self.checkLineToLed_variante(g[8] , g[7] , g[6] , p.ident)

              

              #self.checkLineToLed_variante(g[0] , g[2] , g[4] , p.ident)
              #self.checkLineToLed_variante(g[0] , g[4] , g[2] , p.ident)
              #self.checkLineToLed_variante(g[0] , g[4] , g[6] , p.ident)
              #self.checkLineToLed_variante(g[0] , g[6] , g[4] , p.ident)
              #self.checkLineToLed_variante(g[1] , g[3] , g[5] , p.ident)
              #self.checkLineToLed_variante(g[1] , g[3] , g[7] , p.ident)
              #self.checkLineToLed_variante(g[1] , g[5] , g[3] , p.ident)
              #self.checkLineToLed_variante(g[1] , g[5] , g[7] , p.ident)
              #self.checkLineToLed_variante(g[1] , g[7] , g[3] , p.ident)
              #self.checkLineToLed_variante(g[1] , g[7] , g[5] , p.ident)
              #self.checkLineToLed_variante(g[2] , g[0] , g[4] , p.ident)
              #self.checkLineToLed_variante(g[2] , g[4] , g[0] , p.ident)
              #self.checkLineToLed_variante(g[2] , g[4] , g[8] , p.ident)
              #self.checkLineToLed_variante(g[2] , g[8] , g[4] , p.ident)
              #self.checkLineToLed_variante(g[3] , g[1] , g[5] , p.ident)
              #self.checkLineToLed_variante(g[3] , g[1] , g[7] , p.ident)
              #self.checkLineToLed_variante(g[3] , g[5] , g[1] , p.ident)
              #self.checkLineToLed_variante(g[3] , g[5] , g[7] , p.ident)
              #self.checkLineToLed_variante(g[3] , g[7] , g[1] , p.ident)
              #self.checkLineToLed_variante(g[3] , g[7] , g[5] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[0] , g[2] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[0] , g[6] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[2] , g[0] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[2] , g[8] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[6] , g[0] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[6] , g[8] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[8] , g[2] , p.ident)
              #self.checkLineToLed_variante(g[4] , g[8] , g[6] , p.ident)
              #self.checkLineToLed_variante(g[5] , g[1] , g[3] , p.ident)
              #self.checkLineToLed_variante(g[5] , g[1] , g[7] , p.ident)
              #self.checkLineToLed_variante(g[5] , g[3] , g[1] , p.ident)
              #self.checkLineToLed_variante(g[5] , g[3] , g[7] , p.ident)
              #self.checkLineToLed_variante(g[5] , g[7] , g[1] , p.ident)
              #self.checkLineToLed_variante(g[5] , g[7] , g[3] , p.ident)
              #self.checkLineToLed_variante(g[6] , g[0] , g[4] , p.ident)
              #self.checkLineToLed_variante(g[6] , g[4] , g[0] , p.ident)
              #self.checkLineToLed_variante(g[6] , g[4] , g[8] , p.ident)
              #self.checkLineToLed_variante(g[6] , g[8] , g[4] , p.ident) 
              #self.checkLineToLed_variante(g[7] , g[1] , g[3] , p.ident)
              #self.checkLineToLed_variante(g[7] , g[1] , g[5] , p.ident)
              #self.checkLineToLed_variante(g[7] , g[3] , g[1] , p.ident)
              #self.checkLineToLed_variante(g[7] , g[3] , g[5] , p.ident)
              #self.checkLineToLed_variante(g[7] , g[5] , g[1] , p.ident)
              #self.checkLineToLed_variante(g[7] , g[5] , g[3] , p.ident)
              #self.checkLineToLed_variante(g[8] , g[2] , g[4] , p.ident)
              #self.checkLineToLed_variante(g[8] , g[4] , g[2] , p.ident)
              #self.checkLineToLed_variante(g[8] , g[4] , g[6] , p.ident)
              #self.checkLineToLed_variante(g[8] , g[6] , g[4] , p.ident)


            for s in self.segmentsLed :
                segments[f'S{s}'] = colors[p.ident]
                segments[f'D{s}'] = colors[p.ident]
                segments[f'T{s}'] = colors[p.ident]

        # show segments led
        segmentsAsStr = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
        self.rpi.set_target_leds(segmentsAsStr)

        return return_code

   
   def checkLineToLed(self, case1, case2, caseWin, playerId):
     if not self.variante :
       if case1[1] == playerId and case2[1] == playerId and caseWin[1] == -1:
         if caseWin[0] in self.segmentsLed :
           self.segmentsLed.remove(caseWin[0])
         self.segmentsLed.append(caseWin[0])  
     
     
   def checkLineToLed_variante(self, case1, case2, caseWin, actual_player):
     #### AJOUT CONDITION "si g[7] = 1" - pour segment acquis    
     ### AJOUT actual_player POUR FORCER LA COULEUR DU JOUEUR ACTUAL - si couleur gagnante correspond a un autre joueur aussi  
     if self.variante :
       if case1[1] == actual_player and case1[7] == 1 and case2[1] == actual_player and case2[7] == 1 and caseWin[1] == -1:
         if caseWin[0] in self.segmentsLed :
           self.segmentsLed.remove(caseWin[0])
         self.segmentsLed.append(caseWin[0])
         
         print('case1')
         print(case1)
         print('case1[1]')
         print(case1[1])
         print('')
         print('case2')
         print(case2)
         print('case2[1]')
         print(case2[1])
         print('')
         print('casewin')
         print(caseWin)
         print('casewin[1]')
         print(caseWin[1])
         print('')
         print('segmentled')
         print(self.segmentsLed)
         print('')
         
   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        return_code = 0
        self.show_hit = True

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].segments[player_launch-1] = hit

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D' :
            multi = 2
        if hit[:1] == 'T' :
            multi = 3

        ### OPTION "VARIANTE" NON SELECTIONNE
        if not self.variante :
        # give a random case orphelin
          if hit == 'SB' :
              self.show_hit = False
              lst = []
              for key, value in enumerate(self.grid):
                  if value[1] == -1:
                      lst.append(key)
              h = lst[random.randint(0, len(lst) - 1)]
              self.grid[h] = (self.grid[h][0],actual_player,2)
              self.BlinkCase(h)
              self.DrawCase(h, True)
              self.display.update_screen()
  
          # cancel 1 case for each opponent
          elif hit == 'DB':
              self.show_hit = False
              lst = {}
              lst[0] = []
              lst[1] = []
              lst[2] = []
              lst[3] = []
              for k, v in enumerate(self.grid):
                  if v[1] >= 0 and v[1] != actual_player and v[2] < 3:
                      lst[v[1]].append(k)
  
              for i in range (0,4):
                  if len(lst[i]) > 0:
                      h = random.randint(0,len(lst[i]) - 1)
                      self.grid[lst[i][h]] = (self.grid[lst[i][h]][0], -1, 0)
  
              self.video_player.play_video(self.display.file_class.get_full_filename('morpion/morpion_dbull', 'videos'))

          else:
              for k,v in enumerate(self.grid):
                  if v[0] == int(hit[1:]):
                      if v[2] <= 0 : # cas de prise
                          self.show_hit = False
                          self.grid[k] = (v[0], actual_player, multi)
                          self.BlinkCase(k)
                          self.DrawCase(k, True)
                          self.display.update_screen()
                      elif v[1] != actual_player and v[2]<3 : # cas d'orphelinage ou supression bouclier
                          self.show_hit = False
                          niv = v[2] - multi
                          if niv <= 0:
                              self.grid[k] = (v[0], -1, 0)
                          else:
                              self.grid[k] = (v[0], v[1], niv)
                          self.BlinkCase(k)
                          self.DrawCase(k, True)
                          self.display.update_screen()
                          
        ### OPTION VARIANTE ACTIVEE
        if self.variante :
          '''
          if hit == 'SB' or hit == 'DB' :
            self.show_hit = False
          '''
          ### A ACTIVER/DESACTIVE APRES TEST - VOIR SI INTERESSANT OU NON  
          if hit == 'SB' :  ### SUPPRIME 1 BOUCLIER SI bouclier est > a 1 ET bouclier est < a 4
              self.show_hit = False
              for k,v in enumerate(self.grid):
                print('k')
                print(k)

                if actual_player == 0 :
                      j1 = v[3]
                      print('J1 touche SB')
                      if v[4] < 4 and v[4] > 1 :
                        print('supprime 1 bouclier de j2') 
                        j2 = v[4]
                        j2 -= 1
                      else :
                        j2 = v[4]
                      
                      if v[5] < 4 and v[5] > 1 :
                        print('supprime 1 bouclier de j3') 
                        j3 = v[5]
                        j3 -= 1
                      else :
                        j3 = v[5]
                     
                      if v[6] < 4 and v[6] > 1 :
                        print('supprime 1 bouclier de j4') 
                        j4 = v[6]
                        j4 -= 1
                      else :
                        j4 = v[6]
                
                if actual_player == 1 :
                      j2 = v[4]
                      print('J2 touche SB')
                      if v[3] < 4 and v[3] > 1 : 
                        print('supprime 1 bouclier de j1')  
                        j1 = v[3]
                        j1 -= 1
                      else :
                        j1 = v[3]
                      
                      if v[5] < 4 and v[5] > 1 :
                        print('supprime 1 bouclier de j3') 
                        j3 = v[5]
                        j3 -= 1
                      else :
                        j3 = v[5]
                        
                      if v[6] < 4 and v[6] > 1 :
                        print('supprime 1 bouclier de j4') 
                        j4 = v[6]
                        j4 -= 1
                      else :
                        j4 = v[6]
                        
                if actual_player == 2 :
                      j3 = v[5]
                      print('J3 touche SB')
                      if v[3] < 4 and v[3] > 1 :  
                        print('supprime 1 bouclier de j1') 
                        j1 = v[3]
                        j1 -= 1
                      else :
                        j1 = v[3]
                      
                      if v[4] < 4 and v[4] > 1 : 
                        print('supprime 1 bouclier de j2') 
                        j2 = v[4]
                        j2 -= 1
                      else :
                        j2 = v[4]
                     
                      if v[6] < 4 and v[6] > 1 :
                        print('supprime 1 bouclier de j4') 
                        j4 = v[6]
                        j4 -= 1
                      else :
                        j4 = v[6]
                        
                if actual_player == 3 :
                      j4 = v[6]
                      print('J4 touche SB')
                      if v[3] < 4 and v[3] > 1 : 
                        print('supprime 1 bouclier de j1') 
                        j1 = v[3]
                        j1 -= 1
                      else :
                        j1 = v[3]
                      
                      if v[4] < 4 and v[4] > 1 : 
                        print('supprime 1 bouclier de j2') 
                        j2 = v[4]
                        j2 -= 1
                      else :
                        j2 = v[4]
                     
                      if v[5] < 4 and v[5] > 1 :
                        print('supprime 1 bouclier de j3') 
                        j3 = v[5]
                        j3 -= 1  
                      else :
                        j3 = v[5]
              
                print('maj de la grille apres sb')
                self.grid[k] = (v[0], v[1], v[2], j1, j2, j3, j4, 0)
                print(self.grid)
              print('sb touche')
          
          elif hit == 'DB' :  ### AJOUTE  1 BOUCLIER AU JOUEUR SI bouclier est < 3
              self.show_hit = False
              print('db touche') 
              for k,v in enumerate(self.grid):
                print('k')
                print(k)
                j1 = v[3]
                j2 = v[4]
                j3 = v[5]
                j4 = v[6]
                
                if actual_player == 0 :
                      j1 = v[3]
                      print('J1 touche DB')
                      if v[3] < 3 :
                        print('ajoute 1 bouclier a j1') 
                        j1 = v[3]
                        j1 += 1
                      else :
                        j1 = v[3]
                
                if actual_player == 1 :
                      j2 = v[4]
                      print('J1 touche DB')
                      if v[4] < 3 :
                        print('ajoute 1 bouclier a j2') 
                        j2 = v[4]
                        j2 += 1
                      else :
                        j2 = v[4]
                        
                if actual_player == 2 :
                      j3 = v[5]
                      print('J1 touche DB')
                      if v[5] < 3 :
                        print('ajoute 1 bouclier a j3') 
                        j3 = v[5]
                        j3 += 1
                      else :
                        j3 = v[5]
                        
                if actual_player == 3 :
                      j4 = v[6]
                      print('J1 touche DB')
                      if v[6] < 3 :
                        print('ajoute 1 bouclier a j4') 
                        j4 = v[6]
                        j4 += 1
                      else :
                        j4 = v[6]
      
                print('maj de la grille apres db')
                self.grid[k] = (v[0], v[1], v[2], j1, j2, j3, j4, 0)
                print(self.grid)
          
          else :
            for k,v in enumerate(self.grid):
              if v[0] == int(hit[1:]):
                self.joueur_actif = int(players[actual_player].ident)
                # pour rappel - segment[0],joueur[1],etat[2], (J1[3], J2[4], J3[5], J4[6]  checkcase (acquise) NB TOUCHE (nouveau))
                
                if self.joueur_actif == 0 :
                  test = v[3]
                  test += multi
                  # si nb de touche de j1 est < a 4 touches
                  if v[3] < 4 :
                    self.show_hit = False
                    self.grid[k] = (v[0], actual_player, 0, test, v[4], v[5], v[6], 0)
                    print('condition j1 <4 - self.grid')
                    print(self.grid)
                    print('')
                  for k,v in enumerate(self.grid):
                    # si nb de touche de j1 est > a 4 touches ==
                    if v[3] > 3 and v[7] != 1 :
                      test = v[3]
                      self.grid[k] = (99, actual_player, 3, test, v[4], v[5], v[6], 1)
                      print('condition j1 >6 - self.grid')
                      print(self.grid)
                      print('')
                      self.BlinkCase(k)
                      self.DrawCase(k, True)
                      self.display.update_screen()
                      
                elif self.joueur_actif == 1 :
                  test = v[4]
                  test += multi
                  # si nb de touche de j2 est < a 4 touches
                  if v[4] < 4 :
                    self.show_hit = False
                    self.grid[k] = (v[0], actual_player, 0, v[3], test, v[5], v[6], 0)
                    print('condition j2 <4 - self.grid')
                    print(self.grid)
                    print('')
                  for k,v in enumerate(self.grid):        
                        # si nb de touche de j2 est > a 4 touches ==  
                        if v[4] > 3 and v[7] != 1 :
                          test = v[4]
                          self.grid[k] = (98, actual_player, 3, v[3], test, v[5], v[6], 1)
                          print('condition j2 >6 - self.grid')
                          print(self.grid)
                          print('')
                          self.BlinkCase(k)
                          self.DrawCase(k, True)
                          self.display.update_screen()
                    
                elif self.joueur_actif == 2 :
                  test = v[5]
                  test += multi
                  # si nb de touche de j3 est < a 4 touches
                  if v[5] < 4 :
                    self.show_hit = False
                    self.grid[k] = (v[0], actual_player, 0, v[3], v[4], test, v[6], 0)
                    print('condition j3 <4 - self.grid')
                    print(self.grid)
                    print('')
                  for k,v in enumerate(self.grid):        
                        # si nb de touche de j3 est > a 4 touches ==  
                        if v[5] > 3 and v[7] != 1 :
                          test = v[5]
                          self.grid[k] = (97, actual_player, 3, v[3], v[4], test, v[6], 1)
                          print('condition j3 >6 - self.grid')
                          print('')
                          print(self.grid)
                          self.BlinkCase(k)
                          self.DrawCase(k, True)
                          self.display.update_screen()
                  
                  
                elif self.joueur_actif == 3 :
                  test = v[6]
                  test += multi
                  # si nb de touche de j4 est < a 4 touches
                  if v[6] < 4 :
                    self.show_hit = False
                    self.grid[k] = (v[0], actual_player, 0, v[3], v[4], v[5], test, 0)
                    print('condition j4 <4 - self.grid')
                    print(self.grid)
                    print('')
                  for k,v in enumerate(self.grid):        
                        # si nb de touche de j4 est > a 4 touches ==
                        if v[6] > 3 and v[7] != 1 :
                          test = v[6]
                          self.grid[k] = (96, actual_player, 3, v[3], v[4], v[5], test, 1)
                          print('condition j4 >6 - self.grid')
                          print(self.grid)
                          print('')
                          self.BlinkCase(k)
                          self.DrawCase(k, True)
                          self.display.update_screen()
                        
 

        # test recordille validée
        if not self.variante :
          g = self.grid
          if (g[0][1] == actual_player and g[1][1] == actual_player and g[2][1] == actual_player) or \
             (g[3][1] == actual_player and g[4][1] == actual_player and g[5][1] == actual_player) or \
             (g[6][1] == actual_player and g[7][1] == actual_player and g[8][1] == actual_player) or \
             (g[0][1] == actual_player and g[3][1] == actual_player and g[6][1] == actual_player) or \
             (g[1][1] == actual_player and g[4][1] == actual_player and g[7][1] == actual_player) or \
             (g[2][1] == actual_player and g[5][1] == actual_player and g[8][1] == actual_player) or \
             (g[0][1] == actual_player and g[4][1] == actual_player and g[8][1] == actual_player) or \
             (g[2][1] == actual_player and g[4][1] == actual_player and g[6][1] == actual_player):
               self.drawWin(actual_player)
               players[actual_player].score += 1
               self.creategrid()
          else:
              nb_unlock = 0
              for key, value in enumerate(self.grid):
                  if value[2] != 3:
                      nb_unlock = 1
                      break
              if nb_unlock == 0:
                  self.creategrid()
                  return 1
              else:
                  self.display.sound_for_touch(hit) # Touched !
        ### test recordille validée - OPTION VARIANTE ACTIVEE
        else :
          g = self.grid
          if (g[0][1] == actual_player and g[0][7] == 1 and g[1][1] == actual_player and g[1][7] == 1 and g[2][1] == actual_player and g[2][7] == 1) or \
             (g[0][1] == actual_player and g[0][7] == 1 and g[1][1] == actual_player and g[1][7] == 1 and g[3][1] == actual_player and g[3][7] == 1) or \
             (g[0][1] == actual_player and g[0][7] == 1 and g[1][1] == actual_player and g[1][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[0][1] == actual_player and g[0][7] == 1 and g[3][1] == actual_player and g[3][7] == 1 and g[6][1] == actual_player and g[6][7] == 1) or \
             (g[0][1] == actual_player and g[0][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[8][1] == actual_player and g[8][7] == 1) or \
             (g[0][1] == actual_player and g[0][7] == 1 and g[3][1] == actual_player and g[3][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[1][1] == actual_player and g[1][7] == 1 and g[2][1] == actual_player and g[2][7] == 1 and g[5][1] == actual_player and g[5][7] == 1) or \
             (g[1][1] == actual_player and g[1][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[7][1] == actual_player and g[7][7] == 1) or \
             (g[2][1] == actual_player and g[2][7] == 1 and g[1][1] == actual_player and g[1][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[2][1] == actual_player and g[2][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[6][1] == actual_player and g[6][7] == 1) or \
             (g[2][1] == actual_player and g[2][7] == 1 and g[5][1] == actual_player and g[5][7] == 1 and g[8][1] == actual_player and g[8][7] == 1) or \
             (g[2][1] == actual_player and g[2][7] == 1 and g[5][1] == actual_player and g[5][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[3][1] == actual_player and g[3][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[1][1] == actual_player and g[1][7] == 1) or \
             (g[3][1] == actual_player and g[3][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[5][1] == actual_player and g[5][7] == 1) or \
             (g[3][1] == actual_player and g[3][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[7][1] == actual_player and g[7][7] == 1) or \
             (g[3][1] == actual_player and g[3][7] == 1 and g[1][1] == actual_player and g[1][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[5][1] == actual_player and g[5][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[1][1] == actual_player and g[1][7] == 1) or \
             (g[5][1] == actual_player and g[5][7] == 1 and g[8][1] == actual_player and g[8][7] == 1 and g[7][1] == actual_player and g[7][7] == 1) or \
             (g[5][1] == actual_player and g[5][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[1][1] == actual_player and g[1][7] == 1) or \
             (g[5][1] == actual_player and g[5][7] == 1 and g[4][1] == actual_player and g[4][7] == 1 and g[7][1] == actual_player and g[7][7] == 1) or \
             (g[6][1] == actual_player and g[6][7] == 1 and g[7][1] == actual_player and g[7][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[6][1] == actual_player and g[6][7] == 1 and g[7][1] == actual_player and g[7][7] == 1 and g[8][1] == actual_player and g[8][7] == 1) or \
             (g[6][1] == actual_player and g[6][7] == 1 and g[3][1] == actual_player and g[3][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[7][1] == actual_player and g[7][7] == 1 and g[6][1] == actual_player and g[6][7] == 1 and g[3][1] == actual_player and g[3][7] == 1) or \
             (g[8][1] == actual_player and g[8][7] == 1 and g[7][1] == actual_player and g[7][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             (g[8][1] == actual_player and g[8][7] == 1 and g[5][1] == actual_player and g[5][7] == 1 and g[4][1] == actual_player and g[4][7] == 1):

             #(g[0][1] == actual_player and g[0][7] == 1 and g[2][1] == actual_player and g[2][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             #(g[0][1] == actual_player and g[0][7] == 1 and g[6][1] == actual_player and g[6][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             #(g[1][1] == actual_player and g[1][7] == 1 and g[7][1] == actual_player and g[7][7] == 1 and g[3][1] == actual_player and g[3][7] == 1) or \
             #(g[1][1] == actual_player and g[1][7] == 1 and g[7][1] == actual_player and g[7][7] == 1 and g[5][1] == actual_player and g[5][7] == 1) or \
             #(g[2][1] == actual_player and g[2][7] == 1 and g[8][1] == actual_player and g[8][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             #(g[3][1] == actual_player and g[3][7] == 1 and g[1][1] == actual_player and g[1][7] == 1 and g[5][1] == actual_player and g[5][7] == 1) or \
             #(g[3][1] == actual_player and g[3][7] == 1 and g[7][1] == actual_player and g[7][7] == 1 and g[5][1] == actual_player and g[5][7] == 1) or \
             #(g[6][1] == actual_player and g[6][7] == 1 and g[8][1] == actual_player and g[8][7] == 1 and g[4][1] == actual_player and g[4][7] == 1) or \
             

             self.drawWin(actual_player)
             players[actual_player].score += 1
             self.creategrid()

          else:
            
            nb_unlock = 0
            for key, value in enumerate(self.grid):
                if value[2] != 3:
                    nb_unlock = 1
                    break
            if nb_unlock == 0:
                self.creategrid()
                return 1
            else:
                self.display.sound_for_touch(hit) # Touched !

    
          
        # test for a winner
        if players[actual_player].score >= self.winpoints:
            self.winner =  players[actual_player].ident
            return_code = 3

        return return_code

   def creategrid(self):
      """
      create grid
      """
      if not self.variante :
        self.grid.clear()
        hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        for i in range (0, 9) :
           h = random.randint(0, len(hits) - 1)
           self.grid.append((hits[h], -1, 0)) # segment,joueur,etat
           hits.pop(h)
      
      else :
        self.grid.clear()
        hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        for i in range (0, 9) :
           h = random.randint(0, len(hits) - 1)
           self.grid.append((hits[h], -1, 0, 0, 0, 0, 0, 0)) # segment,joueur,etat, (J1[3], J2[4], J3[5], J4[6]   NB TOUCHE (nouveau))
           hits.pop(h)

   ###############
   # Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical formulas used to calculate stats. Refreshed after every launch
   def refresh_stats(self, players, actual_round):
      for player in players:
         player.stats['Points Per Round'] = player.avg(actual_round)

   ###############
   # Set if a message is shown to indicate the segment hitted !
   #
   def display_segment(self):
      return self.show_hit

   ###############
   # Return the player number max for a game.
   def check_players_allowed(self, nb_players):
      return nb_players > 1 and nb_players < 5

     ###############
   # Refresh In-game screen
   #
   def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       # do not show the table scores
      ClickZones = {}

      # Clear
      self.display.screen.fill( (0,0,0) )
      # background image
      self.display.display_background()

      bw = self.bw
      y = self.y
      x = self.x
      jw= self.jw

      self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_board_back', 'images'),x, y, bw, bw, True, False, False)

      # show values in grid
      for k,v in enumerate(self.grid ):
         self.DrawCase(k)

      self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_board', 'images'),x, y, bw, bw, True, False, False)

      pad = bw/20
      pw = x-pad*2

      self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_dartbg', 'images'),pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(Players[actual_player].segments[0],pad, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[1],pad+pw/3, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[2],pad+pw/3*2, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))

      self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_turnbg', 'images'),x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(str(self.display.lang.translate('round')) +' '+str(actual_round) ,x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, color=(255,255,255))

      self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_name', 'images'),pad, y, pw,pw/4, True, False, False)
      self.display.blit_text(Players[0].name,pad, y, pw,pw/4, color=(255,255,255) if actual_player==0 else (150,0,0) )
      self.display.blit_text(str(Players[0].score),pad+pw*3/4, y+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==0 else (150,0,0) )
      self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_j0', 'images'),pad+pw/4,y+pw/4,pw/4,pw/4, True, False, False)

      if len(Players) > 1:
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_name', 'images'),x+bw+pad, y, pw,pw/4, True, False, False)
        self.display.blit_text(Players[1].name,x+bw+pad, y, pw,pw/4, color=(255,255,255) if actual_player==1 else(150,0,0))
        self.display.blit_text(str(Players[1].score),x+bw+pad+pw*3/4,y+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==1 else(150,0,0))
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_j1', 'images'),x+bw+pad+pw/4,y+pw/4,pw/4,pw/4, True, False, False)

      if len(Players) > 2:
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_name', 'images'),pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[2].name,pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==2 else(150,0,0))
        self.display.blit_text(str(Players[2].score),pad+pw*3/4, y+bw/2+pw/4 , pw/4,pw/4, color=(255,255,255) if actual_player==2 else (150,0,0) )
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_j2', 'images'),pad+pw/4,y+bw/2+pw/4,pw/4,pw/4, True, False, False)

      if len(Players) > 3:
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_name', 'images'),x+bw+pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[3].name,x+bw+pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==3 else(150,0,0))
        self.display.blit_text(str(Players[3].score),x+bw+pad+pw*3/4, y+bw/2+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==3 else(150,0,0))
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_j3', 'images'),x+bw+pad+pw/4,y+bw/2+pw/4,pw/4,pw/4, True, False, False)

      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
          return ClickZones

      self.display.update_screen()

      return [ClickZones]

   #######################"
   def BlinkCase(self,case) :
      for i in range (0,4) :
        self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_j{self.grid[case][1]}', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.update_screen(rect=(self.pos[case][0], self.pos[case][1], self.jw, self.jw))
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_empty', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.update_screen(rect=(self.pos[case][0], self.pos[case][1], self.jw, self.jw))

   #######################"
   def DrawCase(self, case, redrawgrid = False) :

      if not self.variante :
        if self.grid[case][1] >= 0:
          self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_j{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
        
        if self.master :
          if self.grid[case][2] == 3:
            self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_shield', 'images'),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2,self.jw/2, True, False, False)
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2, self.jw/2, color=(230,250,230))
          elif self.grid[case][2] == 2:
            self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_lock', 'images'),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2,self.jw/2, True, False, False)
          elif self.grid[case][1] >= 0:
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0],self.pos[case][1], self.jw, self.jw, color=(150, 150, 150))
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+5,self.pos[case][1]+5, self.jw-10, self.jw-10, color=(30, 50, 30))
          else:
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0],self.pos[case][1], self.jw, self.jw, color=(150, 150, 150))
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+5,self.pos[case][1]+5, self.jw-10, self.jw-10, color=(230, 250, 230))
        if not self.master :
          if self.grid[case][2] == 2:
            self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_shield', 'images'),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2,self.jw/2, True, False, False)
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2, self.jw/2, color=(230,250,230))
          elif self.grid[case][2] == 3:
            self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_lock', 'images'),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2,self.jw/2, True, False, False)
          elif self.grid[case][1] >= 0:
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0],self.pos[case][1], self.jw, self.jw, color=(150, 150, 150))
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+5,self.pos[case][1]+5, self.jw-10, self.jw-10, color=(30, 50, 30))
          else:
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0],self.pos[case][1], self.jw, self.jw, color=(150, 150, 150))
            self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+5,self.pos[case][1]+5, self.jw-10, self.jw-10, color=(230, 250, 230))
          
      else :
        
        ### changement de place, normalement a la fin mais chiffre efface par les lignes ci dessous
        self.display.blit_text(str(self.grid[case][0]),self.pos[case][0],self.pos[case][1], self.jw, self.jw, color=(150, 150, 150))
        self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+5,self.pos[case][1]+5, self.jw-10, self.jw-10, color=(230, 250, 230))
       
       
  ###" AFFICHAGE DES POINTS DE PRISE + IMAGE SI V[2] >= 4
  
        #### AFFICHAGE points 4 joueurs dans case 
        if self.variante :
          if self.nb_players == 4 :
            ### trouver un calcul pour fixer correctement (selon les diverses resolutions) les chiffres dans les 4 coins des cases
            #self.display.blit_text(str(self.grid[case][3]),self.pos[case][0]+self.jw/6 - 20 ,self.pos[case][1]+self.jw/6 - 20, self.jw/4, self.jw/4, color=(0,255,0))
            #self.display.blit_text(str(self.grid[case][4]),self.pos[case][0]+self.jw/6 + 110,self.pos[case][1]+self.jw/6 - 20, self.jw/4, self.jw/4, color=(0,255,255))
            #self.display.blit_text(str(self.grid[case][5]),self.pos[case][0]+self.jw/6 - 20,self.pos[case][1]+self.jw/6 + 110, self.jw/4, self.jw/4, color=(255,0,0))
            #self.display.blit_text(str(self.grid[case][6]),self.pos[case][0]+self.jw/6 + 110,self.pos[case][1]+self.jw/6 + 110, self.jw/4, self.jw/4, color=(255,255,0))
          
            #EN TEST  
            self.display.blit_text(str(self.grid[case][3]),self.pos[case][0]+self.jw/15 ,self.pos[case][1]+self.jw/15, self.jw/4, self.jw/4, color=(0,255,0))
            self.display.blit_text(str(self.grid[case][4]),self.pos[case][0]+self.jw/10*7,self.pos[case][1]+self.jw/15, self.jw/4, self.jw/4, color=(0,255,255))
            self.display.blit_text(str(self.grid[case][5]),self.pos[case][0]+self.jw/15,self.pos[case][1]+self.jw/10*7, self.jw/4, self.jw/4, color=(255,0,0))
            self.display.blit_text(str(self.grid[case][6]),self.pos[case][0]+self.jw/10*7,self.pos[case][1]+self.jw/10*7, self.jw/4, self.jw/4, color=(255,255,0))
          
          if self.nb_players == 3 :
            self.display.blit_text(str(self.grid[case][3]),self.pos[case][0]+self.jw/15 ,self.pos[case][1]+self.jw/15, self.jw/4, self.jw/4, color=(0,255,0))
            self.display.blit_text(str(self.grid[case][4]),self.pos[case][0]+self.jw/10*7,self.pos[case][1]+self.jw/15, self.jw/4, self.jw/4, color=(0,255,255))
            self.display.blit_text(str(self.grid[case][5]),self.pos[case][0]+self.jw/15,self.pos[case][1]+self.jw/10*7, self.jw/4, self.jw/4, color=(255,0,0))
            
          if self.nb_players == 2 :
            self.display.blit_text(str(self.grid[case][3]),self.pos[case][0]+self.jw/15 ,self.pos[case][1]+self.jw/15, self.jw/4, self.jw/4, color=(0,255,0))
            self.display.blit_text(str(self.grid[case][4]),self.pos[case][0]+self.jw/10*7,self.pos[case][1]+self.jw/15, self.jw/4, self.jw/4, color=(0,255,255))
            
                        
          
        if self.grid[case][3] > 3:
          self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_j{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)

        if self.grid[case][4] > 3:
          self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_j{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)

        if self.grid[case][5] > 3:
          self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_j{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)

        if self.grid[case][6] > 3:
          self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_j{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)

    
      if redrawgrid :
        self.display.display_image(self.display.file_class.get_full_filename('morpion/morpion_board', 'images'),self.x, self.y, self.bw, self.bw, True, False, False)

   #######################"
   def drawWin(self,actual_player) :
      g = self.grid

      if g[0][1] == actual_player and g[1][1] == actual_player and g[2][1] == actual_player:
          win = [(0,'wh'),(1,'wh'),(2,'wh')]
      if g[3][1] == actual_player and g[4][1] == actual_player and g[5][1] == actual_player:
          win = [(3,'wh'),(4,'wh'),(5,'wh')]
      if g[6][1] == actual_player and g[7][1] == actual_player and g[8][1] == actual_player:
          win = [(6,'wh'),(7,'wh'),(8,'wh')]
      if g[0][1] == actual_player and g[3][1] == actual_player and g[6][1] == actual_player:
          win = [(0,'wv'),(3,'wv'),(6,'wv')]
      if g[1][1] == actual_player and g[4][1] == actual_player and g[7][1] == actual_player:
          win = [(1,'wv'),(4,'wv'),(7,'wv')]
      if g[2][1] == actual_player and g[5][1] == actual_player and g[8][1] == actual_player:
          win = [(2,'wv'),(5,'wv'),(8,'wv')]
      if g[0][1] == actual_player and g[4][1] == actual_player and g[8][1] == actual_player:
          win = [(0,'wdd'),(4,'wdd'),(8,'wdd')]
      if g[2][1] == actual_player and g[4][1] == actual_player and g[6][1] == actual_player:
          win = [(2,'wdg'),(4,'wdg'),(6,'wdg')]

      ### RETIRE DU CODE POUR VARIANTE - ON N EST PLUS LIMITE PAR LES LIGNES Hor-Vert-Diag en VARIANTE
      if not self.variante :
        for v in win :
            self.display.display_image(self.display.file_class.get_full_filename(f'morpion/morpion_{v[1]}', 'images'),self.pos[v[0]][0],self.pos[v[0]][1], self.jw, self.jw, True, False, False)
            self.display.update_screen(rect=(self.pos[v[0]][0], self.pos[v[0]][1], self.jw, self.jw))
            self.display.play_sound('morpion_win1',wait_finish = True)

      self.display.play_sound('motus_win')
      pygame.time.delay(1500)
