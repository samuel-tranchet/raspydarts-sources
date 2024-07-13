# -*- coding: utf-8 -*-
# Game by ... laDite!
########
import random
from include import cplayer
from include import cgame

############
# Game Variables
############
OPTIONS = {'theme': 'default', 'max_round': 8}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Challenge.png'
HEADERS = ['Jeu', 'D1', 'D2', 'D3', 'Pts', '', ''] # Columns headers - Must be a string

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
    CHALLENGES game class
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
        
        '''
        self.simple = False
        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})
        '''
        
        self.winner = None

        self.video_player = video_player

        ### MINI JEUX
        self.jeux = [['onedart'], ['threedarts'], ['onebulls'], ['threebulls'], ['suite'], ['voisin'], ['lower'], ['inferieur'], ['impair'],
                ['onetriple'], ['onedouble'], ['onesimple'], ['fortune1'], ['fortune2'], ['score_determine'], ['under'], ['oneanimal'], ['color_blue'],
                ['threetriple'], ['threedouble'], ['threesimple'], ['onebombe'], ['777'], ['multiple'], ['superieur'], ['pair'], ['color_white']]

        target_suite = [[1, 2, 3],[2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, 8], [7, 8, 9], [8, 9, 10], [9, 10, 11], [10, 11, 12], [11, 12, 13], [12, 13, 14], [13, 14, 15], [14, 15, 16], [15, 16, 17], [16, 17, 18], [17, 18, 19], [18, 19, 20]]
        target_voisin = [[1, 18, 4], [18, 4, 13], [4, 13, 6], [13, 6, 10], [6, 10, 15], [10, 15, 2], [15, 2, 17], [2, 17, 3], [17, 3, 19], [3, 19, 7], [19, 7, 16], [7, 16, 8], [16, 8, 11], [8, 11, 14], [11, 14, 9], [14, 9, 12], [9, 12, 5], [12, 5, 20]]
        
        self.target_bombe0 = [1,18,4,13,6,10,15,2,17,3]
        self.target_bombe1 = [19,7,16,8,11,14,9,12,5,20]
        self.target_bombe2 = [11,14,9,12,5,20,1,18,4,13]
        self.target_bombe3 = [6,10,15,2,17,3,19,7,16,8]
        self.target_bombeall = {"self.target_bombe0":self.target_bombe0, "self.target_bombe1":self.target_bombe1, "self.target_bombe2":self.target_bombe2, "self.target_bombe3":self.target_bombe3}
        
        self.target_multiple3 = [3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57,60]
        self.target_multiple4 = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]
        self.target_multiple5 = [5,10,15,20,25,30,35,40,45,50,55,60]
        self.target_multiple6 = [6,12,18,24,30,36,42,48,54,60]
        self.target_multiple8 = [8,16,24,32,40,48,54]
        self.target_multiple9 = [9,18,27,36,45,54]
        self.target_multipleall = {"self.target_multiple3":self.target_multiple3, "self.target_multiple4":self.target_multiple4, "self.target_multiple5":self.target_multiple5, "self.target_multiple6":self.target_multiple6, "self.target_multiple8":self.target_multiple8, "self.target_multiple9":self.target_multiple9}
        ### 8 et 9 pas pris en compte, a effacer car peu de chiffre
        self.multiple = random.randint(3, 6)
        
        self.color_white = ['S20','S18','S13','S10','S2','S3','S7','S8','S14','S12','D1','D4','D6','D15','D17','D19','D16','D11','D9','D5','T1','T4','T6','T15','T17','T19','T16','T11','T9','T5']
        self.color_blue = ['S1','S4','S6','S15','S17','S19','S16','S11','S9','S5','D20','D18','D13','D10','D2','D3','D7','D8','D14','D12','T20','T18','T13','T10','T2','T3','T7','T8','T14','T12']
        self.possible_hits = []
        self.all_chiffre = ['20', '1', '18', '4', '13', '6', '10', '15', '2', '17', '3', '19', '7', '16', '8', '11', '14', '9', '12', '5']
        #self.toucher = 0
        self.score2 = 0
        self.chiffre = random.randint(1, 20)
        self.chiffre2 = random.randint(1, 20)
        
        self.target_suite = random.choice(target_suite)
        self.target_suit1 = self.target_suite[0]  
        self.target_suit2 = self.target_suite[1]
        self.target_suit3 = self.target_suite[2]
        
        self.target_voisin = random.choice(target_voisin)
        self.target_voisin1 = self.target_voisin[0]  
        self.target_voisin2 = self.target_voisin[1]
        self.target_voisin3 = self.target_voisin[2]
               
        self.score_min = random.randint(40, 60)
        self.score_max = random.randint(61, 100)
        
        self.superieur = random.randint(40, 50)
        self.inferieur = random.randint(40, 50)
        self.under = random.randint(40, 80)
        self.lower = random.randint(10, 30)
        self.seven77 = random.randint(710,737)
        self.check777 = False
        self.fleche = 0
        self.fleche1 = 0
        self.fleche2 = 0
        self.fleche3 = 0
        
        self.animal = random.randint(1, 20)
        self.ttt = False

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

        if player_launch == 1:
            players[actual_player].reset_darts()

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
                player.seven77 = self.seven77
        
        ### CHOIX DU MINI JEU ET SUPPRESSION DE CELUI CI DANS LA LISTE
        if player_launch == 1 and actual_player == 0 :
            random.shuffle(self.jeux)   
            self.jeuchoisi = random.choice(self.jeux)   ###['color_blue'] ['threebulls']  ###
            print('JEU CHOISI') 
            print(self.jeuchoisi)
               
            try :
                    while True :
                            suppr = self.jeuchoisi
                            self.jeux.remove(suppr)
            except:
                    pass 
                    
            for player in players:
                for c in range(0, 7):
                    player.columns[c] = ['' , 'txt']  
                      
        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score
            self.score2 = 0 
            self.target_suite = [self.target_suit1, self.target_suit2, self.target_suit3]      
            self.target_voisin = [self.target_voisin1, self.target_voisin2, self.target_voisin3]
            self.check777 = False
            
            if self.jeuchoisi == ['inferieur'] :
                    self.fleche = self.inferieur
            else :
                    self.fleche = 0 
             
            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 7):
                for player in players: 
                    player.columns.append(['', 'int'])
                    
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)


        ### affiche D1-D2-D3 suivant les jeux en cours 
        if self.jeuchoisi != ['fortune1'] or self.jeuchoisi != ['fortune2'] or self.jeuchoisi != ['animal']:
                self.headers[3] = 'D3'
                self.headers[2] = 'D2'
                self.headers[1] = 'D1'
                self.headers[5] = '-'
                self.headers[6] = '-'
        ### affiche si colonne 4 = PTS ou SCORE selon le jeu en cours     
        if self.jeuchoisi == ['suite'] or self.jeuchoisi == ['voisin'] or self.jeuchoisi == ['inferieur'] or self.jeuchoisi == ['superieur'] or self.jeuchoisi == ['onetriple'] or self.jeuchoisi == ['threetriple'] or self.jeuchoisi == ['onedouble']  or self.jeuchoisi == ['threedouble'] or self.jeuchoisi == ['onebombe'] or self.jeuchoisi == ['oneanimal'] :
                self.headers[4] = "Pts"
        else :
                self.headers[4] = "SCORE"
                
