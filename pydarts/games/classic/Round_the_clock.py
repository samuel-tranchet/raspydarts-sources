# -*- coding: utf-8 -*-
'''
Game by LB
'''

import random
from include import cplayer
from include import cgame

#
LOGO = 'Round_the_clock.png' # Background image - relative to images folder
HEADERS = ['Hour', 'D1', 'D2', 'D3', '-', '-', '-'] # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'max_round': 7, 'Double': False, 'Triple': False, 'Bull': False, 'Numbers': False, 'Jump': False, 'Time': 0} # Dictionnay of options
NB_DARTS = 3
GAME_RECORDS = {'Score':'DESC', 'Reached Score':'DESC', 'Hits':'DESC'}

class CPlayerExtended(cplayer.Player):
    '''
    Extended Player class
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        #The score the player has to hit
        self.actual_hit = 1
        self.next = 0
        self.targets_list = []
        self.goals = []
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    '''
    Round the clock game class
    '''
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

        self.max_round = int(options['max_round'])
        self.double = options['Double']
        self.triple = options['Triple']
        self.bull = options['Bull']
        self.order = options['Numbers']
        self.jump = options['Jump']
        self.time = int(options['Time'])

        self.m_list = []

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        After eah row : valid launch ? winner ? ...
        '''

        play_hit = False

        handler = self.init_handler()
        score = 0
        self.infos = ''

        if hit in self.targets_list:
            check = True
            self.infos += f"Player {actual_player}, your score was {players[actual_player].score}{self.lf}"
            players[actual_player].increment_hits(hit)
            score = self.score_map.get(hit)
            players[actual_player].score += score

            # Delete from goals
            del players[actual_player].goals[players[actual_player].next]

            if self.jump and handler['return_code'] == 0:
                if hit.startswith('D') and len(players[actual_player].goals) > 0:
                    del players[actual_player].goals[players[actual_player].next]
                    play_hit = True
                    #players[actual_player].next += 1
                if hit.startswith('T'):
                    if len(players[actual_player].goals) > 0:
                        del players[actual_player].goals[players[actual_player].next]
                    if len(players[actual_player].goals) > 0:
                        del players[actual_player].goals[players[actual_player].next]
                    play_hit = True
                    #players[actual_player].next += 2
                self.infos += f'hit={hit}{self.lf}'
                self.infos += f'self.jump={players[actual_player].next}{self.lf}'
            if len(players[actual_player].goals) == 0:
                self.winner = players[actual_player].ident
                handler['return_code'] = 3
            else:
                handler['sound'] = hit
            players[actual_player].columns[player_launch] = ('check-mark', 'image')

        else:
            check = False
            handler['sound'] = 'plouf'
            handler['return_code'] = 0
            players[actual_player].columns[player_launch] = ('cross-mark', 'image')

        players[actual_player].add_dart(actual_round, player_launch, hit, check=check, score=score)

        if play_hit:
            handler['show'] = (players[actual_player].darts, hit, True)
            handler['sound'] = hit

        # Last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts) and handler['return_code'] == 0:
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += 'Here is a winner'
                handler['return_code'] = 3
            else:
                self.infos += 'No winner'
                handler['return_code'] = 2

        # Update Score, darts count and Max score possible
        players[actual_player].columns[0] = (f'{players[actual_player].actual_hit}', 'str')

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        self.logs.log('DEBUG', self.infos)

        return handler


    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Before each throw - update screen, display score, etc...
        '''
        self.infos = ''

        # First round, first player, first dart
        if player_launch == 1 and actual_round == 1 and actual_player == 0:
            for player in players:
                if self.order:
                    player.goals = [str(num) for num in range(1,21)]
                else:
                    player.goals = [target for target in self.target_order]
                if self.bull:
                    player.goals.append('B')
                player.columns[0] = (f'{player.goals[0]}', 'str')
                player.reset_rounds(self.max_round)

        if self.time > 0:
            players[actual_player].next += 1

        if players[actual_player].next >= len(players[actual_player].goals):
            players[actual_player].next = 0

        if player_launch == 1:
            players[actual_player].reset_darts()
            if actual_player == 0:
                # clean checks from previous round
                for player in players:
                    for dart in range(0, NB_DARTS):
                        player.columns[dart + 1] = (None, 'image')

        # Update Score
        players[actual_player].columns[0] = (f'{players[actual_player].goals[players[actual_player].next]}', 'str')

        #if self.time > 0 or self.jump:
        players[actual_player].actual_hit = players[actual_player].goals[players[actual_player].next]
        #else:
        #    players[actual_player].actual_hit = players[actual_player].goals[0]

        self.m_list = []
        if self.double or self.triple:
            if self.double:
                self.m_list.append('D')
            if self.triple:
                self.m_list.append('T')
        else:
            self.m_list.extend(['s', 'S', 'D', 'T'])

        self.targets_list = [f'{mult}{players[actual_player].goals[players[actual_player].next]}' for mult in self.m_list]

        # Return S20#green|D20#red|T20#blue
        self.rpi.set_target_leds('|'.join([f'{target}#{self.colors[0]}' for target in self.targets_list]))

        # For further code cleaning
        return None
        #return (self.targets_list, None, None)

    def pnj_score(self, players, actual_player, computer_level, player_launch):
        '''
        Compute PNJ Score according to compuer level

                       |           Rates           |
           Level       | Pneu  | Touch | Dbl | Tpl | Ngh |
          -------------+-------+-------+-----+-----+-----+
           2 : Noob    |   15  |  25%  | 12% | 16% | 50% |
           3 : Inter   |    1  |  55%  | 30% | 40% | 80% |
           4 : Pro     |    0  |  99%  | 30% | 98% | 99% |
        '''

        levels = [
            [25, 15, 12, 16, 50],
            [15, 25, 12, 16, 50],
            [ 1, 55, 30, 40, 80],
            [ 0, 99, 30, 98, 99],
            [ 0, 99, 30, 98, 99]
        ]

        if random.randint(0, 100) < levels[computer_level - 1][0]:
            return 'MISSDART'

        if random.randint(0, 100) < levels[computer_level - 1][1]:
            segment = players[actual_player].actual_hit
        elif random.randint(0, 100) < levels[computer_level - 1][4]:
            segment = self.neighbors[str(players[actual_player].actual_hit)][random.randint(0, 1)]
        else:
            segment = random.randint(1, 21)

        mult = random.randrange(100)
        if segment != 'B':
            if mult < levels[computer_level - 1][3]:
                score = f'T{segment}'
            elif mult < levels[computer_level - 1][2]:
                score = f'D{segment}'
            else:
                score = f'S{segment}'
        elif mult < levels[computer_level - 1][3]:
            score = 'DB'
        else:
            score = 'SB'

        return score


    def check_winner(self, players):
        '''
        Last round : who is the winner ?
        '''
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
        if deuce:
            self.infos += rf"/!\ There is a score deuce ! Two people have {best_score}\n"
            higher_hit = -1
            best_player = -1
            for player in players:
                if player.score == best_score:
                    if player.actual_hit > higher_hit:
                        best_player = player.ident
                        higher_hit = player.actual_hit
                    elif player.actual_hit == higher_hit:
                        self.infos += rf"/!\ There is also a hit deuce ! Two people have {higher_hit}\n"
                        higher_hit = player.actual_hit
                        best_player = -1
        return best_player


    def early_player_button(self, players, actual_player, actual_round):
        '''
        Pushed Player Early
        '''
        return_code = 1
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += rf"Current winner is Player {self.winner}"
                return_code = 3
            else:
                return_code = 2
        return return_code


    def refresh_stats(self, players, actual_round):
        '''
        Method to refresh players' stats
        '''
        for player in players:
            player.stats['Score'] = player.score
            player.stats['Reached Score'] = player.actual_hit
            player.stats['Hits'] = player.get_total_hit()
