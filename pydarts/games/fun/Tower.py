# -*- coding: utf-8 -*-
# Game by David !
######
from include import cplayer
from include import cgame
import random

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'dragon_hard': False}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Tower.png' # background image
# Columns headers - Better as a string
HEADERS = [ "#", "PTS" ] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}

def check_players_allowed(nb_players):
    '''
    Return the player number max for a game.
    '''
    return nb_players <= 6

#Extend the basic player
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
      self.home = 0
      self.questFlowersDone = False
      self.questCrownDone = False
      self.questDragonDone = False
      self.flower_segment = 0
      self.dragonSegments = [0,0,0]
      self.crownfloor = 0
      self.flowersNbHit = 0
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record]='0'

# Class of the real game
class Game(cgame.Game):
   def __init__(self, display, game, nb_players, options, config, Logs, rpi, dmd, video_player):
      super().__init__(display, game, nb_players, options, config, Logs, rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players
      # GameRecords is the dictionnary of stats (see above)
      self.game_records = GAME_RECORDS

      self.options = options
      self.dragon_hard = options['dragon_hard']

      self.max_round = 100
      #  max floors
      self.floors = 12

      self.nb_dartsHitInTurn = 0

      # gestion de l'affichage du segment
      self.show_hit = True

   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self,players,actual_round,actual_player,player_launch):
        return_code = 0

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.Logs.Log("ERROR","Handicap failed : {}".format(e))
            for player in players:
                # Init score
                player.score = 0

            #change background
            self.display.display_background('bg_tower')

            # Etage du diademe choisi au hasard en début de game
            for _,player in enumerate(players):
                player.crownfloor = random.randint(4, 10)
                player.home = random.randint(1, 20)

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for _ in range(0, 2):
                players[actual_player].columns.append(['', 'int'])

            # set dragon and flower segments
            hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
            hits.pop(players[actual_player].home - 1)
            h = random.randint(0,len(hits) - 1)
            players[actual_player].flower_segment = hits[h]
            hits.pop(h)
            h = random.randint(0,len(hits) - 1)
            d1 = hits[h]
            hits.pop(h)
            h = random.randint(0,len(hits) - 1)
            d2 = hits[h]
            hits.pop(h)
            h = random.randint(0,len(hits) - 1)
            d3 = hits[h]
            if self.dragon_hard:
                players[actual_player].dragonSegments = [d1, d2, d3]
            else :
                players[actual_player].dragonSegments = [d1, d2]
            players[actual_player].flowersNbHit = 0

            self.nb_dartsHitInTurn = 0


        # Display target color of player
        segments = {}
        if players[actual_player].score < self.floors :
            segments[f'S{players[actual_player].home}'] = str('green')
            segments[f'D{players[actual_player].home}'] = str('green')
            segments[f'T{players[actual_player].home}'] = str('green')

        if not players[actual_player].questFlowersDone :
            segments[f'S{players[actual_player].flower_segment}'] = str('blue')
            segments[f'D{players[actual_player].flower_segment}'] = str('blue')
            segments[f'T{players[actual_player].flower_segment}'] = str('blue')

        if not players[actual_player].questDragonDone :
            for segment in players[actual_player].dragonSegments :
                segments[f'S{segment}'] = str('red')
                segments[f'D{segment}'] = str('red')
                segments[f'T{segment}'] = str('red')

        if players[actual_player].crownfloor == players[actual_player].score and not players[actual_player].questCrownDone :
            for index in range(1, 21) :
                segments[f'D{index}'] = str('purple')
                segments[f'T{index}'] = str('purple')

        leds = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
        self.rpi.set_target_leds(leds)

        return return_code

   def early_player_button(self, players, actual_player, actual_round):
        """
        Function launched when the next player button before having launched all his darts
        """

        # darts_thrown for missing target
        players[actual_player].darts_thrown = self.nb_darts
        self.logs.log("DEBUG","nb_dartsHitInTurn : {}/{}".format(self.nb_dartsHitInTurn, self.nb_darts))

        players[actual_player].score -= self.nb_darts - self.nb_dartsHitInTurn
        players[actual_player].score = max(0, players[actual_player].score)
        self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_down', 'videos'))

        return 4

   def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        return_code = 0

        self.show_hit = False

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        self.nb_dartsHitInTurn+= 1

        # stock the segment hitted
        #players[actual_player].columns[player_launch-1] = (hit[1:],'int')

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D' :
            multi = 2
        if hit[:1] == 'T' :
            multi = 3

        # check quest crown
        if multi > 1 and players[actual_player].score == players[actual_player].crownfloor and not players[actual_player].questCrownDone:
            players[actual_player].questCrownDone = True
            self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_crown', 'videos'))
        # opponent down
        elif hit == 'SB' :
            for i, player in enumerate(players):
                if i != actual_player :
                   player.score -= 1
                   if player.score < 0:
                      player.score = 0
            self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_down', 'videos'))

        # cancel opponent quest
        elif hit == 'DB' :
            for i, player in enumerate(players):
                if i != actual_player :
                    if player.questFlowersDone:
                        player.questFlowersDone = False
                    elif player.questDragonDone:
                        player.questDragonDone = False
                    else :
                        # no quest -> down floors
                        player.score -= 2
                        if player.score < 0:
                            player.score = 0
            self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_dbull', 'videos'))

        # check quest flowers
        elif players[actual_player].flower_segment == int(hit[1:]) and not players[actual_player].questFlowersDone:
            players[actual_player].flowersNbHit += multi
            if players[actual_player].flowersNbHit >= 2:
                players[actual_player].questFlowersDone = True
                self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_flowers2', 'videos'))
            else :
                self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_flowers1', 'videos'))

        # check quest dragon
        elif int(hit[1:]) in players[actual_player].dragonSegments and not players[actual_player].questDragonDone:
            players[actual_player].dragonSegments.remove(int(hit[1:]))
            if len(players[actual_player].dragonSegments) == 0 :
                players[actual_player].questDragonDone = True
                self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_dragon2', 'videos'))
            else :
                self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_dragon1', 'videos'))

        # check segment home
        elif players[actual_player].home == int(hit[1:]) and players[actual_player].score < self.floors:
            players[actual_player].score += multi
            if players[actual_player].score > self.floors:
                players[actual_player].score = self.floors
            self.video_player.play_video(self.display.file_class.get_full_filename('tower/tower_up', 'videos'))
        else:
            self.show_hit = True
            self.display.sound_for_touch(hit) # Touched !


        # test for a winner
        if  players[actual_player].score >= self.floors and players[actual_player].questCrownDone and players[actual_player].questDragonDone and players[actual_player].questFlowersDone :
            self.winner =  players[actual_player].ident
            return_code = 3

            # calcul the score for the reorder players on the next game
            for player in players:
                if player.questFlowersDone :
                    player.score += 100
                if player.questDragonDone :
                    player.score += 100
                if player.questCrownDone :
                    player.score +=100

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
      self.display.screen.fill((0, 0, 0))
      # background image
      self.display.display_background('bg_tower')

      # show players pictures and state
      #scale img 507 * 1978
      boxW = self.display.res['x'] / (len(players) + 1)
      scaley = self.display.res['y'] * 3 / 4
      scalex = 507 * scaley / 1978
      x = boxW - scalex / 2

      txtH = 70 * self.display.res['y'] / 1080
      y = self.display.res['y'] - scaley - txtH

      for i,player in enumerate(players):
          # display quests dones for all players
          icow = txtH * 2 / 3
          self.display.blit_rect(x + scalex / 2, y + scaley - icow * 3 - 1, scalex / 2 + icow + 1, icow * 3 + 2, (20, 20, 20))

          self.display.display_image(self.display.file_class.get_full_filename('tower/flowers', 'images'), x + scalex, y + scaley - icow * 3, icow, icow, True, False, False)
          if player.questFlowersDone :
              self.display.display_image(self.display.file_class.get_full_filename('tower/quest_done', 'images'), x + scalex, y + scaley - icow * 3, icow, icow, True, False, False)

          self.display.display_image(self.display.file_class.get_full_filename('tower/dragon', 'images'), x + scalex, y + scaley - icow * 2, icow, icow, True, False, False)
          if player.questDragonDone :
              self.display.display_image(self.display.file_class.get_full_filename('tower/quest_done', 'images'), x + scalex, y + scaley - icow * 2, icow, icow, True, False, False)

          self.display.display_image(self.display.file_class.get_full_filename('tower/crown_1', 'images'), x + scalex, y + scaley - icow, icow, icow, True, False, False)
          if player.questCrownDone :
              self.display.display_image(self.display.file_class.get_full_filename('tower/quest_done', 'images'), x + scalex, y + scaley - icow, icow, icow, True, False, False)

          self.display.display_image(self.display.file_class.get_full_filename(f'tower/tower_{player.ident + 1}', 'images'), x, y, scalex, scaley, True, False, False)

          if i == actual_player :
              self.display.blit_text(player.name, x, y + scaley, scalex, txtH, color=(255, 255, 255))
              #show tower up segment (home)
              self.display.blit_text(str(players[actual_player].home), x + scalex / 2, y + scaley - txtH * 3 / 2, scalex / 3, txtH * 3 / 2, color=(255, 255, 255))
          else :
              self.display.blit_text(player.name, x, y + scaley, scalex, txtH, color=(150, 0, 0))

          #show the knights 137*192, step 109
          step = 105 * scaley / 1978
          ky = step * 2
          kw = 137 * ky / 192
          self.display.display_image(self.display.file_class.get_full_filename(f'tower/tower_knight{player.ident+1}', 'images'),x + scalex / 2 - kw, y + scaley - ky - player.score * step, kw, ky, True, False, False)
          self.display.display_image(self.display.file_class.get_full_filename('tower/tower_crown.png', 'images'), x + scalex / 2, y + scaley - kw / 6 - player.crownfloor * step, kw, kw / 3, True, False, False)

          x += boxW

      # show quests
      width = self.display.res['x'] / 3
      self.display.display_image(self.display.file_class.get_full_filename('tower/flowers', 'images'),0, 0, y, y, True, False, False)
      if players[actual_player].questFlowersDone:
          self.display.display_image(self.display.file_class.get_full_filename('tower/quest_done', 'images'),0, 0, y, y, True, False, False)
      else:
          if players[actual_player].flowersNbHit>0:
              self.display.blit_text(str(players[actual_player].flower_segment) ,y,0,y,y, color=(255,255,255))
          else:
              self.display.blit_text(f"{players[actual_player].flower_segment}/{players[actual_player].flower_segment}", y, 0, y, y, color=(255, 255, 255))

      self.display.display_image(self.display.file_class.get_full_filename('tower/dragon', 'images'),width, 0, y, y, True, False, False)
      if players[actual_player].questDragonDone:
          self.display.display_image(self.display.file_class.get_full_filename('tower/quest_done', 'images'),width, 0, y, y, True, False, False)
      else:
          self.display.blit_text('/'.join(str(x) for x in players[actual_player].dragonSegments), width + y, 0, width - y,y, color=(255 ,255 ,255))

      self.display.display_image(self.display.file_class.get_full_filename('tower/crown_1', 'images'), width * 3 - y * 2, 0, y, y, True, False, False)
      if players[actual_player].questCrownDone:
          self.display.display_image(self.display.file_class.get_full_filename('tower/quest_done', 'images'), width * 3 - y * 2, 0, y, y, True, False, False)
      else:
          self.display.blit_text(str(players[actual_player].crownfloor) ,width * 3 - y, 0, y, y, color=(255, 255, 255))

      if end_of_game:
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

      self.display.update_screen()

      return [ClickZones]

