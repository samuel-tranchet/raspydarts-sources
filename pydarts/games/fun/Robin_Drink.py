#show_message -*- coding: utf-8 -*-
# Game by David !
######
from include import cplayer
from include import cgame
import random
import pygame
from addons import Colors

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': 10, 'mode_random': False, 'chaos': False}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Robin_Drink.png' # background image
# Columns headers - Better as a string
HEADERS = [ "#","PTS" ] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 2 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}

NbSegmentsForOpponents = 7  # nombre de segments pour faire boire un adversaire en le designant avec la deuxieme flechette
NbSegmentsForRandom = 5     # nombre de segments pour faire boire un adversaire aléatoire
NbSegmentsForPlayer = 5     # nombre de segments pour faire le joueur courant
# le reste des segments sont neutres, le joueur passe, un pneu également


segmentsForTarget = [
    ([12, 5], 'red', 'R'),
    ([18, 4], 'green', 'G'),
    ([8, 11], 'blue', 'B'),
    ([10, 15], 'brown', 'M'),
    ([3, 19], 'yellow', 'Y'),
    ([14, 9], 'purple', 'P'),
    ([13, 6], 'orange', 'O'),
    ([7, 16], 'deeppink', 'D'),
    ([17, 2], 'silver', 'S'),
    ([20, 1], 'tan', 'T')
]

def check_players_allowed(nb_players):
    '''
    Return the player number max for a game.
    '''
    return nb_players <= 10

