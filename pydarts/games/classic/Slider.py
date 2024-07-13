########## reste a faire
# ligne 260 - ajouter condition si on touche S ou D et cie pour les autres
# verifier si victoire en 10 tours
# verifier victoire si touche 20 ou bull
# modifier/refaire early bouton 
### mettre info NB fleche jouee et nombre fleche restante 
### tester avec double et triple active et apres avec toutes les options

# -*- coding: utf-8 -*-
# Game by ... LaDite
########
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############

OPTIONS = {'theme': 'default', 'max_round': 20, 'start': '10', 'double': False, 'triple': False, 'jump': False, 'master': False, 'bull': False}

GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Slider.png'
HEADERS = ["D1", "D2", "D3", "", "Rnd", "", "JOUE"] # Columns headers - Must be a string

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
        
        self.character = 0
        

class Game(cgame.Game):
    """
    bowling game class
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
        self.winner = None
        self.video_player = video_player
        
### declaration variable 
        self.next = 0
        self.rate = 0
        self.gagne = False
        self.player_launch = 0
        self.repetition = True
        
        self.options = options
        self.leds = str(options['start'])
        self.double = options['double']
        self.triple = options['triple']
        self.saut = options['jump']
        self.master = options['master']
        self.bull = options['bull']

        
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

        if not players[actual_player].alive:
            self.logs.log("DEBUG", f'Le joueur {actual_player} est éliminé. Il passe son tour')
            return 4
            
        if player_launch == 1:
            players[actual_player].reset_darts()
            self.rate = 0
            self.repetition = True

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
                player.leds = self.leds
                player.lives = 0
                player.alive = True

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

       # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')

### GESTION PLAYERS.LEDS MAX
        if int(players[actual_player].leds) >= 21 and self.bull :
                players[actual_player].columns[6] = ('B', 'txt') 
        elif int(players[actual_player].leds) >= 21 and not self.bull :
                players[actual_player].leds = 20
                players[actual_player].columns[6] = (players[actual_player].leds, 'int') 
        else :
                players[actual_player].columns[6] = (players[actual_player].leds, 'int')

### GESTION DES LEDS        
        if self.bull and int(players[actual_player].leds) == 21 :
                self.rpi.set_target_leds ('')
                leds = f'SB#green|DB#green'
                self.rpi.set_target_leds (leds)
        elif self.double and not self.triple :
                self.rpi.set_target_leds ('')
                leds = f'D{players[actual_player].leds}#green'
                self.rpi.set_target_leds(leds)
        elif self.triple and not self.double :
                self.rpi.set_target_leds ('')
                leds = f'T{players[actual_player].leds}#green'
                self.rpi.set_target_leds(leds)
        elif self.double and self.triple :
                self.rpi.set_target_leds ('')
                leds = f'D{players[actual_player].leds}#green|T{players[actual_player].leds}#green'
                self.rpi.set_target_leds(leds)
        else :
                self.rpi.set_target_leds ('')
                leds = f'S{players[actual_player].leds}#green|D{players[actual_player].leds}#green|T{players[actual_player].leds}#green'
                self.rpi.set_target_leds(leds)

        # Print debug output
        self.logs.log("DEBUG",self.infos)
        return return_code

        self.player_launch = player_launch
        
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

### TOUCHE LE BON SEGMENT       
        if hit[1:] == 'B' and self.bull and int(players[actual_player].leds) == 21 :
                if hit == 'SB' :
                        score = 5
                elif hit == 'DB' :
                        score = 8
                        
                self.gagne = True
                
        elif (hit[1:]) == players[actual_player].leds and players[actual_player].leds != '20' :
                if self.double and not self.triple :
                        if hit[:1] == 'D' :
                                score = 4
                                saut = 2 
                        else :
                                score = 0
                                saut = 0
                elif self.triple and not self.double :
                        if hit[:1] == 'T' :
                                score = 6
                                saut = 3 
                        else :
                                score = 0
                                saut = 0
                                
                elif self.double and self.triple :
                        if hit[:1] == 'D' :
                                score = 4
                                saut = 2
                        elif hit[:1] == 'T' :
                                score = 6
                                saut = 3
                        else :
                                score = 0
                                saut = 0
                                        
                elif not self.triple and not self.double :
                        if hit[:1] == 'S' :
                                score = 1
                                saut = 1
                        elif hit[:1] == 'D' :
                                score = 2
                                saut = 2
                        elif hit[:1] == 'T' :
                                score = 3  
                                saut = 3 
                        else : 
                                score = 0
                                saut = 0
                else :
                        score = 0
                        saut = 0
                        
                if self.saut :
                        a = int(players[actual_player].leds)
                        b = a + saut 
                        players[actual_player].leds = str(b) 
                else :
                        a = int(players[actual_player].leds)
                        b = a + saut 
                        players[actual_player].leds = str(b)        
   
        elif (hit[1:]) == '20' and players[actual_player].leds == '20' :
                if self.double :
                        if hit[:1] == 'D' :
                                score = 4
                                saut = 2 
                        else :
                                score = 0
                                saut = 0
                elif self.triple :
                        if hit[:1] == 'T' :
                                score = 6
                                saut = 3 
                        else :
                                score = 0
                                saut = 0
                elif not self.triple and not self.double :
                        if hit[:1] == 'S' :
                                score = 1
                                saut = 1
                        elif hit[:1] == 'D' :
                                score = 2
                                saut = 2
                        elif hit[:1] == 'T' :
                                score = 3  
                                saut = 3  
                        #else :
                        #        score = 0
                        #        saut = 0
                                    
                else :
                        score = 0
                        saut = 0
                
                ### SI SELF.BULL EST ACTIVE ON NE GAGNE PAS AVEC LE 20        
                if self.bull :
                        self.gagne = False
                else :
                        self.gagne = True
                
                ### GESTION D SAUT QD ON TOUCHE
                if self.saut :
                        a = int(players[actual_player].leds)
                        b = a + saut 
                        players[actual_player].leds = str(b) 
                else :
                        a = int(players[actual_player].leds)
                        b = a + saut 
                        players[actual_player].leds = str(b)

        else :
                
                score = 0
                ### GESTION DU SAUT QD ON RATE
                if self.master :
                        if hit[:1] == 'S' :
                                saut = 1
                        elif hit[:1] == 'D' :
                                saut = 2
                        elif hit[:1] == 'T' :
                                saut = 3  
                        
                        a = int(players[actual_player].leds)
                        b = a - saut
                        players[actual_player].leds = str(b) 
                else :
                        self.rate += 1
                 
                ### QD ON RATE 3x LE SEGMENT
                if self.rate == 3 :
                        a = int(players[actual_player].leds)
                        b = a - 1 
                        players[actual_player].leds = str(b) 

        if self.bull :
                if int(players[actual_player].leds) >= 21 :
                        players[actual_player].leds = 21
                        
                                      
        ### pour determiner si on passe au joueur suivant selon ce qu on a touche
        return_code = self.next
              
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score
####        
        players[actual_player].columns[6] = (players[actual_player].leds, 'int')

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Calculate average and display in column 7

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)
        
        #### JOUEUR DEAD --- arrete de jouer
        if int(players[actual_player].leds) <= 0 :
                players[actual_player].alive = False
                players[actual_player].columns[5] = ('skull', 'image')

            #Someone is dead, is ther a winner ?
                self.winner = self.check_winner(players)
                if self.winner > -1:
                        self.infos += "Here is a winner"
                        return_code = 3
                if len(players) == 1:
                        return 2
                
        self.player_launch = player_launch
### pour determiner si on passe au joueur suivant selon ce qu on a touche
        return_code = self.next


        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1 or self.gagne == True:
                winner = self.best_score(players)
                if winner >= 0:
                        self.winner = winner
                        return_code = 3
                else:
                        # No winner : last round reached
                        return_code = 2

        return return_code

    def early_player_button(self, players, actual_player, actual_round):
        
        if self.master and self.repetition :
                print('early - saut = true')
                print('player_launch =')
                print(self.player_launch)
                if self.player_launch == 0 :
                        print('player launch = 1 doit descendre de 3')
                        a = int(players[actual_player].leds)
                        b = a - 3
                        players[actual_player].leds = str(b)
                        players[actual_player].columns[6] = (players[actual_player].leds, 'int') 
                        self.repetition = False
                elif self.player_launch == 1 :
                        print('player launch = 2 doit descendre de 2')
                        a = int(players[actual_player].leds)
                        b = a - 2
                        players[actual_player].leds = str(b) 
                        players[actual_player].columns[6] = (players[actual_player].leds, 'int')
                        self.repetition = False
                elif self.player_launch == 2 :
                        print('player launch = 3 doit descendre de 1')
                        a = int(players[actual_player].leds)
                        b = a - 1 
                        players[actual_player].leds = str(b) 
                        players[actual_player].columns[6] = (players[actual_player].leds, 'int')
                        self.repetition = False
        if not self.master and self.repetition :
                print('self.rate = ')
                print(self.rate)
                if self.rate == 2 or self.rate == 1 :
                        print('rate est a 0 - descend de 1 car rien touche')
                        a = int(players[actual_player].leds)
                        b = a - 1 
                        players[actual_player].leds = str(b)
                        players[actual_player].columns[6] = (players[actual_player].leds, 'int') 
                        self.repetition = False
                
        return 1
             
                                   
    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        if actual_round >= int(self.max_round) and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2


    def check_winner(self, players, last_round=False):
        """
        Last round (or not) : who is the winner ?
        Last alive player
        or
        best score at last round
        """
        nb_alive = 0
        last_alive = -1
        for player in players:
            if player.alive:
                nb_alive += 1
                last_alive = player.ident

        if nb_alive == 1:
            return last_alive
        if not last_round:
            return -1

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

        return best_player




    '''
    def find_deads(self, players):
        """
        Sudden death option :
        After each round, the lowest score (if alone) is killed
        """
        min_score = None
        nb_min = 0
        for i in range(0, len(players)):
            if not players[i].alive:
                continue

            if min_score is None:
                min_score = players[i].score
                dead = i
                nb_min = 1
            elif players[i].score == min_score:
                nb_min += 1
            elif players[i].score < min_score:
                min_score = players[i].score
                dead = i
                nb_min = 1

        if nb_min == 1:
            players[dead].lives -= 1
            #players[dead].columns[3] = (players[dead].lives, 'int')
            if players[dead].lives < 1:
                return dead
            return None
        return None


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
    '''   
     
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
