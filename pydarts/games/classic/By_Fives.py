# -*- coding: utf-8 -*-
# Game by ... poilou !
"""
Game by Poilou : By Five
"""
import collections
import random

from include import cplayer
from include import cgame

LOGO = 'By_Fives.png'
HEADERS = ['D1', 'D2', 'D3', 'Check', '', '', 'Rnd']
OPTIONS = {'theme': 'default', 'winscore': 5, 'score51': False, 'max_round': 20}
NB_DARTS = 3
GAME_RECORDS = {'Score': 'DESC'}

class CPlayerExtended(cplayer.Player):
    """
    Extended player class
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident , nb_columns, interior)
        self.pre_play_score = None
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    By Five game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS # Total darts the player has to play
        self.options = options
        self.max_round = int(options['max_round'])
        # GameRecords is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS
        # For rpi
        self.rpi = rpi

        self.infos = ''
        self.winner = None
        self.winscore = int(options['winscore'])
        if options['score51']:
            self.score51 = True
            self.winscore = 51
        else:
            self.score51 = False
        self.valid = True

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

        if player_launch == 1:
            players[actual_player].reset_darts()
            self.valid = True

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            for player in players:
                # Init score
                player.score = 0

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for _ in range(0, 7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

        if player_launch == 3:
            targ = []
            for mult in ['S', 'D', 'T']:
                if mult == 'S':
                    multiplier = 1
                elif mult == 'D':
                    multiplier = 2
                else:
                    multiplier = 3

                for number in range(1,22):
                    if number == 21:
                        if multiplier == 3:
                            continue
                        number = 25

                    if self.mod_by_5(players[actual_player].round_points + number * multiplier):
                        if number == 25:
                            number = 'B'
                        targ.append(f'{mult}{number}#{self.colors[0]}')
            self.rpi.set_target_leds('|'.join(targ))
        else :
            self.rpi.set_target_leds('')

        # Print debug output
        self.logs.log("DEBUG", self.infos)
        return return_code

    def pnj_score(self, players, actual_player, level, player_launch):
        """
        Compute pnj score
        """

        letters = 'SDT'
        value = random.randint(1,20)
        multi = ''.join(random.choice(letters) for _ in range(1))
        bull = random.randint(0,100)
        if 85 < bull <= 95:
            return 'SB'
        if bull > 95:
            return 'DB'
        return f'{multi}{value}'

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """

        handler = self.init_handler()
        check = False
        score = self.score_map[hit]

        players[actual_player].round_points += score

        if player_launch == 3:
            checkpoints = self.mod_by_5(players[actual_player].round_points)
            if checkpoints:
                if self.score51:
                    if players[actual_player].score + players[actual_player].round_points / 5 <= self.winscore:
                        score = players[actual_player].round_points / 5
                        players[actual_player].score += score
                        check = True
                    else:
                        score = 0
                        self.display.message(['Score too high !!'], None, None, 'middle', 'big')
                else:
                    check = True
                    players[actual_player].score += 1
                    score = 1
                players[actual_player].columns[3] = ('check-mark', 'image')
            else:
                players[actual_player].columns[3] = ('cross-mark', 'image')

            if players[actual_player].score == self.winscore:
                self.infos = "Game should be over\n"
        players[actual_player].columns[player_launch - 1] = (self.score_map[hit], 'int') ###(score, 'int')

        players[actual_player].add_dart(actual_round, player_launch, hit, check=check, score=score)

        # Change table displayed
        players[actual_player].columns[6] = (players[actual_player].round_points, 'int')

        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Check last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            handler['return_code'] = 2

        #Check if there is a winner
        winner = self.check_winner(players)
        self.infos = f"Check winner module was run. Winner reports {winner}{self.lf}"
        if winner is not None:
            self.infos += f"player {winner} wins !{self.lf}"
            self.winner = winner
            handler['return_code'] = 3
        else:
            handler['show'] = (players[actual_player].darts, hit, False)
            handler['sound'] = hit

        return handler

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        In case of miss dart
        If 51 option is activated, round is unavaiable
        """
        if self.score51:
            self.valid = False

    def mod_by_5(self,score):
        """
        Return True if score is divisible by 5
        """
        return score % 5 == 0

    def check_winner(self, players):
        """
        Method to check if there is a winnner
        """
        #Find the better score
        for player in players:
            if player.score == self.winscore:
                return player.ident
        return None
