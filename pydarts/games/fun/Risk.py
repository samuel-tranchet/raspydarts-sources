# -*- coding: utf-8 -*-
"""
Game by David !
"""
######
import re
import random
import subprocess
import pygame
from copy import deepcopy
from include import cplayer
from include import cgame
# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': 20, 'bouclier': 3, 'bonus':0,'miss':0}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Risk.png'  # background image
# Columns headers - Better as a string
HEADERS = ['#', 'PTS']  # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3  # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round': 'DESC'}


def check_players_allowed(nb_players):
    '''
    Return the player number max for a game.
    '''
    return nb_players in (2, 3, 4, 5)

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """

    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.segments = []
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'
        self.alive = True

class Game(cgame.Game):
    """
    Risk class game
    """

    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players,
                         options, config, logs, rpi, dmd, video_player)
        # For rpi
        self.rpi = rpi
        self.logo = LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS
        self.nb_players = nb_players
        self.options = options
        self.maxSrength = 3
        self.dead = 0
        self.led = ''
        self.bonus = int(options['bonus'])
        self.miss = int(options['miss'])
        # couleurs segment des joueurs
        self.colors = ['red', 'green', 'blue', 'yellow']

        # records is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS

        self.max_round = int(options['max_round'])
        self.bouclier = int(options['bouclier'])
        if self.bouclier > 3 :
            self.bouclier = 3

        # init Hex
        self.scale = self.display.res['x'] / 1920

        # pos hex texte
        self.pos = [
            (1265 * self.scale, 131 * self.scale),
            (981 * self.scale, 287 * self.scale),
            (1170 * self.scale, 287 * self.scale),
            (1355 * self.scale, 287 * self.scale),
            (1541 * self.scale, 287 * self.scale),
            (887 * self.scale, 453 * self.scale),
            (1073 * self.scale, 453 * self.scale),
            (1447 * self.scale, 453 * self.scale),
            (1633 * self.scale, 453 * self.scale),
            (789 * self.scale, 613 * self.scale),
            (977 * self.scale, 613 * self.scale),
            (1537 * self.scale, 613 * self.scale),
            (1725 * self.scale, 613 * self.scale),
            (887 * self.scale, 773 * self.scale),
            (1073 * self.scale, 773 * self.scale),
            (1255 * self.scale, 773 * self.scale),
            (1447 * self.scale, 773 * self.scale),
            (1633 * self.scale, 773 * self.scale),
            (1171 * self.scale, 941 * self.scale),
            (1350 * self.scale, 941 * self.scale),
            (1245 * self.scale, 565 * self.scale)
        ]

        # hex links
        self.link = {
            '1': ('3', '4'),
            '2': ('3', '6', '7'),
            '3': ('1', '2', '4', '7', 'B'),
            '4': ('1', '3', '5', '8', 'B'),
            '5': ('4', '8', '9'),
            '6': ('2', '7', '10', '11'),
            '7': ('2', '3', 'B', '6', '11'),
            '8': ('4', '5', 'B', '9', '12'),
            '9': ('5', '8', '12', '13'),
            '10': ('6', '11', '14'),
            '11': ('6', '7', '10', 'B', '14', '15'),
            '12': ('8', '9', 'B', '13', '17', '18'),
            '13': ('9', '12', '18'),
            '14': ('10', '11', '15'),
            '15': ('11', 'B', '14', '16', '19'),
            '16': ('B', '15', '17', '19', '20'),
            '17': ('B', '12', '16', '18', '20'),
            '18': ('12', '13', '17'),
            '19': ('15', '16', '20'),
            '20': ('16', '17', '19'),
            'B': ('3', '4', '7', '8', '11', '12', '15', '16', '17')
        }

        self.grid = []  # list of (segment, player, strengh)
        
        joueur1 = []
        joueur2 = []
        joueur3 = []
        joueur4 = []
        joueur5 = []
        bull = ['SB#white','DB#white']
        
        # random hex
        hits = [x for x in range(1, 21)]
        
        if nb_players == 4 :
            index_joueur = [0,2,3,1,2,3,1,0,3,1,0,2,3,0,1,2,1,0,2,3]
        elif nb_players == 3 :
            index_joueur = [0,2,9,1,2,9,1,0,9,1,0,2,9,0,1,2,1,0,2,9]
        elif nb_players == 2 :
            index_joueur = [0,9,9,1,9,9,1,0,9,1,0,9,9,0,1,9,1,0,9,9]
        elif nb_players == 5 :
            index_joueur = [0,2,4,1,2,3,1,4,3,1,0,4,3,0,1,2,3,0,2,4]    
       
        random.shuffle(index_joueur)  ### pas obligatoire car deja tirage alea avec random.choice
        
        for i in range(0, 20):
            h = random.randint(0, len(hits) - 1)
            j = random.choice(index_joueur)
            
            # segment, player, strengh   ---  9 pour ne pas ajouter des boucliers aux territoires neutres
            if j != 9 :
                self.grid.append((str(hits[h]), j, self.bouclier))
            elif j == 9 :
                self.grid.append((str(hits[h]), -1, -1))
                
            if j == 0 :
                joueur1.append('S'+str(hits[h])+'#green')
                joueur1.append('D'+str(hits[h])+'#green')
                joueur1.append('T'+str(hits[h])+'#green')
            elif j == 1 :
                joueur2.append('S'+str(hits[h])+'#blue')
                joueur2.append('D'+str(hits[h])+'#blue')
                joueur2.append('T'+str(hits[h])+'#blue')
            elif j == 2 :
                joueur3.append('S'+str(hits[h])+'#red')
                joueur3.append('D'+str(hits[h])+'#red')
                joueur3.append('T'+str(hits[h])+'#red') 
            elif j == 3 :
                joueur4.append('S'+str(hits[h])+'#yellow')
                joueur4.append('D'+str(hits[h])+'#yellow')
                joueur4.append('T'+str(hits[h])+'#yellow')
            elif j == 4 :
                joueur5.append('S'+str(hits[h])+'#purple')
                joueur5.append('D'+str(hits[h])+'#purple')
                joueur5.append('T'+str(hits[h])+'#purple')    

            hits.pop(h)
            index_joueur.remove(j)

            self.led = (joueur1 + joueur2 + joueur3 + joueur4 + joueur5 + bull)
            
### A supprimer - infos led et grid
            print('')
            print('ledstest')
            print(self.led)
            print('')
            print('contenu de self.grid')
            print(self.grid)

        # gestion de l'affichage du segment
        self.show_segment = False

        self.backups = []
        self.backups_grid = []

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.log("ERROR", "Handicap failed : {}".format(e))
            for player in players:
                # Init score
                player.score = 0
                player.alive = True

            # change background
            self.display.specialbg = 'bg_risk'
            self.display.display_background(image='bg_risk.jpg')

        # Each new player
        if player_launch == 1:
            players[actual_player].segments = ['', '', '']
            players[actual_player].round_points = 0
            self.save_turn(players)
            # Backup current score
            players[actual_player].pre_play_score = players[actual_player].score

            # Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 2):
                players[actual_player].columns.append(['', 'int'])

        # Display target color of players
        light_segments = []
        strobe_segments = []

       
### declaration de la variable leds
        leds = self.led 

        self.rpi.set_target_leds ('')
        self.rpi.set_target_leds('|'.join(leds))

### test pour voir si le joueur est mort ou non
        if not players[actual_player].alive :
            return 4
        

        return 0

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        return_code = 0

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].segments[player_launch-1] = hit

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D':
            multi = 2
        if hit[:1] == 'T':
            multi = 3
        
        
        if hit == 'SB' :    ### ajout de renforts sur tous les territoires si bouclier < 3
            
            #self.video_player.play_video(self.display.file_class.get_full_filename('conquer/conquer_bull', 'videos'))
            print('SB touche')
            
            ## creation dunenouvelle liste
            liste2 = []
            for k, v in enumerate(self.grid):
                if v[1] == -1 and v[2] < 0:
                    liste2.append(v)
            ### a effacer - infos        
            print('liste2')
            print(liste2)
            random.shuffle(liste2)
            print('liste2 shuffle')
            print(liste2)
            ## si liste est > 0 - on choisi un chiffre aleatoireement
            if len(liste2) > 0:
                choix = random.choice(liste2)
            else:
                choix = ['0',0,0]
                print('choix alea')
                print(choix)
            ### choix final pour liste
            choix2 = choix[0]
                
            print('choix final')
            print(choix2)
                 
                #for k, v in enumerate(self.grid):
                #    if v[0] == choix2 and choix2 != '0':
            
            
### AJOUT D UNE TROUPE PAR TERRITOIRE
            if players[actual_player].ident == 0 :
                self.dmd.send_text("Renfort des troupes + 1 Territoire")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 0 and v[2] < 3:
                        territoire = v[0]   
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):    
                    ### ajoute un territoire sans renfort
                    if v[0] == choix2 and choix2 != '0':####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]  
                        bouclier = 0 
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#green')
                        self.led.append('D'+str(v[0])+'#green')
                        self.led.append('T'+str(v[0])+'#green')
                        #
                        self.display.play_sound('risk_annexed')
                        break

            elif players[actual_player].ident == 1 :
                self.dmd.send_text("Renfort des troupes + 1 Territoire")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 1 and v[2] < 3:
                        territoire = v[0]
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire sans renfort
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]  
                        bouclier = 0 
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#blue')
                        self.led.append('D'+str(v[0])+'#blue')
                        self.led.append('T'+str(v[0])+'#blue')
                        #
                        self.display.play_sound('risk_annexed')
                        break
              
            elif players[actual_player].ident == 2 :
                self.dmd.send_text("Renfort des troupes + 1 Territoire")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 2 and v[2] < 3:
                        territoire = v[0]
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire sans renfort
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]  
                        bouclier = 0 
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#red')
                        self.led.append('D'+str(v[0])+'#red')
                        self.led.append('T'+str(v[0])+'#red')
                        #
                        self.display.play_sound('risk_annexed')
                        break

            elif players[actual_player].ident == 3 :
                self.dmd.send_text("Renfort des troupes + 1 Territoire")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 3 and v[2] < 3:
                        territoire = v[0]
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):     
                    ### ajoute un territoire sans renfort
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]  
                        bouclier = 0 
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#yellow')
                        self.led.append('D'+str(v[0])+'#yellow')
                        self.led.append('T'+str(v[0])+'#yellow')
                        #
                        self.display.play_sound('risk_annexed')
                        break
                        
            elif players[actual_player].ident == 4 :
                self.dmd.send_text("Renfort des troupes + 1 Territoire")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 4 and v[2] < 3:
                        territoire = v[0]
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):     
                    ### ajoute un territoire sans renfort
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]  
                        bouclier = 0 
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#purple')
                        self.led.append('D'+str(v[0])+'#purple')
                        self.led.append('T'+str(v[0])+'#purple')
                        #
                        self.display.play_sound('risk_annexed')
                        break
        if hit == 'DB' :   ### AJOUT D UN TERRITOIRE 
            #self.video_player.play_video(self.display.file_class.get_full_filename('conquer/conquer_bull', 'videos'))
            print('DB touche')
            
            ## creation dunenouvelle liste
            liste2 = []
            for k, v in enumerate(self.grid):
                if v[1] == -1 and v[2] < 0:
                    liste2.append(v)
            ### a effacer - infos        
            print('liste2')
            print(liste2)
            random.shuffle(liste2)
            print('liste2 shuffle')
            print(liste2)
            ## si liste est > 0 - on choisi un chiffre aleatoireement
            if len(liste2) > 0:
                choix = random.choice(liste2)
            else:
                choix = ['0',0,0]
                print('choix alea')
                print(choix)
            ### choix final pour liste
            choix2 = choix[0]
                
            print('choix final')
            print(choix2)
            
            
            if players[actual_player].ident == 0 :
                self.dmd.send_text("1 Territoire + Renfort des troupes")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 0 and v[2] < 3:
                        territoire = v[0]   
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire avec 1 bouclier
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]   
                        bouclier = 1 
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#green')
                        self.led.append('D'+str(v[0])+'#green')
                        self.led.append('T'+str(v[0])+'#green')
                        #
                        self.display.play_sound('risk_annexed')
                        break
            
            elif players[actual_player].ident == 1 :
                self.dmd.send_text("1 Territoire + Renfort des troupes")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 1 and v[2] < 3:
                        territoire = v[0]   
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire avec 1 bouclier
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]
                        bouclier = 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#blue')
                        self.led.append('D'+str(v[0])+'#blue')
                        self.led.append('T'+str(v[0])+'#blue')
                        ##
                        self.display.play_sound('risk_annexed')
                        break
              
            elif players[actual_player].ident == 2 :
                self.dmd.send_text("1 Territoire + Renfort des troupes")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 2 and v[2] < 3:
                        territoire = v[0]   
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire avec 1 bouclier
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]
                        bouclier = 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#red')
                        self.led.append('D'+str(v[0])+'#red')
                        self.led.append('T'+str(v[0])+'#red')
                        #
                        self.display.play_sound('risk_annexed')
                        break

            elif players[actual_player].ident == 3 :
                self.dmd.send_text("1 Territoire + Renfort des troupes")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 3 and v[2] < 3:
                        territoire = v[0]   
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire avec 1 bouclier
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]
                        bouclier = 1
                        self.grid[k] = (territoire, actual_player, bouclier) 
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#yellow')
                        self.led.append('D'+str(v[0])+'#yellow')
                        self.led.append('T'+str(v[0])+'#yellow')
                        #
                        self.display.play_sound('risk_annexed')
                        break       
            
            elif players[actual_player].ident == 4 :
                self.dmd.send_text("1 Territoire + Renfort des troupes")
                self.display.play_sound('risk_reinforcement')
                for k, v in enumerate(self.grid):
                    ### ajoute un renfort a chaque territoire
                    if v[1] == 4 and v[2] < 3:
                        territoire = v[0]   
                        bouclier = v[2] + 1
                        self.grid[k] = (territoire, actual_player, bouclier)
                for k, v in enumerate(self.grid):         
                    ### ajoute un territoire avec 1 bouclier
                    if v[0] == choix2 and choix2 != '0':  ####if v[1] == -1 and v[2] < 0:
                        territoire = v[0]
                        bouclier = 1
                        self.grid[k] = (territoire, actual_player, bouclier) 
                        self.blink_box(k)
                        self.led.append('S'+str(v[0])+'#purple')
                        self.led.append('D'+str(v[0])+'#purple')
                        self.led.append('T'+str(v[0])+'#purple')
                        #
                        self.display.play_sound('risk_annexed')
                        break          
                            
        for k, v in enumerate(self.grid):
            
            if v[0] == hit[1:]:
                if v[2] == -1 :  ### en cas ou on touche un segment n ayant pas de bouclier (territoire nu)
                    self.grid[k] = (v[0], -1, -1)
                    self.display.play_sound('risk_miss')  
                
                elif v[1] != actual_player:   ### touche le segment d un adversaire
                    ## augmente le score du  joueur (pour fin de partie si pas de gagnant)
                    players[actual_player].score += multi
                    niv = v[2] - multi
                    if niv >= 0 :
                        self.display.play_sound('risk_attack')
                        self.dmd.send_text("Tirs sur l'ennemi")
                    if niv < 0:
                        players[actual_player].score += self.bonus
                        ### SI PLUS DE BOUCLIER, TERRITOIRE DEVIENT NU
                        self.grid[k] = (v[0], -1, -1)
                        self.display.play_sound('risk_enemy_destroyed')
                        self.dmd.send_text("Territoire ennemi anéanti")
                        ### SUPPRIME LES LEDS DU TERRITOIRE NU 
                        
                        if v[1] == 0 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#green')
                                    self.led.remove('D'+v[0]+'#green')
                                    self.led.remove('T'+v[0]+'#green')
                            except:
                                pass
                        
                        elif v[1] == 1 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#blue')
                                    self.led.remove('D'+v[0]+'#blue')
                                    self.led.remove('T'+v[0]+'#blue')
                            except:
                                pass
                                
                        elif v[1] == 2 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#red')
                                    self.led.remove('D'+v[0]+'#red')
                                    self.led.remove('T'+v[0]+'#red')
                            except:
                                pass
                                
                        elif v[1] == 3 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#yellow')
                                    self.led.remove('D'+v[0]+'#yellow')
                                    self.led.remove('T'+v[0]+'#yellow')
                            except:
                                pass
                                
                        elif v[1] == 4 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#purple')
                                    self.led.remove('D'+v[0]+'#purple')
                                    self.led.remove('T'+v[0]+'#purple')
                            except:
                                pass
                                
                    else:
                        # reduction des troupes adverses
                        self.grid[k] = (v[0], v[1], niv)
                        self.display.play_sound('risk_attack')
                        self.dmd.send_text("Territoire ennemi attaqué")
                
                elif v[1] == actual_player:   ### touche son propre segment
                    niv = v[2] - multi
                    if niv >= 0 :
                        self.display.play_sound('risk_allied_fire')
                        self.dmd.send_text("Tirs Alliés")
                    if niv < 0:
                        players[actual_player].score -= self.miss
                        ### SI PLUS DE BOUCLIER, TERRITOIRE DEVIENT NU
                        self.grid[k] = (v[0], -1, -1)
                        self.display.play_sound('risk_friend_destroyed') 
                        self.dmd.send_text("Territoire allié anéanti")
                        ### SUPPRIMER LES LEDS DU TERRITOIRE NU 
                        if v[1] == 0 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#green')
                                    self.led.remove('D'+v[0]+'#green')
                                    self.led.remove('T'+v[0]+'#green')
                            except:
                                pass
                        
                        elif v[1] == 1 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#blue')
                                    self.led.remove('D'+v[0]+'#blue')
                                    self.led.remove('T'+v[0]+'#blue')
                            except:
                                pass
                                
                        elif v[1] == 2 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#red')
                                    self.led.remove('D'+v[0]+'#red')
                                    self.led.remove('T'+v[0]+'#red')
                            except:
                                pass
                                
                        elif v[1] == 3 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#yellow')
                                    self.led.remove('D'+v[0]+'#yellow')
                                    self.led.remove('T'+v[0]+'#yellow')
                            except:
                                pass
                                               
                        elif v[1] == 4 :
                            try :
                                while True :
                                    self.led.remove('S'+v[0]+'#purple')
                                    self.led.remove('D'+v[0]+'#purple')
                                    self.led.remove('T'+v[0]+'#purple')
                            except:
                                pass                 

                    else:
                        
                        # reduction des troupes du joueur actuel
                        self.grid[k] = (v[0], actual_player, niv)
                        #self.display.play_sound('risk_attack')
                        self.dmd.send_text("Tirs alliés")
#### A SUPPRIMER APRES TEST
                '''
                else:
                    niv = v[2] + multi
                    joueur = v[1]
                    if niv > self.maxSrength:
                        niv = self.maxSrength
                        joueur = v[1]
                    if v[2] == 0 :
                        niv = -1
                        joueur = -1
                    # augmentation des troupes
                    self.grid[k] = (v[0], joueur, niv)
                    self.display.play_sound('risk_up')
                '''
### test en retirant blink pour voir si plus rapide
                self.blink_box(k)
                self.draw_box(k)
                self.display.update_screen()

    
                ### tester les joueurs en vie
                for player in players :
                    for k, v in enumerate(self.grid):
                        if v[1] == player.ident :
                            player.alive = True
                            break
                        else :
                            player.alive = False
                                                      
### a supprimer, info score
        for player in players:
            print('player ident')
            print(player.ident)
            print('player.score')
            print(player.score)
                            
        winner = self.check_winner(players, actual_round, player_launch, actual_player)
        if winner > -1:
            self.winner = winner
            return 3
 
        
        return return_code

    def check_winner(self, players, actual_round, player_launch, actual_player):
        # test for a winner
        alive_players = []
        for player in players :
            if player.alive :
                alive_players.append(player.ident)

        # victory 
        if len(alive_players) == 1 :
            self.winner =  alive_players[0]
            players[self.winner].score += 100
            return self.winner

        elif len(alive_players) == 0 or (player_launch == self.nb_darts and \
                actual_round >= self.max_round and actual_player == self.nb_players - 1):
            # victory by points if all are ko or its the last turn
            bestscoreid = -1
            bestscore = 0
            for player in players:
                if player.score > bestscore:
                    bestscore = player.score
                    bestscoreid = player.ident
            return bestscoreid
        return -1

    def getCaseFromSegment(self, segment):
        '''
        Récupération de la case correspondante au segment
        '''
        for k, v in enumerate(self.grid):
            if segment == v[0]:
                return k + 1

    def display_segment(self):
        return False

    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        """
        Refresh In-game screen
        """
        # do not show the table scores
        ClickZones = {}

        sx = 43 * self.scale

        # Clear
        self.display.screen.fill((0, 0, 0))
        # background image

        self.display.display_image(self.display.file_class.get_full_filename(
            'risk/risk_back.png', 'images'), 0, 0, self.display.res['x'], self.display.res['y'], True, False, False)

        # draw playernames
        yp1 = 180 * self.scale
        stepy = 152 * self.scale  ###(182)
        for player in Players:
            self.display.display_image(self.display.file_class.get_full_filename(
                f'risk/risk_j{player.ident + 1}.png', 'images'), sx, yp1+player.ident*stepy, 525 * self.scale, 105 * self.scale, True, False, False)
### affiche le score a cote d nom - a effacer
            self.display.blit_text(player.name + ' (' + str(player.score) + ')', sx, yp1+player.ident*stepy+5 * self.scale, 525 * self.scale,
                                   100 * self.scale, color=(255, 255, 255) if actual_player == player.ident else (0, 0, 0))

        # draw round box
        self.display.blit_text(f"{self.display.lang.translate('round')} {actual_round} / {max_round}",
                               200 * self.scale, 975 * self.scale, 223 * self.scale, 60 * self.scale, color=(255, 255, 255))

        # draw dart box
        self.display.blit_text("-".join(Players[actual_player].segments), 700 * self.scale,
                               975 * self.scale, 223 * self.scale, 60 * self.scale, color=(255, 255, 255))

        # draw hex cases
        for k, v in enumerate(self.grid):
            self.draw_box(k)

        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

        self.display.update_screen()

        return [ClickZones]

    # "
    def blink_box(self, case):
        """
        Blink the touched territory
        """
        pos_x = self.pos[case][0] - 250 * self.scale
        pos_y = self.pos[case][1] - 250 * self.scale
        width = 500 * self.scale
        height = 500 * self.scale

        for i in range(0, 4):
            file_path = self.display.file_class.get_full_filename(
                f'risk/risk_{case + 1}_{i + 1}.png', 'images')
            self.display.display_image(
                file_path, 0, 0, self.display.res['x'], self.display.res['y'], True, False, False, UseCache=False)
            self.display.update_screen((pos_x, pos_y, width, height))

    def draw_box(self, case):
        """
        Draw each territory
        """
        v = self.grid[case]

        
        if v[1] > -1:
            self.display.display_image(self.display.file_class.get_full_filename(
                f'risk/risk_{case + 1}_{v[1] + 1}.png', 'images'), 0, 0, self.display.res['x'], self.display.res['y'], True, False, False, UseCache=False)

            # draw strength logos
            stepx = 50 * self.scale
            for i in range(0, v[2]):
                self.display.display_image(self.display.file_class.get_full_filename('risk/risk_strength_'+str(v[1] + 1)+'.png', 'images'), stepx*i +
                                           self.pos[case][0]-60 * self.scale, self.pos[case][1]+20 * self.scale, 30 * self.scale, 30 * self.scale, True, False, False)
                
        if case < 20:
            self.display.blit_text(str(v[0]), self.pos[case][0] - 40 * self.scale, self.pos[case]
                                   [1] - 40 * self.scale, 90 * self.scale, 90 * self.scale, color=(0, 0, 0))

    def backup_round(self, players, actual_round):
        """
        Backup /restore: In case of BACK or CANCEL button pushed
                BACK   : Cancel the last dart thrown
                CANCEL : Back to first dart
        """
        if len(self.backups) < actual_round:
            self.backups.append(deepcopy(players))
            self.backups_grid.append(deepcopy(self.grid))
        else:
            self.backups[actual_round - 1] = deepcopy(players)
            self.backups_grid[actual_round - 1] = deepcopy(self.grid)

    def restore_round(self, roundtorestore):
        """
        Restore
        """
        try:
            self.grid = self.backups_grid[roundtorestore - 1]
            return self.backups[roundtorestore - 1]
        except:  # pylint: disable=bare-except
            try:
                self.grid = self.backups_grid[roundtorestore]
                return self.backups[roundtorestore]
            except:  # pylint: disable=bare-except
                try:
                    self.grid = self.backups_grid[roundtorestore + 1]
                    return self.backups[roundtorestore + 1]
                except:  # pylint: disable=bare-except
                    return None
