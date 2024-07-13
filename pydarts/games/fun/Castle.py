# -*- coding: utf-8 -*-
# Game by David !
######
from include import cplayer
from include import cgame
import random
import subprocess

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': 20, 'number_of_lives': 15, 'mode_random': False}
# Background image - relative to images folder - Name it like the game itself
LOGO = 'Castle.png' # Background image
# Columns headers - Better as a string
HEADERS = ['#', 'PTS'] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round': 'DESC'}

def check_players_allowed(nb_players):
    '''
    Check number of players
    '''
    return nb_players <= 4

#Extend the basic player
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
      self.home = 0
      self.castleColor = 'None'
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record] = '0'

# Class of the real game
class Game(cgame.Game):
   def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
      super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players
      self.options = options
      #  Get the maximum round number
      self.max_round = int(options['max_round'])
      # GameRecords is the dictionnary of stats (see above)
      self.GameRecords = GAME_RECORDS
      #  Get the maxiumum round number
      self.lives = int(options['number_of_lives'])
      # gestion de l'affichage du segment
      self.show_hit = True

   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0
        castleColors = ['br', 're', 'gr', 'bl']
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.log("ERROR", "Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0
                # choose random castle color
                Player.castleColor = random.choice(castleColors)
                castleColors.remove(Player.castleColor)

            #change background
            self.display.display_background('Castle/background')


        # Each new player
        if player_launch==1:
            if (actual_round == 1 and player_launch == 1 and actual_player == 0) or self.options['mode_random'] == 'True' :
                # segment du joueur choisi au hasard en début de game
                segments = []
                for i, Player in enumerate(players):
                    home=random.randint(1, 20)
                    while home in segments :
                        home=random.randint(1, 20)
                    Player.home=home
                    segments.append(home)
                    Player.columns[0] = (Player.home, 'int')


            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 2):
                players[actual_player].columns.append(['', 'str'])


        # Display target color of player
        segments = {}
        for player in players :

            if player.castleColor == 'br':
                color = 'white' #black
            elif player.castleColor == 'bl':
                color = 'blue' #blue
            elif player.castleColor == 're':
                color = 'red' # red
            else:
                color = 'green' # green
            segments[f'S{player.home}'] = str(color)
            segments[f'D{player.home}'] = str(color)
            segments[f'T{player.home}'] = str(color)
            segments[f'E{player.home}'] = str(color)

        segmentsAsStr = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
        self.rpi.set_target_leds(segmentsAsStr)

        # Display stats
        if actual_round == 1 and player_launch == 1:
            players[actual_player].columns[0] = (players[actual_player].home, 'int')
            players[actual_player].columns[1] = (0, 'int')
        else :
            players[actual_player].columns[0] = (players[actual_player].home, 'int')
            players[actual_player].columns[1] = (players[actual_player].score, 'int')

        return return_code

   def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        return_code = 0

        self.show_hit = True

        self.display.sound_for_touch(hit) # Touched !

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1

        # stock the segment hitted
        #players[actual_player].columns[player_launch-1] = (hit[1:], 'int')

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D' :
            multi = 2
        if hit[:1] == 'T' :
            multi = 3

        # test SB ou DB pour le + / -
        if hit[1:] == 'B' :
            players[actual_player].score+=multi
            players[actual_player].increment_hits(hit)
            for i, Player in enumerate(players):
                if i != actual_player :
                   Player.score-=multi
                   if Player.score<0 :
                      Player.score = 0
            self.show_hit = False
            self.display.play_sound('castle_explosion')
            self.video_player.play_video(self.display.file_class.get_full_filename('castle/castle_bull', 'videos'))
        else :
            # check d'un segment valide
            for i, Player in enumerate(players):
                if i==actual_player and Player.home == int(hit[1:]) :
                    Player.score+=multi
                    players[actual_player].increment_hits(hit)
                    self.show_hit = False
                    self.display.play_sound('castle_up')
                    self.video_player.play_video(self.display.file_class.get_full_filename('castle/castle_up', 'videos'))

                if i != actual_player and Player.home == int(hit[1:]) :
                    Player.score-=multi
                    if Player.score<0 :
                        Player.score = 0
                    else :
                        self.show_hit = False
                        self.display.play_sound('castle_down')
                        self.video_player.play_video(self.display.file_class.get_full_filename('castle/castle_down', 'videos'))

        # test for a winner
        if  players[actual_player].score >= self.lives:
            self.winner =  players[actual_player].ident
            return_code = 3
            self.display.play_sound('castle_win')
            self.video_player.play_video(self.display.file_class.get_full_filename('castle/castle_win', 'videos'))
        elif player_launch == self.nb_darts and actual_round >= self.max_round and actual_player == len(players)-1:
            return_code = 2

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
   def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
      # do not show the table scores
      ClickZones = {}
      # Clear
      self.display.screen.fill(self.display.colorset['color-black'])

      # Background image
      self.display.display_background('Castle/background')

      # Game options
      self.display.display_rem_darts_compact(RemDarts, nb_darts)
      # Rounds
      self.display.new_display_round(players[actual_player], actual_round, max_round)

      print(f"positions={self.display.position}")
      for player in players:
          self.player_line(self.display, self.display.position[player.ident], actual_player, player)
          self.display_player_name(self.display, self.display.position[player.ident], actual_player, player)
          self.display_score(self.display, self.display.position[player.ident], player.home, player.score)

      # show header
      y = self.display.position[0] - self.display.line_height - self.display.margin
      for i in range(0, len(headers) ):
          txt = str(headers[i][:3])
          scaled = self.display.scale_text(txt, self.display.box_width, self.display.line_height)
          font = self.display.get_font(scaled[0])
          Y_txt = int(y + scaled[2])
          text = font.render(txt, True, self.display.colorset['game-text'])
          x_txt = int(self.display.margin + self.display.pn_size + self.display.box_width * i + scaled[1])
          self.display.blit_rect(self.display.margin + self.display.pn_size + self.display.box_width * i, y, self.display.box_width - self.display.margin, self.display.line_height, self.display.colorset['game-table'], False, False, self.display.alpha + 10)
          self.display.screen.blit(text, [x_txt, Y_txt])

      x_txt += self.display.box_width
      cy = self.display.box_height - self.display.line_height  - self.display.margin

      #show castles in prorecordess
      for player in players:
          if player.ident != actual_player :
              self.draw_castle(x_txt, cy, player, actual_player, len(players))
      self.draw_castle(x_txt, cy, players[actual_player], actual_player, len(players))

      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
          return ClickZones

      self.display.update_screen()

      return [ClickZones]

   #
   # Display the player castle
   #
   def draw_castle(self, cx, cy, player, actual_player, nb_players):
        cWidth = self.display.res['x'] - cx
        if player.ident == actual_player :
            scaleY = self.display.res['y'] / 2
            scaleX = 944 * (scaleY / 800)
            x = cx+ cWidth / 2 - scaleX / 2
            y = self.display.res['y'] - scaleY - 25
        elif player.ident == actual_player + 1 or (player.ident == 0 and actual_player == nb_players - 1): # pos right
            scaleY = self.display.res['y'] / 3
            scaleX = 944 * (scaleY / 800)
            x = self.display.res['x']- scaleX - 25
            y = cy + scaleY / 2 - scaleY / 6
        elif player.ident == actual_player - 1 or (player.ident == nb_players - 1 and actual_player == 0): # pos left
            scaleY = self.display.res['y'] / 3 * 0.9
            scaleX = 944 * (scaleY / 800)
            x = cx + 25
            y = cy + scaleY / 2 + scaleY / 6
        else: # pos back
            scaleY = self.display.res['y'] / 4
            scaleX = 944 * (scaleY / 800)
            x = cx + cWidth / 2 - scaleX / 2 - scaleX / 2
            y = cy

        # calculate the good picture to show
        if player.score == self.lives - 1:
            image_file = f'castle_{player.castleColor}_9'
        else :
            val = int(player.score // ( (self.lives - 2) / 7 )) + 1
            image_file = f'castle_{player.castleColor}_{val}'

        self.logs.log("DEBUG", "image_file {} for score {}".format(image_file, player.score))
        self.display.display_image(self.display.file_class.get_full_filename(f'Castle/{image_file}', 'images'), x, y, scaleX, scaleY, True, False, False, UseCache = False)


   #
   # Display score for given player
   #
   def display_score(self, display, posy, home, score):
        scoresize = int(self.display.res['x'] / 5)
        # self.box_width = int(self.res['x'] / 11.7)
        #
        xtxt = self.display.pn_size + self.display.box_width + self.display.box_width / 4
        scaled = self.display.scale_text(str(score), scoresize - self.display.margin * 2, self.display.line_height - self.display.margin * 2)
        font = self.display.get_font(scaled[0])
        # display home
        text = font.render(str(home), True, self.display.colorset['game-text'])
        self.display.screen.blit(text, [self.display.pn_size + self.display.margin * 4 , posy + scaled[2]])
        # display score
        text = font.render(str(score), True, self.display.colorset['game-text'])
        self.display.screen.blit(text, [xtxt + self.display.margin * 2, posy + scaled[2]])

   # Display name of the player if given, Player X otherwise
   #
   def display_player_name(self, display, y, actual_player, player):
        playername = player.name
        if playername is None:
            playername = f'Player {player.ident}'

        if player.castleColor == 'br':
            txtcolor = (255, 255, 255) #white
        elif player.castleColor == 'bl':
            txtcolor = (0, 0, 255) #blue
        elif player.castleColor == 're':
            txtcolor = (255, 0, 0) # red
        else:
            txtcolor = (0, 255, 0) # green
        #  Player name size depends of player name number of char (dynamic size)
        scaled = self.display.scale_text(playername, self.display.pn_size - 2 * self.display.margin, self.display.line_height)
        font = self.display.get_font( scaled[0])
        # Render the text. "True" means anti-aliased text.
        playernamex = self.display.margin * 2 + scaled[1]
        playernamey = y + scaled[2]
        text = font.render(playername, True, txtcolor)
        self.display.screen.blit(text, [playernamex, playernamey])

   #
   # This method fill background squares
   #
   def player_line(self, display, y, actual_player, player):
        if player.ident == actual_player:
            bgcolor = (218, 165, 32)
        else:
            bgcolor = (150, 150, 150)
        self.display.blit_rect(self.display.margin, y, self.display.pn_size - self.display.margin, self.display.line_height - self.display.margin, bgcolor)

        self.display.blit_rect(self.display.margin + self.display.pn_size , y, self.display.box_width - self.display.margin, self.display.line_height - self.display.margin, self.display.colorset['color-black'] )
        self.display.blit_rect(self.display.margin + self.display.pn_size + self.display.box_width, y, self.display.box_width * 1 - self.display.margin, self.display.line_height - self.display.margin, self.display.colorset['color-black'] )
