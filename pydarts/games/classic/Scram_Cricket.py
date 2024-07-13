# -*- coding: utf-8 -*-
'''
Game by Cory Baumgart
'''
import collections
import random
from include import cplayer
from include import cgame

LOGO = 'Cricket.png' # Background image - relative to images folder
HEADERS = ['20', '19', '18', '17', '16', '15', 'B']
OPTIONS = {'theme': 'default', 'optioncrazy' : False, 'cutthroat': False, 'drinkscore': 200, 'teaming': False}
NB_DARTS = 3 # How many darts the player is allowed to throw
SWITCH_TURNS = False #used to determine if players switched their turns
SWITCHED = False #used to say the switch happened
GAME_RECORDS = {'MPR':'DESC','Score':'DESC'}

def check_players_allowed(nb_players):
    '''
    Check if number of players is ok according to options
    '''
    return nb_players in (2, 4)

class CPlayerExtended(cplayer.Player):
    '''
    Extended player class
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Flag used to know if player has reached the drink score
        self.pay_drink = False
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    '''
    Scram cricket game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.nb_darts = NB_DARTS # Total darts the player has to play
        self.logo = LOGO
        self.headers = HEADERS
        # GameRecords is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS

        self.options = options
        self.teaming = options['teaming']
        self.cutthroat = options['cutthroat']
        self.option_crazy = options['optioncrazy']
        self.drink_score = int(options['drinkscore'])

        # TEMP - place it somwhere else - prevent option to be activated in case of odd
        # number of players
        if nb_players >= 4 and nb_players % 2 == 0 and self.teaming:
            # Enable display of teaming
            self.display.teaming = True
        elif self.teaming:
            self.logs.log('ERROR','You asked for a team game but the number of players is not \
                    a multiple of 2 players and is not at least 4 people. Disabling teaming')
            self.teaming = False
        # Fixed number of round
        self.max_round = 99
        self.switch_turns = SWITCH_TURNS
        self.switched = SWITCHED
        # For rpi
        self.rpi = rpi

        self.infos = ''
        self.winner = None

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Post dart method
        '''
        players[actual_player].add_dart(actual_round, player_launch, hit)

        #Init
        play_closed = False # Should we play the closed sound ?
        blink_text = ""
        handler = self.init_handler()
        touchcount4total = False
        self.infos = f"Player {players[actual_player].name} -"
        self.infos += f"Score before playing: {players[actual_player].score}{self.lf}"
        #We put in a variable the affected column
        to_add, value = self.split_key(hit, multiplier=True)

        #If this column is currently displayed - Valid key
        if value in self.headers:
            # column touched
            col_touched = self.headers.index(value)

            # Add points ?
            overtouched = max(players[actual_player].get_col_value(col_touched) + to_add - 3, 0)

            # Increase column
            if players[actual_player].get_col_value(col_touched) < 3:
                players[actual_player].increment_column_touch(col_touched, \
                        min(to_add, 3 - players[actual_player].get_col_value(col_touched)))
                if players[actual_player].get_col_value(col_touched) == 3:
                    play_closed = True

            # Add hit
            players[actual_player].increment_hits()
            players[actual_player].roundhits += 1

            #Look for the column corresponding to the value (return a string)

            #If there is a surplus
            if overtouched > 0:
                for player in players:
                    # Check if this players has closed
                    nb_touch = player.get_col_value(col_touched)

                    # Identify this player's teammate
                    mate = self.mate(player.ident, len(players))

                    # Check if his mate has closed too
                    your_mate_close = players[mate].get_col_value(col_touched)

                    # Multiply the single touch by the number of times the player touched above 3
                    overtouchedpts = overtouched * int(self.score_map[f'S{value}'])

                    # Given that we will also give the teammates (Cut-Throat),
                    # we divide the total points to be given by two if teaming
                    if self.teaming and self.cutthroat:
                        overtouchedpts = overtouchedpts / 2
                    # If Cut Throat and the other team have not closed we add the points to others
                    if self.cutthroat and ((nb_touch < 3 and not self.teaming) \
                            or (self.teaming and your_mate_close >= 3 and nb_touch < 3)):
                        # Points are added to those who do not close
                        self.infos += f"Player {player.ident} takes {overtouchedpts} \
                                points in the nose ! (Cut-throat){self.lf}"
                        player.add_score(overtouchedpts)
                        # Give half points to teammate too if teaming is enabled
                        if self.teaming:
                            players[mate].add_score(overtouchedpts)# And give him half of point too
                            self.infos += f"TeamMate {mate} takes {overtouchedpts} \
                                    points in the nose too ! (Cut-throat){self.lf}"
                        # If players take points, the keys count for the player's total
                        touchcount4total = True
                    # If not Cut Throat we add the points to him only (+ possibly his teammate)
                    # if he is not closed for all
                    elif not self.cutthroat and player.ident == players[actual_player].ident \
                            and (not self.teaming or (self.teaming and your_mate_close >= 3)):
                        totally_closed = True
                        #Check if the gate is totally closed for normal mode
                        for player2 in players:
                            # Identify people who require to be scored (only closed guys and
                            # teammates won't be scored)
                            if player2.get_col_value(col_touched) < 3 and \
                                    (not self.teaming or (self.teaming and player2.ident != mate)):
                                totally_closed = False
                        # If you there is still someone who didn't closed, take score for you
                        # (and your teammate)
                        if not totally_closed:
                            self.infos += f"This player get {overtouchedpts} extra score !{self.lf}"
                            player.add_score(overtouchedpts)
                            # Give half points to your teammate too if teaming is enabled
                            if self.teaming:
                                # And give him half of point too
                                players[mate].add_score(overtouchedpts)
                                self.infos += f"TeamMate {mate} takes {overtouchedpts} points !"
                                self.infos += f"{self.lf}"
                            touchcount4total = True
                    # For fun, if the player reached the required drink score (usually 500),
                    # tell him to pay a drink !
                    if not player.pay_drink and player.score >= self.drink_score and self.cutthroat:
                        player.pay_drink = True
                        handler['sound'] = 'diegoaimaboir'

            # Sound handling to avoid multiple sounds playing at a time
            # # Play sound only once, even if multiple to_add, and only
            # if another sound is not played at the moment
            if play_closed:
                handler['sound'] = 'closed'
            else:
                handler['show'] = (players[actual_player].darts, hit, True)
                handler['sound'] = hit

            self.infos += f"Key: {players[actual_player].get_touch_type(hit)} - \
                    Active Columns: {self.headers}{self.lf}"
            self.infos += f"Total number of hits for this player: \
                    {players[actual_player].get_total_hit()}{self.lf}"
            self.infos += f"Number of darts thrown from this player: {player_launch}{self.lf}"

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players)

        # If it was last throw and no touch : play sound for "round missed"
        if player_launch == self.nb_darts and players[actual_player].roundhits == 0:
            handler['sound'] = 'chaussette'

        # Last throw of the last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == self.nb_darts:
            self.infos += f"Last Round Reached ({actual_round}){self.lf}"
            handler['return_code'] = 2

        # Check if there is a winner
        if self.switched:
            self.check_winner(players)
            if self.winner is not None:
                handler['return_code'] = 3

        # Check if its time to switch turns
        else:
            self.switch_turns = self.switch_turn(players)
            self.infos += f"Switch turns says: {self.switch_turns}{self.lf}"
            if self.switch_turns:
                blink_text = 'Lets switch it up!'
                self.infos += 'Switching players\n'
                if actual_player in (0, 2):
                    self.infos += 'Player 1 is current player\n'
                    return_code = 1
                self.clear_marks(players)

        # If there is blink text to display
        if blink_text != "":
            handler['message'] = blink_text

        # Print debug
        self.logs.log('DEBUG', self.infos)
        return handler

    def clear_marks(self, players):
        '''
        Clear player 1's marks
        '''
        for col in range(0, self.nbcol + 1):
            players[0].columns[col] = [0, 'leds', 'game-grey2']

        if self.teaming:
            for col in range(0, self.nbcol+1):
                players[2].columns[col] = [0, 'leds', 'game-grey2']

        self.switch_turns = False
        self.switched = True

    def switch_turn(self, players):
        '''
        check if we switch turns
        '''
        for columns in players[1].columns:
            if columns[0] != 3:
                return False

        return True

    def check_winner(self, players):
        '''
        Method to check if there is a winnner
        '''
        actual_winner = None
        #Find the better score
        for player in players:
            if actual_winner is None \
                    or (player.score < players[actual_winner].score and self.cutthroat):
                actual_winner = player.ident
            elif actual_winner is None \
                    or (player.score > players[actual_winner].score and not self.cutthroat):
                actual_winner = player.ident

        #Check if the player who have the better score has closed all gates
        for columns in players[actual_winner].columns:
            if columns[0] != 3:
                return
        self.winner = actual_winner
        return

    def random_header(self,players,bypass=False):
        '''
        Generate random headers for open columns
        '''
        for index in range(0, int(self.nbcol)):
            # Check whether the Crazy doors are open or closed and assign
            # new numbers to open and unclosed columns
            unmarked = False
            marked = False
            if bypass:
                unmarked = True
            else:
                for player in players:
                    if player.get_col_value(index) in [1, 2, 3]:
                        marked = True
                        self.infos += f"Column {index} is marked for player {player.name}! \
                                Leave it alone!{self.lf}"
                    else:
                        unmarked = True
                        self.infos += f"Column {index} is open for player {player.name}! \
                                Randomize.{self.lf}"

            #If column is open, randomize number
            if not marked and unmarked:
                self.infos += f"Opened column : {index} Random !{self.lf}"
                randomisdone = False
                while not randomisdone:
                    random_number = random.randint(1, 20)
                    if str(random_number) not in self.headers:
                        self.headers[index] = str(random_number)
                        randomisdone = True
            else:
                self.infos += f"Closed column: {index} Not changed!{self.lf}"

    def get_column_state(self, actual_player, players, col):
        '''
        Get state of column. It can be :
        1 : Not open
        2 : Open,
        3 : Closed by a player or a team
        4 : Closed by everybody
        '''
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
        '''
        Action launched before each dart throw
        '''
        return_code = 0
        self.infos = ""

        if player_launch == 1:
            players[actual_player].reset_darts()

        # If first round - set display as leds
        if player_launch == 1 and actual_round == 1 and actual_player == 0:
            for player in players:
                for index in range(0, self.nbcol + 1):
                    player.columns[index] = [0, 'leds', 'game-grey2']
                    player.reset_rounds(self.max_round)


            for column in range(0, self.nbcol + 1):
                players[actual_player].columns[column] = [3, 'leds', 'game-grey2']
                if self.teaming:
                    mate = self.mate(actual_player, len(players))
                    players[mate].columns[column] = [3, 'leds', 'game-grey2']

        if player_launch == 1:
            # Reset number of hits in this round for this player
            players[actual_player].roundhits = 0
            # Heading definition according to these cases
            if self.option_crazy and actual_round == 1 and actual_player == 0 \
                    and player_launch == 1 and not self.random_from_net:
                self.random_header(players, True)
            # Definition of header - random if option crazy = 1
            elif self.option_crazy and not self.random_from_net:
                self.random_header(players)
            self.infos += f"Active columns : {self.headers}"
            self.logs.log("DEBUG", self.infos)
            self.save_turn(players)

            leds = []
            ind = 0
            closed = 0
            player_scores = False
            already_closed = False
            # On détermine s'il s'agit du joueur qui doit marquer des points
            for hed in self.headers:
                if players[actual_player].get_col_value(ind) >= 3:
                    closed += 1
                ind += 1
            if closed == len(self.headers):
                player_scores = True
            index = 0
            for header in self.headers:
                if player_scores:
                    already_closed = (self.get_column_state(actual_player, players, index) in (3, 4))
                    print(f"col {index} : {self.get_column_state(actual_player, players, index)}")
                    print(f"already_closed = {already_closed}")
                    # Pour le joueur devant marquer
                    if players[actual_player].get_col_value(index) >= 3 and not already_closed:
                        if header == 'B':
                            leds.append('B')
                        else:
                            leds.append(header)
                else:
                    # Pour le joueur devant ouvrir les segments
                    if players[actual_player].get_col_value(index) < 3:
                        if header == 'B':
                            leds.append('B')
                        else:
                            leds.append(header)
                index += 1
            self.rpi.set_target_leds('|'.join(f'{mult}{key}#{self.colors[0]}' for key in leds \
                    for mult in ('S', 'D', 'T') if f'{mult}{key}' != 'TB'))

        return return_code

    def early_player_button(self, players, actual_player, actual_round):
        '''
        If player Hit the Player button before having threw all his darts
        '''
        # Next player by default
        return_code = 1
        # If no touch for this player at this round : play sound for "round missed"
        if players[actual_player].roundhits == 0:
            self.display.play_sound('chaussette')
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            # If its a early_player_button just at the last round - return GameOver
            return 2
        return return_code

    def refresh_stats(self, players):
        '''
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        '''
        for player in players:
            player.stats['MPR'] = player.show_mpr()
            player.stats['Score'] = player.score

    def get_random(self, players, actual_round, actual_player, player_launch):
        '''
        Returns and Random things, to send to clients in case of a network game
        '''
        if self.option_crazy:
            return self.headers
        return False

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        '''
        Set Random things, while received by master in case of a network game
        '''
        if data is not False:
            self.headers = data
            self.random_from_net = True

    def mate(self, actual_player, nb_players):
        '''
        Find TeamMate in case of teaming
        '''
        mate = -1
        if self.teaming:
            if actual_player < nb_players / 2:
                mate = int(actual_player + nb_players / 2)
            else:
                mate = int(actual_player - nb_players / 2)
        return mate

    def check_players_allowed(self, nb_players):
        '''
        Check if number of players is ok according to options
        '''
        if (self.teaming and nb_players != 4) or (not self.teaming and nb_players != 2):
            return False
        return True
