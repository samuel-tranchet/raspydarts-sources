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
OPTIONS = {'theme': 'default', 'max_round': 10, 'simple50': False, 'suddendeath': False, 'lives': 2, 'multix123': False, 'shoot_out': False, 'super_shoot_out': False, 'segment': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'High_Score.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Rnd', 'PPD', 'PPR'] # Columns headers - Must be a string

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
        self.multiplicateur = 1
        self.super_multiplicateur = 1

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
        self.simple = options['simple50']
        self.sudden_death = options['suddendeath']
        self.shoot_out = options['shoot_out']
        self.super_shoot_out = options['super_shoot_out']
        self.lives = int(options['lives'])
        self.segment = options['segment']
        self.multix123 = options['multix123']
        # In order to display dead players at bottom of score's table
        self.position = nb_players

        if self.sudden_death:
            self.headers[3] = 'Vies'

        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None

        self.video_player = video_player

### declaration variable pour shoot out
        self.multiplicateur = 1
        self.super_multiplicateur = 1
        self.leds = True
        self.calcul = False

        if self.shoot_out and not self.super_shoot_out:
            self.headers[6] = 'Mlti'
            self.headers[5] = "--"
            self.max_round = 8
        elif self.super_shoot_out:
            self.headers[5] = 'Mlt1'
            self.headers[6] = "Mlt2"
            self.shoot_out = True
            self.max_round = 8
            self.shoot_out = True
        else:
            self.headers[5] = 'PPD'
            self.headers[6] = "PPR"
            self.max_round = int(options['max_round'])

    def compute_position(self, players, dead=None):

        if dead is None:
            index = 1
            for player in players:
                player.position = index
                index += 1
        else:
            for player in players:
                if player.position == dead:
                    player.position = self.position
                    self.position -= 1
                elif player.alive and player.position > dead:
                    player.position -= 1

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
### AJOUTE LE BULLS DANS LA LISTE TARGETS
        if actual_round == 8 and self.shoot_out and player_launch == 1 or self.multiplicateur == 20:
                ### ajoute le bull
                for player in players:

                        Sbull = [f'SB#{self.colors[0]}']
                        Dbull = [f'DB#{self.colors[0]}']
                        self.rpi.set_target_leds('|'.join(Sbull + Dbull))

                        player.targets = player.targets + Sbull + Dbull

                        print('8eme tour - ajout bull')
                        print('players target')
                        print (player.targets)



### INITIALISE LES LEDS DE TOUTES LES LEDS POUR CHAQUE JOUEUR -- player.targets
        if self.leds:
                for player in players:
                        hitsS = [f'S{number}#{self.colors[0]}' for number in range(1,21)]
                        hitss = [f's{number}#{self.colors[0]}' for number in range(1,21)]
                        hitsD = [f'D{number}#{self.colors[0]}' for number in range(1,21)]
                        hitsT = [f'T{number}#{self.colors[0]}' for number in range(1,21)]
                        self.rpi.set_target_leds('|'.join(hitsS + hitsD + hitsT + hitss))

                        player.targets = hitsS + hitsD + hitsT + hitss

                        print('players target - self.led')
                        print (player.targets)

                        self.leds = False

        if player_launch == 1:
            players[actual_player].reset_darts()

        if not players[actual_player].alive:
            # Player is dead
            return 4

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            self.compute_position(players)
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

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

### affiche les targets du joueur
            if self.shoot_out:
                self.rpi.set_target_leds ('')
                self.rpi.set_target_leds('|'.join(players[actual_player].targets))

                players[actual_player].columns[5] = (players[actual_player].multiplicateur, 'int')

            else:
                self.rpi.set_target_leds ('')


            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)
### AFFICHE LE MULTIPLICATEUR SI SHOOT OUT = TRUE
            if self.shoot_out and not self.super_shoot_out:
                players[actual_player].columns[6] = (players[actual_player].multiplicateur, 'int')
            elif self.shoot_out and self.super_shoot_out:
                players[actual_player].columns[5] = (players[actual_player].multiplicateur, 'int')
                players[actual_player].columns[6] = (players[actual_player].super_multiplicateur, 'int')

        # Display avg
        if actual_round == 1 and player_launch == 1:
                if self.shoot_out and not self.super_shoot_out:
                        players[actual_player].columns[6] = (players[actual_player].multiplicateur, 'int')

                elif self.super_shoot_out and self.shoot_out:
                        players[actual_player].columns[5] = (players[actual_player].multiplicateur, 'int')
                        players[actual_player].columns[6] = (players[actual_player].super_multiplicateur, 'int')
                elif self.super_shoot_out and not self.shoot_out:
                        players[actual_player].columns[5] = (players[actual_player].multiplicateur, 'int')
                        players[actual_player].columns[6] = (players[actual_player].super_multiplicateur, 'int')
                elif not self.shoot_out and not self.super_shoot_out:
                        players[actual_player].columns[5] = (0.0, 'int')
                        players[actual_player].columns[6] = (0.0, 'int')
                else:
                        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
                        players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')
        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')

        if self.multix123:
                self.headers[0] = 'X1'
                self.headers[1] = 'X2'
                self.headers[2] = 'X3'

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
        handler = self.init_handler()

        handler['show'] = (players[actual_player].darts, hit, True)
        handler['sound'] = hit

