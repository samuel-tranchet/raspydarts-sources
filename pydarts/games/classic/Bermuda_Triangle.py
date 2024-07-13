# -*- coding: utf-8 -*-
# Game by Cory Baumgart!
'''
Bermuda triange game
'''

######
import collections
import random
from include import cplayer
from include import cgame

LOGO = 'Bermuda_Triangle.png'
HEADERS = ['12', '-', '-', '-', '-', '-', '-']
OPTIONS = {'theme': 'default', 'Double_bull': False}
NB_DARTS = 3
GAME_RECORDS = {'Points Per Round':'DESC', 'Points Per Dart':'DESC'}

class CPlayerExtended(cplayer.Player):
    '''
    Extended player class
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.pre_play_score = None
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record]='0'

class Game(cgame.Game):
    '''
    Bermuda triange game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # game_records is the dictionnary of stats (see above)
        # For Raspberry
        self.raspberry = rpi
        self.game_records = GAME_RECORDS
        self.logo = LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS # Total darts the player has to play
        self.options = options

        # Number of round is ruled
        self.max_round = 13
        if not options['Double_bull']:
            self.doublebull = False
            self.score_map.update({'DB': 25})
            # One more round if double bull enabled
            self.max_round = 12
        else:
            self.doublebull = True

        self.infos = ''
        self.winner = None

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Actions done before each dart throw - for example, check if the player is allowed to play
        '''
        return_code = 0

        if player_launch == 1:
            players[actual_player].reset_darts()

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score

            # Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for _ in range(0, 7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

        # Display headers depending of round
        if actual_round == 1:
            self.headers[0] = '12'
        elif actual_round == 2:
            self.headers[0] = '13'
        elif actual_round == 3:
            self.headers[0] = '14'
        elif actual_round == 4:
            self.headers[0] = 'DBL'
        elif actual_round == 5:
            self.headers[0] = '15'
        elif actual_round == 6:
            self.headers[0] = '16'
        elif actual_round == 7:
            self.headers[0] = '17'
        elif actual_round == 8:
            self.headers[0] = 'TPL'
        elif actual_round == 9:
            self.headers[0] = '18'
        elif actual_round == 10:
            self.headers[0] = '19'
        elif actual_round == 11:
            self.headers[0] = '20'
        elif actual_round == 12:
            self.headers[0] = 'SB'
        elif actual_round == 13:
            self.headers[0] = 'DB'

        self.headers[1] = self.headers[0]
        self.headers[2] = self.headers[0]

        if self.headers[0] == 'DBL':
            targ = [f'D{num}' for num in range(1, 21)]
        elif self.headers[0] == 'TPL':
            targ = [f'T{num}' for num in range(1, 21)]
        elif self.headers[0] == 'SB':
            targ = ['SB', 'DB']
        elif self.headers[0] == 'DB':
            targ = ['DB']
        else:
            targ = [f'{mult}{self.headers[0]}' for mult in ['S', 'D', 'T']]

        self.raspberry.set_target_leds('|'.join([f'{key}#{self.colors[0]}' for key in targ]))

        # Print debug output
        self.logs.log('DEBUG', self.infos)
        return return_code

    def pnj_score(self, players, actual_player, level, player_launch):
        '''
        pnj_socre
        '''
        letters = 'SDT'
        value = random.randint(1, 20)
        multi = ''.join(random.choice(letters) for _ in range(1))
        bull = random.randint(0, 100)
        if 85 < bull <= 95:
            return 'SB'
        if bull > 95:
            return 'DB'
        return f'{multi}{value}'

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Function run after each dart throw - for example, add points to player
        '''

        self.infos = ""
        handler = self.init_handler()
        score = 0
        # Define a var for adding score
        if actual_round == 1 and hit[1:] == '12' \
                or actual_round == 2 and hit[1:] == '13' \
                or actual_round == 3 and hit[1:] == '14' \
                or actual_round == 4 and hit[:1] == 'D' \
                or actual_round == 5 and hit[1:] == '15' \
                or actual_round == 6 and hit[1:] == '16' \
                or actual_round == 7 and hit[1:] == '17' \
                or actual_round == 8 and hit[:1] == 'T' \
                or actual_round == 9 and hit[1:] == '18' \
                or actual_round == 10 and hit[1:] == '19' \
                or actual_round == 11 and hit[1:] == '20' \
                or actual_round == 12 and hit in ('SB', 'DB') \
                or actual_round == 13 and hit == 'DB':
            score = self.score_map[hit]
            check = True
            players[actual_player].columns[player_launch - 1] = ('check-mark', 'image')
        else:
            check = False
            return_code = -1
            players[actual_player].columns[player_launch - 1] = ('cross-mark', 'image')

        # Classic case (between start and end)
        if score > 0:
            handler['show'] = (players[actual_player].darts, hit, False)
            handler['sound'] = hit # Touched !
            players[actual_player].score += score # add score
            players[actual_player].round_points += score # Keep total for this round
            # You may want to keep the "Total Points" (Global amount of grabbed points,
            # follow the player all game long)
            players[actual_player].points += score   #self.score_map.get(hit)
        # No dart marked
        elif players[actual_player].round_points == 0 and player_launch == 3:
            self.infos += "Dividing score by half!\n"
            # Divide score by half
            handler['return_code'] = 1 # Next player
            players[actual_player].score = int(players[actual_player].score / 2)
            handler['sound'] = 'whatamess'

        # Check last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            winner = self.check_winner(players)
            if winner != -1:
                self.infos += f"Player {winner} wins !{self.lf}"
                self.winner = winner
                handler['return_code'] = 3
            else:
                handler['return_code'] = 2

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score, check=check)

        # You may want to count how many touches (Simple = 1 touch, Double = 2 touches, Triple = 3 touches)
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Store what he played in the table
        #players[actual_player].columns[0] = (score, 'int')

        # Print debug
        self.logs.log('DEBUG', self.infos)

        # Next please !
        return handler

    def check_winner(self, players):
        '''
        Method to check if there is a winnner
        '''
        bestscoreid = -1
        # Find the better score
        for player in players:
            if bestscoreid == -1 or player.score > players[bestscoreid].score:
                bestscoreid = player.ident
        return bestscoreid

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Function launched if the player hit the player button before having
        thrown all his darts (Pneu)
        '''
        self.infos += f"EarlyPlayer function. Actual player marked \
                {players[actual_player].round_points}{self.lf}"
        self.display.play_sound('whatamess')
        # Jump to next player by default
        return_code = 1

        # Eventually divide by 2
        if players[actual_player].round_points == 0:
            self.infos += 'Dividing score by half! And early !{self.lf}'
            # Divide score by half
            players[actual_player].score = int(players[actual_player].score / 2)

        # Last round - check winner or return Game over
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            # Game over
            return_code = 2
            winner = self.check_winner(players)
            if winner != -1:
                self.winner = winner
                self.infos += f'Player {winner} wins !{self.lf}'
                # Victory
                return_code = 3

        return return_code

    def refresh_stats(self, players, actual_round):
        '''
        Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical
        formulas used to calculate stats. Refreshed after every launch
        '''
        for player in players:
            player.stats['Points Per Round'] = player.show_ppr()
            player.stats['Points Per Dart'] = player.show_ppd()

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        To avoid Ouin ouin
        '''
        pass

    def next_game_order(self, players):
        '''
        Define the next game players order, depending of previous games' score
        '''
        scores = {}
        # Create a dict with player and his score
        for player in players:
            scores[player.name] = player.score
        # Order this dict depending of the score
        new_order = collections.OrderedDict(sorted(scores.items(), key=lambda t: t[1],
            reverse=True))
        # Return
        return list(new_order.keys())
