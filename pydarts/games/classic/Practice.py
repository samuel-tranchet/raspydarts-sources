# -*- coding: utf-8 -*-
# Game by ... Poilou !
# Options by ... LaDite
########
from include import cplayer
from include import cgame
import collections# To use OrderedDict to sort players from the last score they add
import random# To choose wich hit to play
import pygame

from copy import deepcopy

from include import cstats
from include import chandicap


LOGO = 'Practice.png' # Background image - relative to images folder
HEADERS = [ 'Try', 'D1', 'D2', 'D3', '-', '-', '-'] # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'max_round': 10, 'master': False, 'bulls': False, 'double': False, 'triple': False, 'threeonthebed': False, 'suite': False, 'voisin': False} # Dictionnay of options in string format

GAME_RECORDS = {'Hits per round': 'DESC', 'MPR': 'DESC'} # Dictionnary of stats (For exemple, avg is displayed in descending order)
NB_DARTS = 3


class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Read the CJoueur class parameters, and add here yours if needed
        # Init all the Game stats
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    Your Game's Class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # GameRecords is a descriptive dictionnary of stats to display at the end of a game
        self.GameRecords = GAME_RECORDS
        # Local data
        self.logo = LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS # Total darts the player has to play
        self.options = options
        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        # For rpi
        self.rpi = rpi
        # Master ?
        self.master = options['master']
        #self.finish=options['finish']
        self.bulls = options['bulls']
        self.triple = options['triple']
        self.double = options['double']
        self.threeonthebed = options['threeonthebed']
        self.suite = options['suite']
        self.voisin = options['voisin']
        self.toucher = 0
        self.target = []
        
        ### ajout ho one
        self.max_round = int(options['max_round'])
        self.split_bull = False
        self.double_out = False
        self.master_out = False
        self.double_in = True
        self.master_in = False
        #self.starting_at = int(options['startingat'])
        self.starting_at = random.randint(40, 177)

            
        self.league = False
        self.zap = False
        self.frozen = False
        self.infos = ""
        self.winner = None
        self.finish = False
        if not self.split_bull:
            self.score_map.update({'SB': 50})
            
            
#### interdit les multiple choix des options  
        if self.bulls :
            #options['split_bull'] = False
            #options['finish'] = False
            options['bulls'] = True
            options['triple'] = False
            options['double'] = False
            options['threeonthebed'] = False
            options['master'] = False
            options['suite'] = False
            options['voisin'] = False
        elif self.double :
            #options['split_bull'] = False
            #options['finish'] = False
            options['bulls'] = False
            options['triple'] = False
            options['double'] = True
            options['threeonthebed'] = False
            options['master'] = False
            options['suite'] = False
            options['voisin'] = False
        elif self.triple :
            #options['split_bull'] = False
            #options['finish'] = False
            options['bulls'] = False
            options['triple'] = True
            options['double'] = False
            options['threeonthebed'] = False
            options['master'] = False 
            options['suite'] = False
            options['voisin'] = False 
        elif self.threeonthebed :
            #options['split_bull'] = False
            #options['finish'] = False
            options['bulls'] = False
            options['triple'] = False
            options['double'] = False
            options['threeonthebed'] = True
            options['master'] = False
            options['suite'] = False
            options['voisin'] = False
        elif self.suite :
            #options['split_bull'] = False
            #options['finish'] = False
            options['bulls'] = False
            options['triple'] = False
            options['double'] = False
            options['threeonthebed'] = False
            options['master'] = False
            options['suite'] = True
            options['voisin'] = False    
        elif self.voisin :
            #options['split_bull'] = False
            #options['finish'] = False
            options['bulls'] = False
            options['triple'] = False
            options['double'] = False
            options['threeonthebed'] = False
            options['master'] = False
            options['suite'] = False
            options['voisin'] = True   
            
        self.master = options['master']
        #self.finish = options['finish']
        self.bulls = options['bulls']
        self.triple = options['triple']
        self.double = options['double']
        self.threeonthebed = options['threeonthebed']
        self.suite = options['suite'] 
        self.voisin = options['voisin'] 
        
        self.target_suite = [[1, 2, 3],[2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, 8], [7, 8, 9], [8, 9, 10], [9, 10, 11], [10, 11, 12], [11, 12, 13], [12, 13, 14], [13, 14, 15], [14, 15, 16], [15, 16, 17], [16, 17, 18], [17, 18, 19], [18, 19, 20]]
        self.target_voisin = [[1, 18, 4], [18, 4, 13], [4, 13, 6], [13, 6, 10], [6, 10, 15], [10, 15, 2], [15, 2, 17], [2, 17, 3], [17, 3, 19], [3, 19, 7], [19, 7, 16], [7, 16, 8], [16, 8, 11], [8, 11, 14], [11, 14, 9], [14, 9, 12], [9, 12, 5], [12, 5, 20]]

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        if not self.finish :
            
            if player_launch == 1:
                players[actual_player].reset_darts()
                if actual_round == 1 and actual_player == 0:
                    for player in players:
                        player.reset_rounds(self.max_round)
    
            return_code = 0
            # You will probably save the turn to be used in case of backup turn (each first launch) :
            if player_launch == 1:
                self.save_turn(players)
                rand = random.randint(1, 22)
                