### SI ON TOUCHE SB OU DB AU 8eme TOUR, ON AJOUTE LES POINTS DE BULL * MULTIPLICATEUR
        if hit == 'SB' and actual_round == 8 or self.multiplicateur == 20:
            self.multiplicateur = players[actual_player].multiplicateur
            players[actual_player].multiplicateur += 1
            if self.super_shoot_out:
                self.super_multiplicateur = players[actual_player].super_multiplicateur
                players[actual_player].super_multiplicateur += 1

            self.calcul = True
        if hit == 'DB' and actual_round == 8 or self.multiplicateur == 20:
            self.multiplicateur = players[actual_player].multiplicateur
            players[actual_player].multiplicateur += 1
            if self.super_shoot_out:
                self.super_multiplicateur = players[actual_player].super_multiplicateur
                players[actual_player].super_multiplicateur += 1
            self.calcul = True

### QD ON TOUCHE UN SEGMENT ALLUME, ON LE SUPPRIME

        if hit + '#green' in players[actual_player].targets:
            if self.shoot_out:
                try:
                    while True:
                        if self.segment:
                            players[actual_player].targets.remove(hit+'#green')
                        else:
                            players[actual_player].targets.remove('s'+hit[1:]+'#green')
                            players[actual_player].targets.remove('S'+hit[1:]+'#green')
                            players[actual_player].targets.remove('D'+hit[1:]+'#green')
                            players[actual_player].targets.remove('T'+hit[1:]+'#green')

                        self.multiplicateur = players[actual_player].multiplicateur
                        players[actual_player].multiplicateur += 1
                        if self.super_shoot_out:
                            self.super_multiplicateur = players[actual_player].super_multiplicateur
                            players[actual_player].super_multiplicateur += 1

### TEST pour calcul - calcule = true
                        self.calcul = True

                except:
                    pass

            elif self.multix123:
                score = self.score_map[hit]
                self.calcul = True

### MAJ DES TARGETS DU JOUEUR
            if self.shoot_out:
                self.rpi.set_target_leds ('')
                self.rpi.set_target_leds('|'.join(players[actual_player].targets))
            else:
                self.rpi.set_target_leds ('')

        elif not (hit+'#green') in players[actual_player].targets:
            #score = 0
            players[actual_player].darts_thrown += 1
            if self.super_shoot_out:
                self.super_multiplicateur = 1
                players[actual_player].super_multiplicateur = 1

### AJOUTE OU NON LE SCORE SI SLEF.CALCUL EST TRUE OU FALSE SINON SCORE = A HIT
        if self.shoot_out:
            if self.calcul:
                if self.shoot_out and self.super_shoot_out:
                    score = self.score_map[hit] * self.multiplicateur * self.super_multiplicateur
                    self.calcul = False
                elif self.shoot_out and not self.super_shoot_out:
                    score = self.score_map[hit] * self.multiplicateur
                    self.calcul = False
            else:
                score = self.score_map[hit] * 0

        elif self.multix123:
            if self.calcul:
                if player_launch == 1:
                    score = self.score_map[hit]
                    self.calcul = False
                elif player_launch == 2:
                    score = self.score_map[hit] * 2
                    self.calcul = False
                elif player_launch == 3:
                    score = self.score_map[hit] * 3
                    self.calcul = False
        else:
            score = self.score_map[hit]

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Calculate average and display in column 7
        if self.shoot_out and not self.super_shoot_out:
            players[actual_player].columns[6] = (players[actual_player].multiplicateur, 'int')
        elif self.shoot_out and self.super_shoot_out:
            players[actual_player].columns[5] = (players[actual_player].multiplicateur, 'int')
            players[actual_player].columns[6] = (players[actual_player].super_multiplicateur, 'int')
        elif self.super_shoot_out and not self.shoot_out:
            players[actual_player].columns[5] = (players[actual_player].multiplicateur, 'int')
            players[actual_player].columns[6] = (players[actual_player].super_multiplicateur, 'int')
        else:
            players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
            players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')

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
                handler['return_code'] = 3
            else:
                # No winner : last round reached
                handler['return_code'] = 2

        return handler

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        handler = self.init_handler()
        handler['return_code'] = -2
        if self.sudden_death:
            dead = self.find_deads(players)
            if dead is not None:
                players[dead].alive = False
                self.compute_position(players, players[dead].position)

                winner = self.get_winner(players)
                if winner is not None:
                    self.winner = winner
                    self.logs.log("DEBUG", f"winner is {winner}")
                    handler['return_code'] = winner
                else:
                    self.logs.log("DEBUG", f"dead is {dead}")
                    handler['announcement'] = f'{players[dead].name} est éliminé'
        elif actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            handler['return_code'] = self.best_score(players)
        return handler

    def find_deads(self, players):
        """
        Sudden death option:
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
            players[dead].columns[3] = (players[dead].lives, 'int')
            if players[dead].lives < 1:
                return dead
            return None
        return None

    def get_winner(self, players):
        """
        Sudden death option:
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
