# -*- coding: utf-8 -*-
'''
Game by LB, idea by Manouk : Kinito
'''

import random
from copy import deepcopy# For backupTurn

from include import cplayer
from include import cgame

LOGO = 'Kinito.png'
HEADERS = ['Min', 'Total', 'K\'to', '', '', '', '']
OPTIONS = {'theme': 'default', 'max_round': 10, 'winscore': 221, 'kinito': 21, 'master': False}
NB_DARTS = 3
GAME_RECORDS = {'Points Per Round' : 'DESC'}

class CPlayerExtended(cplayer.Player):
    '''
    Extended player class
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.min_score = None
        # Read the CJoueur class parameters, and add here yours if needed
        self.kinito = False
        # Total points
        self.points = 0
        # Score to hit when Kinito occur
        self.kinito_score = ""
        self.headers = HEADERS
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    '''
    Kinito game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # Nb players
        self.nb_players = nb_players
        # records is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS
        # Set config string to integer
        self.nb_darts = 3
        self.headers = HEADERS
        self.logo = LOGO
        self.options = options
        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        if options['master']:
            self.master = True
        else:
            self.master = False
        self.winscore = int(options['winscore'])
        self.kinito = int(options['kinito'])
        # For rpi
        self.rpi = rpi

        self.infos = ''
        self.winner = None

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Actions done before each dart throw - for example, check if the player is allowed to play
        '''
        return_code = 0
        self.infos = ""

        if player_launch == 1:
            players[actual_player].reset_darts()

        if player_launch == 1 and actual_player == 0 and actual_round == 1:
            for player in players:
                player.columns[0] = (0, 'int', 'game-green')
                player.reset_rounds(self.max_round)

        # Init first player score to do (first player of first round random)
        if actual_round == 1 and actual_player == 0 and player_launch == 1 \
                and not self.random_from_net:
            players[actual_player].min_score = random.randint(1, 20)
        if players[actual_player].min_score is None:
            players[actual_player].min_score = 0
        self.infos += "You have to reach at least score {players[actual_player].min_score}{self.lf}"

        # Reset Per round total and kinito status
        players[actual_player].columns[0] = (players[actual_player].min_score, 'int', None)
        if player_launch == 1:
            # Backup Turn save
            self.save_turn(players)
            players[actual_player].columns[1] = (0, 'int', None)
            # Update Screen for new challenger
            for player in players:
                player.kinito = False
                player.kinito_score = ''
                player.columns[2] = ('', 'str', 'game-green')

        # Put kinito_score in table
        for player in players:
            if player.kinito_score == 'K\'to':
                player.columns[2] = (player.kinito_score, 'str', 'game-red')
            else:
                player.columns[2] = (player.kinito_score, 'int', 'game-red')

        if players[actual_player].kinito:
            possibilities = []
            for player in players:
                if player.kinito_score != 'K\'to' and player.ident != actual_player:
                    possibilities.extend(self.get_possibilitirs(player.kinito_score, True))

            if len(possibilities)> 0:
                self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                        for key in possibilities]))
            else:
                self.rpi.set_target_leds('')

        else:
            possibilities = self.get_possibilitirs(players[actual_player].min_score, False)
            if len(possibilities)> 0:
                self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                        for key in possibilities]))
            else:
                self.rpi.set_target_leds('')

        # Check winner
        self.check_winner(players, actual_player, player_launch)
        if self.winner is not None:
            return 3

        self.logs.log("DEBUG", self.infos)
        return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Function run after each dart throw - for example, add points to player
        '''

        players[actual_player].add_dart(actual_round, player_launch, hit)

        self.infos = ""
        handler = self.init_handler()
        # Who is next player ?
        if actual_player == self.nb_players - 1:
            nextplayer = 0
        else:
            nextplayer = actual_player + 1
        # Basic Score check
        if self.score_map[hit] >= players[actual_player].min_score and \
                (player_launch == self.nb_darts or hit != "T7") and \
                not players[actual_player].kinito:
            self.infos += f"Good. You reached {self.score_map[hit]} score{self.lf}"
            players[actual_player].min_score = self.score_map[hit]
            players[actual_player].increment_column(self.score_map[hit], 1)
            players[actual_player].score += self.score_map[hit]
            players[actual_player].points += self.score_map[hit]
            handler['show'] = (players[actual_player].darts, hit, True)
            handler['sound'] = hit


        # bad bluff (score is under the min score)
        if self.score_map[hit] < players[actual_player].min_score and \
                (hit != "T7" or player_launch == self.nb_darts) and \
                not players[actual_player].kinito:
            self.infos += "What a mess. You reached {self.score_map[hit]}{self.lf}"
            players[actual_player].score -= players[actual_player].get_col_value(1)
            players[actual_player].points -= players[actual_player].get_col_value(1)
            handler['return_code'] = 1 # next player
            handler['sound'] = 'whatamess'

        # Kinito Open
        if self.score_map[hit] == self.kinito \
                and int(player_launch) < int(self.nb_darts):
            players[actual_player].score += self.score_map[hit]
            players[actual_player].points += self.score_map[hit]
            self.infos += "Kinito ! You reached special score ! ({self.score_map[hit]}){self.lf}"
            #self.display.DisplayBlinkCentered("Kinito !")
            handler['message'] = 'Kinito !'
            handler['sound'] = 'kinito'
            players[actual_player].kinito = True
            players[actual_player].kinito_score = 'K\'to'
            if self.random_from_net is False:
                self.kinito_score(players)

        # If Kinito played
        if players[actual_player].kinito:
            for player in players:
                if self.score_map[hit] == player.kinito_score and player.ident != actual_player:
                    players[actual_player].score += self.score_map[hit]
                    players[actual_player].points += self.score_map[hit]
                    player.score = int(player.score / 2)
                    self.infos += f"You hit the Kinito score of player {player.ident} !{self.lf}"

        # Put score / 2 to min score to next player
        if len(players) > 1:
            self.infos += "Hit : {}".format(hit)
            players[nextplayer].min_score = int(self.score_map[hit] / 2)
        else:
            players[actual_player].min_score = self.score_map[hit]

        # Player get over Winscore with master option
        if players[actual_player].score > self.winscore and self.master:
            players[actual_player].score = 2 * self.winscore - players[actual_player].score
            players[actual_player].points += self.score_map[hit]
            handler['sound'] = 'toohigh'
            handler['message'] = 'Too high !'
            handler['return_code'] = 1

        # Populate screen table
        players[actual_player].columns[0] = (players[actual_player].min_score, 'int')
        for player in players:
            if player.kinito_score == 'K\'to':
                player.columns[2] = (player.kinito_score, 'str', 'game-red')
            else:
                player.columns[2] = (player.kinito_score, 'int', 'game-red')

        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Check last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and (player_launch == self.nb_darts or handler['return_code'] == 1):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            handler['return_code'] = 2
        # Check winner
        self.check_winner(players, actual_player, player_launch)
        if self.winner is not None:
            handler['return_code'] = 3

        self.logs.log("DEBUG", self.infos)
        return handler

    def check_winner(self, players, actual_player, player_launch):
        '''
        Function to check winner
        '''
        self.winner = None
        # Check winner if no master option
        if players[actual_player].score >= self.winscore and not self.master:
            self.winner = players[actual_player].ident
        elif players[actual_player].score == self.winscore and self.master:
            self.winner = players[actual_player].ident

    def save_turn(self, players):
        '''
        Function used to backup turn - you don't needs to modify it (for the moment)
        '''
        #Create Backup Properies Array
        try:
            self.previous = deepcopy(self.backup_player)
        except: # pylint: disable=bare-except
            self.infos += "No previous turn to backup.\n"
        self.backup_player = deepcopy(players)
        self.infos += "Score Backup.\n"

    def get_possibilitirs(self, target_score, kinito=False):
        '''
        Get possibilities in ordre to light leds
        '''
        possibilities = []
        for multiplier in ['S', 'D', 'T']:
            if multiplier == 'S':
                mult = 1
            elif multiplier == 'D':
                mult = 2
            else:
                mult=3

            for i in range(1, 22):
                if i == 21:
                    if multiplier == 'T':
                        continue
                    i = 25

                if not kinito and i * mult >= target_score:
                    if i == 25:
                        i = 'B'
                    possibilities.append(f'{multiplier}{i}')

                if kinito and i * mult == target_score:
                    if i == 25:
                        i = 'B'
                    possibilities.append(f'{multiplier}{i}')

        return possibilities

    def kinito_score(self, players):
        '''
        Function to attribute a kinito score to everyone
        '''
        for player in players:
            if not player.kinito:
                done = False
                while not done:
                    kinitoscore = random.choice(list(self.score_map.values()))
                    # If NOT master, player's kinito score is less than General Kinito score
                    if kinitoscore < self.kinito:
                        player.kinito_score = kinitoscore
                        done = True

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Fonction pneu
        '''
        # If master option and early player button pushed, return to original score
        # and refresh screen
        if self.master:
            players[actual_player].score -= players[actual_player].columns[1][0]
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            # If its a early_player_button just at the last round - return GameOver code
            return 2
        return 1

    def refresh_stats(self, players, actual_round):
        '''
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        '''
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)

    def get_random(self, players, actual_round, actual_player, player_launch):
        '''
        Returns and Random things, to send to clients in case of a network game
        '''
        # Send initial random score value
        ret = {'PLAYERKINITO': None, 'KINITOSCORE': None, 'MINSCORE': None}
        if actual_round == 1 and actual_player == 0 and player_launch == 1:
            ret['MINSCORE'] = players[0].min_score

        # Check if Kinito is open and if true, send random values to other players
        kinito_open = False
        for player in players:
            if player.kinito:
                kinito_open = True

        if kinito_open:
            scores = []
            for player in players:
                scores.append(player.kinito_score)
            ret = {'PLAYERKINITO': player.ident, 'KINITOSCORES': scores}

        return ret

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        '''
        Set Random things, while received by master in case of a network game
        '''
        kinito_open = False
        for player in players:
            if player.kinito:
                kinito_open = True
                self.logs.log("DEBUG", "KINITO is open ! We wait for random score via network :)")
        if kinito_open and 'KINITOSCORES' in data:
            scores = data['KINITOSCORES']
            for player in players:
                if player.kinito is False:
                    player.kinito_score = int(scores[player.ident])
                else:
                    player.kinito_score = 'K\'to'
        if actual_round == 1 and actual_player == 0 and player_launch == 1:
            players[0].min_score = int(data['MINSCORE'])
        self.random_from_net = True
