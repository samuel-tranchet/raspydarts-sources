# -*- coding: utf-8 -*-
"""
game by LaDite : Golf
"""
#######
import time
from include import cplayer
from include import cgame
#
#
LOGO = 'Golf.png' # Background image
HEADERS = ['*', 'D1', 'D2', 'D3', '', 'MRQ', 'PAR'] # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'nine_holes': False, 'bulls': True, 'master': False}
NB_DARTS = 3
### voir avec olivier ce que je dois mettre pour afficher le PAR dans les statistiques
GAME_RECORDS = {'Score': 'DESC', 'Par': 'DESC'}


class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

        self.contrat_done = False

class Game(cgame.Game):
    """
    GOLF class game
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS # Total darts the player has to play
        self.options = options
        self.game_records = GAME_RECORDS
        # For rpi
        self.rpi = rpi

        self.winner = None
        self.infos = ''

        if options['nine_holes']:
            self.max_round = 9
        else:
            self.max_round = 18

        if options['master']:
            self.master = True
            self.bulls = True
        else:
            self.master = False
            self.bulls = options['bulls']

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
        self.infos += ""
        self.rpi.set_target_leds('')
        # Init
        if player_launch == 1:
            players[actual_player].contrat_done = False # First Dart, reset contract to NOT DONE.

            self.save_turn(players)

            # Clear table for current player
            for i in range(1, 4):
                players[actual_player].columns[i] = ('', 'txt', 'game-grey')
### Vide la colonne MARQUE en debut de tour
            players[actual_player].columns[5] = ('', 'txt', 'game-grey')

        leds = []
        tour = actual_round
        #Allume les leds correspondant au chiffre a jouer SELON la variable TOUR
        if actual_round == tour:
            self.rpi.set_target_leds('')
            text = str(tour)
            leds = f'S{tour}#{self.colors[0]}|D{tour}#{self.colors[0]}|T(tour)#{self.colors[0]}|SB#{self.colors[0]}|DB#{self.colors[0]}'

        if player_launch == 1:
            for player in players:
                player.columns[0] = (text, 'txt', 'game-text')

        self.rpi.set_target_leds(leds)
        return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Is the contract done ?
        """

        self.infos = ""
        if player_launch == 1:
            players[actual_player].contrat_done = False

        multiplier, value = self.split_key(hit)
        score = self.score_map.get(hit)

        if multiplier == 'D':
            led_color = self.colors[0]
        elif multiplier == 'T':
            led_color = self.colors[1]
        else:
            led_color = self.colors[2]

        # affiche le chiffre a viser dans la colonne JOUEUR
        players[actual_player].columns[player_launch] = (str(hit), 'txt', f'game-{led_color}')
        play_sound = True
        players[actual_player].contrat_done = False

        # Default
        hit = 'double_bogey'
        points = 5

        if value == str(actual_round) and not hit in ['SB', 'DB']:
            if multiplier == 'D':
                hit = 'eagle'
                points = 1
            elif multiplier == 'T':
                hit = 'birdie'
                points = 2
            else:
                hit = 'bogey'
                points = 4

        elif hit in ['SB', 'DB']:
            if self.master and hit == 'DB':
                hit = 'condor'
                points = - 1
            elif self.bulls and not self.master:
                hit = 'albatros'
                points = 0

        super(Game, self).SendTextToDmd(self.display.lang.translate(f'Golf-{hit}'), tempo=3, sens=None, iteration=None)
        self.video_player.play_video(self.display.file_class.get_full_filename(f'golf/{hit}', 'videos'))
        players[actual_player].marque = points
        players[actual_player].columns[5] = [players[actual_player].marque, 'int']
        players[actual_player].contrat_done = True
        play_sound = False

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        #Check actual winnner if last round reached
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            self.winner = self.check_winner(players)
            if self.winner is not None:
                self.infos += f"Current winner is Player {self.winner}{self.lf}"
                return 3
            # Last round
            if actual_player == self.nb_players - 1 and player_launch == int(self.nb_darts):
                self.infos += f"Last round reached ({actual_round}){self.lf}"
                return 2

        if players[actual_player].contrat_done and player_launch == 3:
            players[actual_player].score += players[actual_player].marque
            players[actual_player].par = players[actual_player].score - (actual_round * 3)
            players[actual_player].columns[6] = [players[actual_player].par, 'int']

        # Display Recapitulation Text
        self.logs.log("DEBUG", self.infos)
        return 0

    def check_winner(self, players):
        """
        Method to check WHO is the winnner
        """
        deuce = False
        best_score = 1000
        best_player = None
        for player in players:
            if player.score < best_score:
                best_score = player.score
                deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = None
        if deuce:
            self.infos += f"There is a score deuce ! Two people have {best_score}.{self.lf}"
            self.infos += f"No winner!{self.lf}"
            return None
        return best_player

    def early_player_button(self, players, actual_player, actual_round):
        """
        Function launched when the player put player button before having launched all his darts
        """
        # Jump to next player by default
        self.infos = "Pneu (or early player buttton) function\n"
        self.logs.log('DEBUG', f'actual_round={actual_round} / max_round={self.max_round} / contrat_done={players[actual_player].contrat_done}')

        # CONDITION SI JOUEUR NE TOUCHE RIEN
        if not players[actual_player].contrat_done:
            hit = 'double_bogey'

            self.logs.log('DEBUG', 'je suis dans la condiftion IF NOT PLAYERS[ACTUAL-PLAYER].CONTRAT..DONE')

            # contrat non reussi : penalite
            self.logs.log('DEBUG', 'contrat non reussi - appui sur next player (section early player button)')
            self.dmd.send_text(self.display.lang.translate(f'Golf-{hit}'), tempo=3, sens=None, iteration=None)
            self.video_player.play_video(self.display.file_class.get_full_filename(f'golf/{hit}', 'videos'))
            points = 5
            players[actual_player].marque = points
            players[actual_player].columns[5] = [players[actual_player].marque, 'int']
            #calcul score
            players[actual_player].score += players[actual_player].marque
            players[actual_player].par = players[actual_player].score - (actual_round * 3)
            players[actual_player].columns[6] = [players[actual_player].par, 'int']

            # Go te next player. Avoid multiple calls of miss_button method
            return 4
        else:
            self.logs.log('DEBUG', 'contrat reussi - 1 ou 2 fleches jouees')
            #self.infos += f"Bien joué Calhagan ! {self.jackpot} touches !{self.lf}"
            players[actual_player].score += players[actual_player].marque
            players[actual_player].par = players[actual_player].score - (actual_round * 3)
            players[actual_player].columns[6] = [players[actual_player].par, 'int']

        # Check actual winnner if last round reached
        if actual_round >= self.max_round:
            self.winner = self.check_winner(players)
            if self.winner is not None:
                self.infos += f"Current winner is Player {self.winner}{self.lf}"
            # Last round
            if actual_player == self.nb_players - 1:
                self.infos += f"Last round reached ({actual_round}){self.lf}"
                if self.winner is not None:
                    return 3
                return 2

        # Pas de gagnant, sauvegarde du score
        self.display.message([self.display.lang.translate('Golf-save')], 1000, None, 'middle', 'big')

        self.logs.log('DEBUG', self.infos)
        return 4

    def display_segment(self):
       """
       Set if a message is shown to indicate the segment hitted !
       """
       return False
