# -*- coding: utf-8 -*-
# Game by ... you !
########
from include import cplayer
from include import cgame
import time
import random

############
# Game Variables
############
#options = {'max_round': '7'}
#MODE AVEC OPTIONS
OPTIONS = {'theme': 'default', 'max_round': 7, 'nb_bonus_darts': 1}
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in descending order)
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Simon.png'
# Columns headers - Better as a string
HEADERS = ['1', '2', '3', '4', '5', '6', '7']

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Extend the basic players property with your own here
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    Extend the common Game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        ##############
        # VAR
        ##############
        # Dictionary of options in STRING format.
        # You can use any numeric value or 'True' or 'False', but in string format.
        # Don't put more than 10 options per game or you will experience display issues
        self.options = options
        # Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in descending
        # order)
        self.GameRecords = GAME_RECORDS
        # background image - relative to images folder - Name it like the game itself
        self.logo = LOGO
        # allow the game to stop raspydart color target
        self.game_is_ok_for_color = False #by Manu script.
        # Columns headers - Better as a string
        self.headers = HEADERS
        # self.score_map.update({'SB':50})
        #  Get the maximum round number
        self.max_round = int(options['max_round'])
        self.nb_bonus_darts = int(self.options['nb_bonus_darts'])

        # For rpi
        self.rpi = rpi

        self.segments = (
            (20, 1, 18, 4, 13),
            (6, 10, 15, 2, 17),
            (3, 19, 7, 16, 8),
            (11, 14, 9, 12, 5)
        )

        self.Colors = ('red', 'green', 'blue', 'yellow')

        self.scores = {}
        self.sequence_index = 0

        self.sequence = []
        self.Incsequence()

        self.light_segment = False

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)
            player.stats['Points Per Dart'] = player.show_ppd()

    def display_segment(self):
        return False

    def reset_leds(self):
        """
        Reset target's leds
        """
        for index in range(len(self.segments)):
            self.set_leds(index, 'black')

    def set_leds(self, pos, color, blink=False):
        strings = []
        for segment in self.segments[pos]:
            for mult in ('S', 'D', 'T'):
                strings.append(f"{mult}{segment}#{color}")
        s = '|'.join(strings)
        self.rpi.set_target_leds(s)
        if blink:
            self.rpi.event.publish('simon', s)
        else:
            self.rpi.event.publish('goal', s)

    def Incsequence(self):
        last = None
        if len(self.sequence) > 0:
            last = self.sequence[-1]
        while True:
            i = random.randint(0, len(self.segments) - 1)
            if last is None or i != last:
                break
        self.sequence.append(i)

    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):

        seq_len = self.scores[actual_player] + 1
        if player_launch == 1:
            time.sleep(1)
            for i in self.sequence[0:seq_len]:
                self.set_leds(i, self.Colors[i])
                time.sleep(0.5)
                self.reset_leds()

        return None

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            self.logs.log("DEBUG", 'RESET')
            self.reset_leds()

            #change background
            self.display.display_background('bg_simon')

        if not actual_player in self.scores:
            self.scores[actual_player] = 0

        if player_launch == 1:
            self.sequence_index = 0

        seq_len = self.scores[actual_player] + 1

        while len(self.sequence) < seq_len:
            self.Incsequence()

        #Gestion des options
        try:
            n = self.nb_bonus_darts
        except ValueError:
            n = 0
        self.nb_darts = seq_len + n

        self.logs.log("DEBUG", 'Player:{} Tour:{} Seq:{} Nb darts:{}'.format(actual_player, self.scores[actual_player], self.sequence, self.nb_darts))

        return 0
	
    def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        ret = 0
        if hit[1:] != 'B':
            pts = int(hit[1:])
        else:
            pts = None

        seq_len = self.scores[actual_player] + 1
        targets = self.segments[self.sequence[self.sequence_index]]

        finished = False

        self.logs.log("DEBUG", f'Launch:{player_launch} SeqLen:{seq_len}')
        self.logs.log("DEBUG", f'INDEX:{self.sequence_index} PTS:{pts} TARGETS:{targets} SEGMENTS:{self.segments}')

        if pts in targets:
            self.sequence_index += 1

            for index in range(len(self.segments)):
                if pts in self.segments[index]:
                    self.set_leds(index, self.Colors[index], True)
                    #time.sleep(1)
                    self.reset_leds()
                    break

            if self.sequence_index == seq_len:
                self.scores[actual_player] += 1
                players[actual_player].add_score(1)
                players[actual_player].columns[self.scores[actual_player] - 1] = ['/', 'txt']
                self.logs.log("DEBUG", 'FINI {}'.format(self.scores[actual_player]))
                # added by Manu script.
                if player_launch != self.nb_darts:
                    self.nb_darts = player_launch
                # end added by Manu script.
                ret = 4
                finished = True
        elif self.nb_darts - player_launch < seq_len - self.sequence_index:
            self.logs.log("DEBUG", 'ERR')
            ret = 1
            finished = True
        else:
            return -1

        # Check for end of game (no more rounds to play)
        if finished and actual_round >= self.max_round and actual_player == len(players)-1:
            winner = -1
            best_score = -1
            for player in players:
                if player.score > best_score:
                    best_score = player.score
                    winner = player.ident
            self.winner = winner
            ret = 3

        return ret
