# -*- coding: utf-8 -*-
# Game by ... you !
########
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############
OPTIONS = {'theme': 'default', 'max_round': 10, 'simple50': False, 'segment': False, 'lives': 3}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'BIG 6.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Rnd', '', ''] # Columns headers - Must be a string

class CPlayerExtended(cplayer.Player):
    """
    Exetended player class
    """
    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        # Extend the basic players property with your own here
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return 1 < nb_players < 13


class Game(cgame.Game):
    """
    High score game class
    """
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
        
        self.sudden_death = True ###options['suddendeath']
        self.lives = int(options['lives'])

        if self.sudden_death:
            self.headers[3] = 'Vies'

        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})
            
        self.segment = options['segment']
            
        if self.segment :
                self.targets = ['S6#green', 'D6#green', 'T6#green']
        else :
                self.targets = ['S6#green']
        
        self.check = False
        self.miss = 1
        self.nextplayer = False
        
        self.winner = None

        self.video_player = video_player
        

            
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
        
                                
        print('self.targets')
        print (self.targets)
                       

                        
        if player_launch == 1:
            players[actual_player].reset_darts()
            self.check = False
            #reinitialise le compteur miss
            self.miss = 1
            print('self.nextplayer')
            print(self.nextplayer)
            
            ### si joueur n a pas touche de segment avec ses fleches 2 et 3
            if self.targets == [''] :
                    if self.segment :
                            self.targets = ['S6#green', 'D6#green', 'T6#green']
                    else :
                            self.targets = ['S6#green']

        if not players[actual_player].alive:
            # Player is dead
            return 4

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
                # Lives
                player.lives = self.lives
                player.alive = True
                player.columns[3] = (player.lives, 'int')

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score


            
            

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

### affiche les targets du joueur  
        print('self.targets - predarts')
        print(self.targets)
        self.rpi.set_target_leds ('')
        self.rpi.set_target_leds('|'.join(self.targets))
        
        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')


        if self.sudden_death:
            players[actual_player].columns[3] = (players[actual_player].lives, 'int')
            
        # Print debug output
        self.logs.log("DEBUG",self.infos)
        

        
        return return_code

    def pnj_score(self, players, actual_player, level, player_launch):
        """
        pnj score
        """
        letters = 'SDT'
        value = random.randint(1, 20)
        multi = ''.join(random.choice(letters) for _ in range(1))
        bull = random.randint(0, 100)
        if 85 < bull <= 95:
            return 'SB'
        if bull > 95:
            return 'DB'
        return f'{multi}{value}'

    def best_score(self, players):
        """
        Find the winner
        Only one player with best score
        """
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
                self.logs.log("DEBUG", \
                        f"Best found : {best_score} / Count={best_count} / player = {best_player}")
            elif player.score == best_score:
                best_count += 1

        self.logs.log("DEBUG", \
                f"Best score : {best_score} / Count={best_count} / Player = {best_player}")

        if best_count == 1:
            return best_player
        return -1

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """

        # Play DMD animation
        if super().play_show(players[actual_player].darts, hit, play_special=True):
            self.display.sound_for_touch(hit)

            
                
        print('hit')
        print(hit)
        score = 0
        

        
        
        if (hit+'#green') in self.targets and not self.check :   
                print('dans condition chiffre touche')

                score = self.score_map[hit]
                
                S = ['S1#green', 'S2#green', 'S3#green', 'S4#green', 'S5#green', 'S6#green', 'S7#green', 'S8#green', 'S9#green', 'S10#green', 'S11#green', 'S12#green', 'S13#green', 'S14#green', 'S15#green', 'S16#green', 'S17#green', 'S18#green', 'S19#green', 'S20#green']
                D = ['D1#green', 'D2#green', 'D3#green', 'D4#green', 'D5#green', 'D6#green', 'D7#green', 'D8#green', 'D9#green', 'D10#green', 'D11#green', 'D12#green', 'D13#green', 'D14#green', 'D15#green', 'D16#green', 'D17#green', 'D18#green', 'D19#green', 'D20#green']
                T = ['T1#green', 'T2#green', 'T3#green', 'T4#green', 'T5#green', 'T6#green', 'T7#green', 'T8#green', 'T9#green', 'T10#green', 'T11#green', 'T12#green', 'T13#green', 'T14#green', 'T15#green', 'T16#green', 'T17#green', 'T18#green', 'T19#green', 'T20#green']
                
                
                self.targets = S + D + T
                
                self.rpi.set_target_leds ('')
                self.rpi.set_target_leds('|'.join(self.targets))   
                
                print('score')
                print(score)
                self.check = True

        
        if (hit) and self.check and player_launch != 1 :
                
                print('dans condition hit + self.check')
                 
                #self.targets = ['S'+hit[1:]+'#green', 'D'+hit[1:]+'#green', 'T'+hit[:1]+'#green']
                if self.segment :
                        self.targets = ['s'+hit[1:]+'#green', 'S'+hit[1:]+'#green', 'D'+hit[1:]+'#green', 'T'+hit[1:]+'#green']
                        
                else :
                        self.targets = [hit+'#green']
                
                #self.targets = [hit+'#green']
                
                print('self.targets')
                print(self.targets)
                
                self.rpi.set_target_leds ('')
                self.rpi.set_target_leds('|'.join(self.targets))   
                
                #self.rpi.set_target_leds ('')
                #self.rpi.set_target_leds('|'.join(self.targets))  
                
                score = self.score_map[hit]
        
        self.rpi.set_target_leds ('')
        self.rpi.set_target_leds('|'.join(self.targets))       
               
        return_code = 0


        if not self.check :
                self.miss += 1
                
        if self.miss > 3 :
                if self.segment :
                        self.targets = ['S6#green', 'D6#green', 'T6#green']
                else :
                        self.targets = ['S6#green']
                
                players[actual_player].lives -= 1
                players[actual_player].columns[3] = (players[actual_player].lives, 'int')
                self.miss = 1
        
        if players[actual_player].lives == 0 :
                    players[actual_player].alive = False 
                    players[actual_player].columns[3] = ('big6_skull', 'image')

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score
        


        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Calculate average and display in column 7
        
        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner >= 0:
                self.winner = winner
                return_code = 3
            else:
                # No winner : last round reached
                return_code = 2

        return return_code

    def early_player_button(self, players, actual_player, actual_round):
        

        if self.segment :
                self.targets = ['S6#green', 'D6#green', 'T6#green']
        else :
                self.targets = ['S6#green']
                

    
    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        
        
        if self.sudden_death:
            if players[actual_player].lives == 0 :
                    players[actual_player].alive = False 
   
            winner = self.get_winner(players)
            if winner is not None:
                self.winner = winner
                self.logs.log("DEBUG", f"winner is {winner}")
                return winner
        elif actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2

    
    def get_winner(self, players):
        """
        Sudden death option :
        After each round, the winner is the last alive player
        """
        nb_winner = 0
        for i in range(0, len(players)):
            if players[i].alive:
                winner = i
                nb_winner += 1

        if nb_winner == 1:
            return winner
        return None

    def get_score(self, player):
        """
        Return score of player
        """
        return player.score

    def next_set_order(self, players):
        """
        Sort players for next set
        """
        players.sort(key=self.get_score)

    def refresh_stats(self, players, actual_round):
        """
        refresh players' stats
        """
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)
            player.stats['Points Per Dart'] = player.show_ppd()
