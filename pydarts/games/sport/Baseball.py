# -*- coding: utf-8 -*-
"""
Game by LaDite - jeu base sur le castle de david
"""

"""

---------------------- RESTE A FAIRE

- remettre option tour max 9 et option egalite = false

"""

from include import cplayer
from include import cgame
import random
import subprocess

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': 9, '7eme_manche': False, 'noequal': True, 'team': False}

# Background image - relative to images folder - Name it like the game itself
LOGO = 'Baseball.png' # Background image
# Columns headers - Better as a string

HEADERS = ['*', ' ', 'D1', 'D2', 'D3', '', 'BASE'] # Columns headers - Must be a string

NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}

def check_players_allowed(nb_players):
    """
    Return the player number max for a game.
    """
    return nb_players <= 4

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
      self.home = 0
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record] = '0'
      self.columns[6] = ['baseball_image0', 'image']

class Game(cgame.Game):
    """
    Class of the real game
    """
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

      # gestion de l'affichage du segment
      self.show_hit = True

      self.septieme = options['7eme_manche']
      self.noequal = options['noequal']

      self.winner = None

      self.base = 0
      self.nb_touche = 0
      self.egalite = 'ko'

   # Actions done before each dart throw - for example, check if the player is allowed to play
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0
        self.infos = ''
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.log("ERROR", "Handicap failed : {}".format(e))
            for player in players:
                # Init score
                player.score = 0
                player.base_occupee = 0

### AFFICHE LE MESSAGE AU DEBUT DU TOUR SI 7eme manche = True
        if self.septieme and actual_round == 7:
            self.display.message([self.display.lang.translate('Baseball-septieme')], 1000, None, 'middle', 'big')

        # Determine le segment du joueur et des advs
        if player_launch == 1:
            # segment du joueur choisi au hasard à chaque fléchette
            segments = []
            for i, player in enumerate(players):
                home = random.randint(1, 20)
                while home in segments:
                    home = random.randint(1, 20)
                player.home = home
                segments.append(home)
                # affiche le chiffre a toucher dans la premiere colonne
                player.columns[0] = (player.home, 'int')

            if actual_round == 1:
                players[actual_player].base_occupee = 0

            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            #Reset display Table
            players[actual_player].columns = []
            # Efface les colonne 1-7
            for i in range(0, 7):
                players[actual_player].columns.append(['', 'str'])

        # Determine la couleur des segments
        segments = []
        index = 0
        for player in players:
            # J'ajoute dans le tableau les valeurs : S12#green, D12#green, T12|#green, E12#green
            # green est un exemple. player.color est la couleur du joueur
            for multiplier in ('S', 'D', 'T', 'E'):
                segments.append(f'{multiplier}{player.home}#{player.color}')

        # Ajout des SB/DB
        segments.append(f'SB#{players[actual_player].color}')
        segments.append(f'DB#{players[actual_player].color}')

        # Construction de la chaine S12#green|D12#green|T12|#green|E12#green|SB#green|DB#green
        self.rpi.set_target_leds('|'.join(segments))

        # Display stats
        players[actual_player].columns[0] = (players[actual_player].home, 'int')
        image_bb = f'baseball_image{players[actual_player].base_occupee}'
        players[actual_player].columns[6] = [image_bb, 'image']

        return return_code


    def early_player_button(self, players, actual_player, actual_round):

        if self.noequal and player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:

            bestscore = 2  ### JUSTE POUR TEST - modifier par le score d un joueur ou autre
            for player in players:
                ### AVEC EGALITE
                if player.score == bestscore:
                    self.infos += 'egalité - manche supplémentaire'
                    #self.egalite = 'ok'
                else:
                    ### PAS D EGALITE
                    self.infos += 'pas d egalite - fin de partie'
                    bestscoreid = -1
                    bestscore = -1
                    for player in players:
                        if player.score > bestscore:
                            bestscore = player.score
                            bestscoreid = player.ident
                    self.winner = bestscoreid
                    return_code = 3

            return return_code

### FIN DE PARTIE (ET OPTION NOEQUAL = FALSE)
        if not self.noequal and player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            self.infos += 'avec ou sans egalite - fin de partie'
            bestscoreid = -1
            bestscore = -1
            for player in players:
                if player.score > bestscore:
                    bestscore = player.score
                    bestscoreid = player.ident
            self.winner = bestscoreid
            return_code = 3

        return return_code


    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):

        return_code = 0

        self.show_hit = True

        self.display.sound_for_touch(hit) # Touched !

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1

        # stock the segment hitted
        #players[actual_player].columns[player_launch + 1] = (hit[1:], 'int')
        players[actual_player].columns[player_launch + 1] = [hit, 'txt']

        # test multiplicateur
        multiplier, value = self.split_key(hit, multiplier=True)

