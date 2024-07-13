# -*- coding: utf-8 -*-
# Game by ... laDite!
########
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############
OPTIONS = {'theme': 'default', 'max_round': 10, 'winscore': 300, 'simple50': False, 'points': False, 'points_advs': False, 'penalite': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Color.png'
HEADERS = ['D1', 'D2', 'D3', '', '', '', ''] # Columns headers - Must be a string

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

class Game(cgame.Game):
    """
    Color game class
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
        
        self.points_advs = options['points_advs']
        self.penalite = options['penalite']
        self.points = options['points']

        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None
        self.winscore = int(options['winscore'])
        self.video_player = video_player
        self.targets = ''
        self.leds = True

  
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
        
        if player_launch == 1:
            players[actual_player].reset_darts()
   
        if actual_round in (1, 3, 5, 7, 9) : 
                
                Sbull = [f'SB#green']
                Dbull = [f'DB#green']
                hits_blancS = [20,18,13,10,2,3,7,8,14,12]
                hits_blancDT = [1,4,6,15,17,19,16,11,9,5]
                hits_bleuS = [1,4,6,15,17,19,16,11,9,5]
                hits_bleuDT = [20,18,13,10,2,3,7,8,14,12]
                        
                hits_j1S = [f'S{hit}#green' for hit in hits_blancS]
                hits_j1DT = [f'{mult}{hit}#green' for hit in hits_blancDT for mult in ['D', 'T']]
                
                hits_j2S = [f'S{hit}#red' for hit in hits_bleuS]
                hits_j2DT = [f'{mult}{hit}#red' for hit in hits_bleuDT for mult in ['D', 'T']]
            
                led = hits_j1S + hits_j1DT + hits_j2S + hits_j2DT + Sbull + Dbull
                #leds = '|'.join(led)
                
                '''
                Sbull = [f'SB#green']
                Dbull = [f'DB#green']
                               
                hits_j1 = [20,18,13,10,2,3,7,8,14,12]
                hits_j2 = [1,4,6,15,17,19,16,11,9,5]
                
                hits_j1 = [f'{mult}{hit}#{self.colors[0]}' for hit in hits_j1 for mult in ['S', 'D', 'T']]
                hits_j2 = [f'{mult}{hit}#{self.colors[1]}' for hit in hits_j2 for mult in ['S', 'D', 'T']]
                '''
                #self.targets =  hits_j1 + hits_j2 + Sbull + Dbull
                self.targets = led
        else:
                '''
                Sbull = [f'SB#green']
                Dbull = [f'DB#green']
                               
                hits_j2 = [20,18,13,10,2,3,7,8,14,12]
                hits_j1 = [1,4,6,15,17,19,16,11,9,5]
                
                hits_j1 = [f'{mult}{hit}#{self.colors[0]}' for hit in hits_j1 for mult in ['S', 'D', 'T']]
                hits_j2 = [f'{mult}{hit}#{self.colors[1]}' for hit in hits_j2 for mult in ['S', 'D', 'T']]
                                
                self.targets =  hits_j1 + hits_j2 + Sbull + Dbull
                '''
                Sbull = [f'SB#green']
                Dbull = [f'DB#green']
                hits_blancS = [20,18,13,10,2,3,7,8,14,12]
                hits_blancDT = [1,4,6,15,17,19,16,11,9,5]
                hits_bleuS = [1,4,6,15,17,19,16,11,9,5]
                hits_bleuDT = [20,18,13,10,2,3,7,8,14,12]
                        
                hits_j1S = [f'S{hit}#red' for hit in hits_blancS]
                hits_j1DT = [f'{mult}{hit}#red' for hit in hits_blancDT for mult in ['D', 'T']]
                
                hits_j2S = [f'S{hit}#green' for hit in hits_bleuS]
                hits_j2DT = [f'{mult}{hit}#green' for hit in hits_bleuDT for mult in ['D', 'T']]
            
                led = hits_j1S + hits_j1DT + hits_j2S + hits_j2DT + Sbull + Dbull
                self.targets = led
                
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
                player.bouclier = False
                # Lives

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            for player in players :
                    player.columns = []
                    # clean all box
                    for i in range(0,7):
                            player.columns.append(['', 'int'])
            
            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])
            
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)
 
        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')
        
        # Print debug output
        self.logs.log("DEBUG",self.infos)
        
        self.rpi.set_target_leds('|'.join(self.targets))
        
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
        self.display.sound_for_touch(hit)

        score = 0
        
        multi = 1
        if hit[:1] == 'D':
            multi = 2
        if hit[:1] == 'T':
            multi = 3
                
                     
        if (hit+'#green') in self.targets :
                if self.points :
                        score = 10 * multi
                else :
                        score = self.score_map[hit] 
                        
        else :
                if self.points_advs and not self.penalite :
                        # points pour l advs
                        for player in players :
                                if player.ident != players[actual_player].ident : 
                                        if self.points :
                                                player.score += 10 * multi
                                                player.columns[player_launch - 1] = (10 * multi, 'int')
                                        else :
                                                player.score += self.score_map[hit] 
                                                player.columns[player_launch - 1] = (self.score_map[hit], 'int' )
                                        score = 0
                                        
                elif self.penalite and not self.points_advs :
                        #perte de points (penalite)
                        if self.points :
                                score -= 10 * multi 
                        else :
                                score -= self.score_map[hit]
                                
                elif self.penalite and self.points_advs :
                        #points pourl advs
                        for player in players :
                                if player.ident != players[actual_player].ident : 
                                        if self.points :
                                                player.score += 10 * multi
                                                player.columns[player_launch - 1] = (10 * multi, 'int')
                                        else :
                                                player.score += self.score_map[hit] 
                                                player.columns[player_launch - 1] = (self.score_map[hit], 'int' )

                        # perte de points (penalite)
                        if self.points :
                                score -= 10 * multi 
                        else :
                                score -= self.score_map[hit]
                else :
                        score=0

        return_code = 0
        
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)
        '''
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
        '''
        #return return_code
        
                # Check last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and (player_launch == self.nb_darts or return_code == 1):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            return_code = 2
        # Check winner
        self.check_winner(players, actual_player, player_launch)
        if self.winner is not None:
            return_code = 3

        self.logs.log("DEBUG", self.infos)
        
        return return_code

    def check_winner(self, players, actual_player, player_launch):
        '''
        Function to check winner
        '''
        self.winner = None
        # Check winner if no master option
        if players[actual_player].score >= self.winscore :
            self.winner = players[actual_player].ident
        
        
        

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2
    
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

    def display_segment(self):
       """
       Set if a message is shown to indicate the segment hitted !
       """
       return False
