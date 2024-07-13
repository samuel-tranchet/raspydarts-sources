# -*- coding: utf-8 -*-
"""
Game by poilou
"""

import random
import collections
import pygame
from copy import deepcopy
from include import cgame
from include import cplayer
from include import chandicap
from math import sqrt

LOGO = 'Cricket'
HEADERS = ['20', '19', '18', '17', '16', '15', 'B']
OPTIONS = {'theme': 'default', 'max_round': 20, 'optioncrazy': False, 'optioncutthroat': False, 'drinkscore': 200,
        'Teaming': False, 'optionteamscore': False, 'optionhandicap': False, 'mpr': False}
NB_DARTS = 3
GAME_RECORDS = {'MPR': 'DESC', 'Hits per round': 'DESC', 'GiveOut': 'ASC'}

def check_players_allowed(nb_players):
    """
    Check if numbers of players is ok according to options
    """
    return nb_players <= 8

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.pay_drink = False  # Flag used to know if player has reached the drink score
        self.distrib_points = 0  # COunt how many points the player gave to the others (cut throat)
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    Cricket game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.handicap = chandicap.Handicap('Cricket', config, logs)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS  # Total darts the player has to play
        self.logo = LOGO
        self.headers = HEADERS[:]
        self.nb_players = nb_players
        # For rpi
        self.raspberry = rpi
        self.logs = logs
        self.options = options

        #Options
        self.cutthroat = options['optioncutthroat']
        if nb_players % 2 == 1:
            self.teaming = False
        else:
            self.teaming = options['Teaming']
        self.teamscore = options['optionteamscore']
        self.crazy = options['optioncrazy']
        self.handicap = options['optionhandicap']
        self.show_mpr = options['mpr']
        self.drink_score = int(options['drinkscore'])

        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        # TEMP - place it somwhere else - prevent option to be activated in case of
        # odd number of players
        if not self.teaming:
            self.teamscore = False
        else:
            self.display.teaming = True

        self.winner = None
        self.infos = ''
        self.to_randomize = []

        self.trail = self.display.file_class.get_full_filename('trail', 'images')
        self.dart = self.display.file_class.get_full_filename('dart3', 'images')
        self.dart_icon = self.display.file_class.get_full_filename('dart_icon', 'images')
        self.online_icon = self.display.file_class.get_full_filename('online', 'images')

        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        self.margin_4 = 4 * self.display.margin

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Post dart check
        """

        # Find teamMate (only for teaming)
        mate = self.mate(actual_player, len(players))
        # Init
        play_closed = False  # Should we play the closed sound ?
        play_open = False  # Should we play the open sound ?
        play_hit = False  # Should we play the Double & triple sound ?
        play_scored = False  # Should we play the Scored sound ?

        return_code = 0
        touchcount4total = False
        self.infos = f"Player {players[actual_player].ident} -\
                Score before playing: {players[actual_player].score}\n"

        to_add, value = self.split_key(hit, multiplier=True)
        hit_value = 0

        #If this column is currently displayed - Valid key
        if value in self.headers and self.get_column_state(actual_player, players, self.headers.index(value)) < 4:
            # Launch animation
            self.ok = True
            # column touched
            column_hit = self.headers.index(value)
            # Add points ?
            overtouched = max(players[actual_player].get_col_value(column_hit) + to_add - 3, 0)

            hit_value = min(to_add, 3 - players[actual_player].get_col_value(column_hit))

            if players[actual_player].get_col_value(column_hit) == 0 and to_add < 3:
                # column is open
                play_open = True
            elif players[actual_player].get_col_value(column_hit) + to_add >= 3 \
                    and players[actual_player].get_col_value(column_hit) < 3:
                # column is closed
                play_closed = True
            else:
                # open and not closed : increment
                play_hit = True

            if self.crazy and value != 'B' and not play_closed:
                self.to_randomize.append(value)

            if self.teaming:
                mate = self.mate(players[actual_player].ident, len(players))
                mate_closed = players[mate].get_col_value(column_hit) >= 3

            # Increase column
            if players[actual_player].get_col_value(column_hit) < 3:
                players[actual_player].increment_column_touch(column_hit, \
                        min(to_add, 3 - players[actual_player].get_col_value(column_hit)))

                if self.teaming and self.teamscore:
                    # Do the same for mate's column
                    players[mate].increment_column_touch(column_hit, \
                        min(to_add, 3 - players[mate].get_col_value(column_hit)))

            if self.get_column_state(actual_player, players, self.headers.index(value)) > 3:
                overtouched = 0
            else:
                hit_value += overtouched

            # Add points ? Only if column is already open
            if overtouched > 0:
                # Score to add
                score_to_add = overtouched * self.score_map[f'S{value}']

                play_scored = True
                if not self.teaming:
                    if self.cutthroat:
                        index = 0
                        for player in players:
                            if index != actual_player and players[index].get_col_value(column_hit) < 3:
                                players[index].add_score(score_to_add)
                            index += 1
                    else:
                        players[actual_player].add_score(score_to_add)

                elif mate_closed or self.teamscore:
                    if self.teamscore and not self.cutthroat:
                        players[actual_player].add_score(score_to_add)
                        players[mate].add_score(score_to_add)

                    elif self.cutthroat:
                        index = 0
                        for player in players:
                            if index != actual_player and index != mate and players[index].get_col_value(column_hit) < 3:
                                players[index].add_score(score_to_add)
                            index += 1
                    else:
                        players[actual_player].add_score(score_to_add)
                else:
                    play_scored = False

            # Add hit
            players[actual_player].roundhits += 1

            # Actual player is up to date
            ###################################################################

            # For fun, if the player reached the required drink score (usually 500),
            # tell him to pay a drink !
            if not players[actual_player].pay_drink and \
                    players[actual_player].score >= self.drink_score and self.cutthroat:
                players[actual_player].pay_drink = True
                self.display.play_sound('diegoaimaboir')

            # Added buttons if the player had a surplus (common to Cut Throat and Normal Mode)
            if overtouched > 0 and touchcount4total:
                # We add his extra hits to his total since they counted (players took points)
                play_hit = True  # Its a valid hit, play sound

            # Sound handling to avoid multiple sounds playing at a time
            if play_scored:
                self.display.play_sound('very_deep')
                self.logs.log("DEBUG", "Playing Scored Sound")
            elif play_open:
                self.display.play_sound('open')
                self.logs.log("DEBUG", "Playing Open Sound")
            elif play_closed:
                self.display.play_sound('closed')
                self.logs.log("DEBUG", "Playing Closed Sound")
            elif play_hit:
                if super().play_show(players[actual_player].darts, hit, play_special=True):
                    self.display.sound_for_touch(hit)  # Its a valid hit, play sound
                self.logs.log("DEBUG", "Playing Simple Hit Sound")
            else:
                self.display.play_sound('plouf')

        # Count darts played
        players[actual_player].add_dart(actual_round, player_launch, hit, hit_value=hit_value)

        # It is recommanded to update stats evry dart thrown
        self.refresh_stats(players, actual_round)

        self.infos += f"Hit: {players[actual_player].get_touch_type(hit)} - Active Columns: \
                {self.headers}{self.lf}"
        self.infos += f"Total number of hits for this player: \
                {players[actual_player].get_total_hit()}{self.lf}"
        self.infos += f"Number of darts thrown from this player: {player_launch}{self.lf}"
        self.infos += f"Number of total darts thrown from this player: \
                {players[actual_player].darts_thrown}{self.lf}"

        # If it was last throw and no touch : play sound for "round missed"
        if player_launch == self.nb_darts and players[actual_player].roundhits == 0:
            self.display.play_sound('chaussette')

        # Check if there is a winner
        winner = self.check_winner(players)
        if winner is not None:
            self.infos += f"Player {winner} wins !{self.lf}"
            self.winner = winner
            return_code = 3

        # Last throw of the last round
        elif actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == self.nb_darts:
            self.infos += f"Last Round Reached ({actual_round}{self.lf}"
            return_code = 2

        # Display Recap text
        self.logs.log("DEBUG", self.infos)

        # And return code
        return return_code

    def nb_touch(self, player):
        """
        Count number of valid touch
        """
        nb_hit = 0
        closed = True
        for column in range(0, int(self.nbcol) + 1):
            nb_hit += int(player.columns[column][0])
            if int(player.columns[column][0]) < 3:
                closed = False

        return (nb_hit, closed)

    def check_winner(self, players):
        """
        Method to check if there is a winnner
        """
        winner_id = None
        index = 0
        if self.teaming:
            max_player = int(len(players) / 2)
            teams = []
            for team_id in range(0, max_player):
                mate = self.mate(team_id, len(players))
                closed = self.nb_touch(players[team_id])[1] and self.nb_touch(players[mate])[1]
                score = players[team_id].score + players[mate].score
                teams.append((team_id, closed, score))

            for team_id in range(0, max_player):
                if winner_id is not None and score == teams[winner_id][2]:
                    best.append(teams[team_id])
                elif winner_id is None \
                    or (teams[team_id][2] < teams[winner_id][2] and self.cutthroat) \
                    or (teams[team_id][2] > teams[winner_id][2] and not self.cutthroat):
                        best = []
                        best.append(teams[team_id])
                        winner_id = team_id

            winners = []
            for team in best:
                if team[1]:   # All closed
                    winners.append(team[0])

        else:
            # Find the best score
            for player in players:
                if winner_id is not None and player.score == players[winner_id].score:
                    # Same score
                    best.append((player.ident, self.nb_touch(player)))
                elif winner_id is None \
                    or (player.score < players[winner_id].score and self.cutthroat) \
                    or (player.score > players[winner_id].score and not self.cutthroat):
                    best = []
                    best.append((player.ident, self.nb_touch(player)))
                    winner_id = index
                index += 1

            winners = []
            for player in best:
                if player[1][1]:   # All closed
                    winners.append(player[0])

        # If the player who have the best score has closed all the gates
        if len(winners) == 1:
            return winners[0]
        return None

    def random_header(self, actual_player, players, force=False, columns=None):
        """
        New RandomHeader Method that use the get_column_state internal method to check column.
        More reliable.
        """
        for column in range(0, int(self.nbcol)):
            if columns is None or self.headers[column] in self.to_randomize:
                self.infos += f"Working on column {column}{self.lf}"
                # Check state of column (none, open or closed)
                randomize = self.get_column_state(actual_player, players, column) == 2

                # Randomizing column...
                if randomize or force:
                    self.infos += f"Column {column} will randomize.{self.lf}"
                    while True:
                        random_number = random.randint(1, 20)
                        if str(random_number) not in self.headers:
                            self.headers[column] = str(random_number)
                            break
                else:
                    self.infos += f"Column {column} will not be randomized.{self.lf}"

    def get_column_state(self, actual_player, players, col):
        """
        Get state of column. It can be :
        1 : Not open
        2 : Open,
        3 : Closed by a player or a team
        4 : Closed by everybody
        """
        # Init
        state = 1
        nb_closed = 0
        index = 0
        # Loop on players
        for player in players:
            # Get Mate if Teaming enabled
            if self.teaming:
                if index >= int(len(players) / 2):
                    break
                mate = self.mate(index, len(players))
                self.infos += f"Analyse players {index} and {mate}{self.lf}"
                self.infos += f"Columns are {player.get_col_value(col)} and {players[mate].get_col_value(col)}{self.lf}"
                # TEAMING CASE 1 - state can only go upper
                if player.get_col_value(col) in [1, 2]:
                    self.infos += f"[TEAMING] This column {col} is OPEN for at least player \
                            {player.name}!{self.lf}"
                    state = max(state, 2)
                # NOTEAMING CASE 2
                if player.get_col_value(col) == 3 and players[mate].get_col_value(col) == 3:
                    state = max(state, 3)
                    nb_closed += 2
                    self.infos += f"[TEAMING] This column {col} is CLOSED by both players \
                            {player.name} and {players[mate].name} !{self.lf}"
                elif player.get_col_value(col) == 3 and players[mate].get_col_value(col) < 3:
                    state = max(state, 2)
                    self.infos += f"[TEAMING] This column {col} is CLOSED by one player only{self.lf}"
            else:
                # NOTEAMING CASE 1
                if player.get_col_value(col) in [1, 2]:
                    self.infos += f"[NOTEAMING] This column {col} is still OPEN (marked) by \
                            at least player {player.name}!{self.lf}"
                    state = max(state, 2)
                # NOTEAMING CASE 2
                elif player.get_col_value(col) == 3:
                    state = max(state, 3)
                    nb_closed += 1
                    self.infos += f"[NOTEAMING] This column {col} is CLOSED by at least \
                            player {player.name} !{self.lf}"
            index += 1

        if nb_closed == len(players):
            state = 4
            self.infos += f"ALL PLAYERS (OR TEAM) has closed this column {col} !{self.lf}"

        return state

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Action launched before each dart throw
        """
        self.infos = ""
        self.ok = False
        # If first round - set display as leds
        if player_launch == 1 and actual_round == 1 and actual_player == 0:
            for player in players:
                for column, value in enumerate(player.columns):
                    player.columns[column] = [0, 'leds', 'game-grey2']
                player.reset_rounds(self.max_round)
            if self.handicap and self.teaming:
                self.check_handicap(players)

        if player_launch == 1:
            if (self.crazy and actual_player > 0 or actual_round > 1) and not self.random_from_net:
                self.random_header(actual_player, players, columns=self.to_randomize)
            elif self.crazy and not self.random_from_net:
                self.random_header(actual_player, players, True)
            else:
                self.headers = HEADERS[:]

            self.to_randomize = []
            # Reset number of hits in this round for this player
            players[actual_player].roundhits = 0
            players[actual_player].reset_darts()

            self.infos += f"Active columns : {self.headers}"
            self.logs.log("DEBUG", self.infos)
            self.save_turn(players)

        leds = []
        ind = 0
        for header in self.headers:
            already_closed = 0
            test_player = 0
            column_state = self.get_column_state(actual_player, players, ind)
            for player in players:
                if test_player != actual_player:
                    if isinstance(player.get_col_value(ind), int) and \
                            player.get_col_value(ind) >= 3:
                        already_closed += 1
                test_player += 1

            if column_state == 4:
                # Closed by everyone
                pass
            elif int(players[actual_player].get_col_value(ind)) < 3 and self.teaming:
                mate = self.mate(actual_player, len(players))
                if column_state == 3:
                    leds.extend([f'{mult}{header}#{self.colors[2]}' for mult in ['E', 'S', 'D', 'T']])
                elif int(players[mate].get_col_value(ind)) == 3:
                    #Closed by mate
                    leds.extend([f'{mult}{header}#{self.colors[3]}' for mult in ['E', 'S', 'D', 'T']])
                else:
                    leds.extend([f'{mult}{header}#{self.colors[0]}' for mult in ['E', 'S', 'D', 'T']])

            elif int(players[actual_player].get_col_value(ind)) < 3 and not self.teaming:
                # Open for player
                if column_state == 3:
                    # And closed by one other
                    # Blue
                    leds.extend([f'{mult}{header}#{self.colors[2]}' for mult in ['E', 'S', 'D', 'T']])
                else:
                    # Green
                    leds.extend([f'{mult}{header}#{self.colors[0]}' for mult in ['E', 'S', 'D', 'T']])

            elif column_state == 2:
                pass
            elif self.teaming:
                mate = self.mate(actual_player, len(players))
                if int(players[actual_player].get_col_value(ind)) == 3 and int(players[mate].get_col_value(ind)) < 3:
                    pass
                elif column_state == 3 and int(players[actual_player].get_col_value(ind)) < 3:
                    leds.extend([f'{mult}{header}#{self.colors[2]}' for mult in ['E', 'S', 'D', 'T']])
                elif column_state == 3:
                    leds.extend([f'{mult}{header}#{self.colors[1]}' for mult in ['E', 'S', 'D', 'T']])
            else:
                leds.extend([f'{mult}{header}#{self.colors[1]}' for mult in ['E', 'S', 'D', 'T']])

            ind += 1
            self.raspberry.set_target_leds(('|'.join(leds)))

    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Called after player annoucement,...
        """
        if self.can_win(players[actual_player], self.nb_darts - player_launch + 1):
            return ['PRESSURE']
        return ['NOPRESSURE']

    def pnj_score(self, players, actual_player, level, player_launch):
        """
        Computer Strike

        Principe:
          Affecter à différentes possibilités un taux de réussite :
          - Pneu ou pas (L'expert ne fait jamais de pneu, le noob beaucoup)
          - Echec ou pas : 1 échec est une fléchette plantée dans un chiffre qui ne compte pas
              pour le cricket
          - Définition de la liste des segments :
              . 1 à 20
              . Bull en fonction du % de Bull du niveau (le noob a du mal à toucher la bull)
          - Pour chaque segment de la liste : Affectation d'un score, le score le plus élevé est
                  le "tir" du PNJ. Sont pris en compte :
              . La liste des segments à fermer (headers)
              . La liste des segments ouverts (par n'importe quel joueur)
              . La liste des segments ouverts par le PNJ
              . La liste des segments fermés (par n'importe quel joueur)
              . La liste des segments fermés par le PNJ
              . Meilleur score pour le PNJ ou non

          - Pour chaque "score", un random est effectué et est comparé aux différents seuils du
                niveau du joueur
          - Ensuite est effecté le multiplicateur, en fonction de taux de réussites également

        Ainsi, meilleur est le niveau du PNJ, plus il va :
          . Taper dans la cible
          . Dans les chiffres indiqués
          . Fermer les segments ouverts par d'autres joueurs
          . Essayer de mettre plus de points qu'un autre joueur ou ouvrir un segment qu'il n'a
                pas ouvert.
          . Viser les recordos scores plus que les petits.

                      |                                Rates                           |
          Level       | Pneu  |Failure| Prefered|Prefered| Max  |Prefered|Triple|Double| Bull |
                      |       |       |  open   | closed |number| points |      |      |      |
         -------------+-------+-------+---------+--------+------+--------+------+------+------+
          1 : noob    |   30  |   65  |     3%  |   0%   |  1%  |   0%   |  1   |   2  |  40  |
          2           |   15  |   55  |    15%  |   2%   |  25% |   5%   |  5   |   8  |  50  |
          3           |    3  |   15  |    35%  |   6%   |  45% |   7%   |  12  |  12  |  65  |
          4           |    1  |    5  |    65%  |   8%   |  65% |  10%   |  25  |  16  |  80  |
          5 : Expert  |    0  |    1  |    98%  |  16%   |  98% |  25%   |  55  |  32  |  95  |
        """

        levels = [
                    [30, 65,  3, 0, 1, 0,  1,  2, 40]
                   ,[15, 55, 15, 2, 25, 5, 5,  8, 50]
                   ,[3, 15, 35, 6, 45, 7, 12, 12, 65]
                   ,[1, 5, 65, 8, 65, 10, 25, 16, 80]
                   ,[0, 1, 98, 16, 98, 25, 45, 32, 95]
                ]

        tyre_rate = levels[level - 1][0]
        failure_rate = levels[level - 1][1]
        open_rate = levels[level - 1][2]
        close_rate = levels[level - 1][3]
        max_rate = levels[level - 1][4]
        points_rate = levels[level - 1][5]
        triple_rate = levels[level - 1][6]
        double_rate = levels[level - 1][7]
        bull_rate = levels[level - 1][8]
        tyre_range = random.randrange(100)

        if tyre_rate > 0 and tyre_range < tyre_rate:
            return 'MISSDART'

        scores = {}
        open_list = []
        closed_list = []

        max_header = 0
        max_score = 0
        im_the_best = False

        for player in players:
            index = 0
            for header in self.headers:
                # 1=No hit, 2=Hit by a player or a team, 3=Closed by a player or a team
                # 4=Closed by everybody
                column_state = self.get_column_state(player.ident, players, index)

                if column_state in (2,3) :        # Open by someone
                    if player.ident == actual_player:
                        if header not in open_list and not player.get_col_value(index) == 3:
                            open_list.append(header)
                    elif header not in open_list:
                        open_list.append(header)

                if column_state == 3 :     # Closed by someone
                    if player.ident == actual_player:
                        if header not in closed_list  and player.get_col_value(index) == 3:
                            closed_list.append(header)
                    elif header not in closed_list and column_state == 4:
                        closed_list.append(header)
                index += 1
            if player.get_score() > max_score:
                max_score = player.get_score()

        if players[actual_player].get_score() == max_score and max_score > 0:
            im_the_best = True

        for header in self.headers:
            if header in open_list:
                max_header = header

        possibilities = [f'{number}' for number in range(1, 21)]
        if random.randrange(100) < bull_rate:
            possibilities.append('B')
        random.shuffle(possibilities)

        failure = random.randrange(100) < failure_rate

        for poss in possibilities:
            score = random.randrange(63)

            # Failure Rate
            if poss in self.headers and failure:
                score -= 500    # out
            elif poss in self.headers:
                score += 200
            else:
                score += 100

            # Prefered Open
            if poss in open_list and random.randrange(100) < open_rate and not poss in closed_list:
                score += 200

            # Prefered Close
            if poss in closed_list and random.randrange(100) < close_rate and poss in open_list:
                score += 99

            # Prefered max score
            if poss == max_header and random.randrange(100) < max_rate and not poss in closed_list:
                score += 30

            # Prefered add points
            if poss in closed_list and random.randrange(100) < points_rate \
                    and poss in open_list and not im_the_best:
                score += 70

            # Prefere open a new segment
            if random.randrange(100) < open_rate and poss not in closed_list and \
                    poss not in open_list and im_the_best and poss in self.headers:
                score += 100

            scores[poss] = score

        best = sorted(scores.items(), key=lambda item: item[1],reverse=True)[0][0]
        mult_rate = random.randrange(100)
        if best != 'B':
            if mult_rate < triple_rate:
                score = f'T{best}'
            elif mult_rate < double_rate:
                score = f'D{best}'
            else:
                score = f'S{best}'
        elif mult_rate < triple_rate:
            score = 'DB'
        else:
            score = 'SB'

        return score

    def early_player_button(self, players, actual_player, actual_round):
        """
        If player Hit the Player button before having threw all his darts
        """
        # Jump to next player by default
        return_code = 1
        self.infos += "You hit Player button before throwing all your darts \
                ! Did you hit the PNEU ?"
        self.infos += f"actual_round {actual_round} Max Round {self.max_round} \
                actual_player {actual_player} nb_players {self.nb_players - 1}"
        # If no touch for this player at this round : play sound for "round missed"
        if players[actual_player].roundhits == 0:
            self.display.play_sound('chaussette')

        # If last round reached
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            winner = self.check_winner(players)
            if winner != -1:
                self.winner = winner
                self.infos += f"Player {winner} wins !{self.lf}"
                return 3
            return 2
        return return_code

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats.
        Refreshed after every launch
        """
        for player in players:
            player.stats['MPR'] = player.show_mpr()
            player.stats['Hits per round'] = player.hits_per_round(actual_round)
            player.stats['GiveOut'] = player.distrib_points

    def get_random(self, players, actual_round, actual_player, player_launch):
        """
        Returns and Random things, to send to clients in case of a network game
        """
        if self.crazy:
            return self.headers
        return False

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        """
        Set Random things, while received by master in case of a network game
        """
        if data is not False:
            self.headers = data
            self.random_from_net = True

    def next_game_order(self, players):
        """
        Define the next game players order, depending of previous games' scores
        """
        scores = {}
        # Create a dict with player and his score
        for player in players:
            scores[player.name] = player.score
        # Order this dict depending of the score
        new_order = collections.OrderedDict(sorted(scores.items(), key=lambda t: t[1],
                                                      reverse=self.cutthroat))
        # Return
        return list(new_order.keys())

    def can_win(self, player, darts):
        """
        Return "player can win with x darts"
        """
        total_hit = 0
        for target in player.columns:
            total_hit += target[0]
        return 21 - total_hit <= darts

    def get_score(self, player):
        """
        Return score of player
        """
        total_hit = 0
        for target in player.columns:
            total_hit += target[0]
        return float(f'{player.score}.{total_hit}')

    def next_set_order(self, players):
        """
        Sort players for next set
        """
        players.sort(key=self.get_score)

    def mate(self, actual_player, nb_players):
        """
        Find TeamMate in case of Teaming
        """
        mate = -1
        if self.teaming:
            if actual_player < (nb_players / 2):
                mate = actual_player + int(nb_players / 2)
            else:
                mate = actual_player - int(nb_players / 2)
        return mate

    def check_handicap(self, players):
        """
        Check for handicap and record appropriate marks for player
        """
        if len(players) != 4:
            self.logs.log("WARNING", "Handicap is available in Cricket only for 4 players.")
        else:
            self.logs.log("DEBUG", "Looking for handicaps")
            handimarks = []
            mpr = []
            maxid = 0
            for player in players:
                name = player.name
                if name.lower() not in self.stats.PlayerStatDict:
                    mpr.append(0.0)
                else:
                    mpr.append(self.stats.PlayerStatDict[name.lower()][2])
                # Load Handicaps from CHandicap
            handimarks = self.handicap.FindCricketHandicap(mpr)
            maxid = self.handicap.ReturnMaxid()
            # load handicaps into players
            for column in range(0, int(self.nbcol + 1)):
                for handmark in range(handimarks[column] + 1):
                    self.logs.log("DEBUG", f"Handicap : Column = {column}, handmark = {handmark}")
                    if maxid == 0:
                        if handmark == 0:
                            pass
                        else:
                            players[1].increment_column_touch(column)
                            players[3].increment_column_touch(column)
                    elif maxid == 1:
                        if handmark == 0:
                            pass
                    else:
                        players[0].increment_column_touch(column)
                        players[2].increment_column_touch(column)

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        Miss button pressed
        """
        self.logs.log("DEBUG", "MissButtonPressed")
        players[actual_player].darts_thrown += 1

    def check_players_allowed(self, nb_players):
        """
        Check if numbers of players is ok according to options
        """
        if self.teaming and (nb_players % 2 != 0 or nb_players < 4):
            return False
        return nb_players <= 8

    def draw_symbol(self, color, center_x, center_y, size, thickness, score, ratio=None):
        pos_x = int(center_x - size / 2)
        pos_y = int(center_y - size / 2)
        if ratio is None:
            for index in range(0, size + 1):
                if score > 0:
                    pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + index), thickness, 0)
                if score > 1:
                    pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + size - index), thickness, 0)
                if score < 0:
                    pygame.draw.circle(self.display.screen, color, (pos_x + index, center_y), thickness, 0)
            if score > 2:
                 pygame.draw.circle(self.display.screen, color, (center_x, center_y), int(size / sqrt(2)), int(thickness * sqrt(2)))
        else:
            index = int(size * ratio)
            width = int(ratio * thickness * sqrt(2))
            if score > 0:
                pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + index), thickness, 0)
            if score > 1:
                pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + size - index), thickness, 0)
            if score > 2 and width > 0:
                pygame.draw.circle(self.display.screen, color, (center_x, center_y), int(size / sqrt(2)), width)
            if score < 0:
                pygame.draw.circle(self.display.screen, color, (pos_x + index, center_y), thickness, 0)

    def draw_rect(self, rect, thickness, color):
        pos_x = rect[0]
        pos_y = rect[1]
        width = rect[2]
        height = rect[3]

        pygame.draw.line(self.display.screen, color, (pos_x, pos_y), (pos_x, pos_y + height), thickness)
        pygame.draw.line(self.display.screen, color, (pos_x + width, pos_y), (pos_x + width, pos_y + height), thickness)
        pygame.draw.line(self.display.screen, color, (pos_x, pos_y), (pos_x + width, pos_y), thickness)
        pygame.draw.line(self.display.screen, color, (pos_x, pos_y + height), (pos_x + width, pos_y + height), thickness)

    def draw_dart_score(self, dart_position, dart_value):
        mid_x = int(self.display.res_x / 4)
        mid_y = self.margin
        mid_w = self.display.mid_x
        mid_h = int(self.display.res_y * 2 / 3) - mid_y

        target_x = self.display.mid_x - int(self.display.res_x / 32)
        # target_y = mid_y + int(mid_h / 16)
        target_y = mid_y + self.margin_2
        target_w = int(self.display.res_x / 16)
        # target_h = int(mid_h / 8)
        target_h = int((mid_h - self.margin_4)/ 7)

        scores_y = mid_y + self.margin
        scores_w = int(self.display.res_x * 3 / 32)
        scores_h = mid_h - self.margin_2

        dart_x = int(self.display.res_x / 4 + self.margin / 2)
        dart_x_increment = int(self.display.mid_x / 3)
        dart_y = scores_y + scores_h + int(self.display.res_y / 32)
        dart_h = target_h
        dart_w = int(self.display.mid_x / 3 - 2 * self.margin)

        # For scrolling dart
        pos_y = dart_y + dart_h + self.margin
        height = int(self.display.res_y / 24)

        if dart_value[:1] == 'T' or dart_value == 'DB':
            dart_color = self.display.colorset['game-gold']
        elif dart_value[:1] == 'D' or dart_value == 'SB':
            dart_color = self.display.colorset['game-silver']
        else:
            dart_color = self.display.colorset['game-bronze']
        self.display.blit_rect(dart_x + dart_position * dart_x_increment, dart_y, dart_w, dart_h, self.display.colorset['game-bg'])
        self.display.blit_text(f"{dart_value}", dart_x + dart_position * dart_x_increment, dart_y, dart_w, dart_h, color=dart_color, dafont='Impact', align='Center')


    def onscreen_buttons(self):
        '''
        On screen buttons
        '''
        # Init
        click_zones = {}

        # GAME BUTTON
        right_x = int(self.display.res['x'] * 12 / 16)
        right_y = self.display.margin
        right_width = int(self.display.res['x'] * 4 / 16)
        right_height = int(self.display.res['y'] * 1.5 / 16)

        buttons = []
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-alternate'], 'GAMEBUTTON', 'Exit'])
        right_y += right_height + self.display.margin
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-shortcut'], 'BACKUPBUTTON', 'Back'])
        right_y += right_height + self.display.margin
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-ok'], 'PLAYERBUTTON', 'Next Player'])

        for button in buttons:
            # Blit Background rect
            self.display.blit_rect(button[0], button[1], button[2], button[3], button[4], 2, self.display.colorset['menu-buttons'], self.display.alpha)
            click_zones[button[5]] = (button[0], button[1], button[2], button[3], button[4])

            # Blit button
            self.display.blit_text(button[6], button[0], button[1], button[2], button[3], self.display.colorset['menu-text-white'])

        # Return Dict of tuples representing clickage values
        return click_zones

    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):

        self.display.reset_background()

        game = 'Cricket'
        hit = ''

        scores = players[actual_player].rounds
        mpr = players[actual_player].show_mpr()
        self.mpr = mpr

        game_background = f"background_{logo}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display.display_background(image=game_background)
            self.display.save_background()
        else:
            self.display.display_background()

        if len(players) > 6:
            left_x = self.margin
            left_y = int(self.display.res_y * 2 / 3) + self.margin
            left_w = int(self.display.res_x / 6) - left_x
            left_h = self.display.res_y - left_y
        else:
            left_x = self.margin
            left_y = self.margin
            left_w = int(self.display.res_x / 6) - left_x
            left_h = int(((self.display.res_y / 3) - left_y) * 1.2)

        mid_y = self.margin
        mid_h = int(self.display.res_y * 2 / 3) - mid_y

        if len(players) < 5:
            mid_x = int(self.display.res_x / 4)
            mid_w = int(self.display.res_x / 2)
        elif len(players) < 7:
            mid_x = int(self.display.res_x / 4)
            mid_w = int(self.display.res_x * 34 / 48)
        else:
            mid_x = int(self.display.res_x / 24)
            mid_w = int(self.display.res_x * 44 / 48)
            symbol_w = int(left_w / 6)
            symbol_h = int(left_h / 6)

        target_x = int(mid_x + (mid_w / 2)) - int(self.display.res_x / 32)
        target_y = mid_y + self.margin_2
        target_w = int(self.display.res_x / 16)
        target_h = int((mid_h - self.margin_4)/ 7)

        symbol_w = int(left_w / 4)
        symbol_h = int(left_h / 5)
        self.symbol_thickness = self.margin_2
        self.symbol_size = int(target_h * 3 / 4 - self.margin)
        self.symbol_thickness2 = self.symbol_thickness
        self.symbol_size2 = self.symbol_size
        if len(players) > 6:
            self.symbol_thickness2 = int(self.symbol_thickness / 2)
            self.symbol_size2 = int(self.symbol_size / 2)

        darts_x = int(self.display.res_x / 4)

        scores_m = int(self.display.res_x / 96)
        scores_x = mid_x + scores_m
        scores_y = mid_y + self.margin
        scores_w = int(self.display.res_x * 3 / 32)
        scores_h = mid_h - self.margin_2

        dart_x = int(darts_x + self.margin / 2)
        dart_x_increment = int(self.display.res_x / 6)
        dart_y = scores_y + scores_h + int(self.display.res_y / 32)
        dart_h = target_h
        dart_w = int(self.display.res_x / 6 - 2 * self.margin)

        # Game type
        game_width = int(self.display.res['x'] / 16)
        game_x = int((self.display.res['x'] - game_width) / 2)
        game_y = dart_y + dart_h + 2 * self.margin
        game_height = int(self.display.res['y'] / 24)

        # Background
        self.display.blit_rect(0, 0, self.display.res_x, self.display.res_y, self.display.colorset['game-bg'])

        # Round informations
        self.display.blit_rect(left_x, left_y, left_w, left_h, self.display.colorset['game-bg'])
        self.display.blit_text(f"Round", left_x, left_y, int(left_w / 3), left_h, color=self.display.colorset['game-round'], dafont='Impact', align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", left_x + int(left_w / 2), left_y, left_w - int(left_w / 2), int(left_h / 4), color=self.display.colorset['game-round'], dafont='Impact', align='Right', valign='top', margin=False)

        left_y += int(left_h / 5)

        mpr_rectangle = (left_x, left_y, left_w, symbol_h)
        self.display.blit_text(f'MPR', left_x, left_y, left_w, symbol_h, color=self.display.colorset['game-score'], dafont='Impact', align='Left')
        sub = self.display.screen.subsurface(mpr_rectangle)
        screenshot2 = pygame.Surface((mpr_rectangle[2], mpr_rectangle[3]))
        self.display.blit_screen(screenshot2, sub, (0, 0))
        self.display.blit_text(f'{mpr}', left_x , left_y, left_w, symbol_h, color=players[actual_player].color, dafont='Impact', align='Right')

        left_y += int(left_h / 5)
        rect_dart = None
        for index in range(3):
            if end_of_game:
                continue
            if actual_round - index > 0:
                text1 = f'R{actual_round - index}'
                score = 0
                self.display.blit_text(text1, left_x, left_y, symbol_w, symbol_h, color=self.display.colorset['game-score'], dafont='Impact', align='Left')
                index_s = 1
                for dartx in scores[actual_round - 1 - index]:
                    if dartx is not None and dartx[1::] in self.headers:
                        multiplier = self.get_hit_unit(dartx)
                        if multiplier > 0:
                            self.draw_symbol(players[actual_player].color, \
                                left_x + int(symbol_w / 2) + symbol_w * index_s, left_y + int(symbol_h / 2), \
                                int(self.symbol_size / 2), int(self.symbol_thickness / 2), multiplier)
                    elif dartx is not None:
                        self.draw_symbol(self.display.colorset['game-darts'], left_x + int(symbol_w / 2) + symbol_w * index_s, \
                                left_y + int(symbol_h / 2), int(self.symbol_size2 / 2), int(self.symbol_thickness2 / 2), -1)
                    elif rect_dart is None:
                        rect_dart = (left_x + symbol_w * index_s, left_y, symbol_w, symbol_h)

                    index_s += 1

            left_y += int(left_h / 5)

        # Scores part
        self.display.blit_rect(mid_x, mid_y, mid_w, mid_h, self.display.colorset['game-bg'])

        index = 0
        for target in self.headers:
            if index % 2 == 0:
                self.display.blit_rect(mid_x + self.margin, target_y + target_h * index, mid_w - self.margin_2, target_h, self.display.colorset['game-bg'])
            self.display.blit_text(f'{target}', target_x, target_y + target_h * index, target_w, target_h, color=self.display.colorset['game-score'], dafont='Impact', align='Center')
            index += 1

        index = 0
        for player in players:
            if index == int((len(players) + 1) / 2) or (len(players) == 2 and index == 1):
                scores_x += target_w + scores_m
            elif(len(players) == 2 and index == 0):
                scores_x += scores_w + scores_m

            players[index].scores_x = int(scores_x + scores_w / 2)

            if index == actual_player:
                rectangle_color = players[actual_player].color
            else:
                rectangle_color = self.display.colorset['game-player']
            self.draw_rect((scores_x, scores_y, scores_w, scores_h), 5, rectangle_color)

            index_c = 0
            for column in players[index].columns:
                if self.get_column_state(player.ident, players, index_c) == 4:
                    self.draw_symbol(self.display.colorset['game-player'], players[index].scores_x, target_y + target_h * index_c + int(target_h / 2), self.symbol_size, self.symbol_thickness, column[0])
                else:
                    self.draw_symbol(players[index].color, players[index].scores_x, target_y + target_h * index_c + int(target_h / 2), self.symbol_size, self.symbol_thickness, column[0])
                index_c += 1

            scores_x += scores_w + scores_m
            index += 1

        # For scrolling dart
        pos_y = dart_y + dart_h + self.margin
        height = int(self.display.res_y / 24)

        index_d = 0
        if not end_of_game:
            for dart in players[actual_player].darts:
                if dart is None:
                    if index_d == 0:
                        dart_color = self.display.colorset['game-gold']
                    elif index_d == 1:
                        dart_color = self.display.colorset['game-silver']
                    else:
                        dart_color = self.display.colorset['game-bronze']
                    self.display.blit_rect(dart_x + index_d * dart_x_increment, dart_y, dart_w, dart_h, self.display.colorset['game-bg'])
                    self.display.display_image(self.dart, dart_x + index_d * dart_x_increment, dart_y, dart_w, dart_h, center_x=True, change_colors=[[(0, 0, 0), dart_color]])
                    #pass
                else:
                    self.draw_dart_score(index_d, dart)
                index_d += 1

        right_x = int(self.display.res['x'] * 13 / 16)
        right_y = self.margin
        right_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        if not end_of_game:
            if self.display.game_type == 'online':
                self.display.display_image(self.online_icon, game_x - 40, game_y + self.margin, width=32, height=32, UseCache=True)
            self.display.blit_text(f"{self.display.game_type} game", game_x, game_y, game_width, game_height, color=(255, 0, 0), dafont='Impact', align='Center', valign='top', margin=False)

        self.display_players(players, actual_player, end_of_game)

        # On screen buttons
        if OnScreenButtons is True or self.display.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
            click = self.onscreen_buttons()

        # Game's options
        option_height = right_height / 2
        option_y = self.display.res['y'] - option_height

        if self.display.colorset['game-option'] is not None:
            for option, value in self.options.items():
                if option == 'theme':
                    continue
                if value is True:
                    self.display.blit_text(f'{game}-{option}', right_x, option_y, right_width, option_height, color=self.display.colorset['game-green'], dafont='Impact', align='Right')
                elif value is False:
                    self.display.blit_text(f'{game}-{option}', right_x, option_y, right_width, option_height, color=self.display.colorset['game-red'], dafont='Impact', align='Right')
                else:
                    self.display.blit_text(f'{self.display.lang.translate(game + "-" + option)} : {value}', right_x, option_y, right_width, option_height, color=self.display.colorset['game-option'], dafont='Impact', align='Right')
                option_y -= option_height
        self.display.blit_text(f"{game.replace('_', ' ')}", right_x, option_y - option_height, right_width, option_height * 2, color=(255, 0, 0), dafont='Impact', align='Right')

        self.display.save_background()
        self.display.update_screen()

        # scrolling dart
        rect1 = pygame.Rect(0, dart_y, self.display.res['x'], dart_h)
        sub = self.display.screen.subsurface(rect1)
        screenshot1 = pygame.Surface((self.display.res['x'], dart_h))
        self.display.blit_screen(screenshot1, sub, (0, 0))

        if rect_dart is not None:
            sub = self.display.screen.subsurface(rect_dart)
            screenshot3 = pygame.Surface((rect_dart[2], rect_dart[3]))
            self.display.blit_screen(screenshot3, sub, (0, 0))
        else:
            screenshot3 = None

        if end_of_game:
            click = self.display.end_of_game_menu()
            return click

        if OnScreenButtons is True or self.display.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
            return [click, [screenshot1, rect1], [screenshot2, mpr_rectangle], [screenshot3, rect_dart]]
        else:
            return [[], [screenshot1, rect1], [screenshot2, mpr_rectangle], [screenshot3, rect_dart]]

    def display_players(self, players, actual_player, end_of_game):

        heading_color = self.display.colorset['game-bg']
        player_color = self.display.colorset['game-alt-headers']
        # Display players and scores
        player_width = int(self.display.res['x'] / max(2 * len(players), 6))
        player_height = int(self.display.res['y'] / 8)
        heading_height = int(self.display.res['y'] / 24)
        players_x = int(self.display.res['x'] / 4 + (self.display.res['x'] / 2 - player_width * len(players)) / 2)
        player_y = self.display.res_y - player_height - self.margin

        if end_of_game:
            player_y = self.display.res_y - 2 * player_height - self.margin
        else:
            player_y = self.display.res_y - player_height - self.margin

        index = 0
        for player in players:
            color = player.color
            if self.show_mpr :
                if self.mpr:
                    mpr = player.show_mpr()
                    name = f'{player.name} - {mpr}'
                else:
                    name = f'{player.name} - 0.0'
            else:
                name = f'{player.name}'

            score = player.score
            player_x = players_x + index * player_width
            if index != actual_player:
                if index < actual_player:
                    player_x -= int(player_width / 2)
                else:
                    player_x += int(player_width / 2)

                self.display.blit_rect(player_x, player_y, player_width, heading_height, heading_color)
                self.display.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, player_color)

                if self.display.colorset['game-bg'] is not None:
                    pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
                    pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
                    pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)

                if index < actual_player:
                    self.display.blit_text(name, player_x, player_y - self.margin, player_width, heading_height + self.margin_2, color=player_color, dafont='Impact', align='Left')
                    self.display.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=self.display.colorset['game-score'], dafont='Impact', align='Left')
                else:
                    self.display.blit_text(name, player_x, player_y - self.margin, player_width, heading_height + self.margin_2, color=player_color, dafont='Impact', align='Right')
                    self.display.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=self.display.colorset['game-score'], dafont='Impact', align='Right')
                pygame.draw.line(self.display.screen, color, (player_x, player_y), (player_x + player_width, player_y), 8)
            else:
                # For actual player's infos
                actual_color = color
                actual_x = player_x - int(player_width / 2)
                actual_name = name
                actual_score = score
            index += 1

        # Actual player and his score
        player_x = int(self.display.res['x'] / 4 + (self.display.res['x'] / 2 - player_width * len(players)) / 2) + actual_player * player_width - (player_width / 2)
        player_x = actual_x
        player_y -= self.margin
        player_height += self.margin_2
        player_width *= 2
        dart_icon_size = player_height - heading_height - self.margin_2
        self.display.blit_rect(player_x, player_y, player_width, heading_height, actual_color)
        self.display.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, actual_color)
        if self.display.colorset['game-bg'] is not None:
            pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
            pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
            pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)
        self.display.display_image(self.dart_icon, player_x + self.margin, player_y + heading_height + self.margin, width=dart_icon_size, height=dart_icon_size, UseCache=True)
        self.display.blit_text(actual_name, player_x, player_y - self.margin, player_width, heading_height + self.margin_2, color=self.display.colorset['game-player-name'], dafont='Impact', align='Center')
        self.display.blit_text(actual_score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=self.display.colorset['game-score'], dafont='Impact', align='Right')

        return (player_x, player_y, player_width, player_height)

    def display_hit(self, rectangles, players, actual_player, player_launch, hit):
        """
        Nice hit animation
        """

        if hit == 'MISSDART':
            return
        screenshot1 = rectangles[1][0]
        rect1 = rectangles[1][1]

        screenshot_mpr = rectangles[2][0]
        rectangle_mpr = rectangles[2][1]

        screenshot_dart = rectangles[3][0]
        rectangle_dart = rectangles[3][1]

        mpr = players[actual_player].show_mpr()

        width, height = self.display.display_image(self.trail, 0, rect1[1], rect1[2], rect1[3], UseCache=True)
        # Image movement step
        nb_steps = 15
        step = int((self.display.res['x'] + width) / nb_steps)

        sens = -1
        min_x = int(self.display.res['x'])
        max_x = -width

        hit_x = int(self.display.res['x'] / 4) - self.margin_2
        hit_y = int(self.display.res['y'] / 4) - self.margin_2
        hit_w = self.display.mid_x + 4 * self.margin
        hit_h = self.display.mid_y + 4 * self.margin

        mid_x = int(self.display.res_x / 4)
        mid_y = self.margin
        mid_w = self.display.mid_x
        mid_h = int(self.display.res_y * 2 / 3) - mid_y

        target_x = self.display.mid_x - int(self.display.res_x / 32)
        target_y = mid_y + self.margin_2
        target_w = int(self.display.res_x / 16)
        target_h = int((mid_h - self.margin_4)/ 7)

        scores_m = int(self.display.res_x / 96)
        scores_x = mid_x + scores_m
        scores_y = mid_y + self.margin
        scores_w = int(self.display.res_x * 3 / 32)
        scores_h = mid_h - self.margin_2

        mid_x = int(self.display.res['x'] / 4) + self.margin
        mid_y = int(self.display.res['y'] * 3 / 4) + self.margin

        mid_width = self.display.mid_x - self.margin_2
        mid_height = int(self.display.res['y'] / 4) - self.margin_2

        symbol_size = int(target_h * 3 / 4 - self.margin)
        self.symbol_thickness = self.margin_2

        rect_players = self.display_players(players, actual_player, False)
        self.display.update_screen(rect=rect_players)


        if hit[1::] in self.headers:
            # column touched
            column_hit = self.headers.index(hit[1::])
        else:
            column_hit = None

        index = 0
        for index in range(0, nb_steps + 2):
            ratio = min(1, index / nb_steps)
            dart_x = min_x + step * sens * index

            # Scrolling dart
            rect = (dart_x, rect1[1] , rect1[2] + 4 * step, rect1[3])
            self.display.blit(screenshot1, (rect1[0], rect1[1]))
            self.draw_dart_score(player_launch - 1, hit)

            self.display.display_image(self.trail, dart_x, rect1[1], rect1[2], rect1[3], UseCache=True)
            if index == nb_steps + 1:
                act_mpr = mpr
            else:
                act_mpr = round(self.mpr + (mpr - self.mpr) / (nb_steps + 1 - index), 2)
            self.display.blit(screenshot_mpr, (rectangle_mpr[0] , rectangle_mpr[1]))
            self.display.blit_text(f'{act_mpr}', rectangle_mpr[0] , rectangle_mpr[1], rectangle_mpr[2], rectangle_mpr[3], color=players[actual_player].color, dafont='Impact', align='Right')

            multiplier = self.get_hit_unit(hit)
            pos_x = int(rectangle_dart[0] + rectangle_dart[2] / 2)
            pos_y = int(rectangle_dart[1] + rectangle_dart[3] / 2)
            if column_hit is None:
                self.draw_symbol(self.display.colorset['game-darts'], pos_x, pos_y, int(self.symbol_size / 2), int(self.symbol_thickness / 2), -1, ratio=ratio)
            else:
                self.draw_symbol(players[actual_player].color, pos_x, pos_y, int(self.symbol_size2 / 2), int(self.symbol_thickness2 / 2), multiplier, ratio=ratio)

            # Dart's symbol
            if column_hit is not None and self.ok:
                hit_x = players[actual_player].scores_x
                hit_y = target_y + target_h * column_hit + int(target_h / 2)
                self.draw_symbol(players[actual_player].color, hit_x, hit_y, self.symbol_size, self.symbol_thickness, players[actual_player].columns[column_hit][0], ratio=ratio)
                rect2 = (hit_x - symbol_size, hit_y - symbol_size, 2 * symbol_size, 2 * symbol_size)
                rect_array = [rect, rect2, rectangle_mpr, rectangle_dart]
            else:
                rect_array = [rect, rectangle_mpr, rectangle_dart]

            self.display.update_screen(rect_array=rect_array)
            index += 1

        self.display.save_background()
