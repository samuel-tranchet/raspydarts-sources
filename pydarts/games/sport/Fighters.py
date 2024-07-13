# -*- coding: utf-8 -*-
# Game by David !
######
from include import cplayer
from include import cgame
import random

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': 20, 'number_of_lives': 15, 'points':False}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Fighters.png' # background image
# Columns headers - Better as a string
HEADERS = ['D1', 'D2', 'D3', '', 'Hit', '', 'PPR']
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round': 'DESC'}

def check_players_allowed(nb_players):
   """
   Return the player number max for a game.
   """
   return nb_players in (2, 3, 4, 5)

class CPlayerExtended(cplayer.Player):
   """
   Extend the basic player
   """
   def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)

      self.character = 0
      self.targets = []
      self.lives = 0
      self.segments = []
      self.alive = True
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record]='0'

class Game(cgame.Game):
   """
   Class of the real game
   """
   def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
      super().__init__(display, game, nb_players, options, config, logs,rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players

      self.options = options
      self.points = options['points']
      #  Get the maximum round number
      self.max_round = int(options['max_round'])
      # GameRecords is the dictionnary of stats (see above)
      self.game_records = GAME_RECORDS
      #  Get the maxiumum round number
      self.lives = int(options['number_of_lives'])

   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

        # gestion de l'affichage du segment
        self.show_hit = True

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.log("ERROR", f"Handicap failed : {e}")
            for player in players:
                # Init score
                player.score = 0

                if self.points :
                    print('dans if self.points true')
                    self.lives = 300
                else :
                    self.lives = int(self.options['number_of_lives'])
                # nb lives    
                player.lives = self.lives
                player.alive = True
            #change background
            self.display.display_background('bg_fighters')

            # random character defined
            characters = []
            for player in players:
                if self.display.file_class.get_full_filename(f'fighters/{player.name}-1', 'images') is not None:
                    player.character = player.name
                else :
                    character = random.randint(1, 8)
                    while character in characters :
                        character = random.randint(1, 8)
                    player.character = f'j{character}'
                    characters.append(character)

        # Each new player
        if player_launch == 1:
            players[actual_player].segments = ['__','__','__']
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            # change all others players hitbox
            medic = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
            for player in players:
                player.targets.clear()
                if actual_player != player.ident and player.lives > 0:
                    hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                    for _ in range (0, 3) :
                        header = random.randint(0, len(hits) - 1)
                        player.targets.append(hits[header])
                        if hits[header] in medic :
                            medic.remove(hits[header])
                        hits.pop(header)

            # set medic hitbox of the actual player
            h = random.randint(0, len(medic) - 1)
            players[actual_player].targets.append(medic[h])

        # this player is game over
        if not players[actual_player].alive :
            return_code  = 4
        else :
            # Display target color of players
            segments = {}
            blinks = {}
            for player in players:
                if player.ident == actual_player:
                    color = 'green'
                    segments[f'S{player.targets[0]}'] = str(color)
                    segments[f'D{player.targets[0]}'] = str(color)
                    segments[f'T{player.targets[0]}'] = str(color)
                    segments[f'E{player.targets[0]}'] = str(color)
                else:
                    for header in player.targets:
                        color = 'red'
                        if segments.get(f'S{header}', None) is not None \
                                or blinks.get(f'S{header}', None) is not None:
                            blinks[f'S{header}'] = str(color)
                            blinks[f'D{header}'] = str(color)
                            blinks[f'T{header}'] = str(color)
                            blinks[f'E{header}'] = str(color)
                            if segments.get(f'S{header}', None) is not None:
                                segments.pop(f'S{header}')
                                segments.pop(f'D{header}')
                                segments.pop(f'T{header}')
                                segments.pop(f'E{header}')
                        else:
                            segments[f'S{header}'] = str(color)
                            segments[f'D{header}'] = str(color)
                            segments[f'T{header}'] = str(color)
                            segments[f'E{header}'] = str(color)

            segmentsAsStr = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
            self.rpi.set_target_leds(segmentsAsStr)
            self.rpi.set_target_leds_blink("|".join("{}#{}".format(*s) for s in blinks.items()))

        return return_code

   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        """
        Post dart actions
        """
        return_code = 0

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1

        # stock the segment hitted
        players[actual_player].columns[player_launch - 1] = (hit[1:], 'int')
        players[actual_player].segments[player_launch - 1] = hit


        multi = self.get_hit_unit(hit)

        # test SB ou DB
        if hit == 'SB' :
            for player in players :
                if player.ident != actual_player and player.lives > 0:
                    if self.points :
                         player.lives -= self.score_map[hit] ###multi
                    else: 
                         player.lives -= 1
            if self.points :
                players[actual_player].score += self.score_map[hit]  ###(len(players))*5 
            else: 
                players[actual_player].score+=(len(players))*1
                
            self.video_player.play_video(self.display.file_class.get_full_filename('fighters/fighters_bull', 'videos'))
            self.show_hit = False
        elif hit == 'DB' :
            for player in players :
                if player.ident!=actual_player and player.lives > 0:
                    if self.points :
                         player.lives -= self.score_map[hit] ###multi
                    else: 
                         player.lives -= 2
                         
            if self.points :
                players[actual_player].score += self.score_map[hit]    ####(len((players))*5) *2
            else: 
                players[actual_player].score+=(len(players))*2
                
            self.video_player.play_video(self.display.file_class.get_full_filename('fighters/fighters_bull', 'videos'))
            self.show_hit = False
        else :
            # check d'un segment medic
            if int(hit[1:]) in players[actual_player].targets :
                if self.points :
                    players[actual_player].lives += self.score_map[hit] ###multi
                else: 
                    players[actual_player].lives += multi
                    
                if players[actual_player].lives > self.lives :
                     players[actual_player].lives = self.lives
                self.display.play_sound('fighters_medic')
                self.video_player.play_video(self.display.file_class.get_full_filename('fighters/fighters_medic', 'videos'))
                self.show_hit = False

            # check d'un segment adversaire
            playerHitted = False
            for index, player in enumerate(players):
                if index != actual_player and int(hit[1:]) in player.targets :
                    if self.points :
                        players[actual_player].score += self.score_map[hit] ###multi
                        player.lives -= self.score_map[hit] ###multi
                    else: 
                        players[actual_player].score += multi
                        player.lives -= multi
                    players[actual_player].score += multi
                    players[actual_player].increment_hits(hit)
                    playerHitted = True
                    self.show_hit = False
                    
            if playerHitted :
                self.video_player.play_video(self.display.file_class.get_full_filename(f'fighters/fighters_hit{multi}', 'videos'))
            else:
                self.display.sound_for_touch(hit) # Touched !


        # test for a player KO
        for player in players:
            if player.lives <= 0 and player.alive:
                player.alive = False
                if self.points :
                         players[actual_player].lives += 30   ### test : ajout 1/10 des points de vies du depart a la place d augmenter le score
                else: 
                         players[actual_player].score += 5
                self.video_player.play_video(self.display.file_class.get_full_filename('fighters/fighters_ko', 'videos'))

        winner = self.check_winner(players, actual_round, player_launch, actual_player)
        if winner > -1:
            self.video_player.play_video(self.display.file_class.get_full_filename('fighters/fighters_victory', 'videos'))
            self.winner = winner
            return 3
        return return_code

   def post_round_check(self, players, actual_round, actual_player):
        check_winner = self.check_winner(players, actual_round, 3, actual_player)
        if check_winner >= 0:
            return check_winner
        if actual_round < self.max_round:
            return -2
        else:
            return -1

   def check_winner(self, players, actual_round, player_launch, actual_player):
        # test for a winner
        alive_players = []
        for player in players :
            if player.alive :
                alive_players.append(player.ident)

        # victory by KO
        if len(alive_players) == 1 :
            self.winner =  alive_players[0]
            players[self.winner].score += 100
            return self.winner

        elif len(alive_players) == 0 or (player_launch == self.nb_darts and \
                actual_round >= self.max_round and actual_player == self.nb_players - 1):
            # victory by points if all are ko or its the last turn
            bestscoreid = -1
            bestscore = 0
            for player in players:
                if player.score > bestscore:
                    bestscore = player.score
                    bestscoreid = player.ident
            return bestscoreid
        return -1

   def refresh_stats(self, players, actual_round):
      """
      Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical formulas used to calculate stats. Refreshed after every launch
      """
      for player in players:
         player.stats['Points Per Round'] = player.avg(actual_round)

   def display_segment(self):
       """
       Set if a message is shown to indicate the segment hitted !
       """
       return self.show_hit

   def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnlogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
      """
      Refresh In-game screen
      """
      # do not show the table scores
      ClickZones = {}

      # Clear
      self.display.screen.fill( (0, 0, 0) )
      # background image
      self.display.display_background('bg_fighters')
      colorset = self.display.colorset

      # show players pictures and state
      #scale img 368 * 670
      scalex = 368 * self.display.res['x'] / 1920
      scaley = 670 * self.display.res['y'] / 1080

      y = self.display.res['y'] / 2 - scaley / 2
      marge = int((self.display.res['x'] - len(players) * scalex) / (len(players) + 1))

      x = marge
      for i,p in enumerate(players):
          # find the good character picture to show
          if actual_player == p.ident :
              level = 5
          elif p.lives > self.lives - (self.lives / 4) :
              level = 1
          else :
              level = int(5 - ((p.lives // (self.lives / 5)) + 1))

          self.display.display_image(self.display.file_class.get_full_filename(f'fighters/{p.character}-{level}', 'images'),x, y, scalex, scaley, True, False, False)
          self.logs.log("DEBUG", f"character img loaded : {p.character}-{level}.png")

          if i == actual_player :
              self.display.blit_text(p.name, x, y + scaley, scalex, scaley / 4, color=colorset['fighters-actual-player'])
              self.display.display_image(self.display.file_class.get_full_filename('fighters/fighters_medic', 'images'),x + scalex / 2 - scalex / 6, y + scaley * 2 / 3, scalex / 3, scalex / 3, False, False, False)
              self.display.blit_text(str(p.targets[0]),x + scalex / 2 - scalex / 6, y + scaley * 2 / 3 + 20, scalex / 3, scalex / 3, color=colorset['fighters-medic'])
          elif p.alive :
              self.display.blit_text(p.name, x, y + scaley, scalex ,scaley / 4, color=colorset['fighters-alive-player'])
              self.display.display_image(self.display.file_class.get_full_filename('fighters/hit', 'images'),x, y, scalex / 3, scalex / 3, True, False, False)
              self.display.blit_text(str(p.targets[0]),x, y,scalex / 3,scalex / 4, color=colorset['fighters-targets'])
              self.display.display_image(self.display.file_class.get_full_filename('fighters/hit', 'images'),x + scalex - scalex / 3, y, scalex / 3, scalex / 3, True, False, False)
              self.display.blit_text(str(p.targets[1]),x + scalex - scalex / 3, y, scalex / 3, scalex / 4, color=colorset['fighters-targets'])
              self.display.display_image(self.display.file_class.get_full_filename('fighters/hit', 'images'),x + scalex / 2 - scalex / 6, y, scalex / 3, scalex / 3, True, False, False)
              self.display.blit_text(str(p.targets[2]),x + scalex / 2 - scalex / 6, y, scalex / 3,scalex / 4, color=colorset['fighters-targets'])
          elif colorset['fighters-dead-player'] is not None:
              self.display.blit_text(p.name, x, y + scaley, scalex ,scaley / 4, color=colorset['fighters-dead-player'])

          # show lives and score
          self.display.blit_text(str(p.lives),x + scalex / 5, y + scaley - scalex / 4, scalex / 3, scalex / 4, color=colorset['fighters-scores'])
          self.display.blit_text(str(p.score),x + scalex - scalex / 3, y + scaley - scalex / 4, scalex / 3, scalex / 4, color=colorset['fighters-scores'])

          if not p.alive :
              self.display.display_image(self.display.file_class.get_full_filename('fighters/fighters_ko', 'images'),x, y, scalex, scaley, True, False, False)

          x += scalex + marge

      # show round state
      self.display.blit_rect(self.display.res['x']/8 - scalex/2, 0, scalex,y*2/3, (0, 0, 0), Alpha=150)
      self.display.blit_text(f"{self.display.lang.translate('round')} {actual_round} / {max_round}" ,self.display.res['x']/8 - scalex/2,0,scalex, y/3, color=colorset['fighters-round'])

      # show segments hitted on the round
      self.display.blit_text(" / ".join(players[actual_player].segments) ,self.display.res['x']/8 - scalex/2,y/3,scalex,y/3, color=colorset['fighters-darts'])

      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
          return ClickZones

      self.display.update_screen()

      return [ClickZones]
