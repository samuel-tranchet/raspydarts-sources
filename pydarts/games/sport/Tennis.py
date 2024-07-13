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
OPTIONS = {'set': 2, 'cote': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Tennis.png'
HEADERS = ['Zone', 'Pts', '1', '2', '3', '4', '5'] # Columns headers - Must be a string

SCORES = {0: 0, 1: 15, 2: 30, 3: 40, 4:40}

def check_players_allowed(nb_players):
   '''
   Return the player number max for a game.
   '''
   return nb_players % 2 == 0

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
        self.character = 0


class Game(cgame.Game):
    '''
    tennis game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options

        self.nb_players = nb_players

        self.nb_set = int(options['set'])

        #  Get the maximum round number
        self.max_round = 99   ###int(options['max_round'])

        self.cote = not(options['cote'])

        self.winner = None

        self.leds = True
        self.next = 0

        self.nb_set = min(3, max(1, self.nb_set))
        self.nb_game = 1

        self.set = (self.nb_set * 2) - 1

        self.points_j1 = 0
        self.points_j2 = 0
        self.pointsTB_j1 = 0
        self.pointsTB_j2 = 0
        self.flecheTB_jouee = 0

        self.game_j1 = 0
        self.game_j2 = 0

        self.sets_j1 = 0
        self.sets_j2 = 0

        self.tiebreak = False
        self.calcul = True

        ### pour test early car compte 2x
        self.early = False

        ### Colonne qui affiche le score du set (pour player.columns)
        self.set_column = 2

        self.num_set = 1
        #test
        self.my_hits = []

        if self.nb_players == 4:
            self.display.teaming = True
        else:
            self.display.teaming = False

        # Vitesse de pronociation 80 - 150
        # = Arbitre aléatoire ?
        self.speed = random.randint(90, 120)

    def init_leds(self, players, actual_player, actual_round, hit=None):
        '''
        Compute leds coloration depending on round and "hit"
        '''

        self.hits_bull = ['SB', 'DB']
        self.leds_bull = ['SB#white|DB#white']

        if self.cote:
            # Haut
            # ----
            # Bas
            hits_j1 = [8, 16, 7, 19, 17, 2, 15, 10]
            hits_j2 = [14, 9, 12, 5, 1, 18, 4, 13]
            net = [11, 6]
            out = [20, 3]
        else:
            # Gauche | Droite
            hits_j1 = [5, 12, 9, 14, 8, 16, 7, 19]
            hits_j2 = [1, 18, 4, 13, 10, 15, 2, 17]
            net = [20, 3]
            out = [11, 6]

        # Pour fixer le segment à toucher
        if hit is not None:
            hits_j1 = [hit]
            hits_j2 = []

        hits_j1 = [f'{mult}{hit}' for hit in hits_j1 for mult in ['S', 'D', 'T']]
        hits_j2 = [f'{mult}{hit}' for hit in hits_j2 for mult in ['S', 'D', 'T']]

        ### Le terrain change a chaque jeu impair
        if int(self.nb_game / 2) % 2 == 0:
            if hit is None:
                self.hits = hits_j1
                self.hits_inv = hits_j2
                self.my_hits = hits_j1
            else:
                self.hits = [f'{mult}{hit}' for mult in ['S', 'D', 'T']]
                self.hits_inv = []
                self.my_hits = [hit]
            cote = "terrain 1"
        else:
            if hit is None:
                self.hits = hits_j2
                self.hits_inv = hits_j1
                self.my_hits = hits_j2
            else:
                self.hits = []
                self.hits_inv = [f'{mult}{hit}' for mult in ['S', 'D', 'T']]
                self.my_hits = [hit]
            cote = "terrain 2"

        ### Terrains
        leds_j1 = [f'{hit}#{self.colors[0]}' for hit in self.hits]
        leds_j2 = [f'{hit}#{self.colors[2]}' for hit in self.hits_inv]

        #### out et net
        self.hits_net = [f'{mult}{number}' for mult in ['S', 'D', 'T'] for number in net]
        self.hits_out = [f'{mult}{number}' for mult in ['S', 'D', 'T'] for number in out]

        self.leds_net = [f'{hit}#white' for hit in self.hits_net]
        self.leds_out = [f'{hit}#red' for hit in self.hits_out]

        ####
        self.logs.log("DEBUG", f"game={self.nb_game} cote={cote} self.my_hits = {self.my_hits}")
        self.logs.log("DEBUG", f"return {leds_j1 + leds_j2 + self.leds_bull + self.leds_out}")

        return leds_j1 + leds_j2 + self.leds_bull + self.leds_out

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Actions done before each dart throw - for example, check if the player is allowed to play
        '''
        return_code = 0
        self.early = False
        
        #### AJOUT - recupere lID du joueur actif pour dire les score (15 ou 0-15)
        self.p_ident = players[actual_player].ident
        
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            # Init oolumns
            for player in players:
                player.reset_rounds(self.max_round)
                for c in range(0, 7):
                    player.columns[c] = ['' , 'txt']

            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.points = 0
                player.targets = ''
            self.display.speech(f'{players[actual_player].name} au service', speed=self.speed)

        # Each new player
        if player_launch == 1:
            # Nouveau jeu
            if not self.tiebreak:
                for player in players:
                    player.columns[1] = [0 , 'int']
                self.pointsTB_j1 = 0
                self.pointsTB_j2 = 0

            players[actual_player].reset_darts()
            ### test pour early
            self.fleche_jouee = player_launch
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            self.points_j1 = 0
            self.points_j2 = 0
            self.calcul = False
            ### pour test early car compte 2x
            self.early = False

            #DMD
            self.dmd.send_text(f"{players[actual_player].name} au Service")

            # Init leds
            self.targets = self.init_leds(players, actual_player, actual_round)

        self.rpi.set_target_leds('|'.join(self.targets))

        # gestion fleche
        if self.points_j1 < 10:
                self.nb_darts = 99

        #self.calcul_points(players)
        self.update_columns(players)

        # Print debug output
        self.logs.log("DEBUG", self.infos)
        return return_code

    def mate_name(self, players, player_id):
        if len(players) == 2:
            return players[player_id].name
        else:
            return f'Equipe {player_id + 1}'

    def calcul_points(self, players, actual_player):

        '''
        Mise à jour des points
        '''

        message = ''
        announcement = ''

        if not self.tiebreak:
            # Maximum 5 points
            self.points_j1 = min(5, self.points_j1)
            self.points_j2 = min(5, self.points_j2)

            if self.points_j1 == 4 and self.points_j2 < 3:
                # Jeu gagné pour J1
                self.points_j1 = 5
            elif self.points_j2 == 4 and self.points_j1 < 3:
                # Jeu gagné pour J2
                self.points_j2 = 5

            if self.points_j1 == self.points_j2 and self.points_j1 in (0, 4):
                if self.points_j1 == 4:
                    # Egalié, on remet à 40-40
                    self.points_j1 = 3
                    self.points_j2 = 3

                score = SCORES[self.points_j1]
                for player in players:
                    player.columns[1] = [score, 'int']

            if self.points_j1 in (1, 2, 3):
                for player in players:
                    if player.ident in (0, 2):
                        player.columns[1] = [SCORES[self.points_j1], 'int']

            if self.points_j2 in (1, 2, 3):
                for player in players:
                    if player.ident in (1, 3):
                        player.columns[1] = [SCORES[self.points_j2], 'int']

            ### ADV
            if self.points_j1 == 4 and self.points_j2 == 3:
                for player in players:
                    if player.ident == 0 or player.ident == 2:
                        player.columns[1] = ['ADV' , 'txt']

            elif self.points_j2 == 4 and self.points_j1 == 3:
                for player in players:
                    if player.ident == 1 or player.ident == 3:
                        player.columns[1] = ['ADV' , 'txt']
        else:
            '''
            Tie break
            '''
            for player in players:
                if player.ident in (0, 2):
                    player.columns[1] = [self.pointsTB_j1 , 'int']
                else:
                    player.columns[1] = [self.pointsTB_j2 , 'int']

                self.dmd.send_text(f'{self.pointsTB_j1} - {self.pointsTB_j2}')

        '''
        Mise à jour des jeux
        '''

        next_game = False
        next_set = False

        if self.points_j1 >= 5 or (self.pointsTB_j1 > self.pointsTB_j2 + 1 and self.pointsTB_j1 >= 7):
            # J1 gagne le set
            self.game_j1 += 1
            next_game = True
            message = f'Jeu {self.mate_name(players, 0)}'

        elif self.points_j2 >= 5 or (self.pointsTB_j2 > self.pointsTB_j1 + 1 and self.pointsTB_j2 >= 7):
            # J2 gagne le set
            self.game_j2 += 1
            next_game = True
            message = f'Jeu {self.mate_name(players, 1)}'

        if self.game_j1 == self.game_j2 == 6 and not self.tiebreak:
            self.tiebreak = True
            self.dmd.send_text("TIEBREAK")
            for player in players:
                player.columns[0] = ('', 'str')
            announcement = f'{self.next_player(players, actual_player)} au service'
            return 1, 'TIEBREAK', announcement

        self.update_columns(players)
        print(f"calcul_points : Flechette {self.flecheTB_jouee}")
        print(f"calcul_points : Joueur 1 : {self.points_j1}/{self.game_j1}/{self.sets_j1} -- {self.pointsTB_j1}")
        print(f"calcul_points : Joueur 2 : {self.points_j2}/{self.game_j2}/{self.sets_j2} -- {self.pointsTB_j2}")
        print(f"calcul_points : next_game = {next_game}")

        if next_game:
            announcement = f'{self.next_player(players, actual_player)} au service'
            self.nb_game += 1
            # Raz points
            self.points_j1 = 0
            self.points_j2 = 0
            self.pointsTB_j1 = 0
            self.pointsTB_j2 = 0
            self.tiebreak = False
            self.update_columns(players)
            for player in players:
                player.columns[0] = ('', 'str')
            
            '''
            Mise à jour des sets
            '''
            if (self.game_j1 >= 6 and self.game_j1 > self.game_j2 + 1) or self.game_j1 == 7:
                next_set = True
                message = f'Manche {self.mate_name(players, 0)}'
                players[0].score += 1
                if len(players) == 4:
                    players[2].score += 1
                self.sets_j1 += 1

            elif (self.game_j2 >= 6 and self.game_j2 > self.game_j1 + 1) or self.game_j2 == 7:
                next_set = True
                players[1].score += 1
                message = f'Manche {self.mate_name(players, 1)}'
                if len(players) == 4:
                    players[3].score += 1
                self.sets_j2 += 1

            print(f"next_set = {next_set}")
            if players[0].score >= self.nb_set:
                message = f'Jeu, Set et Match {players[0].name}'
                self.display.speech(message, speed=self.speed)
                self.winner = 0
                self.logs.log("DEBUG", message)
                return 3, None, None
            elif players[1].score >= self.nb_set:
                message = f'Jeu, Set et Match {players[1].name}'
                self.display.speech(message, speed=self.speed)
                self.winner = 1
                self.logs.log("DEBUG", message)
                return 3, None, None
            # Joueur suivant
            #self.display.speech(message, speed=self.speed)
            if next_set:
                self.set_column += 1
                self.game_j1 = 0
                self.game_j2 = 0

            return 1, message, announcement
        elif self.tiebreak:
            if self.pointsTB_j1 == self.pointsTB_j2 == 0:
                # Ne pas prononcer le 0-0 au début du tiebreak
                return None, None, None
            ### AJOUT condition pour dire le scoreTB suivant le joueur actif (15-0 ou 0-15)
            if self.p_ident == 0 or self.p_ident == 2 :
                message = f'{self.pointsTB_j1} - {self.pointsTB_j2}'
            else :
                message = f'{self.pointsTB_j2} - {self.pointsTB_j1}'
        elif self.points_j1 != self.points_j2:
            if self.points_j1 == 4:
                message = f'Avantage {self.mate_name(players, 1)}'
            elif self.points_j2 == 4:
                message = f'Avantage {self.mate_name(players, 1)}'
            elif self.points_j1 in (0, 1, 2, 3) and self.points_j2 in (0, 1, 2, 3):
                ### AJOUT condition pour dire le score suivant le joueur actif (15-0 ou 0-15)
                if self.p_ident == 0 or self.p_ident == 2 :
                    message = f'{SCORES[self.points_j1]} - {SCORES[self.points_j2]}'
                else :
                    message = f'{SCORES[self.points_j2]} - {SCORES[self.points_j1]}'
            else:
                message = f'{self.pointsTB_j1} - {self.pointsTB_j2}'
        elif self.points_j1 in (1, 2, 3):
            # Egalite
            message = f'{SCORES[self.points_j1]} A'
        else:
            message = None

        #self.display.speech(message, speed=self.speed)
        return 0, message, announcement

    def next_player(self, players, actual_player):

        return players[(actual_player + 1) % len(players)].name

    def pnj_score(self, players, actual_player, level, player_launch):
        '''
        pnj score
        '''
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
        '''
        Function run after each dart throw - for example, add points to player
        '''
        handler = self.init_handler()
        handler['speech_speed'] = self.speed

        ### test pour early
        self.fleche_jouee = player_launch

        ### retire le bandeau de ce qu on a touche
        self.show_segment = False

        ###DMD
        if player_launch == 4 or player_launch == 7:
            self.dmd.send_text("Nouvelle Balle")
            
        #### AJOUT - affiche HIT
        
        pointsTB = 1
        if hit == 'SB' :
            points123 = 1
            points135 = 1
        elif hit == 'DB' :
            points123 = 2
            points135 = 2
        elif hit[0:1] == 'S':
            points123 = 1
            points135 = 1
        elif hit[0:1] == 'D':
            points123 = 2
            points135 = 5
        elif hit[0:1] == 'T':
            points123 = 3
            points135 = 3
        ### AJOUT  ==> ne compte pas les points si on touche SB/DB, pas compris pourquoi
        else:
            points123 = 0
            points135 = 0
            pointsTB = 0

        if players[actual_player].ident in (0, 2):
            color = 'green'
            team = 1
        else:
            color = 'blue'
            team = 2

        self.logs.log("DEBUG", f"hit is {hit} / points123 = {points123} / points135 = {points135}")
        self.logs.log("DEBUG", f"color is {color} / team = {team}")

        #### DMD - TOUCHE LE SEGMENT WHITE / RED
        if hit in self.hits_bull:
            self.dmd.send_text("FILET")
            self.display.speech('Filet', speed=self.speed)

        elif hit in self.hits_net + self.hits_out:
            self.dmd.send_text("BALLE OUT")
            self.display.speech('out', speed=self.speed)

        print(f"hit : {hit}#{color}")
        print(f"targets : {self.targets}")
        print(f"player_launch = {player_launch}")
        if f'{hit}#{color}' in self.targets and player_launch == 1:
            print(f"ok 1ere flechette")
            # 1ère fléchette : je joueur touche le bon segment
            # On fixe le bon segment
            self.targets = self.init_leds(players, actual_player, actual_round, hit[1:])

            if self.tiebreak:
                if players[actual_player].ident in (0, 2):
                    self.pointsTB_j1 += 1
                else:
                    self.pointsTB_j2 += 1
                self.flecheTB_jouee += 1
            elif players[actual_player].ident in (0, 2):
                self.points_j1 += points135
            else:
                # Equipe 2, bon segment touche
                self.points_j2 += points135

            #self.display.play_sound('tennis_hit')
            players[actual_player].columns[0] = (hit[1:], 'int')

        elif player_launch == 1:
            print(f"ko 1ere flechette")
            # 1ère fléchette : je joueur ne touche pas le bon segment
            # On lui affecte un segment de son terrain au hasard

            hits = self.my_hits
            alea = random.choice(hits)
            players[actual_player].targets = self.init_leds(players, actual_player, actual_round, alea[1:])
            players[actual_player].columns[0] = (alea[1:], 'int')

            if self.tiebreak:
                if players[actual_player].ident in (0, 2):
                    self.pointsTB_j2 += 1
                else:
                    self.pointsTB_j1 += 1
                self.flecheTB_jouee += 1
            elif players[actual_player].ident in (0, 2):
                self.points_j2 += points135
            else:
                self.points_j1 += points135

            #self.display.play_sound('tennis_miss')

        else:
            # Fléchettes suivantes, le joueur touche le bon segment
            if f'{hit}#{color}' in players[actual_player].targets:
                print(f"ok 2eme flechette")
                if self.tiebreak:
                    if players[actual_player].ident in (0, 2):
                        self.pointsTB_j1 += 1
                    else:
                        self.pointsTB_j2 += 1
                    self.flecheTB_jouee += 1
                elif players[actual_player].ident in (0, 2):
                    self.points_j1 += points123
                else:
                    self.points_j2 += points123

                #self.display.play_sound('tennis_hit')

                players[actual_player].targets = self.init_leds(players, actual_player, actual_round, hit[1:])
                players[actual_player].columns[0] = (hit[1:], 'int')

            else:
                print(f"ko 2eme flechette")
                # Fléchettes suivantes, le joueur ne touche pas le segement demandé
                #self.display.play_sound('tennis_miss')

                alea = random.choice(self.my_hits)
                players[actual_player].targets = self.init_leds(players, actual_player, actual_round, alea[1:])
                players[actual_player].columns[0] = (alea[1:], 'int')

                if players[actual_player].ident in (0, 2):
                    if self.tiebreak:
                        self.pointsTB_j2 += 1
                        self.flecheTB_jouee += 1
                    else:
                        self.points_j2 += points123
                elif self.tiebreak:
                    ### Forcement equipe 2
                    self.pointsTB_j1 += 1
                    self.flecheTB_jouee += 1
                else:
                    self.points_j1 += points123

        '''
        Calcul des points, mise à jour affichage, identification du gagnant
        '''
        return_code, message, announcement = self.calcul_points(players, actual_player)

        handler['return_code'] = return_code
        handler['speech'] = message
        handler['message'] = message
        handler['dmd'] = message
        handler['announcement'] = announcement

        if return_code == 0 and self.tiebreak and self.flecheTB_jouee % 2 == 1:
            # Tiebreak, le joueur 1 lance 1 flechette puis c'est au joueur 2 d'en lancer 2
            handler['return_code'] = 1

        return handler

    def update_columns(self, players):

        SETS = {
                1: (['1', '', '', '', ''], [0]),
                3: (['1', '2', '3', '', ''], [0, 2, 4]),
                5: (['1', '2', '3', '4', '5'], [0, 2, 4, 6, 8])
                }
        infos = SETS[self.set]
        for h in (0, 1, 2, 3, 4):
            self.headers[2 + h] = infos[0][h]

        for player in players:
            c = 2
            if player.ident in (0, 2):
                player.columns[self.set_column] = [self.game_j1, 'int']
            else:
                player.columns[self.set_column] = [self.game_j2, 'int']

    def check_winner(self, players):

        win_score = [(1, 1), (3, 2), (5,3)]

        for player in players:
            if (self.set, player.score) in win_score:
                return player.ident
        return None

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Next player : Le joueur adverse gagne le set
        '''

        if not self.early:
            if actual_player in (0, 2):
                if self.tiebreak:
                    self.pointsTB_j2 = max(self.pointsTB_j1 + 2, 7)
                else:
                    self.points_j2 = 4
            else:
                if self.tiebreak:
                    self.pointsTB_j1 = max(self.pointsTB_j2 + 2, 7)
                else:
                    self.points_j1 = 4

            return_code, message, announcement = self.calcul_points(players, actual_player)

            self.display.message([message], 0, None, 'middle', 'big')
            self.display.speech(message, speed=self.speed)
            self.dmd.send_text(message)

            self.early = True
            return return_code


    def post_round_check(self, players, actual_round, actual_player):
        '''
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        '''

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2

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

    def miss_button(self, players, actual_player, actual_round, player_launch):
        pass
