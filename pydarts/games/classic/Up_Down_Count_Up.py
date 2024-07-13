# -*- coding: utf-8 -*-
"""
Game by ... David !
"""

from include import cplayer
from include import cgame

OPTIONS = {'theme': 'default', 'max_round': 10, 'penalty': 50, 'start_negative': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3
LOGO = 'Up_Down_Count_Up.png'
HEADERS = ['D1', 'D2', 'D3', '+/-', '', 'PPD', 'PPR']

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
    Up Down class game
    """
    # Like player_launch but not visible inside method early_player_button
    nb_darts_hit_in_turn = 0

    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)

        # Dictionary of stats and display order
        # For example : Points Per Darts and avg are displayed in descending order
        self.game_records = GAME_RECORDS
        # How many darts per player and per round ? Yes ! this is a feature :)
        self.nb_darts = NB_DARTS  # Total darts the player has to play
        # Background image - relative to images folder - Name it like the game itself
        self.logo = LOGO
        # Columns headers - Better as a string
        self.headers = HEADERS

        self.options = options
        # self.score_map.update({'SB':50})
        #  Get the maximum round number
        self.max_round = int(options['max_round'])
        #  penalty points for a missing dart
        self.penalty = int(options['penalty'])
        # start the game with a negative round
        self.negative = options['start_negative']

        self.winner = None

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
        if player_launch == 1:
            players[actual_player].reset_darts()

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")
            for player in players:
                # Init score
                player.score = 0
                player.reset_rounds(self.max_round)

        # Each new player
        if player_launch == 1:
            self.nb_darts_hit_in_turn = 0

            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for _ in range(0, 7):
                players[actual_player].columns.append(['', 'int'])

            # show the type of actual Round
            if self.is_positive_round(actual_round):
                self.display.message([self.display.lang.translate('UDCP-tourpos')], \
                        3000, 'blue', 'middle', 'huge')
                players[actual_player].columns[3] = ('+', 'string')
            else:
                self.display.message([self.display.lang.translate('UDCP-tourneg')], \
                        3000, 'red', 'middle', 'huge')
                players[actual_player].columns[3] = ('-', 'string')

        # Display stats
        if actual_round == 1 and player_launch == 1:
            players[actual_player].columns[5] = (0.0, 'int')
            players[actual_player].columns[6] = (0.0, 'int')
        else:
            players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
            players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')

        # Print debug output
        self.logs.log("DEBUG", self.infos)
        return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        handler = self.init_handler()

        self.nb_darts_hit_in_turn = player_launch

        # factor to add or substract points by the round type
        factor = -1
        if self.is_positive_round(actual_round):
            factor = 1
        score = self.score_map[hit] * factor

        players[actual_player].score += score
        # Keep total for this round
        players[actual_player].round_points += score
        players[actual_player].points += score

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)

        # Historize
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score,'int')

        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            bestscoreid = -1
            bestscore = -10000
            for player in players:
                if player.score > bestscore:
                    bestscore = player.score
                    bestscoreid = player.ident
            self.winner = bestscoreid
            handler['return_code'] = 3
        else:
            handler['show'] = (players[actual_player].darts, hit, True)
            handler['sound'] = hit

        return handler

    def early_player_button(self, players, actual_player, actual_round):
        """
        Function launched when the  put player button before having launched all his darts
        """
        # Jump to next player by default
        return_code = 1

        # darts_thrown for missing target
        players[actual_player].darts_thrown += (self.nb_darts - self.nb_darts_hit_in_turn)

        # substract penalty points if the round is a nagative round
        #if not self.is_positive_round(actual_round):
        score_penalty = (self.nb_darts - self.nb_darts_hit_in_turn) * self.penalty
        if score_penalty > 0:
            players[actual_player].score -= score_penalty
            players[actual_player].round_points -= score_penalty # Keep total for this round
            players[actual_player].points -= score_penalty #for ppd,ppr

        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
        self.refresh_stats(players, actual_round)

        # play penalty sound
        self.display.play_sound('penality')

        if actual_round >= self.max_round and actual_player == self.nb_players - 1:
            bestscoreid = -1
            bestscore = -10000
            for player in players:
                if player.score > bestscore:
                    bestscore = player.score
                    bestscoreid = player.ident
            self.winner = bestscoreid
            return_code = 3

        return return_code

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        Miss button
        """
        players[actual_player].columns[player_launch - 1] = ('MISS', 'str')
        players[actual_player].darts_thrown += 1
        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
        self.refresh_stats(players, actual_round)

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh player.stat - Adapt to the stats you want.
        hey represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)
            player.stats['Points Per Dart'] = player.show_ppd()

    def is_positive_round(self, actual_round):
        """
        detect the type of round (negative or positive)
        """
        return (actual_round % 2 == 1 and not self.negative) \
                or (actual_round % 2 == 0 and self.negative)
