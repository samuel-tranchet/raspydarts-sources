# -*- coding: utf-8 -*-
"""
Game by LaDite
"""

import random
from include import cplayer
from include import cgame

#
LOGO = 'Balltrap.png' # Background image - relative to images folder
HEADERS = ['PL1', 'PL2', '-', '-', '-', 'BULL', '-'] # Columns headers - Must be a string
#OPTIONS = {'Time':'500', 'Repetition': 10} # Dictionnay of options
OPTIONS = {'theme': 'default', 'Time': 500} # Dictionnay of options
NB_DARTS = 3
GAME_RECORDS = {'Score': 'DESC', 'Reached Score': 'DESC', 'Hits': 'DESC'}

class CPlayerExtended(cplayer.Player):
    """
    Extended Player class
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        #The score the player has to hit
        self.actual_hit = 1
        self.next = 0
        self.targets_list = []
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    """
    balltrap game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.options = options
        self.nb_players = nb_players
        #  Get the maxiumum round number
        # For rpi
        self.rpi = rpi
        self.dmd = dmd

        self.max_round = 12
        self.time = int(options['Time'])
        self.tirsrestant = 3
        #self.repetition = int(options['Repetition'])
        self.repetition = 10

        self.bull = False
        self.first = True
        
    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        After eah row : valid launch ? winner ? ...
        """

        play_hit = False
        players[actual_player].add_dart(actual_round, player_launch, hit)

        return_code = 0
        self.infos = ''
        # Reactive le compte à rebours
        self.first = True

        '''
        touche le plateau lors de la 2eme fleche 
        donne 1 points
        active l option Bulls et donne 1 tirs dans celui ci
        '''

        if self.bull and hit == 'SB':
            players[actual_player].score += 2
            self.display.play_sound('pan-cloche')
        elif self.bull and hit == 'DB':
            players[actual_player].score += 3
            self.display.play_sound('pan-cloche')
        elif hit in self.targets_list:
            #self.tirsrestant = 3
            self.display.play_sound('pan-touche')
            self.infos += f"Player {players[actual_player].name}, your score was {players[actual_player].score}{self.lf}"
            self.infos += f"at round {actual_round}{self.lf} You add to touch {self.targets_list}{self.lf}"
            self.infos += f"and you hit {hit}{self.lf}"

            ### voir si necessaire
            players[actual_player].increment_hits(hit)

            if actual_round in (3, 6, 9, 12):
                if self.left == 2 and \
                        hit == self.targets_list[0] and hit == self.targets_list[1] \
                        or hit == self.targets_list[1] and hit == self.targets_list[3] \
                        or hit == self.targets_list[4] and hit == self.targets_list[5] \
                        or hit == self.targets_list[6] and hit == self.targets_list[7]:
                    players[actual_player].score += (3 - player_launch) * 4
                    self.bull = True
                    self.left = 0
                    players[actual_player].columns[0] = ('B', 'str')
                else:
                    players[actual_player].score += 2
                    self.left -= 1
                    if self.left == 1:
                        # On enleve le bon plateau
                        if hit == self.targets_list[0]:
                            self.targets_list.pop(0)
                            self.drop = 'master'
                        else:
                            self.drop = 'opposite'
                            self.targets_list.pop(1)

                    elif self.left == 0:
                        self.bull = True
            else:
                players[actual_player].score += (3 - player_launch)
                players[actual_player].columns[0] = ('B', 'str')
                self.bull = True

        elif player_launch == 1:
            self.display.play_sound('pan-rate')
        elif player_launch == 2:

            self.display.play_sound('pan-rate')
            if not self.bull:
                self.bull = False
                # Penality : Next player !
                self.first = True
                # Force return code to -& in order to check if this is the last dart
                # of last round of last player
                return_code = -1
        elif player_launch == 3:
            self.display.play_sound('pan-rate')
        
        players[actual_player].increment_hits(hit)
        self.tirsrestant -= 1

        ### affiche ou pas le nb de tirs dans bull
        if self.bull:
            players[actual_player].columns[5] = (self.tirsrestant, 'int')
        else:
            players[actual_player].columns[5] = ('0', 'int')
            
        if play_hit:
            if super().play_show(players[actual_player].darts, hit, play_special=True):
                self.display.sound_for_touch(hit) # Play hit sound

        # Last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and ((player_launch == self.nb_darts and return_code <= 1) or return_code == -1):
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += "Here is a winner"
                return_code = 3
            else:
                self.infos += "No winner"
                return_code = 2
        if return_code == -1:
            return_code = 1

        # Update Score, darts count and Max score possible
        players[actual_player].columns[0] = (players[actual_player].actual_hit, 'int')

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        self.logs.log("DEBUG", self.infos)

        return return_code

    def post_round_check(self, players, actual_round, actual_player):

        if actual_round >= self.max_round and actual_player == self.nb_players - 1:
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            return self.winner
        else:
            return -2

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Before each throw - update screen, display score, etc...
        """
        return_code = None
        self.infos = ''

        ### affiche ou pas le nb de tirs dans bull
        if self.bull:
            players[actual_player].columns[5] = (self.tirsrestant, 'int')
        else:
            players[actual_player].columns[5] = ('0', 'str')
    
        # First round, first player, first dart
        if player_launch == 1 and actual_round == 1 and actual_player == 0 and self.first:
            for player in players:
                # DETERMINE LE CHIFFRE DE DEPART
                start = random.choice(self.target_order)
                player.goals = self.target_order[::]
                player.next = random.randint(0, 19)
                player.columns[0] = (f'{player.goals[player.next]}', 'str')
                player.reset_darts()
                player.reset_rounds(self.max_round)

        if player_launch == 1 and self.first:
            # Compte à rebours

            self.display.message('321', int(1000 / min(actual_round, 3)), None, 'middle', 'big')
            # joue son POULL
            self.display.play_sound('pull', wait_finish=True)
            # for rounds 3/6/9/12
            self.left = 2

            self.iteration = 1
            self.offset = random.randint(-5, 5)

        if not self.first:
            players[actual_player].next += 1
            if players[actual_player].next >= len(self.target_order):
                players[actual_player].next = 0
            self.iteration += 1
            #if self.iteration > self.repetition:
            #    self.first = 1
            #    return 0

        if player_launch == 1:
            self.tirsrestant = 3
            self.bull = False

        if self.bull:
            #classic round, asked target touched : bull's mode
            players[actual_player].columns[0] = ('B' , 'str')
            players[actual_player].columns[1] = ('', 'str')
        elif actual_round in (3, 6, 9, 12):
            next_index = players[actual_player].next
            next_target = players[actual_player].goals[next_index]
            opposite = players[actual_player].goals[(20 + 2 * self.offset - next_index) % 20]

            if self.left == 2:
                # Pour initialiser les 2 cibles
                self.targets_list = [f'{mult}{value}' for mult in ['S', 's', 'D', 'T'] for value in [next_target, opposite]]

                players[actual_player].columns[0] = (f'{next_target}', 'str')
                players[actual_player].columns[1] = (f'{opposite}', 'str')
            elif self.drop == 'opposite':
                self.targets_list = [f'{mult}{next_target}' for mult in ['S', 's', 'D', 'T']]

                players[actual_player].columns[0] = (f'{next_target}', 'str')
                players[actual_player].columns[1] = ('', 'str')
            else:
                self.targets_list = [f'{mult}{opposite}' for mult in ['S', 's', 'D', 'T']]

                players[actual_player].columns[0] = ('', 'str')
                players[actual_player].columns[1] = (f'{opposite}', 'str')
        else:
            # Classic round, asled target not touched yet
            players[actual_player].columns[1] = ('', 'str')
            players[actual_player].columns[0] = (f'{players[actual_player].goals[players[actual_player].next]}', 'str')
            players[actual_player].actual_hit = players[actual_player].goals[players[actual_player].next]
            self.targets_list = [f'{mult}{players[actual_player].goals[players[actual_player].next]}' for mult in ['S', 's', 'D', 'T']]

        if not self.bull:
            # Return S20#green|D20#red|T20#blue
            self.rpi.set_target_leds('|'.join([f'{value}#{self.colors[0]}' \
                    for value in self.targets_list]))
        else:
            self.rpi.set_target_leds(f'SB#{self.colors[0]}|DB#{self.colors[0]}')

        if self.first:
            self.first = False

        return return_code

    def check_winner(self, players):
        """
        Last round : who is the winner ?
        """
        deuce = False
        best_score = -1
        best_player = -1
        for player in players:
            if player.score > best_score:
                best_score = player.score
                deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = -1
        return best_player

    def early_player_button(self, players, actual_player, actual_round):
        """
        Pushed Player Early
        """

        return_code = 1
        self.first = True
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += rf"Current winner is Player {self.winner}"
                return_code = 3
            else:
                return_code = 2
        return return_code

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh players' stats
        """

        for player in players:
            player.stats['Score'] = player.score
            player.stats['Reached Score'] = player.actual_hit
            player.stats['Hits'] = player.get_total_hit()