### GESTION DES MINI JEUX EN PREDARTS                
        if self.jeuchoisi == ['onedart'] or self.jeuchoisi == ['threedarts']:
                text = 'Score'
                leds = '|'.join(f'S{number}#{self.colors[0]}|D{number}#{self.colors[0]}|T{number}#{self.colors[0]}' for number in range(1, 21))
                
                if self.jeuchoisi == ['onedart'] :
                        self.headers[1] = 'D1'
                        self.headers[2] = '-'
                        self.headers[3] = '-'
                else :
                        self.headers[1] = 'D1'
                        self.headers[2] = 'D2'
                        self.headers[3] = 'D3'
                
        elif self.jeuchoisi == ['score_determine'] :
                text = 'Entre 2'
                self.headers[4] = 'SCORE'     
                self.headers[5] = 'Min'
                self.headers[6] = 'Max'   
                
                #### tirs possibles
                if self.score2 > self.score_min and self.score2 < self.score_max :
                        players[actual_player].min_score = self.score_max - self.score2
                elif self.score2 < self.score_min :
                        players[actual_player].min_score = self.score_min - self.score2
                elif self.score2 > self.score_max :
                        self.rpi.set_target_leds('')        
                
                possibilities = self.get_possibilitirs(players[actual_player].min_score)
                if len(possibilities)> 0:
                        self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                                for key in possibilities]))
                else:
                        self.rpi.set_target_leds('')

                ### infos colonnes
                players[actual_player].columns[5] = (self.score_min, 'int')
                players[actual_player].columns[6] = (self.score_max, 'int')
                
        elif self.jeuchoisi == ['fortune1'] or self.jeuchoisi == ['fortune2'] :
                if self.jeuchoisi == ['fortune1'] : 
                        self.headers[3] = 'x15'
                        self.headers[2] = 'x10'
                        self.headers[1] = 'x5'
                else :
                        self.headers[3] = 'x3'
                        self.headers[2] = 'x2'
                        self.headers[1] = 'x1'
                        
                text = 'Fortune'
                leds = '|'.join(f'S{number}#{self.colors[0]}|D{number}#{self.colors[0]}|T{number}#{self.colors[0]}' for number in range(1, 21))


        elif self.jeuchoisi == ['onebulls'] or self.jeuchoisi == ['threebulls'] :
                leds = f'SB#{self.colors[0]}|DB#{self.colors[0]}'
                text = 'Bull'
                
                if self.jeuchoisi == ['onebulls'] :
                        self.headers[1] = 'B'
                        self.headers[2] = '-' 
                        self.headers[3] = '-' 
                else :
                        self.headers[1] = 'B'
                        self.headers[2] = 'B'
                        self.headers[3] = 'B'
        
               
        elif self.jeuchoisi == ['onetriple'] or self.jeuchoisi == ['threetriple']:
                text = 'Triple'
                leds = '|'.join(f'T{number}#{self.colors[0]}' for number in range(1, 21))
                
                if self.jeuchoisi == ['onetriple'] :
                        self.headers[1] = 'Trp'
                        self.headers[2] = '-'
                        self.headers[3] = '-'
                else :
                        self.headers[1] = 'Trp'
                        self.headers[2] = 'Trp'
                        self.headers[3] = 'Trp'  
        
                
        elif self.jeuchoisi == ['onedouble'] or self.jeuchoisi == ['threedouble'] :
                text = 'Double'
                leds = '|'.join(f'D{number}#{self.colors[0]}' for number in range(1, 21))
                
                if self.jeuchoisi == ['onedouble'] :
                        self.headers[1] = 'Dbl'
                        self.headers[2] = '-'
                        self.headers[3] = '-'
                else :
                        self.headers[1] = 'Dbl'
                        self.headers[2] = 'Dbl'
                        self.headers[3] = 'Dbl'

        
        elif self.jeuchoisi == ['onesimple'] or self.jeuchoisi == ['threesimple'] :
                if self.jeuchoisi == ['onesimple'] :
                        leds = f'S{self.chiffre}#{self.colors[0]}'
                        text = 'S' + str(self.chiffre) 
                        self.headers[1] = 'S' + str(self.chiffre)
                        self.headers[2] = '-'
                        self.headers[3] = '-'
                else : 
                        leds = f'S{self.chiffre2}#{self.colors[0]}'
                        text = 'S' + str(self.chiffre2) 
                        self.headers[1] = 'S' + str(self.chiffre2)
                        self.headers[2] = 'S' + str(self.chiffre2)
                        self.headers[3] = 'S' + str(self.chiffre2)
        
                
        elif self.jeuchoisi == ['suite'] :
                text = 'Suite'
                
                if len(self.target_suite) == 3 :
                        leds = (f'S{self.target_suite[0]}#{self.colors[0]}|D{self.target_suite[0]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[0]}|S{self.target_suite[1]}#{self.colors[0]}|D{self.target_suite[1]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[1]}|S{self.target_suite[2]}#{self.colors[0]}|D{self.target_suite[2]}#{self.colors[0]}|T{self.target_suite[2]}#{self.colors[0]}')
                elif len(self.target_suite) == 2 :
                        leds = (f'S{self.target_suite[0]}#{self.colors[0]}|D{self.target_suite[0]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[0]}|S{self.target_suite[1]}#{self.colors[0]}|D{self.target_suite[1]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[1]}')
                elif len(self.target_suite) == 1 :
                        leds = (f'S{self.target_suite[0]}#{self.colors[0]}|D{self.target_suite[0]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[0]}')
                elif len(self.target_suite) == 0 :
                        self.target_suite = [self.target_suit1, self.target_suit2, self.target_suit3]
                        leds = (f'S{self.target_suite[0]}#{self.colors[0]}|D{self.target_suite[0]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[0]}|S{self.target_suite[1]}#{self.colors[0]}|D{self.target_suite[1]}#{self.colors[0]}|T{self.target_suite[0]}#{self.colors[1]}|S{self.target_suite[2]}#{self.colors[0]}|D{self.target_suite[2]}#{self.colors[0]}|T{self.target_suite[2]}#{self.colors[0]}')

        elif self.jeuchoisi == ['voisin'] :
                text = 'Voisin'
                
                if len(self.target_voisin) == 3 :
                        leds = (f'S{self.target_voisin[0]}#{self.colors[0]}|D{self.target_voisin[0]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[0]}|S{self.target_voisin[1]}#{self.colors[0]}|D{self.target_voisin[1]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[1]}|S{self.target_voisin[2]}#{self.colors[0]}|D{self.target_voisin[2]}#{self.colors[0]}|T{self.target_voisin[2]}#{self.colors[0]}')
                elif len(self.target_voisin) == 2 :
                        leds = (f'S{self.target_voisin[0]}#{self.colors[0]}|D{self.target_voisin[0]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[0]}|S{self.target_voisin[1]}#{self.colors[0]}|D{self.target_voisin[1]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[1]}')
                elif len(self.target_voisin) == 1 :
                        leds = (f'S{self.target_voisin[0]}#{self.colors[0]}|D{self.target_voisin[0]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[0]}')
                elif len(self.target_voisin) == 0 :
                        self.target_voisin = [self.target_voisin1, self.target_voisin2, self.target_voisin3]
                        leds = (f'S{self.target_voisin[0]}#{self.colors[0]}|D{self.target_voisin[0]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[0]}|S{self.target_voisin[1]}#{self.colors[0]}|D{self.target_voisin[1]}#{self.colors[0]}|T{self.target_voisin[0]}#{self.colors[1]}|S{self.target_voisin[2]}#{self.colors[0]}|D{self.target_voisin[2]}#{self.colors[0]}|T{self.target_voisin[2]}#{self.colors[0]}')

        elif self.jeuchoisi == ['oneanimal'] :
                text = 'Animal'
                
                ### choisi 3 chiffres uniques aleatoirement
                hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                h = random.randint(0,len(hits) - 1)
                d1 = hits[h]
                hits.pop(h)
                h = random.randint(0,len(hits) - 1)
                d2 = hits[h]
                hits.pop(h)
                h = random.randint(0,len(hits) - 1)
                d3 = hits[h]
                hits.pop(h)
                ### cree la liste led + choix du chiffre relie a l animal
                listeled = [d1, d2, d3]
                self.animal = random.choice(listeled)
                
                leds = (f'S{listeled[0]}#{self.colors[0]}|D{listeled[0]}#{self.colors[0]}|T{listeled[0]}#{self.colors[0]}|S{listeled[1]}#{self.colors[0]}|D{listeled[1]}#{self.colors[0]}|T{listeled[0]}#{self.colors[1]}|S{listeled[2]}#{self.colors[0]}|D{listeled[2]}#{self.colors[0]}|T{listeled[2]}#{self.colors[0]}')
                
                self.headers[1] = str(d1)
                self.headers[2] = str(d2)
                self.headers[3] = str(d3)

        elif self.jeuchoisi == ['onebombe'] :
                self.bombe = random.randint(0, 3)
                
                text = 'Bombe'
                leds = '|'.join(f'S{number}#{self.colors[0]}|D{number}#{self.colors[0]}|T{number}#{self.colors[0]}' for number in range(1, 21))
                self.headers[1] = 'Bombe' 
                self.headers[2] = '-'
                self.headers[3] = '-'
                
        elif self.jeuchoisi == ['multiple'] :
                if self.multiple == 3 :
                        text = 'Multiple de 3'
                        ledsS = [f'S3#green','S6#green','S9#green','S12#green','S15#green','S18#green']  
                        ledsD = [f'D3#green','D6#green','D9#green','D12#green','D15#green']
                        ledsT = [f'T1#green','T7#green','T8#green','T9#green','T10#green','T11#green','T12#green','T13#green','T14#green','15#green','T16#green','T17#green','T18#green','T19#green','T20#green']
                        led = ledsS + ledsD + ledsT
 
                elif self.multiple == 4 :
                        text = 'Multiple de 4'
                        ledsS = [f'S4#green','S8#green','S12#green','S16#green','S20#green']  
                        ledsD = [f'D2#green','D4#green','D6#green','D8#green','D10#green','D12#green','D14#green','D16#green','D18#green','D20#green']
                        ledsT = [f'T3#green','T4#green','T8#green','T12#green','T16#green','T20#green']
                        led = ledsS + ledsD + ledsT

                elif self.multiple == 5 :
                        text = 'Multiple de 5'
                        ledsS = [f'S5#green','S10#green','S15#green','S20#green']  
                        ledsD = [f'D5#green','D10#green','D15#green','D20#green']
                        ledsT = [f'T5#green','T10#green','T15#green','T20#green']
                        led = ledsS + ledsD + ledsT
                        
                elif self.multiple == 6 :
                        text = 'Multiple de 6'
                        ledsS = [f'S6#green','S12#green','S18#green']  
                        ledsD = [f'D3#green','D6#green','D9#green','D12#green','D15#green','D18#green']
                        ledsT = [f'T2#green','T4#green','T6#green','T8#green','T10#green','T12#green','T14#green','T16#green','T18#green','T20#green']
                        led = ledsS + ledsD + ledsT

                leds = '|'.join(led)
                players[actual_player].columns[5] = (self.multiple, 'int') 

                
        elif self.jeuchoisi == ['lower'] or self.jeuchoisi == ['under'] :
                
                if self.jeuchoisi == ['lower'] :
                        players[actual_player].columns[5] = (self.lower, 'int')
                        text = 'Score < ' + str(self.lower)

                        if player_launch == 1 :
                                players[actual_player].min_score = self.lower
                        else : 
                                players[actual_player].min_score = self.lower - self.score2
                else : 
                        players[actual_player].columns[5] = (self.under, 'int')
                        text = 'Score > ' + str(self.under)

                        if player_launch == 1 :
                                players[actual_player].min_score = self.under
                        else : 
                                players[actual_player].min_score = self.under - self.score2
                
                possibilities = self.get_possibilitirs(players[actual_player].min_score)
                if len(possibilities)> 0:
                        self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                                for key in possibilities]))
                else:
                        self.rpi.set_target_leds('')


        elif self.jeuchoisi == ['777'] :
                self.headers[6] = 'Score'
                text = '777'

                ### s active - affiche le print mais return 1 ne va pas ????
                if players[actual_player].seven77 > 777 :
                        print('if 397 check true')
                        return 1
                
                
                reste = 777 - players[actual_player].seven77
                if reste >= 0 :
                        players[actual_player].columns[player_launch] = (reste, 'int') 
                else :
                        players[actual_player].columns[5] = ("cross-mark", 'image')
                        
                players[actual_player].columns[6] = (players[actual_player].seven77, 'int')

                #### fpossibilite de tirs
                players[actual_player].min_score = reste
                possibilities = self.get_possibilitirs(players[actual_player].min_score)
                if len(possibilities)> 0:
                        self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                                for key in possibilities]))
                else:
                        self.rpi.set_target_leds('')

        elif self.jeuchoisi == ['superieur'] or self.jeuchoisi == ['inferieur'] :
                if self.jeuchoisi == ['superieur'] :
                        text = 'flèche > ' + str(self.fleche)
                        players[actual_player].min_score = self.fleche
                else :
                        text = 'flèche < ' + str(self.fleche)
                        players[actual_player].min_score = self.fleche 
                
                ### possibilite de tirs
                possibilities = self.get_possibilitirs(players[actual_player].min_score)
                if len(possibilities)> 0:
                        self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                                for key in possibilities]))
                else:
                        self.rpi.set_target_leds('')

        elif self.jeuchoisi == ['pair'] or self.jeuchoisi == ['impair'] :
                if self.jeuchoisi == ['pair'] :
                        text = 'Pair'
                        Dbull = [f'DB#green']
                        ledsS = [f'S2#green','S4#green','S6#green','S8#green','S10#green','S12#green','S14#green','S16#green','S18#green','S20#green']  
                        ledsD = [f'D1#green','D2#green','D3#green','D4#green','D5#green','D6#green','D7#green','D8#green','D9#green','D10#green']
                        ledsD2 = [f'D11#green','D12#green','D13#green','D14#green','D15#green','D16#green','D17#green','D18#green','D19#green','D20#green']
                        ledsT = [f'T2#green','T4#green','T6#green','T8#green','T10#green','T12#green','T14#green','T16#green','T18#green','T20#green']
                               
                        led = ledsS + ledsD + ledsD2 + ledsT + Dbull
                else :
                        text = 'Impair'
                        Sbull = [f'SB#green']
                        ledsS = [f'S1#green','S3#green','S5#green','S7#green','S9#green','S11#green','S13#green','S15#green','S17#green','S19#green']  
                        ledsT = [f'T1#green','T3#green','T5#green','T7#green','T9#green','T11#green','T13#green','T15#green','T17#green','T19#green']
                        
                        led = ledsS + ledsT + Sbull

                leds = '|'.join(led)
 
                
        elif self.jeuchoisi == ['color_white'] or self.jeuchoisi == ['color_blue'] :
                if  self.jeuchoisi == ['color_blue'] :
                        text = 'Bleu'
                else :
                        text = 'Blanc'
                        
                Dbull = [f'DB#white']
                hits_blancS = [20,18,13,10,2,3,7,8,14,12]
                hits_blancDT = [1,4,6,15,17,19,16,11,9,5]

                Sbull = [f'SB#blue']
                hits_bleuS = [1,4,6,15,17,19,16,11,9,5]
                hits_bleuDT = [20,18,13,10,2,3,7,8,14,12]
                        
                hits_j1S = [f'S{hit}#white' for hit in hits_blancS]
                hits_j1DT = [f'{mult}{hit}#white' for hit in hits_blancDT for mult in ['D', 'T']]
                
                hits_j2S = [f'S{hit}#blue' for hit in hits_bleuS]
                hits_j2DT = [f'{mult}{hit}#blue' for hit in hits_bleuDT for mult in ['D', 'T']]
            
                led = hits_j1S + hits_j1DT + hits_j2S + hits_j2DT + Sbull + Dbull
                leds = '|'.join(led)

        else :
                leds = ''
                text = ''
                
        players[actual_player].columns[0] = (text, 'txt')        
        
        ### n utilise pas la commande led standard pour ces jeux car ils sont traites par "tirpossibilities"
        if self.jeuchoisi != ['superieur'] and self.jeuchoisi != ['inferieur'] and self.jeuchoisi != ['under'] and self.jeuchoisi != ['lower'] and self.jeuchoisi != ['777'] and self.jeuchoisi != ['score_determine'] :
                self.rpi.set_target_leds(leds)
        
        # Clean next boxes
        for i in range(player_launch + 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')
        
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
        ### dit le chiffre touche
        self.display.sound_for_touch(hit)

        score = 0

        ### GESTION DES MINI JEUX   POSTDARTS     
        if self.jeuchoisi == ['onedart'] or self.jeuchoisi == ['threedarts'] :
                if hit :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = (score, 'int')
                        players[actual_player].columns[4] = (self.score2, 'int')
                                
                return_code = 0 

        elif self.jeuchoisi == ['threebulls'] or self.jeuchoisi == ['onebulls']:        
                if hit == 'SB' or hit == 'DB' :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = (score, 'int')
                        players[actual_player].columns[4] = (self.score2, 'int')

                else :
                        score = 0
                        self.score2 += score
                        players[actual_player].columns[player_launch] = (score, 'int')
                        players[actual_player].columns[4] = (self.score2, 'int')
                                
                return_code = 0 
                
        elif self.jeuchoisi == ['threesimple'] or self.jeuchoisi == ['onesimple'] : 
                if self.jeuchoisi == ['onesimple'] :
                        chiffre = self.chiffre
                elif self.jeuchoisi == ['threesimple'] :
                        chiffre = self.chiffre2
    
                if hit == 'S'+str(chiffre) :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')

                else :
                        score = 0
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')
                
                return_code = 0 
                        
        elif self.jeuchoisi == ['fortune1'] :
                if hit :
                        if player_launch == 1 :
                                score = self.score_map[hit] * 5
                                self.score2 += score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                        elif player_launch == 2 :
                                score = self.score_map[hit] * 10
                                self.score2 += score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                        elif player_launch == 3 :
                                score = self.score_map[hit] * 15
                                self.score2 += score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                                
                return_code = 0 
                
        elif self.jeuchoisi == ['fortune2'] :
                if hit :
                        if player_launch == 1 :
                                score = self.score_map[hit] * 1
                                self.score2 += score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                        elif player_launch == 2 :
                                score = self.score_map[hit] * 2
                                self.score2 += score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                        elif player_launch == 3 :
                                score = self.score_map[hit] * 3
                                self.score2 += score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                                
                return_code = 0    
                            
        elif self.jeuchoisi == ['onetriple'] or self.jeuchoisi == ['threetriple'] :
                if hit[:1] == 'T' :
                        score = 1
                        self.score2 += score 
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')
                else :
                        score += 0
                        self.score2 += score 
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')
                        
                return_code = 0 

        elif self.jeuchoisi == ['onedouble'] or self.jeuchoisi == ['threedouble'] :
                if hit[:1] == 'D' :
                        score = 1
                        self.score2 += score 
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')
                else :
                        score += 0
                        self.score2 += score 
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')
                
                return_code = 0 
         
        elif self.jeuchoisi == ['score_determine'] :
                if hit :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = (score, 'int')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                
                if self.score2 >= self.score_min and self.score2 <= self.score_max :
                        players[actual_player].columns[5] = ("check-mark", 'image')
                        players[actual_player].columns[6] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                elif self.score2 > self.score_max :
                        players[actual_player].columns[5] = ("cross-mark", 'image')
                        players[actual_player].columns[6] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (0, 'int') 
                elif self.score2 <= self.score_min or self.score2 >= self.score_max :
                        #self.score2 = 0
                        players[actual_player].columns[5] = ("cross-mark", 'image')
                        players[actual_player].columns[6] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (0, 'int') 
                        
                return_code = 0 
         
                
        elif self.jeuchoisi == ['suite'] :
                if hit == 'SB' or hit == 'DB' :
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        self.score2 += 0
                        players[actual_player].columns[4] = (self.score2, 'int')
                        return_code = 0 
                        
                elif int(hit[1:]) in self.target_suite :
                        self.score2 += 1
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')

                        try :
                                while True :
                                        suppr = int(hit[1:])
                                        self.target_suite.remove(suppr)
                        except:
                                pass  
                                
                        return_code = 0 
         
                else :
                        self.score2 += 0
                        players[actual_player].columns[4] = (self.score2, 'int')
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        return_code = 0 
                        
        elif self.jeuchoisi == ['voisin'] :
                if hit == 'SB' or hit == 'DB' :
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        self.score2 += 0
                        players[actual_player].columns[4] = (self.score2, 'int')
                        return_code = 0 
 
                elif int(hit[1:]) in self.target_voisin :
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        self.score2 += 1
                        players[actual_player].columns[4] = (self.score2, 'int')
                            
                        try :
                                while True :
                                        suppr = int(hit[1:])
                                        self.target_voisin.remove(suppr)
                        except:
                                pass  
                                return_code = 0   
         
                else :
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        self.score2 += 0
                        players[actual_player].columns[4] = (self.score2, 'int')
                        return_code = 0 

        elif self.jeuchoisi == ['under'] :
                if hit :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = (score, 'int')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                if player_launch == 3 :
                        if self.score2 > self.under :
                                players[actual_player].columns[5] = ("check-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        else :
                                score = self.score_map[hit]
                                self.score2 = 0 
                                players[actual_player].columns[5] = ("cross-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int')         
                return_code = 0 
 
        elif self.jeuchoisi == ['lower'] :
                if hit :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = (score, 'int')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                
                if player_launch == 3 :
                        if self.score2 < self.lower :
                                players[actual_player].columns[5] = ("check-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        else :
                                score = self.score_map[hit]
                                self.score2 = 0
                                players[actual_player].columns[5] = ("cross-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        
                return_code = 0  
                
        elif self.jeuchoisi == ['superieur'] :
                if hit :
                        if player_launch == 1 :
                                self.fleche1 = self.score_map[hit]
                                self.fleche = self.fleche1
                                score = self.score_map[hit]
                                self.score2 += 1 ###score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                players[actual_player].columns[5] = (self.fleche, 'int')
                        
                        elif player_launch == 2 and self.score_map[hit] > self.fleche :
                                self.fleche2 = self.score_map[hit]
                                self.fleche = self.fleche2
                                score = self.score_map[hit]
                                self.score2 += 1 ####score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                players[actual_player].columns[2] = ("check-mark", 'image')
                                players[actual_player].columns[5] = (self.fleche, 'int')
                        
                        elif player_launch == 3 and self.score_map[hit] > self.fleche :
                                self.fleche3 = self.score_map[hit]
                                self.fleche = self.fleche3
                                score = self.score_map[hit]
                                self.score2 += 1 #### score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                players[actual_player].columns[3] = ("check-mark", 'image')
                                players[actual_player].columns[5] = (self.fleche, 'int')
                        
                        else : 
                                score = self.score_map[hit]
                                if player_launch == 2 :
                                        self.fleche = self.fleche1
                                elif player_launch == 3 :
                                        self.fleche = self.fleche2
                                self.score2 += 0  ####score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                                players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                                players[actual_player].columns[5] = (self.fleche, 'int')
                        
                return_code = 0 
                         
        elif self.jeuchoisi == ['inferieur'] :
                if hit :
                        if player_launch == 1 and self.score_map[hit] < self.inferieur :
                                self.fleche1 = self.score_map[hit]
                                self.fleche = self.fleche1
                                score = self.score_map[hit]
                                self.score2 += 1 ###score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                players[actual_player].columns[5] = (self.fleche, 'int') 
                                
                        elif player_launch == 2 and self.score_map[hit] < self.fleche :
                                self.fleche2 = self.score_map[hit]
                                self.fleche = self.fleche2
                                score = self.score_map[hit]
                                self.score2 += 1   ###score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                players[actual_player].columns[2] = ("check-mark", 'image')
                                players[actual_player].columns[5] = (self.fleche, 'int') 
                        
                        elif player_launch == 3 and self.score_map[hit] < self.fleche :
                                self.fleche3 = self.score_map[hit]
                                self.fleche = self.fleche3
                                score = self.score_map[hit]
                                self.score2 += 1   ####score
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                players[actual_player].columns[3] = ("check-mark", 'image')
                                players[actual_player].columns[5] = (self.fleche, 'int') 
                        else : 
                                score = self.score_map[hit]
                                if player_launch == 1 :
                                        self.fleche = self.inferieur
                                        self.fleche1 = self.fleche
                                elif player_launch == 2 :
                                        self.fleche = self.fleche1
                                elif player_launch == 3 :
                                        self.fleche = self.fleche2
                                self.score2 += 0
                                players[actual_player].columns[player_launch] = (score, 'int')
                                players[actual_player].columns[4] = (self.score2, 'int')
                                players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                                players[actual_player].columns[5] = (self.fleche, 'int') 
                        
                return_code = 0 
                
        elif self.jeuchoisi == ['onebombe'] :
                if hit == 'SB' or hit == 'DB' :
                        self.score2 = 0
                        players[actual_player].columns[player_launch] = ("bombe", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')                        
                          
                elif int(hit[1:]) in self.target_bombeall["self.target_bombe"+str(self.bombe)] :
                        score = self.score_map[hit]
                        self.score2 = 0
                        players[actual_player].columns[player_launch] = ("bombe", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                else :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (1, 'int') 
                
                return_code = 0
                        
        elif self.jeuchoisi == ['oneanimal'] :
                if hit == 'SB' or hit == 'DB' :
                        self.score2 = 0
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int')                        
                          
                elif int(hit[1:]) == self.animal :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("lion", 'image')
                        players[actual_player].columns[4] = (1, 'int') 
                else :
                        score = self.score_map[hit]
                        self.score2 = 0
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                        
                return_code = 0

        elif self.jeuchoisi == ['multiple'] :
                if hit :
                        score = self.score_map[hit]
                if score in self.target_multipleall["self.target_multiple"+str(self.multiple)] :
                        score = self.score_map[hit]
                        self.score2 += 1  
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                else :
                        score = 0
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                
                return_code = 0
                
        elif self.jeuchoisi == ['impair'] :          
                if hit :
                        test_impair = self.score_map[hit]
                        if hit == 'DB' :
                                score = 0
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                
                        elif hit == 'SB' :
                                score = self.score_map[hit]
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("check-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        
                        elif (test_impair % 2) == 1:
                                score = self.score_map[hit]
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("check-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        else :
                                score = 0
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                return_code = 0
                
        elif self.jeuchoisi == ['pair'] :          
                if hit :
                        test_pair = self.score_map[hit]
                        if hit == 'SB' :
                                score = 0
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                                
                        elif hit == 'DB' :
                                score = self.score_map[hit]
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("check-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        
                        elif (test_pair % 2) == 0:
                                score = self.score_map[hit]
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("check-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int') 
                        else :
                                score = 0
                                self.score2 += score
                                players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                                players[actual_player].columns[4] = (self.score2, 'int')  
                return_code = 0
                
        elif self.jeuchoisi == ['color_white'] or self.jeuchoisi == ['color_blue']:
                if self.jeuchoisi == ['color_white'] :
                        couleur = self.color_white
                else : 
                        couleur = self.color_blue
                        
                if hit in couleur :
                        score = self.score_map[hit]
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("check-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                else :
                        score = 0
                        self.score2 += score
                        players[actual_player].columns[player_launch] = ("cross-mark", 'image')
                        players[actual_player].columns[4] = (self.score2, 'int') 
                
                return_code = 0
                                  
        elif self.jeuchoisi == ['777'] :
                if hit :
                        #check777 = False
                        code = 0
                        score = self.score_map[hit]
                        self.score2 += score
                        
                        if players[actual_player].seven77 <= 777 :
                                players[actual_player].seven77 += score   
                        
                        ### Si SCORE SUP A 777 - PASSE LE TOUR
                        elif players[actual_player].seven77 > 777 :
                                print('if 1070 check true')
                                self.check777 = True
                                code = 1

                        if players[actual_player].seven77 == 777 and player_launch == 3 and not self.check777 :
                               players[actual_player].columns[4] = (3, 'int') 
                               players[actual_player].columns[5] = ("check-mark", 'image')
                               code = 0
                               self.check777 = True
                        elif players[actual_player].seven77 == 777 and player_launch == 2 and not self.check777 :
                               players[actual_player].columns[4] = (2, 'int') 
                               players[actual_player].columns[5] = ("check-mark", 'image')
                               code = 0       
                               self.check777 = True
                        elif players[actual_player].seven77 == 777 and player_launch == 1 and not self.check777 :
                               players[actual_player].columns[4] = (1, 'int') 
                               players[actual_player].columns[5] = ("check-mark", 'image')
                               self.check777 = True
                               code = 0       
       
                        elif players[actual_player].seven77 != 777 and player_launch == 3 :
                               self.score2 = 0
                               players[actual_player].columns[4] = (self.score2, 'int')  
                               players[actual_player].columns[player_launch] = (0, 'int') 
                               players[actual_player].columns[5] = ("cross-mark", 'image')
                               code = 0 
                               #print('if 1182 - check false')
                               #self.check777 = False
                               
                        players[actual_player].columns[6] = (players[actual_player].seven77, 'int') 

                return_code = code
        

        if 'one' in self.jeuchoisi[0] or self.check777 :
                print('self.check777 et/ou one ligne 1138')
                print(self.check777)
                
                self.calcul(players, actual_player)
                
                return 1
                #elif actual_round >= self.max_round and actual_player == len(players) - 1:
                        # Last round, last player
                #        return self.best_score(players)
                #return -2

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
        print('early - nextplayer presse')
        if self.score2 == 0 :
                players[actual_player].columns[4] = (0, 'int') 
        else :
                players[actual_player].columns[4] = (self.score2, 'int') 
                
        return 1
         
        
    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        print('post_round_check')
        self.calcul(players, actual_player)

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        EMPTY
        """  
        pass
          
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
       

    def calcul(self, players, actual_player) :
        print('def calcul')
        if self.score2 == 0 :
                players[actual_player].columns[4] = (0, 'int') 
        else :
                players[actual_player].columns[4] = (self.score2, 'int') 

        liste_score = []
        if players[actual_player].ident == self.nb_players -1 :
                for player in players :
                        ### creation de la liste des scores (recuperation du score dans la colonne 4 et de l ident du joueur)
                        liste_score.extend([[player.columns[4][0],player.ident]]) 

                score_trie=sorted(liste_score)
                print('liste des scores tries')
                print(score_trie)

                #### attribution des points
                ## meilleur score = 2 points (si egalite, 2 points pour chaque joueur)
                ## 2eme meilleur score = 1 point (si egalite, 1 point pour chaque joueur)
                ## 3eme et reste = 0 points
                if score_trie[-1][0] == 0 :
                        points = 0
                else :
                        points = 2	
       
                score_acquis=[]
                for i in range(-1, -len(score_trie)-1, -1) :
                        if points > 0 and i < -1  and score_trie[i][0] != score_trie[i+1][0]:
                                if score_trie[i][0] == 0 :
                                        points = 0
                                else :
                                        points -= 1
                              
                        score_acquis.append((points, score_trie[i][1]))

                print('resultat points')
                print(score_acquis)

                ### suivant le nb de joueur, execute X fois le code pour ajouter les points au score
                for i in range(self.nb_players) :
                        for k, v in enumerate(score_acquis):
                                if v[1] == i :
                                        for player in players :
                                                if player.ident == i :
                                                        player.score += v[0]    
        
        return 1

    def get_possibilitirs(self, target_score):
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
            
            if self.jeuchoisi == ['superieur'] or self.jeuchoisi == ['under'] :    
                    for i in range(1, 22):
                        if i == 21:
                            if multiplier == 'T':
                                continue
                            i = 25
        
                        if i * mult > target_score:
                            if i == 25:
                                i = 'B'
                            possibilities.append(f'{multiplier}{i}')
                            
            elif self.jeuchoisi == ['inferieur'] or self.jeuchoisi == ['lower'] : 
                    for i in range(1, 22):
                        if i == 21:
                            if multiplier == 'T':
                                continue
                            i = 25
        
                        if i * mult < target_score:
                            if i == 25:
                                i = 'B'
                            possibilities.append(f'{multiplier}{i}')
                            
            elif self.jeuchoisi == ['777'] :    
                    for i in range(1, 22):
                        if i == 21:
                            if multiplier == 'T':
                                continue
                            i = 25
        
                        if i * mult == target_score:
                            if i == 25:
                                i = 'B'
                            possibilities.append(f'{multiplier}{i}')  
               
            elif self.jeuchoisi == ['score_determine'] :    
                    for i in range(1, 22):
                        if i == 21:
                            if multiplier == 'T':
                                continue
                            i = 25
                        if self.score2 < self.score_min :
                                if i * mult > target_score and i * mult < (self.score_max - self.score2):
                                    if i == 25:
                                        i = 'B'
                                    possibilities.append(f'{multiplier}{i}')
                                    
                        elif self.score2 > self.score_min and self.score2 < self.score_max :
                                if i * mult < target_score:
                                    if i == 25:
                                        i = 'B'
                                    possibilities.append(f'{multiplier}{i}')

            print('possibilites')
            print(possibilities) 

        return possibilities