#### GETSION BULLS
                if self.bulls :
                    rand = 21
#### GESTION TRIPLE                    
                if self.triple :
                    text = 'Trpl'
                    rand = '|'.join(f'T{number}#{self.colors[0]}' for number in range(1, 21))
#### GESTION DOUBLE
                if self.double :
                    text = 'Dbl'
                    rand = '|'.join(f'D{number}#{self.colors[0]}' for number in range(1, 21))
#### GESTION 3 ON THE BED
                if self.threeonthebed :
                    rand = random.randint(1, 22)
                    self.toucher = 0
                    
#### GESTION SUITE
                if self.suite :
                    rand = random.choice(self.target_suite)
                    self.target = rand
                    print('self.target - suite')
                    print(self.target)
                    self.toucher = 0
#### GESTION VOISIN
                if self.voisin :
                    rand = random.choice(self.target_voisin)
                    self.target = rand
                    print('self.target - voisin')
                    print(self.target)
                    self.toucher = 0

                    
                if rand == 21 and self.master:
                    rand = 'SB'
                elif rand == 22 and self.master:
                    rand = 'DB'
                elif rand in (21, 22):
                    rand = 'B'
                elif not(self.master):
                    rand = f'{rand}'
                else:
                    randMultiple = random.randint(1, 3)
                    if randMultiple == 1:
                        rand = f'S{rand}'
                    elif randMultiple == 2:
                        rand = f'D{rand}'
                    elif randMultiple == 3:
                        rand = f'T{rand}'
    
                if not(self.random_from_net):
                    # Clean table of any previousinformation
                    for Column, Value in enumerate(players[actual_player].columns):
                        players[actual_player].columns[Column] = ('', 'txt')
                    # Then Rand it
                    players[actual_player].columns[0] = (rand, 'txt')
#### GESTION TRIPLE
                    if self.triple :
                        players[actual_player].columns[0] = ('Trpl', 'txt')
#### GESTION DOUBLE
                    if self.double :
                        players[actual_player].columns[0] = ('Dbl', 'txt')
#### GESTION SUITE
                    if self.suite :
                        players[actual_player].columns[0] = ('Suite', 'txt') 
#### GESTION VOISIN                    
                    if self.voisin :
                        players[actual_player].columns[0] = ('Voisin', 'txt')
                        
                if not self.suite and not self.voisin :
                    if rand[:1] in ('S', 'D', 'T'):
                        self.rpi.set_target_leds(f"{rand}#{self.colors[0]}")
                    else:
                        self.rpi.set_target_leds('|'.join([f"{m}{rand}#{self.colors[0]}" for m in ('S', 'D', 'T')]))

                #score = 90

