# -*- coding: utf-8 -*-
# Game by ... LaDite - jeu base sur le high score de Olivier Lu
########
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############

OPTIONS = {'theme': 'default', 'max_round': 10, 'simple50' : False, 'penality': 10}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Batard.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Rnd', 'PPD', 'PPR'] # Columns headers - Must be a string

class CPlayerExtended(cplayer.Player):
    '''
    Exetended player class
    '''
    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        # Extend the basic players property with your own here
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    '''
    Batard game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        #  Get the maximum round number
        self.max_round = int(options['max_round'])
        self.simple = options['simple50']

        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None
        self.dart = 0

        #  Penality points for a missing dart
        self.penality = int(options['penality'])

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Actions done before each dart throw - for example, check if the player is allowed to play
        '''
        return_code = 0

        if player_launch == 1:
            players[actual_player].reset_darts()

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log('ERROR', f'Handicap failed : {exception}')

            for player in players:
                # Init score
                player.score = 0
                player.alive = True

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

        # Display avg
        if actual_round == 1 and player_launch == 1:
            players[actual_player].columns[5] = (0.0, 'int')
            players[actual_player].columns[6] = (0.0, 'int')
        else:
            players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
            players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')
        # Clean next boxes
        for i in range(player_launch - 1, self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')

        # Print debug output
        self.logs.log('DEBUG', self.infos)
        return return_code

    def best_score(self, players):
        '''
        Find the winner
        Only one player with best score
        '''
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
                self.logs.log('DEBUG', \
                        f'Best found : {best_score} / Count={best_count} / player = {best_player}')
            elif player.score == best_score:
                best_count += 1

        self.logs.log('DEBUG', \
                f'Best score : {best_score} / Count={best_count} / Player = {best_player}')

        if best_count == 1:
            return best_player
        return -1

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Function run after each dart throw - for example, add points to player
        '''

        handler = self.init_handler()
        handler['show'] = (players[actual_player].darts, hit, True)
        handler['sound'] = hit

        score = self.score_map[hit]

### DETERMINE LA VALEUR DE LA PREMIERE FLECHE
        self.dart = players[actual_player].columns[0]

        if player_launch >= 2 and score < self.dart[0]:
            self.logs.log('DEBUG', f'score fleche {player_launch} inferieur a fleche 1 : {score}')
            score = -score
            handler['sound'] = 'penality'
        else:
            score = score

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        self.logs.log('DEBUG', 'score fleche superieur ')
        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
        self.refresh_stats(players, actual_round)

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner > 0:
                self.winner = winner
                handler['return_code'] = 3
            else:
                # No winner : last round reached
                handler['return_code'] = 2

        return handler

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        players[actual_player].score -= self.penality
        players[actual_player].columns[player_launch-1] = ('MISS', 'str')
        players[actual_player].darts_thrown += 1
        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
        self.refresh_stats(players, actual_round)

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Function launched when the  put player button before having launched all his darts
        '''
        # Jump to next player by default
        return_code = 1

        # darts_thrown for missing target
        #players[actual_player].darts_thrown += (self.nb_darts - players[actual_player].darts_thrown)

        # Check missing darts
        #penality = (self.nb_darts - players[actual_player].darts_thrown) * self.penality

        if player_launch == 1:
                penality = 30
        elif player_launch == 2:
                penality = 20
        elif player_launch == 3:
                penality = 10

        if penality > 0:
            # add penality points
            players[actual_player].score -= penality
            players[actual_player].round_points -= penality # Keep total for this round
            players[actual_player].points -= penality #for ppd,ppr

            # Refresh stats
            players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
            players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
            self.refresh_stats(players, actual_round)

            # play penality sound
            self.display.play_sound('penality')

            # anim leds for the penality
            #Event.Publish('penalty')

    def post_round_check(self, players, actual_round, actual_player):
        '''
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        '''
        if actual_round >= self.max_round:
            winner = self.check_winner(players)
            if winner is not None:
                self.winner = winner
                self.logs.log('DEBUG', f'winner is {winner}')
                return winner
            elif actual_round >= self.max_round:
                # Last round, last player
                return self.best_score(players)
        return -2

    def check_winner(self, players):
        nb_winner = 0
        for i in range(0, len(players)):
            if players[i].alive:
                winner = i
                nb_winner += 1

        if nb_winner == 1:
            return winner
        return None

    def get_score(self, player):
        '''
        Return score of player
        '''
        return player.score

    def next_set_order(self, players):
        '''
        Sort players for next set
        '''
        players.sort(key=self.get_score)

    def refresh_stats(self, players, actual_round):
        '''
        refresh players' stats
        '''
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)
            player.stats['Points Per Dart'] = player.show_ppd()
