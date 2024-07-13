# -*- coding: utf-8 -*-
# Game by ... LaDite
########
import random
import pygame
from include import cplayer
from include import cgame

#

############
# Game Variables
############
OPTIONS = {'max_round': '10', 'simple50' : False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Voleur.png'
HEADERS = ["D1", "D2", "D3", "", "Rnd", "PPD", "PPR"] # Columns headers - Must be a string

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
    >Voleur game class
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


        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None

        self.video_player = video_player
        
        self.scale = self.display.res['x'] / 1920
        
### declaration variable 
        self.chiffre_joue = [0, 0, 0]
        self.leds = True
        self.next_player = 0
        self.p_ident = 0
        self.p_name = ''
        
        self.options = OPTIONS
        
        self.listeS = []
        self.listeD = []
        self.listeT = []
        
        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        self.margin_4 = 4 * self.display.margin
        
        self.dart = self.display.file_class.get_full_filename('dart', 'images')
        self.dart_icon = self.display.file_class.get_full_filename('dart_icon', 'images')
        self.online_icon = self.display.file_class.get_full_filename('online', 'images')

            
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

### INITIALISE LES LEDS DE TOUTES LES LEDS POUR CHAQUE JOUEUR -- player.targets
        if self.leds :
                for player in players :
                        hitsS = [f'S{number}#{self.colors[0]}' for number in range(1,21)]
                        hitsD = [f'D{number}#{self.colors[0]}' for number in range(1,21)]
                        hitsT = [f'T{number}#{self.colors[0]}' for number in range(1,21)]
                        Sbull = [f'SB#{self.colors[0]}']
                        Dbull = [f'DB#{self.colors[0]}']
                        
                        self.rpi.set_target_leds('|'.join(hitsS + hitsD + hitsT + Sbull + Dbull))
                        
                        player.targets = hitsS + hitsD + hitsT + Sbull + Dbull
                                   
                        print('players target')
                        print (player.targets)
                       
                        self.leds = False
                        
                        
                #### choisi 3 chiffres au hasard pour j1 a enlever lors du premier tour
                SDT = ['S' , 'D', 'T']
                lettre1 = random.choice(SDT)
                lettre2 = random.choice(SDT)
                lettre3 = random.choice(SDT)
#### POUR TEST - J1 s20-s5-s1 supprimer et remettre apres test
                self.chiffre_joue[0] = lettre1 + str(random.randint(1, 19))
                self.chiffre_joue[1] = lettre2 + str(random.randint(1, 19))
                self.chiffre_joue[2] = lettre3 + str(random.randint(1, 19))
                
                print('contenu de chiffre_joue - CHOIX ALEATOIRE')
                print (self.chiffre_joue)        
        
        if player_launch == 1: 
            players[actual_player].reset_darts()

        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
            
            print('')
            print('retire les segments alea de j1 au premier tour - ligne 117') 
            print('contenu de chiffre_jou - self.led')
            print (self.chiffre_joue)  
            ### RETIRE LES SEGMENT ALEATOIRE DE J1 AU DEBUT DU PREMIER TOUR
            try :
                    while True :
                            players[actual_player].targets.remove(self.chiffre_joue[0]+'#green') 
                            players[actual_player].targets.remove(self.chiffre_joue[1]+'#green') 
                            players[actual_player].targets.remove(self.chiffre_joue[2]+'#green') 
            except :
                    pass 

            print('ontenu de target j1 apres suppression')
            print(players[actual_player].targets)

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score
            
            print('contenu de chiffre_jou - predart - player_launch = 1 - avant while try - ligne 146')
            print (self.chiffre_joue) 
            ### SUPPRIME les chiffres joue par le joueur precedent (NORMALEMENT DEJA RETIRE QD JOUEUR PRECEDENT A JOUER - verifier et effacer)
            try :
                    while True :
                            players[actual_player].targets.remove(self.chiffre_joue[0]+'#green') 
            except :
                    print('condition except [0]')
                    
            try :
                    while True :
                            players[actual_player].targets.remove(self.chiffre_joue[1]+'#green') 
            except :
                    print('condition except [1]')
                    
            try :
                    while True :
                            players[actual_player].targets.remove(self.chiffre_joue[2]+'#green') 
            except :
                    print('condition except [2]')       

            ### REINITIALISE LES CHIFFRES JOUES
            self.chiffre_joue[0] = 0    
            self.chiffre_joue[1] = 0    
            self.chiffre_joue[2] = 0  
            
            print('contenu de chiffre_jou - predart - player_launch = 1 - APRES while try - ligne 167')
            print (self.chiffre_joue)   
                        
            
            ### MAJ DES TARGETS DU JOUEUR
            self.rpi.set_target_leds ('')
            self.rpi.set_target_leds('|'.join(players[actual_player].targets))
                           

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

        # Display avg
        if actual_round == 1 and player_launch == 1:
                
                players[actual_player].columns[5] = (0.0, 'int')
                players[actual_player].columns[6] = (0.0, 'int')

        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')
            
        '''
        if self.nb_players == 2 :
                if players[actual_player].ident == 0 :
                        self.p_ident = 0
                        self.next_player = 1
                
                elif players[actual_player].ident == 1 :
                        self.p_ident = 1
                        self.next_player = 0        
        '''
        print('self.nb_player')
        print(self.nb_players)
        if players[actual_player].ident == 0 :
                self.p_ident = 0
                self.next_player = 1
                print('ident == 0 - ligne 209')
                print('self.p_ident')
                print(self.p_ident)
                print('self.next_player')
                print(self.next_player)
        elif players[actual_player].ident == self.nb_players -1 :
                self.p_ident = players[actual_player].ident
                self.next_player = 0
                print('ident => self.nb_player - ligne 217')
                print('self.p_ident')
                print(self.p_ident)
                print('self.next_player')
                print(self.next_player)
        else :
                self.p_ident = players[actual_player].ident  
                self.next_player = self.p_ident + 1 
                print('ident < nb_player - ligne 221')
                print('self.p_ident')
                print(self.p_ident)
                print('self.next_player')
                print(self.next_player)
        


        if actual_player == self.p_ident : ###0 : 
                print('condition player= 0 ')
                listeS = []
                listeD = []
                listeT = []
                for player in players :
                        if player.ident == self.next_player :  ###1 
                                print('condition player in player - player.ident == self.next_player')
                                self.p_name = player.name
                                for liste in player.targets:
                                        if liste[:1] == 'S':
                                                listeS.append(liste)
                                        if liste[:1] == 'D' :
                                                listeD.append(liste)
                                        if liste[:1] == 'T' :
                                                listeT.append(liste)
        
                                print('')
                                print('listeS')
                                print(listeS)
                                print('listeD')
                                print(listeD)
                                print('listeT')
                                print(listeT)
                                
                                nvellListeS = []
                                for val in listeS:
                                        indexDiese = val.find('#')
                                        nvellListeS.append(val[1:indexDiese])
                                
                                nvellListeD = []
                                for val in listeD:
                                        indexDiese = val.find('#')
                                        nvellListeD.append(val[1:indexDiese])
                                        
                                nvellListeT = []
                                for val in listeT:
                                        indexDiese = val.find('#')
                                        nvellListeT.append(val[1:indexDiese])        
                                        
                                print('')
                                print('nvellListeS')
                                print(nvellListeS)
                                print('nvellListeD')
                                print(nvellListeD)
                                print('nvellListeT')
                                print(nvellListeT)
                                
                                self.listeS = nvellListeS
                                self.listeD = nvellListeD
                                self.listeT = nvellListeT
                                ### supprime le dernier element de la liste ('B')
                                self.listeS.pop()
                                self.listeD.pop()
       
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
        
   
    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """

        # Play DMD animation
        if super().play_show(players[actual_player].darts, hit, play_special=True):
            self.display.sound_for_touch(hit)
    
### QD ON TOUCHE UN SEGMENT ETEINT, ON NE PREND PAS DE POINTS MAIS ON LE SUPPRIME POUR LE JOUEUR SUIVANT             
        if not (hit+'#green') in players[actual_player].targets:
                
                print('SEGMENT NON TOUCHE')
                
                if player_launch == 1 :
                        self.chiffre_joue[0] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[0]+'#green') 
                
                                        except :
                                                print('condition except [0]')
                                                pass
                                        
                elif player_launch == 2 :
                        self.chiffre_joue[1] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[1]+'#green') 
                
                                        except :
                                                print('condition except [1]')
                                                pass
                elif player_launch == 3 :
                        self.chiffre_joue[2] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[2]+'#green') 
                
                                        except :
                                                print('condition except [2]')
                                                pass
                
                
                print ('chiffre a retirer de la liste S-D-T - ligne 409')
                print(hit)
                print('')
                print('postdart contenu de chiffre_joue')
                print(self.chiffre_joue)   
                        
                #players[actual_player].darts_thrown += 1
                score = 0
                
        if (hit[1:]) == 'B' :
                print('BULL touche')

                score = self.score_map[hit] 
                
                
        ### QD ON TOUCHE UN SEGMENT ALLUME, ON LE SUPPRIME POUR LE JOUEUR SUIVANT SAUF BULL            
        if (hit+'#green') in players[actual_player].targets and (hit[1:]) != 'B':
                print('')
                print('player target - dans condition chiffre touche - avant supprssion - ligne 282')
                print(players[actual_player].targets)
                
                if player_launch == 1 :
                        self.chiffre_joue[0] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[0]+'#green') 
                
                                        except :
                                                print('condition except [0]')
                                                pass
                                        
                elif player_launch == 2 :
                        self.chiffre_joue[1] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[1]+'#green') 
                
                                        except :
                                                print('condition except [1]')
                                                pass
                elif player_launch == 3 :
                        self.chiffre_joue[2] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[2]+'#green') 
                
                                        except :
                                                print('condition except [2]')
                                                pass
                            
                
                print ('chiffre a retirer de la liste S-D-T - ligne 466')
                print(hit)
                print('')
                print('postdart contenu de chiffre_joue')
                print(self.chiffre_joue)   
                             
                score = self.score_map[hit] 
                
                ### MAJ DES TARGETS DU JOUEUR
                self.rpi.set_target_leds ('')
                self.rpi.set_target_leds('|'.join(players[actual_player].targets))
       
        return_code = 0

               
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score


        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Calculate average and display in column 7
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= int(self.max_round) \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner >= 0:
                self.winner = winner
                return_code = 3
            else:
                # No winner : last round reached
                return_code = 2
       
        
        return return_code       

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


    def display_segment(self):
        """
        Set if a message is shown to indicate the segment hitted !
        """
        return False

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        if actual_round >= int(self.max_round) and actual_player == len(players) - 1:
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
    
    
    def actual_player_score(self, pos_x, pos_y, width, height, heading_height, dart_icon_size, color, name, score):

        self.display.blit_rect(pos_x, pos_y, width, heading_height, color)
        self.display.blit_rect(pos_x, pos_y + heading_height, width, height - heading_height, color)
        pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x, pos_y + heading_height), (pos_x + width, pos_y + heading_height), 2)
        pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x, pos_y), (pos_x, pos_y + height), 2)
        pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x + width, pos_y), (pos_x + width, pos_y + height), 2)
        self.display.display_image(self.dart_icon, pos_x + self.margin, pos_y + heading_height + self.margin, width=dart_icon_size, height=dart_icon_size, UseCache=True)
        self.display.blit_text(name, pos_x, pos_y - self.margin, width, heading_height + self.margin_2, color=self.display.colorset['game-bg'], dafont='Impact', align='Center')
        self.display.blit_text(score, pos_x, pos_y + heading_height, width, height - heading_height, color=self.display.colorset['game-score'], dafont='Impact', align='Right')
        ###
        #self.display.blit_text(score, pos_x, pos_y + heading_height, width, height +500, color=self.display.colorset['game-score'], dafont='Impact', align='Right')


        
    ###############
    # Refresh In-game screen
    ###############
   
    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        
        # Clear
        self.display.screen.fill((0, 0, 0))
        
        game_background = f"background_{logo.replace('_', '_').replace('!', '').split('.')[0]}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display.display_background(image=game_background)
            self.display.save_background()
        else:
            self.display.display_background()
           
        
        game = 'Voleur'
        hit = ''
        ppd = players[actual_player].show_ppd()
        ppr = players[actual_player].show_ppr()

        scores = players[actual_player].rounds
        score = players[actual_player].score
        darts = None
        
        for dart in players[actual_player].darts:
            if dart is None:
                dart = '___'
            if darts is None:
                darts = dart
            else:
                darts = f"{darts} / {dart}"

        dart = self.display.file_class.get_full_filename('dart', 'images')
        
        right_x = int(self.display.res['x'] * 13 / 16)
        right_y = self.margin
        right_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        ppdr_x = right_x + int(self.display.res['x'] * 3 / 32)

        right_mid_x = right_x + (self.display.res['x'] - right_x) / 2
        right_mid_width = (self.display.res['x'] - right_x) / 2      
     
     
        self.display.blit_rect(0, 0, self.display.res['x'], self.display.res['y'], self.display.colorset['game-bg'])

        self.display.blit_text(f"Round", right_x, right_y, int(right_width / 3), right_height, color=self.display.colorset['game-round'], dafont='Impact', align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", right_x + int(right_width / 2), 0, self.display.res['x'] - right_x - int(right_width / 2), right_height * 2, color=self.display.colorset['game-round'], dafont='Impact', align='Right', valign='top', margin=False)
        right_y += right_height

        heading_height = int(self.display.res['y'] / 24)

        # Game type
        game_width = int(self.display.res['x'] / 16)
        game_x = int(self.display.res['x'] / 2) - game_width
        game_y = self.margin
        game_height = int(self.display.res['y'] / 24)

        heading_color = self.display.colorset['game-headers']
        player_color = self.display.colorset['game-alt-headers']
        if self.display.game_type == 'online':
            self.display.display_image(self.online_icon, game_x - 40, game_y + self.margin, width=32, height=32, UseCache=True)

        self.display.blit_text(f"{self.display.game_type} game", game_x, game_y, game_width, game_height, color=(255, 0, 0), dafont='Impact', align='Center', valign='top', margin=False)

        hit_x = int(self.display.res['x'] / 4) - self.margin_2
        hit_y = int(self.display.res['y'] / 4) - self.margin_2
        hit_w = self.display.res['x'] - (2 * hit_x)   ###self.display.mid_x + 4 * self.margin
        hit_h = self.display.mid_y + 4 * self.margin

        '''
        # Score - score affiche en gros au centre
        rect6 = pygame.Rect(hit_x, hit_y, hit_w, hit_h)
        sub6 = self.display.screen.subsurface(rect6)
        screenshot6 = pygame.Surface((hit_w, hit_h))
        screenshot6.blit(sub6, (0, 0))
        self.display.blit_text(f'{score}', hit_x, hit_y, hit_w, hit_h, color=self.display.colorset['game-score'], dafont='Impact', align='Center')
        '''
        
        # Display players ans scores 
        if not end_of_game:
            player_y = int(self.display.res['y'] / 16)
        else:
            player_y = int(self.display.res['y'] / 3)
        player_height = int(self.display.res['y'] / 8)
        player_width = int(self.display.res['x'] / max(2 * len(players), 6))
        players_x = int(self.display.res['x'] / 4 + (self.display.res['x'] / 2 - player_width * len(players) - int(player_width / 2)) / 2)

        index = 0

        ### AFFICHE LES JOUEURS
        for player in players:
            color = player.color
            name = player.name
            score = player.score
            player_x = players_x + index * player_width

            if index != actual_player:
                if index < actual_player:
                    player_x -= int(player_width / 2)
                else:
                    player_x += int(player_width / 2)

                self.display.blit_rect(player_x, player_y, player_width, heading_height, heading_color)
                self.display.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, player_color)

                pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
                pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
                pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)

                if index < actual_player:
                    align = 'Left'
                else:
                    align = 'Right'
                pygame.draw.line(self.display.screen, color, (player_x, player_y), (player_x + player_width, player_y), self.margin_2)
                self.display.blit_text(name, player_x, player_y - self.margin_2, player_width, heading_height + self.margin_2, color=player_color, dafont='Impact', align=align)
                self.display.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=heading_color, dafont='Impact', align=align)
            else:
                # For actual player's infos
                actual_color = color
                actual_x = player_x - int(player_width / 2)
                actual_name = name
                actual_score = score
            index += 1

        # Actual player and his score
        player_y -= self.margin
        player_height += self.margin_2
        player_width *= 2
        dart_icon_size = player_height - heading_height - self.margin_2

        #self.actual_player_score(actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)
        
        ppdr_width = int(self.display.res['x'] / 24)
        # Previous rounds scores
        for index in range(3):
            if end_of_game:
                continue
            if actual_round - index > 0:
                text1 = f'R{actual_round - index}'
                score = 0
                for dartx in scores[actual_round -  1 - index]:
                    if dartx is not None:
                        score += self.score_map[dartx]
                
                #text2 = f'{sum(scores[actual_round - index - 1] if scores[actual_round - index - 1] is not None else 0)}'
                #text2 = score
                #self.display.blit_text(text1, right_x, right_y, ppdr_width, right_height, color=self.display.colorset['game-score'], dafont='Impact', align='Left')
                #self.display.blit_text(text2, right_x + ppdr_width, right_y, ppdr_width, right_height, color=actual_color, dafont='Impact', align='Right', margin=False)
                # a effacer - self.display.blit_text(f'{score}', right_x + ppdr_width, right_y, ppdr_width, right_height, color=actual_color, dafont='Impact', align='Right', margin=False)
            # PPR and PPD
            if index == 1:
                self.display.blit_text(f'PPR', ppdr_x, right_y, ppdr_width, right_height, color=self.display.colorset['game-score'], dafont='Impact', align='Right')
                self.display.blit_text(f'{ppr}', ppdr_x + ppdr_width, right_y, right_width - ppdr_width, right_height, color=actual_color, dafont='Impact', align='Left')
            elif index == 2:
                self.display.blit_text(f'PPD', ppdr_x, right_y , ppdr_width, right_height, color=self.display.colorset['game-score'], dafont='Impact', align='Right')
                self.display.blit_text(f'{ppd}', ppdr_x + ppdr_width, right_y , right_width - ppdr_width, right_height, color=actual_color, dafont='Impact', align='Left')

            right_y += right_height
            
            
        # Dartts' scores
        mid_x = int(self.display.res['x'] / 4) + self.margin
        mid_y = int(self.display.res['y'] * 3 / 4) + self.margin
        mid_width = self.display.mid_x - self.margin_2
        mid_height = int(self.display.res['y'] / 4) - self.margin_2

        if not end_of_game:
            min_pos_y = int(self.display.res['y'] / 32)
        else:
            min_pos_y = int(self.display.res['y'] / 3)
        max_pos_y = int(self.display.res['y'] * 31 / 32)

        round_pos_x = int(self.display.res['x'] / 32)
        round_pos_y = int(self.display.res['y'] / 32)
        round_radius = int(round_pos_x / 4)
        line_add = int(self.display.res['x'] / 64)

       
        
        for index in range(3):
            if index == rem_darts - 1:

                # Actual player's score
                rect5 = pygame.Rect(actual_x, player_y, player_width, player_height)
                sub5 = self.display.screen.subsurface(rect5)
                screenshot5 = pygame.Surface((mid_width, mid_height))
                screenshot5.blit(sub5, (0, 0))
                rect5 = (actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)

            if index < rem_darts and not end_of_game:
                self.display.display_image(self.dart, right_x, right_y, width=right_width ,height=right_height, UseCache=True)
            right_y += right_height

        self.actual_player_score(actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)
        if not end_of_game:
            if OnScreenButtons:
                mid_y -= int(self.display.res['y'] / 16)

            self.display.blit_text(darts, mid_x, mid_y, mid_width, mid_height, color=self.display.colorset['game-score'], dafont=None, align='Center')

            
        ''' 
        self.display.blit_text(f"VOLE LES SEGMENTS DE " + str(self.p_name) , 50 , 125 , 1000 , 60 , color=(255, 255, 0)) 
        self.display.blit_text('S : ' + ','.join(self.listeS), 50 , 175 , 1000 , 60 , color=(0, 0, 255))
        self.display.blit_text('D : ' + ','.join(self.listeD), 50 , 225 , 1000 , 60 , color=(255, 0, 255))
        self.display.blit_text('T : ' + ','.join(self.listeT), 50 , 275 , 1000 , 60 , color=(255, 0, 0)) 
        ''' 
        
        image_voleur = self.display.file_class.get_full_filename('voleur', 'images')
        self.display.display_image(image_voleur, 15, int(self.display.res['y'] * 2 / 4) + self.margin , width=320, height=320, UseCache=True)
        if not end_of_game:
                self.display.blit_text(f"VOLE LES SEGMENTS DE " + str(self.p_name) , hit_x , hit_y + 50 , hit_w, 60 , color=(255, 255, 0)) 
                self.display.blit_text('S : ' + ','.join(self.listeS),  hit_x , hit_y + 100 , hit_w , 60 , color=(0, 0, 255))
                self.display.blit_text('D : ' + ','.join(self.listeD),  hit_x , hit_y + 150 , hit_w , 60 , color=(255, 0, 255))
                self.display.blit_text('T : ' + ','.join(self.listeT),  hit_x , hit_y + 200 , hit_w , 60 , color=(255, 0, 0))
                
                self.display.blit_text(f'{players[actual_player].round_points}', right_x + self.margin, right_y  - self.margin ,  150, 150, color=self.display.colorset['game-score'], dafont='Impact', align='Center')
                
        self.display.update_screen()   
        
        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=True)
            return ClickZones