#### GESTION SUITE OU VOISIN
            if self.suite or self.voisin :
                if len(self.target) == 3 :
                    leds = f'S'+str(self.target[0])+'#green', 'D'+str(self.target[0])+'#green', 'T'+str(self.target[0])+'#green', 'S'+str(self.target[1])+'#green', 'D'+str(self.target[1])+'#green', 'T'+str(self.target[1])+'#green', 'S'+str(self.target[2])+'#green', 'D'+str(self.target[2])+'#green', 'T'+str(self.target[2])+'#green'
                elif len(self.target) == 2 :
                    leds = f'S'+str(self.target[0])+'#green', 'D'+str(self.target[0])+'#green', 'T'+str(self.target[0])+'#green', 'S'+str(self.target[1])+'#green', 'D'+str(self.target[1])+'#green', 'T'+str(self.target[1])+'#green'
                if len(self.target) == 1 :
                    leds = f'S'+str(self.target[0])+'#green', 'D'+str(self.target[0])+'#green', 'T'+str(self.target[0])+'#green'
                
                self.rpi.set_target_leds('|'.join(leds))
   
            #return return_code

        # Print debug output
        self.logs.log("DEBUG", self.infos)
        return return_code
                

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """

        if not self.finish :
            
            return_code = 0
    
            # Apply the coefficient to simple double triple and bull (Master case)
            if self.master:
                if hit[:1] in ('s', 'S'):
                    hitcoeff = 1
                elif hit[:1] == 'D':
                    hitcoeff = 3
                elif hit[:1] == 'T':
                    hitcoeff = 6
                if hit == 'SB':
                    hitcoeff = 5
                elif hit == 'DB':
                    hitcoeff = 10
    
            # Apply the coefficient to simple double triple and bull (No Master case)
            else:
                if hit[:1] in ('s', 'S'):
                    hitcoeff = 1
                elif hit[:1] == 'D':
                    hitcoeff = 2
                elif hit[:1] == 'T':
                    hitcoeff = 3
                if hit == 'SB' and self.bulls :
                    hitcoeff = 3
                elif hit == 'DB' and self.bulls:
                    hitcoeff = 3
            # GOOD HIT
            if not self.triple and not self.double and not self.threeonthebed and not self.suite and not self.voisin :
                
                if (self.master and hit == players[actual_player].get_col_value(0)) or (not(self.master) and (hit[1:] == players[actual_player].get_col_value(0))):
                    # Keep it for Stats
                    players[actual_player].increment_hits(hit)
                    # Play sound if touch is valid
                    self.display.sound_for_touch(hit) # Play sound
                    # Add value score (score equals hits in this game)
                    players[actual_player].score += hitcoeff
                    # Display hits on screen
                    players[actual_player].columns[player_launch] = (f"+{hitcoeff}", 'txt')
                    if super(Game, self).play_show(players[actual_player].darts, hit, play_special=True):
                        self.display.sound_for_touch(hit) # Good start !
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=hitcoeff, check=True)
                else:
                    self.display.play_sound('plouf')
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=0, check=False)
                    players[actual_player].columns[player_launch] = ("cross-mark", 'image')
    

### GESTION TRIPLE
            if self.triple :
                if (hit[:1] == 'T'):
                    # Keep it for Stats
                    players[actual_player].increment_hits(hit)
                    # Play sound if touch is valid
                    self.display.sound_for_touch(hit) # Play sound
                    # Add value score (score equals hits in this game)
                    hitcoeff = 3
                    players[actual_player].score += hitcoeff
                    # Display hits on screen
                    players[actual_player].columns[player_launch] = (f"+{hitcoeff}", 'txt')
                    if super(Game, self).play_show(players[actual_player].darts, hit, play_special=True):
                        self.display.sound_for_touch(hit) # Good start !
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=hitcoeff, check=True)
                else:
                    self.display.play_sound('plouf')
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=0, check=False)
                    players[actual_player].columns[player_launch] = ("cross-mark", 'image')
#### GESTION DOUBLE            
            if self.double :
                if (hit[:1] == 'D'):
                    # Keep it for Stats
                    players[actual_player].increment_hits(hit)
                    # Play sound if touch is valid
                    self.display.sound_for_touch(hit) # Play sound
                    # Add value score (score equals hits in this game)
                    hitcoeff = 3
                    players[actual_player].score += hitcoeff
                    # Display hits on screen
                    players[actual_player].columns[player_launch] = (f"+{hitcoeff}", 'txt')
                    if super(Game, self).play_show(players[actual_player].darts, hit, play_special=True):
                        self.display.sound_for_touch(hit) # Good start !
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=hitcoeff, check=True)
                else:
                    self.display.play_sound('plouf')
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=0, check=False)
                    players[actual_player].columns[player_launch] = ("cross-mark", 'image')

#### GESTION THREE ON THE BED
            if self.threeonthebed :
                
                if (self.master and hit == players[actual_player].get_col_value(0)) or (not(self.master) and (hit[1:] == players[actual_player].get_col_value(0))):
                        # Keep it for Stats
                        players[actual_player].increment_hits(hit)
                        # Play sound if touch is valid
                        self.display.sound_for_touch(hit) # Play sound
                        self.toucher += 1
                        ### gestion nb de touche
                        if self.toucher == 3 :
                            # Add value score (score equals hits in this game)
                            players[actual_player].score += 3
                            self.toucher = 0
                            
                        # Display hits on screen
                        #players[actual_player].columns[player_launch] = (f"+{hitcoeff}", 'txt')
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        if super(Game, self).play_show(players[actual_player].darts, hit, play_special=True):
                            self.display.sound_for_touch(hit) # Good start !
                        players[actual_player].add_dart(actual_round, player_launch, hit, score=hitcoeff, check=True)
                else:
                    self.display.play_sound('plouf')
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=0, check=False)
                    players[actual_player].columns[player_launch] = ("cross-mark", 'image')
        
#### GESTION SUITE OU VOISIN
            if self.suite or self.voisin :
                if int(hit[1:]) in self.target :
                        # Keep it for Stats
                        players[actual_player].increment_hits(hit)
                        # Play sound if touch is valid
                        self.display.sound_for_touch(hit) # Play sound
                        self.toucher += 1
                        ### gestion nb de touche
                        if self.toucher == 3 :
                            # Add value score (score equals hits in this game)
                            players[actual_player].score += 3
                            self.toucher = 0
                            
                        # Display hits on screen
                        #players[actual_player].columns[player_launch] = (f"+{hitcoeff}", 'txt')
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        if super(Game, self).play_show(players[actual_player].darts, hit, play_special=True):
                            self.display.sound_for_touch(hit) # Good start !
                        players[actual_player].add_dart(actual_round, player_launch, hit, score=hitcoeff, check=True)
                        
                        try :
                            while True :
                                suppr = int(hit[1:])
                                self.target.remove(suppr)
                        except:
                            pass        
                else:
                    self.display.play_sound('plouf')
                    players[actual_player].add_dart(actual_round, player_launch, hit, score=0, check=False)
                    players[actual_player].columns[player_launch] = ("cross-mark", 'image')

                    
            # Check for end of game (no more rounds to play)
            if player_launch >= self.nb_darts and actual_round >= self.max_round and actual_player >= len(players) - 1:
                bestscoreid = -1
                bestscore = -1
                for player in players:
                    if player.score > bestscore:
                        bestscore = player.score
                        bestscoreid = player.ident
                self.winner = bestscoreid
                pourcent = int((bestscore / 3))
                self.display.message([self.display.lang.translate('Practice-pourcent')+ str(pourcent) + ' fois '], 5000, None, 'middle', 'big')
                return_code = 3
    
            # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
            players[actual_player].darts_thrown += 1
            self.refresh_stats(players, actual_round)
    
            return return_code
        
    

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        Whan missed button pressed
        """
        self.logs.log("DEBUG", f"MissButtonPressed : {player_launch}")
        players[actual_player].columns[player_launch - 1] = ('tyre', 'image')
        players[actual_player].darts_thrown += 1
        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
        self.refresh_stats(players, actual_round)

    def update_stats(self, players, actual_player, hit):
        """
        Updates PPR / PPD ...
        """
        try:
            score = self.score_map[hit]
        except: # pylint: disable=bare-except
            score = 0
        players[actual_player].round_points += score
        players[actual_player].points += score
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')


    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh Each player.stat
        """
        for player in players:
            player.stats['Hits per round'] = player.hits_per_round(actual_round)
            player.stats['MPR'] = player.show_mpr()

    def get_random(self, players, actual_round, actual_player, player_launch):
        """
        Returns Random things, to send to clients in case of a network game
        """
        if player_launch == 1:
            return players[actual_player].get_col_value(0)
        else:
            return None

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        """
        Set Random things, while received by master in case of a network game
        """
        if data is not None:
            players[actual_player].columns[0] = (data, 'txt')
            self.logs.log("DEBUG", "Setting random value for player {actual_player} to {data}")
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
        new_order = collections.OrderedDict(sorted(scores.items(), key=lambda t: t[1]))# For DESC order, add "reverse=True" to the sorted() function
        return list(new_order.keys())

    def check_handicap(self, players):
        """
        Check for handicap and record appropriate marks for player
        """
        pass
        
    def mate(self, actual_player, nb_players):
        """
        Find your teammate
        """
        mate = -1
        if actual_player < nb_players / 2:
            mate = actual_player + nb_players / 2
        else:
            mate = actual_player - nb_players / 2
        return int(mate)

    def get_score(self, player):
        """
        Return score of player
        """
        return player.score


  
