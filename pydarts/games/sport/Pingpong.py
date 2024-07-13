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
OPTIONS = {'theme': 'default', 'win': 11, 'simple50': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Ping-Pong.png'
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
        #self.multiplicateur = 1 

class Game(cgame.Game):
    """
    PingPong game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        #  Get the maximum round number
        self.max_round = 99
        self.simple = options['simple50']
       
        self.winscore = options['win']
        
        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None

        self.video_player = video_player

        self.points = 0
        self.test_win = False
  
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
                  
        if player_launch == 1:
            players[actual_player].reset_darts()
            self.points = 0
            

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0

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
        

        # Check winner
        self.check_winner(players, actual_player)
        
        if self.winner is not None:
            return_code = 3

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

        if hit :
                score = self.score_map[hit]
                self.points += score
                players[actual_player].columns[4] = (self.points, 'int')

        
        return_code = 0
        
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        #players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score
        
        

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        
        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

   
        # Check last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and (player_launch == self.nb_darts or return_code == 1)  :
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            return_code = 2
            
        # Check winner
        self.check_winner(players, actual_player)
        if self.winner is not None:
            return_code = 3

        self.logs.log("DEBUG", self.infos)
        
        return return_code

       

            
    def early_player_button(self, players, actual_player, actual_round):
        print('early - nextplayer presse')
        
                
        return 1

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        print('post round check')
        self.calcul(players, actual_player)
        #self.check_winner(players, actual_player)      
        
        if actual_round >= self.max_round and actual_player == len(players) - 1 or self.test_win :
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

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        EMPTY
        """  
        print('miss boutton - pass')
        pass

    def display_segment(self):
       """
       Set if a message is shown to indicate the segment hitted !
       """
       return False

    def calcul(self, players, actual_player) :
        print('def calcul')
        liste_score = []
        if players[actual_player].ident == self.nb_players -1 :
                for player in players :
                        ### creation de la liste des scores (recuperation du score dans la colonne 4 et de l ident du joueur)
                        liste_score.extend([[player.columns[4][0],player.ident]]) 

                score_trie=sorted(liste_score)
                print('liste des scores tries')
                print(score_trie)

                #### attribution des points
                ## meilleur score = 1 point (si egalite, 1 points pour chaque joueur)
                ## 2eme et reste = 0 points
                if score_trie[-1][0] == 0 :
                        points = 0
                else :
                        points = 1	
       
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

                ### ajoute les points au score des joueurs
                for i in range(self.nb_players) :
                        for k, v in enumerate(score_acquis):
                                if v[1] == i :
                                        for player in players :
                                                if player.ident == i :
                                                        player.score += v[0]    
                
                score_joueur = []
                for player in players :
                       score_joueur.append([player.score, player.ident])
                score_joueur = sorted(score_joueur)

                print('score_joueur')
                print(score_joueur)

		
                ### determine le gagnant
                if int(score_joueur[-1][0]) >= int(self.winscore) and score_joueur[-2][0] <= int(score_joueur[-1][0])-2 :
                        print('winner')
                        winner = score_joueur[-1][1]
                        print(winner)
                        self.test_win = True
                        self.winner = score_joueur[-1][1]
                        self.check_winner(players, actual_player)        
                else :
                        print('pas de gagnant, le jeu continue')

        return 1
        
    def check_winner(self, players, actual_player):
        '''
        Function to check winner
        '''
        print('dans checkwinner - winner')
        print(self.winner)
        if self.winner is not None:
            return 3
