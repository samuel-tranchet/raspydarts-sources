# -*- coding: utf-8 -*-
'''
Game by LB : Shangau
'''

from copy import deepcopy# For backupTurn
from include import cplayer
from include import cgame

#
LOGO = 'Shanghai.png'
HEADERS = ['HIT', 'MAX', '-', '-', '-', '-', '-']
OPTIONS = {'theme': 'default', 'max_round': 7, 'Master': False, 'Points': False}
NB_DARTS = 3
GAME_RECORDS = {'Score': 'DESC', 'Reached Score': 'DESC', 'Hits': 'DESC'}

class CPlayerExtended(cplayer.Player):
    '''
    Extend the basic player
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        #The score the player has to hit
        self.actual_hit = 0
        self.targets_list = []
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    '''
    Shangai game clsas
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS # Total darts the player has to play
        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        # For Raspberry
        self.rpi = rpi
        self.options = options
        self.master = options['Master']
        self.points = options['Points']

        self.m_list = []

        self.infos = ''
        self.winner = None

    def save_turn(self, players):
        '''
        Create Backup Properies Array
        '''
        try:
            self.previous_backup = deepcopy(self.backup)
        except: # pylint: disable=bare-except
            self.infos += "No previous turn to backup."
            self.infos += "You cannot use BackUpTurn since you threw no darts"
        self.backup = deepcopy(players)
        self.infos += "Score Backup."

    def check_shangai(self, darts):
        '''
        Check Shangai
        '''
        if self.master:
            return [darts[0][0], darts[1][0], darts[2][0]] == ['S', 'D', 'T'] \
                and darts[0][1:] == darts[1][1:] \
                and darts[0][1:] == darts[2][1:]
        else:
            return sorted([darts[0][0], darts[1][0], darts[2][0]]) == ['D', 'S', 'T'] \
                and darts[0][1:] == darts[1][1] \
                and darts[0][1:] == darts[2][1:]

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Post dart check
        '''

        check = False
        score = 0

        handler = self.init_handler()

        if hit in self.targets_list:
            check = True
            score = self.score_map.get(hit)
            players[actual_player].increment_hits(hit)
            self.infos += f"Player {actual_player} :{self.lf}"
            self.infos += f"    your score was {players[actual_player].score}{self.lf}"
            players[actual_player].score += score
            self.infos += f"    hit a {players[actual_player].get_touch_type(hit)}{self.lf}"
            self.infos += f"    your score is now {players[actual_player].score}"
            self.infos += f"    you have now to hit {players[actual_player].actual_hit}{self.lf}"

        elif self.master:
            # Missed and ( master or not points )
            # => next player
            handler['return_code'] = 1

        players[actual_player].add_dart(actual_round, player_launch, hit, check=check, score=score)

        if player_launch == 3 and self.check_shangai(players[actual_player].darts):
            self.infos += f"Victory of player {players[actual_player].ident} !{self.lf}"
            self.winner = players[actual_player].ident
            handler['return_code'] = 3
        elif player_launch == 3:
            # Check actual winnner
            self.winner = -1
            if actual_round == self.max_round and actual_player == self.nb_players - 1:
                self.winner = self.check_winner(players)

            if self.winner == -1 and self.play_show(players[actual_player].darts, hit):
                if check:
                    handler['sound'] = hit
                else:
                    handler['sound'] = 'plouf'
        else:
            self.winner = -1
            if check:
                handler['sound'] = hit
            else:
                handler['sound'] = 'plouf'

        self.infos += f"self.winner={self.winner}{self.lf}"
        self.infos += f"player_launch={player_launch}{self.lf}"

        if self.winner != -1:
            self.infos += f"Current winner is Player {self.winner}{self.lf}"

        # Last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts) and handler['return_code'] == 0:
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            if self.winner != -1 and self.points:
                self.infos += "Here is a winner"
                handler['return_code'] = 3
            else:
                self.infos += "No winner"
                handler['return_code'] = 2

        # Update Score, darts count and Max score possible
        max_score = self.check_max(player_launch + 1, actual_round, \
                players[actual_player].actual_hit, players[actual_player].score)
        players[actual_player].columns[0] = (players[actual_player].actual_hit, 'int')
        players[actual_player].columns[1] = (max_score, 'int', 'game-green')

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Print debug infos
        self.logs.log("DEBUG", self.infos)

        return handler

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Before each throw - update screen, display score, etc...
        '''
        self.infos = ''

        if player_launch == 1:
            players[actual_player].reset_darts()

            if players[actual_player].actual_hit == 20:
                players[actual_player].actual_hit = 'B'
                self.infos += "now B"
            else:
                players[actual_player].actual_hit += 1
                self.infos += f"now {players[actual_player].actual_hit}"

            self.save_turn(players)

            # Update Score
            for player in players:
                player.columns[0] = (player.actual_hit, 'int')
                player.reset_rounds(self.max_round)

            if self.master:
                self.m_list = ['S']
            else:
                self.m_list = ['S', 'D', 'T']
        elif player_launch == 2 and self.master:
            self.m_list = ['D']
        elif player_launch == 3 and self.master:
            self.m_list = ['T']
        else:
            try:
                self.m_list.remove(players[actual_player].darts[-1][0])
            except: # pylint: disable=bare-except
                self.logs.log("DEBUG", "already hit")

        # Compte S18, D18
        self.targets_list = [f'{mult}{players[actual_player].actual_hit}' for mult in self.m_list]

        max_score = self.check_max(player_launch, actual_round, \
                players[actual_player].actual_hit, players[actual_player].score)
        players[actual_player].columns[1] = (max_score, 'int', 'game-green')

        self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                for key in self.targets_list]))

        # For further code cleaning
        # Return 18$|D18$
        return (self.targets_list, None, None)

    def check_winner(self, players):
        '''
        Method to check WHO is the winnner
        '''
        deuce = False
        best_score = -1
        best_player = -1
        for player in players:
            self.logs.log("DEBUG", f"{player.name} : {player.score}")
            if player.score > best_score:
                best_score = player.score
                deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = -1
        self.logs.log("DEBUG", f"best player is {best_player}")
        self.logs.log("DEBUG", f"deuce is {deuce}")

        if deuce:
            self.infos += f"There is a score deuce ! Two people have {best_score}{self.lf}"
            higher_hit = -1
            best_player = -1
            for player in players:
                if player.score == best_score:
                    if player.actual_hit > higher_hit:
                        best_player = player.ident
                        higher_hit = player.actual_hit
                    elif player.actual_hit == higher_hit:
                        self.infos += f"There is also a hit deuce ! Two people have {higher_hit}"
                        higher_hit = player.actual_hit
                        best_player = -1
        return best_player

    def check_max(self, player_launch, actual_round, actual_hit, actual_score):
        '''
        Search MAX possible score for this player
        '''
        max_score = actual_score
        darts_left = 25 - actual_round * 3 - player_launch
        # Bull special case
        if actual_hit == 'B':
            actual_hit = 21
        for i in range(0, darts_left):
            if actual_hit + i == 21:
                max_score += 50
            else:
                max_score += (actual_hit + i) * 3
        return max_score

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Pushed Player Early
        '''
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += f"Current winner is Player {self.winner}"
                return 3
            return 2
        return 1

    def refresh_stats(self, players, actual_round):
        '''
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        '''
        for player in players:
            player.stats['Score'] = player.score
            player.stats['Reached Score'] = player.actual_hit
            player.stats['Hits'] = player.get_total_hit()