### JOUEUR TOUCHE LE BULLS (OK)
        if hit == 'SB':
            players[actual_player].increment_hits(hit)
            ### AJOUTE UN BONUS DE 1 POINT SUPPLEMENTAIRE POUR LE SUPER HOMERUN
            temporaire = players[actual_player].base_occupee + 1
            players[actual_player].score = (players[actual_player].score + temporaire)
            players[actual_player].base_occupee = 0

            self.infos += f'valeur temporaire (bull) : {temporaire}'

            self.show_hit = False
            self.display.play_sound('baseball_homerun')

            ### 0 à 3 bases occupée(sà
            if 1 <= temporaire <= 4:
                self.video_player.play_video(self.display.file_class.get_full_filename(f'baseball/homerun{temporaire}', 'videos'))

            ### RE-INITIALISE LE NOMBRE DE BASES DU JOUEUR
            image_bb = f'baseball_image{players[actual_player].base_occupee}'
            players[actual_player].columns[6] = [image_bb, 'image']

        elif hit == 'DB':
            players[actual_player].increment_hits(hit)
            ### AJOUTE UN BONUS DE 2 POINTS SUPPLEMENTAIRES POUR LE SUPER HOMERUN
            temporaire = players[actual_player].base_occupee + 2
            players[actual_player].score = (players[actual_player].score + temporaire)
            players[actual_player].base_occupee = 0

            self.infos += f'valeur temporaire (bull) : {temporaire}'

            self.show_hit = False
            self.display.play_sound('baseball_super_homerun')

            ### 0 à 3 bases occupée(sà
            if 2 <= temporaire <= 5:
                self.video_player.play_video(self.display.file_class.get_full_filename(f'baseball/super_homerun{temporaire - 1}', 'videos'))

            ### RE-INITIALISE LE NOMBRE DE BASES DU JOUEUR
            image_bb = f'baseball_image{players[actual_player].base_occupee}'
            players[actual_player].columns[6] = [image_bb, 'image']
        else:
            ### JOUEUR TOUCHE SON SEGMENT (OK)
            for i, player in enumerate(players):
                if i == actual_player and player.home == int(value):
                    players[actual_player].base_occupee += multiplier
                    self.infos += 'base occupee : {players[actual_player].base_occupee}'
                    players[actual_player].increment_hits(hit)
                    self.show_hit = False
                    self.display.play_sound('baseball_batte')
                    self.display.play_sound('baseball_base_acquise')

                    if 1 <= players[actual_player].base_occupee <= 3:
                        self.video_player.play_video(self.display.file_class.get_full_filename(f'baseball/base{players[actual_player].base_occupee}_acquise', 'videos'))

                    elif players[actual_player].base_occupee > 3:
                        temporaire = (players[actual_player].base_occupee - 3)
                        players[actual_player].score = players[actual_player].score + temporaire
                        players[actual_player].base_occupee = players[actual_player].base_occupee - temporaire

                        self.infos += f'valeur temporaire : {temporaire}'
                        self.display.play_sound('baseball_points_gagne')

                        ### 1 POINT
                        if 1 <= temporaire <= 3:
                            self.video_player.play_video(self.display.file_class.get_full_filename(f'baseball/score{temporaire}', 'videos'))

### JOUEUR TOUCHE LE SEGMENT D UN ADVS (OK)
                if i != actual_player and player.home == int(value):
                    player.base_occupee -= multiplier
                    # Pour ne pas descendre en dessous de 0
                    player.base_occupee = max(player.base_occupee, 0)

                    ### RE-INITIALISE LES BASES DE L ADVERSAIRE
                    if player.base_occupee >= 0:
                        self.show_hit = False
                        self.display.play_sound('baseball_joueur_out')
                        self.video_player.play_video(self.display.file_class.get_full_filename('baseball/runner_out', 'videos'))

### SEPTIEME MANCHE (si joueur ne touche pas son segment 1x sur la volee, son score est divise par 2)
                if i == actual_player and players[actual_player].home != int(value):
                    if self.septieme and actual_round == 7:

                        self.infos += f'self.septieme : {self.septieme}'
                        self.nb_touche += 1
                        self.infos += f'touche : (self.nb_touche)'
                        if self.nb_touche == 3:
                            self.display.play_sound('baseball_balle_ratee')
                            self.video_player.play_video(self.display.file_class.get_full_filename('baseball/strike', 'videos'))
                            players[actual_player].score = int((players[actual_player].score / 2))
                            self.nb_touche = 0

                image_bb = f'baseball_image{player.base_occupee}'
                player.columns[6] = [image_bb ,'image']

        self.logs.log("DEBUG", self.infos)
        return return_code

    def check_winner(self, players):
        """
        Method to identify the winner, in case
        """
        bestscore = -1
        return_code = -1
        for player in players:
            ### AVEC EGALITE
            if player.score == bestscore:
                self.winner = None
                return_code = 2
            elif player.score > bestscore:
                bestscore = player.score
                self.winner = player.ident
                return_code = 3

        return return_code

    def post_round_check(self, players, actual_round, actual_player):
        """
        In case of "Early player button" pressed on last dart of last player round of last round
        Return id of winner of -1 if None
        """
        self.logs.log("DEBUG", f"Post round : actual_round={actual_round} / self.max_round={self.max_round} / actual_player={actual_player}")

        if actual_round < self.max_round:
            return -2

        winner = self.check_winner(players)
        if winner == 2:
            if self.noequal:
                self.max_round += 1
                self.display.message([self.display.lang.translate('Baseball-egalite')], 1000, None, 'middle', 'big')
                # One more round
                return -2
            return -1

        return self.winner

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical formulas used to calculate stats. Refreshed after every launch
        for player in players:
        """
        player.stats['Points Per Round'] = player.avg(actual_round)

    def display_segment(self):
        """
        Set if a message is shown to indicate the hit segment
        """
        return self.show_hit