#Extend the basic player
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
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
      self.nb_darts = 2
      self.nb_players = nb_players
      # game_records is the dictionnary of stats (see above)
      self.game_records = GAME_RECORDS
      self.options = options

      self.max_round = int(options['max_round'])
      self.random = options['mode_random']
      if options['chaos']:
          self.time = 3000
      self.currentMulti = 1

      # tailles des elements
      self.space = self.display.res['y']/20
      self.bh = self.display.res['y']/10
      self.targetH = self.display.res['y'] - self.bh*2 -self.space*2
      self.bw = (self.display.res['x'] - self.targetH) /2 -self.space*2

      # position des box des joueurs (x,y)
      self.pos = [
      (0, self.display.res['y'] / 5),
      (self.display.res['x'] - self.bw - self.space, self.display.res['y'] / 5),
      (0, self.display.res['y'] * 3 / 5),
      (self.display.res['x'] - self.bw - self.space, self.display.res['y']* 3 / 5),
      (self.display.res['x'] / 2 - self.bw / 2 , self.display.res['y'] - self.bh),
      (0, self.display.res['y'] * 2 / 5),
      (self.display.res['x'] - self.bw - self.space, self.display.res['y'] * 2 / 5),
      (0, self.display.res['y'] * 4 / 5),
      (self.display.res['x'] - self.bw - self.space, self.display.res['y'] * 4 / 5),
      (self.display.res['x'] / 2 - self.bw / 2 ,0)
      ]

      if nb_players < 5:
          segmentsForTarget[0] = ([5, 12, 9, 14], segmentsForTarget[0][1], segmentsForTarget[0][2])
          segmentsForTarget[1] = ([1, 18, 4, 13], segmentsForTarget[1][1], segmentsForTarget[1][2])
          segmentsForTarget[2] = ([8, 16, 7, 19], segmentsForTarget[2][1], segmentsForTarget[2][2])
          segmentsForTarget[3] = ([10, 15, 2, 17], segmentsForTarget[3][1], segmentsForTarget[3][2])
      elif nb_players < 7:
          segmentsForTarget[0] = ([9, 5, 12], segmentsForTarget[0][1], segmentsForTarget[0][2])
          segmentsForTarget[1] = ([1, 18, 4], segmentsForTarget[1][1], segmentsForTarget[1][2])
          segmentsForTarget[2] = ([7, 16, 19], segmentsForTarget[2][1], segmentsForTarget[2][2])
          segmentsForTarget[3] = ([6, 10, 15], segmentsForTarget[3][1], segmentsForTarget[3][2])
          segmentsForTarget[4] = ([3, 17, 2], segmentsForTarget[4][1], segmentsForTarget[4][2])
          segmentsForTarget[5] = ([14, 11, 8], segmentsForTarget[5][1], segmentsForTarget[5][2])

      # gestion de l'affichage du segment
      self.show_hit = True
      self.firstStart = True

   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self,players,actual_round,actual_player,player_launch):
        return_code = 0

        self.player_launch = player_launch

        self.display.specialbg = 'bg_robin_drink.jpg'

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0 and self.firstStart:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.log("ERROR","Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0

            #change background
            self.display.display_background('bg_robin_drink.jpg')

            self.firstStart = False

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,2):
                players[actual_player].columns.append(['','int'])

            hits = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
            segments = {}
            self.segmentsOpponents = []
            self.segmentsRamdom = []
            self.segmentsPlayer = []
            # define segments for opponents
            for i in range (0,NbSegmentsForOpponents) :
                h = random.randint(0,len(hits)-1)
                self.segmentsOpponents.append(hits[h])
                segments['S'+str(hits[h])]='green'
                segments['D'+str(hits[h])]='green'
                segments['T'+str(hits[h])]='green'
                hits.pop(h)


            # define segments for opponents randomly
            for i in range (0,NbSegmentsForRandom) :
                h = random.randint(0,len(hits)-1)
                self.segmentsRamdom.append(hits[h])
                segments['S'+str(hits[h])]='blue'
                segments['D'+str(hits[h])]='blue'
                segments['T'+str(hits[h])]='blue'
                hits.pop(h)

            # define segments for current player
            for i in range (0,NbSegmentsForPlayer) :
                h = random.randint(0,len(hits)-1)
                self.segmentsPlayer.append(hits[h])
                segments['S'+str(hits[h])]='red'
                segments['D'+str(hits[h])]='red'
                segments['T'+str(hits[h])]='red'
                hits.pop(h)


        #show opponents choosing targets
        if player_launch == 2 :
            #mode random
            if self.random:
                hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                for p in players :
                    old = segmentsForTarget[p.ident]
                    targets = []
                    h = random.randint(0,len(hits)-1)
                    targets.append(hits[h])
                    hits.pop(h)
                    h = random.randint(0,len(hits)-1)
                    targets.append(hits[h])
                    hits.pop(h)
                    if len(players)<7 :
                        h = random.randint(0,len(hits)-1)
                        targets.append(hits[h])
                        hits.pop(h)
                    elif len(players)<5 :
                        h = random.randint(0,len(hits)-1)
                        targets.append(hits[h])
                        hits.pop(h)
                    segmentsForTarget[p.ident] = (targets,old[1],old[2])

            segments = {}
            for i,p in enumerate(players) :
                for sft in segmentsForTarget[i][0] :
                    segments['S'+str(sft)]=segmentsForTarget[i][1]
                    segments['D'+str(sft)]=segmentsForTarget[i][1]
                    segments['T'+str(sft)]=segmentsForTarget[i][1]

        # show segments led
        segmentsAsStr = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
        self.rpi.set_target_leds(segmentsAsStr)

        return return_code

   # Function launched when the  put player button before having launched all his darts
   def early_player_button(self,players,actual_player,actual_round):
        # Jump to next player by default
        return_code=1

        players[actual_player].score+=1
        self.show_message('player',players[actual_player],1)

        return return_code


   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        return_code = 0
        self.show_hit = False

        self.display.sound_for_touch(hit) # Touched !

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D' :
            multi = 2
        if hit[:1] == 'T' :
            multi = 3

        # test DB : all opponents drink
        if hit[1:] == 'B' :
            for p in players:
                if p.ident != actual_player :
                    p.score+=multi
            self.show_message('all',players[actual_player],multi)
            return_code = 4

        elif player_launch == 1 :
            self.currentMulti = multi

            # an opponent have to drink
            if int(hit[1:]) in self.segmentsOpponents :
                self.show_message('targetOpponent',players[actual_player],multi,delay = 3000)

            # a random opponent have to drink
            elif int(hit[1:]) in self.segmentsRamdom :
                op = self.random_opponent(players, actual_player)
                players[op].score += multi
                self.show_message('opponent', players[op], multi)
                return_code = 4

            # the player have to drink
            elif int(hit[1:]) in self.segmentsPlayer :
                players[actual_player].score += multi

                self.show_message('player', players[actual_player], multi)
                return_code = 4

            # pass, no penalty
            else :
                self.show_message('pass',players[actual_player],multi)
                return_code = 4
        else :
            if multi > self.currentMulti :
                self.currentMulti = multi

            # choosing opponent dart
            opponentHitted = False
            for i,p in enumerate(players) :
                if int(hit[1:]) in segmentsForTarget[i][0] :
                    p.score+=self.currentMulti
                    opponentHitted = True
                    self.show_message('opponent',p, self.currentMulti)

            if not opponentHitted :
                self.show_message('pass',players[actual_player], self.currentMulti)
                return_code = 4

        # Check for end of game (no more rounds to play)
        if (player_launch == self.nb_darts or return_code==4)and actual_round >= self.max_round and actual_player == len(players)-1:
          bestscoreid = -1
          bestscore = 10000
          for player in players:
             if player.score < bestscore:
                bestscore = player.score
                bestscoreid = player.ident
          self.winner = bestscoreid
          return_code = 3

        return return_code

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
   # Refresh In-game screen
   #
   def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       # do not show the table scores
      ClickZones = {}

      # Clear
      self.display.screen.fill( (0,0,0) )
      # background image
      self.display.display_background('bg_robin_drink_back')

      pos_x = (self.display.res['x'] - self.targetH) / 2
      pos_y = (self.display.res['y'] - self.targetH) / 2

      self.display.display_image(self.display.file_class.get_full_filename('robin_drink/robin_target', 'images'), pos_x, pos_y, self.targetH, self.targetH, True, False, False)

      if self.player_launch == 1 :
          for s in self.segmentsOpponents :
            self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/G{s}', 'images'), pos_x, pos_y, self.targetH, self.targetH, True, False, False)
          for s in self.segmentsRamdom :
            self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/B{s}', 'images'), pos_x, pos_y, self.targetH, self.targetH, True, False, False)
          for s in self.segmentsPlayer :
            self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/R{s}', 'images'), pos_x, pos_y, self.targetH, self.targetH, True, False, False)
      else :
          for player in players :
            for s in segmentsForTarget[player.ident][0] :
               self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/{segmentsForTarget[player.ident][2]}{s}', 'images'), pos_x, pos_y, self.targetH, self.targetH, True, False, False)

      for player in players :
        selected = (1 if player.ident == actual_player else 0)
        self.show_player_name(player, Colors.Colors.get(segmentsForTarget[player.ident][1], 'color-black'), selected)


      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
          return ClickZones

      self.display.update_screen()

      return [ClickZones]

   ###############
   # show the selection of a random player
   #
   def random_opponent(self, players, actual_player) :

      # list to random without actual player
      pls = []
      for j in range(0, len(players)) :
        if j != actual_player :
          pls.append((players[j], j))

      o = random.randint(0, len(pls) - 1)

      self.display.play_sound('robin_random')

      nb = 24 + random.randint(1, len(self.target_order))
      seg = 1   #random.randint(1, len(self.target_order)]
      p = 0
      for i in range(0, nb - 1):
        self.show_player_name(pls[p][0], (0, 0, 0), 2)

        self.display.display_image(self.display.file_class.get_full_filename('robin_drink/robin_target', 'images'), self.display.res['x'] / 2 - self.targetH/2 , self.display.res['y'] / 2 - self.targetH/2, self.targetH, self.targetH, True, False, False)
        self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/R{self.target_order[seg % 20]}', 'images'), self.display.res['x'] / 2 - self.targetH/2 , self.display.res['y'] / 2 - self.targetH/2, self.targetH, self.targetH, True, False, False)

        self.display.update_screen(rect=(self.display.res['x'] / 2 - self.targetH / 2 , self.display.res['y'] / 2 - self.targetH / 2, self.targetH, self.targetH))

        pygame.time.wait(30)
        self.show_player_name(pls[p][0], (0, 0, 0), 0)

        seg = seg + 1
        p = (p + 1) % len(pls)
      return pls[o][1]

    ###############
   # show player name
   #
   def show_player_name(self, player, color, selected) :

      self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/robin_player_sel{selected}', 'images'), self.pos[player.ident][0], self.pos[player.ident][1], self.bw, self.bh, True, False, False)
      self.display.blit_text( f"{player.name}  : {player.score}", self.pos[player.ident][0], self.pos[player.ident][1], self.bw, self.bh, color=color)
      self.display.update_screen(rect=(self.pos[player.ident][0], self.pos[player.ident][1], self.bw, self.bh))

    ###############
   # show message on screen
   #
   def show_message(self,typeMessage,player,multi,delay = 4000,refreshbackground = True) :

      if refreshbackground :
          self.display.display_background('bg_robin_drink_back')

      message = 'rien a dire...'
      numImg=random.randint(1,6)

      if typeMessage == 'opponent' :
          message = self.display.lang.translate('robin-opponent')
          self.display.play_sound('robin_opponent')
      if typeMessage == 'targetOpponent' :
          message = self.display.lang.translate('robin-targetOpponent')
          self.display.play_sound('robin_targeted')
      elif typeMessage == 'player' :
          message = self.display.lang.translate('robin-player')
          self.display.play_sound('robin_player')
      elif typeMessage == 'all' :
          message = self.display.lang.translate('robin-all')
          self.display.play_sound('robin_bull')
          numImg = 0
      elif typeMessage == 'pass' :
          message = self.display.lang.translate('robin-pass')
          self.display.play_sound('robin_pass')

      glasses = f"{multi} {self.display.lang.translate('robin-glasses') if multi>1 else self.display.lang.translate('robin-glass')}"
      message = message.replace('#drink#',glasses).replace("#PlayerName#",player.name)

      x = self.display.res['x'] / 6
      y = self.display.res['y'] / 5 * 2
      w = self.display.res['x'] * 2 / 3
      h = self.display.res['y'] / 5

      self.display.display_image(self.display.file_class.get_full_filename('robin_drink/robin_box', 'images'), x, y - h / 3, w, h + h * 2 / 3, True, False, False)
      self.display.display_image(self.display.file_class.get_full_filename(f'robin_drink/robin_img_{numImg}', 'images'), x - h / 3, y + h / 2, h, h * 2, True, False, False)

      self.display.blit_text(message.split("\n")[0], x, y, w, h / 2, color=(0, 0, 0))
      self.display.blit_text(message.split("\n")[1], x, y + h / 2, w, h / 2, color=(30, 0, 0))

      self.display.update_screen()

      pygame.time.wait(delay)
