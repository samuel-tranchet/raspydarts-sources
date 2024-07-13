########## reste a faire
# SUPPRIMER STRIKE/SPARE APRES LE CALCUL
# condition calcul
# condition pour denier tour en cas de strike (+ 1 coup supplementaire)
# modifier condition STRIKE (player.strike envoie next_player 1 - pas bon)
# modifier condition STRIKE (donne 20 points qd on le fait la 1ere fois a la pplace de le faire le tour d apres)


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
OPTIONS = {'theme': 'default', 'max_round': 10, 'master': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Bowling.png'
HEADERS = ['PIST', '1', '2', '', 'Rnd', 'SPAR', 'STRK'] # Columns headers - Must be a string

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

        #self.columns[6] = '1'
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

        self.master = options['master']

        if self.master :
            self.simple = 4
            self.double = 7
        else:
            self.simple = 5
            self.double = 9

        self.winner = None
        self.video_player = video_player

### declaration variable
        self.leds = True
        self.next = 0
        #self.score_temp = 0
        self.fleche1 = 0
        self.fleche2 = 0
        self.fleche3 = 0
        self.fleche4 = 0
        self.multiplie = 1
        self.fleche_jouee = 0
        self.bonus = 0

        #self.var = False

        self.headers[6] = "STRK"
        self.headers[5] = "SPAR"
        self.message = 'Bowling-choix'
        self.video = 0


    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

        if self.leds :
            for player in players :
                hitsS = [f'S{number}#{self.colors[0]}' for number in range(1,21)]
                hitsD = [f'D{number}#{self.colors[0]}' for number in range(1,21)]
                hitsT = [f'T{number}#{self.colors[0]}' for number in range(1,21)]

                player.targets = hitsS + hitsD + hitsT

                print('players target')
                print (player.targets)

                self.leds = False

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
                player.choix = True
                player.ajouer = 1
                player.targets_ajouer = ''
                player.spare = False
                player.strike = False
                player.poststrike = False
                player.bonus = False
                player.double = 0
                player.triple = 0

        ### TEST POUR AFFICHER LA CASE BONUS TOUR 10
        if actual_round == self.max_round :
            self.headers[3] = '3'
        else:
            self.headers[3] = ''

        # Each new player
        if player_launch == 1:
            players[actual_player].reset_darts()

            ### test pour early
            self.fleche_jouee = player_launch

            players[actual_player].choix = True

            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            self.fleche1 = 0
            self.fleche2 = 0
            self.fleche3 = 0
            self.fleche4 = 0

            self.message = 'Bowling-choix'
            self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')

            #Reset display Table
            players[actual_player].columns = []

            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])

            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

        if players[actual_player].poststrike :
            players[actual_player].strike = True
            #self.var = False

        if players[actual_player].poststrike :
            players[actual_player].columns[6] = ['bowling_strike', 'image']
            players[actual_player].columns[5] = ['bowling_nospare', 'image']
            players[actual_player].poststrike = False
            self.next = 1

        if not players[actual_player].bonus :
            self.nb_darts = 3

        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')

### SIMPLE VERIFICATION - A EFFACER
        print('')
        print('PRE DART')
        print('PHASE CHIFFRE A JOUER')
        print('player.choix doit etre false')
        print(players[actual_player].choix)
        print('player.ajouer doit etre different de 0')
        print(players[actual_player].ajouer)
        print('player.target_ajouer est ')
        print(players[actual_player].targets_ajouer)
        print('spare est en ')
        print(players[actual_player].spare)
        print('strike est en ')
        print(players[actual_player].strike)
        print('fleche2 = ')
        print(self.fleche2)
        print('fleche3 = ')
        print(self.fleche3)
        print('multiple = ')
        print(self.multiplie)
        print('')
        print('')
        print('bonus est en ')
        print(players[actual_player].bonus)
        ### test pour voir contenu de self.double
        print ('players[actual_player].double - pre dart')
        print(players[actual_player].double)
        print('tour en cours')
        print(actual_round)

        if players[actual_player].choix :
            print('CHOISI UNE PISTE')
            self.rpi.set_target_leds('|'.join(players[actual_player].targets))
        else:
            print('PISTE CHOISIE')
            print('target a jouer')
            print(players[actual_player].targets_ajouer)
            self.rpi.set_target_leds(players[actual_player].targets_ajouer)

### AFFICHE STRIKE OU SPARE OU RIEN
        if players[actual_player].spare :
            players[actual_player].columns[5] = ['bowling/bowling-check', 'image']
            #players[actual_player].columns[6] = ['bowling/bowling_nostrike', 'image']
            #self.multiplie = 2
        elif players[actual_player].strike :
            players[actual_player].columns[6] = ['bowling/bowling-check', 'image']
            #players[actual_player].columns[5] = ['bowling/bowling_nospare', 'image']
            players[actual_player].spare = False
            #self.multiplie = 2
        #else:
            #players[actual_player].columns[6] = ['bowling_nostrike', 'image']
            #players[actual_player].columns[5] = ['bowling_nospare', 'image']
            #self.multiplie = 1

### TEST SUR STRIKE CONSECUTIF
        if players[actual_player].double in (2,3):##and actual_round != self.max_round:
            self.bonus = 10
        elif actual_round == self.max_round:
            self.bonus = 10
        else:
            self.bonus = 0

        if players[actual_player].double > 3 :
            players[actual_player].double = 0
            print(' ligne 238 - bonus double = 0')
            print (players[actual_player].double)

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
        ### test pour early
        self.fleche_jouee = player_launch

        # Play DMD animation
        if super().play_show(players[actual_player].darts, hit, play_special=False):
            self.display.sound_for_touch(hit)

### CHOIX DE LA PISTE
        if f'{hit}#green' in players[actual_player].targets and players[actual_player].choix and player_launch == 1:
            try :
                while True :
                    players[actual_player].targets.remove(f'S{hit[1:]}#green')
                    players[actual_player].targets.remove(f'D{hit[1:]}#green')
                    players[actual_player].targets.remove(f'T{hit[1:]}#green')

                    print('LA PISTE A ETE SELECTIONNEE')
                    print(players[actual_player].targets_ajouer)

                    players[actual_player].targets_ajouer = f'S{hit[1:]}#green|D{hit[1:]}#green|T{hit[1:]}#green'

                    players[actual_player].choix = False
            except:
                    print('pas trouve le segment - PASS')

                    pass

            ### ON MET 0 AU SCORE CAR C EST LE TIR DU CHOIX DE LA PISTE
            print('score a 0 car fleche1 (choix de la piste)')
            score = 0
            self.fleche1 = 0
            self.display.play_sound('bowling-choix')
            players[actual_player].choix = False

        ### si ne touche pas la cible
        elif players[actual_player].choix == False :
            score = 0
        else:
            score = 0
            self.fleche1 = 0

            self.display.play_sound('bowling-miss')
            self.message = 'Bowling-miss'
            self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')
            self.next = 1

# ~ ### PHASE CHIIFRRE A JOUER
        if players[actual_player].ajouer != 0 and not players[actual_player].choix :
### TOUCHE LE SEGMENT CHOISI
                if f'{hit}#green' in players[actual_player].targets_ajouer :

                        print('')
                        print('postdart')
                        print('player.strike')
                        print (players[actual_player].strike)
                        print('player_launch')
                        print(player_launch)
                        print('')
### FLECHE 2
                        if player_launch == 2 :
                                print('')
                                print ('FLECHE 2')
                                print('')

                                if (hit[:1]) == 'S' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche2 = self.simple  ##4
                                        print('')
                                        print('score fleche 2')
                                        print(self.fleche2)
                                        print('')
                                        self.display.play_sound('bowling-4quilles')
                                        #players[actual_player].double = 0

                                elif (hit[:1]) == 'D' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche2 = self.double  ##7
                                        print('')
                                        print('score fleche 2')
                                        print(self.fleche2)
                                        print('')
                                        self.display.play_sound('bowling-7quilles')
                                        #players[actual_player].double = 0

                                elif (hit[:1]) == 'T' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        ###
                                        if players[actual_player].spare :
                                                self.fleche2 = 10 * 2
                                                ### passe strike en true
                                                players[actual_player].poststrike = True
                                                players[actual_player].spare = False
                                                print('')
                                                print('score fleche 2')
                                                print(self.fleche2)
                                                print('')
                                                self.display.play_sound('bowling-strike')
                                                self.dmd.send_text("STRIKE", sens=None, iteration=None)
                                        else:
                                                self.fleche2 = 10
                                                ### passe strike en true
                                                players[actual_player].poststrike = True
                                                players[actual_player].spare = False
                                                print('')
                                                print('score fleche 2')
                                                print(self.fleche2)
                                                print('')
                                                self.display.play_sound('bowling-strike')
                                                self.dmd.send_text("STRIKE", sens=None, iteration=None)

                                        #players[actual_player].double += 1
                                        #print(' ligne 395 - bonus double +1 (car triple voir si pas doublon avec playerlaunch 2 = 10')
                                        #print (players[actual_player].double)

#### FLECHE 3
                        if player_launch == 3 :
                                print('')
                                print ('FLECHE 3')
                                print('')

                                if (hit[:1]) == 'S' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche3 = self.simple ###4
                                        print('')
                                        print('score fleche 3')
                                        print(self.fleche3)
                                        print('')
                                        self.display.play_sound('bowling-4quilles')
                                        #players[actual_player].double = 0

                                elif (hit[:1]) == 'D' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche3 = self.double ###7
                                        print('')
                                        print('score fleche 3')
                                        print(self.fleche3)
                                        print('')
                                        self.display.play_sound('bowling-7quilles')
                                        #players[actual_player].double = 0

                                elif (hit[:1]) == 'T' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche3 = 10
                                        print('')
                                        print('score fleche 3')
                                        print(self.fleche3)
                                        print('')
                                        self.display.play_sound('bowling-spare')
                                        self.dmd.send_text("SPARE", sens=None, iteration=None)
                                        #players[actual_player].double += 1

### CALCUL DU SCORE
                        if player_launch == 1 :
                                score_temporaire = 0

                        if player_launch == 2 :
                                if not players[actual_player].spare and not players[actual_player].strike :
                                        score_temporaire = self.fleche2

                                elif players[actual_player].spare and not players[actual_player].strike :
                                        score_temporaire = (self.fleche2 * 2)

                                elif players[actual_player].strike and not players[actual_player].spare :
                                        score_temporaire = (self.fleche2 * 2)
                                ### si on ne touche pas
                                else:
                                        score_temporaire = 0

                        if player_launch == 3 :
                                if not players[actual_player].spare and not players[actual_player].strike :
                                        score_temporaire = self.fleche3
                                        print('playerlaunch = 3 et player_strike = false')
                                        if (self.fleche2 + self.fleche3) > 10 :
                                                ttt = 10 - self.fleche2
                                                score_temporaire = ttt
                                                self.fleche3 = ttt
                                                print('fleche 3 = ttt soit 6 pour le test')

                                elif players[actual_player].spare and not players[actual_player].strike :
                                        score_temporaire = self.fleche3
                                        print('playerlaunch = 3 et player_spare = true - strike = false')
                                        if (self.fleche2 + self.fleche3) > 10 :
                                                ttt = 10 - self.fleche2
                                                score_temporaire = ttt
                                                self.fleche3 = ttt
                                                #if players[actual_player].double == 2 :
                                                #        self.message = 'Bowling-double-strike'
                                                #        self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')

                                        if self.fleche2 == 10 and self.fleche3 == 10 :
                                                score_temporaire = self.fleche3 * 2
                                                #if players[actual_player].double == 2 :
                                                #        self.message = 'Bowling-double-strike'
                                                #        self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')

                                elif players[actual_player].strike and not players[actual_player].spare :
                                        print('playerlaunch = 3 et player_strike = true')
                                        score_temporaire = (self.fleche3 * 2)
                                        if (self.fleche2 + self.fleche3) > 10 and (self.fleche2 + self.fleche3) < 20:
                                                ttt = 10 - self.fleche2
                                                score_temporaire = ttt * 2
                                                self.fleche3 = ttt
                                                #if players[actual_player].double == 2 :
                                                #        self.message = 'Bowling-double-strike'
                                                #        self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')

                                ### si on touche pas
                                else:
                                        print('print pas de points en fleche 3 car pas condition ')
                                        score_temporaire = 0

                          ### test sur bonus
                        if player_launch == 4 and players[actual_player].bonus :
                                print('')
                                print ('FLECHE 4')
                                print('')
                                if (hit[:1]) == 'S' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche4 = self.simple ###* 2 ###4 * 2
                                        print('')
                                        print('score fleche 4')
                                        print(self.fleche4)
                                        print('')
                                        self.display.play_sound('bowling-4quilles')
                                        score_temporaire = self.fleche4 * 2
                                        players[actual_player].bonus = False
                                        players[actual_player].strike = False
                                        players[actual_player].spare = False

                                elif (hit[:1]) == 'D' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche4 = self.double ###* 2  ###7 * 2
                                        print('')
                                        print('score fleche 4')
                                        print(self.fleche4)
                                        print('')
                                        self.display.play_sound('bowling-7quilles')
                                        score_temporaire = self.fleche4 * 2
                                        players[actual_player].bonus = False
                                        players[actual_player].strike = False
                                        players[actual_player].spare = False

                                elif (hit[:1]) == 'T' in players[actual_player].targets_ajouer and not players[actual_player].choix:
                                        self.fleche4 = 10 ###* 2
                                        print('')
                                        print('score fleche 4')
                                        print(self.fleche4)
                                        print('')
                                        self.display.play_sound('bowling-spare')
                                        score_temporaire = self.fleche4 * 2
                                        players[actual_player].bonus = False
                                        players[actual_player].strike = False
                                        players[actual_player].spare = False

                        else:

                                self.next = 1

### TEST SUR AJOUT BONUS STRIKE CONS
                        if players[actual_player].double >= 2 :
                                #if players[actual_player].double == 2 :
                                #        self.message = 'Bowling-double-strike'
                                #        self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')
                                #elif players[actual_player].double == 3 :
                                #        self.message = 'Bowling-triple-strike'
                                #        self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')
                                score = score_temporaire ###+ self.bonus
                                print ('a enlever la condition')

                        else:
                                score = score_temporaire

                        ### pour determiner si on passe au joueur suivant
                        self.next = 0

                #### SI NE TOUCHE PAS LE SEGMENT
                else:
                        print('')
                        print('score = 0 car pas touche ce qu on demander - else')
                        print ('segment touche - ELSE')
                        print (hit+'#green')
                        ### si on rate, on remet player.double = 0
                        players[actual_player].double = 0
                        score = 0


                #### test sur round 10
                if actual_round == self.max_round :
                    if self.fleche2 + self.fleche3 == 20:
                        print('4 fleches double strike')
                        self.nb_darts = 4
                        players[actual_player].bonus = True
                    elif self.fleche2 + self.fleche3 == 10:
                        print('4 fleches spare')
                        self.nb_darts = 4
                        players[actual_player].bonus = True
                    else:
                        print('3 fleches')
                        self.nb_darts = 3
                        players[actual_player].bonus = False

        ### pour determiner si on passe au joueur suivant selon ce qu on a touche
        return_code = self.next

        ###  supprimer pour retirer le bug 4 fleches (ne sert pas apparemment)
        '''
        if player_launch == 1 and not players[actual_player].choix:
            players[actual_player].add_dart(actual_round, player_launch, hit[1::], hit_value=0)
        elif score == 0:
            players[actual_player].add_dart(actual_round, player_launch, '', hit_value=0)
        elif players[actual_player].spare:
            players[actual_player].add_dart(actual_round, player_launch, '/', hit_value=0)
        elif players[actual_player].strike:
            players[actual_player].add_dart(actual_round, player_launch, 'X', hit_value=0)
        '''

        if player_launch == 1 :
            if hit[1:] == 'B':
                players[actual_player].columns[0] = (hit[1:], 'txt')
                return 1
            else:
                players[actual_player].columns[0] = (hit[1:], 'int')

### determine si spare ouu strike ou rien
        if player_launch == 2 :
            if self.fleche2 == 10 :
                players[actual_player].double += 1

        if player_launch == 3 :
            if self.fleche2 + self.fleche3 == 10 :
                players[actual_player].spare = True
                self.dmd.send_text("SPARE", sens=None, iteration=None)

        if player_launch == 3 :
            if self.fleche2 + self.fleche3 == 20 and not players[actual_player].spare :
                players[actual_player].poststrike = True
                self.dmd.send_text("STRIKE", sens=None, iteration=None)
                players[actual_player].double += 1

        if player_launch == 3 :
            if self.fleche2 + self.fleche3 < 10 :
                players[actual_player].spare = False
                players[actual_player].poststrike = False
                players[actual_player].double = 0

        if players[actual_player].strike and not players[actual_player].bonus and player_launch == 3 :
                if players[actual_player].double == 2 or players[actual_player].double == 3 :

                        if actual_round != self.max_round:
                                self.bonus = 10
                        elif actual_round == self.max_round:
                                self.bonus = 10
                        else:
                                self.bonus = 0

                        if players[actual_player].double == 0 :
                                self.message = 'A effacer double= 0'
                                self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        if players[actual_player].double == 2 :
                                self.message = 'Bowling-double-strike'
                                if self.bonus == 10 :
                                        self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        if players[actual_player].double == 3 :
                                self.message = 'Bowling-triple-strike'
                                if self.bonus == 10 :
                                        self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus


                        print('ligne 580 - bonus double =')
                        print(players[actual_player].double)
                        if players[actual_player].double > 3 :
                                players[actual_player].double = 0

                players[actual_player].score += score
                players[actual_player].round_points += score
                players[actual_player].points += score
                players[actual_player].strike = False

        ### test round 10
        elif players[actual_player].strike and players[actual_player].bonus and player_launch == 3 :
                if players[actual_player].double == 2 or players[actual_player].double == 3 :

                        if actual_round != self.max_round:
                                self.bonus = 10
                        elif actual_round == self.max_round:
                                self.bonus = 10
                        else:
                                self.bonus = 0

                        if players[actual_player].double == 0 :
                                self.message = 'A effacer double= 0'
                                self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        if players[actual_player].double == 2 :
                                self.message = 'Bowling-double-strike'
                                if self.bonus == 10 :
                                        self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        if players[actual_player].double == 3 :
                                self.message = 'Bowling-triple-strike'
                                if self.bonus == 10 :
                                        self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        print('ligne 592 - bonus double =')
                        print(players[actual_player].double)
                        if players[actual_player].double > 3 :
                            players[actual_player].double = 0
                players[actual_player].score += score
                players[actual_player].round_points += score
                players[actual_player].points += score


        else:
                if players[actual_player].double == 2 or players[actual_player].double == 3 :

                        if actual_round != self.max_round and player_launch > 1:
                            self.bonus = 10
                        elif actual_round == self.max_round :
                            self.bonus = 10
                        else:
                            self.bonus = 0

                        if players[actual_player].double == 0 :
                                self.message = 'A effacer double= 0'
                                self.display.message([self.display.lang.translate(self.message)], 500, None, 'middle', 'big')
                                score += self.bonus

                        if players[actual_player].double == 2 :
                                self.message = 'Bowling-double-strike'
                                if self.bonus == 10 :
                                        self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        if players[actual_player].double == 3 :
                                self.message = 'Bowling-triple-strike'
                                if self.bonus == 10 :
                                        self.display.message([self.display.lang.translate(self.message)], 1000, None, 'middle', 'big')
                                score += self.bonus

                        print('ligne 604 - bonus double =')
                        print(players[actual_player].double)
                        if players[actual_player].double > 3 :
                                players[actual_player].double = 0

                players[actual_player].score += score
                players[actual_player].round_points += score
                players[actual_player].points += score

        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Calculate average and display in column 7

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

## AFFICHE STRIKE OU SPARE OU RIEN
        if players[actual_player].spare:
            players[actual_player].columns[5] = ['bowling_spare', 'image']
            players[actual_player].columns[6] = ['bowling_nostrike', 'image']

        elif players[actual_player].strike:
            players[actual_player].columns[6] = ['bowling_strike', 'image']
            players[actual_player].columns[5] = ['bowling_nospare', 'image']
            players[actual_player].spare = False
        else:
            players[actual_player].columns[6] = ['bowling_nostrike', 'image']
            players[actual_player].columns[5] = ['bowling_nospare', 'image']

        if players[actual_player].poststrike:
            players[actual_player].columns[6] = ['bowling_strike', 'image']
            players[actual_player].columns[5] = ['bowling_nospare', 'image']
            #passe ou non au joueur suivant selon si on est au 10eme tour
            if actual_round == self.max_round:
                self.next = 0
            else:
                self.next = 1

        #### TEST A EFFACER
        print('')
        print('fleche2')
        print(self.fleche2)
        print('fleche3')
        print(self.fleche3)
        print('calcul de fleche 2 + fleche3 avant affichage image ')
        a = self.fleche2 + self.fleche3
        print(a)
        print('')
        ### test pour voir contenu de self.double
        print ('players[actual_player].double - post dart')
        print(players[actual_player].double)
        print('tour en cours')
        print(actual_round)

        # Affiche ce qui a ete touche avec la fleche2 dans la colonne 2
        if self.fleche2 >= 1 and self.fleche2 <= 9:
                players[actual_player].columns[1] = [f'bowling/bowling-{self.fleche2}', 'image']

        elif self.fleche2 == 10 :
                players[actual_player].columns[1] = ['bowling/bowling-strike', 'image']
                players[actual_player].columns[6] = ['bowling_strike', 'image']

        elif self.fleche2 == 0 :
                players[actual_player].columns[1] = ['bowling/bowling-0', 'image']
                self.display.play_sound('bowling-miss')

        # Affiche ce qui a ete touche avec la fleche3 dans la colonne 3
        if self.fleche3 >= 1 and self.fleche3 <= 9:
                players[actual_player].columns[2] = [f'bowling/bowling-{self.fleche3}', 'image']

        if self.fleche3 == 10:
            if actual_round == self.max_round: ###and not players[actual_player].bonus and not players[actual_player].strike :
                players[actual_player].columns[2] = ['bowling/bowling-strike', 'image']
            else:
                players[actual_player].columns[2] = ['bowling/bowling-spare', 'image']

        if self.fleche2 + self.fleche3 == 10:
            if self.fleche3 != 0 :
                players[actual_player].columns[2] = ['bowling/bowling-spare', 'image']
            else:
                players[actual_player].columns[2] = ['', 'txt']

        if self.fleche3 == 0:
            if self.fleche2 == 10:
                players[actual_player].columns[1] = ['bowling/bowling-strike', 'image']
            elif self.fleche2 == 20:
                players[actual_player].columns[1] = ['bowling/bowling-strike', 'image']
                players[actual_player].columns[2] = ['', 'txt']
            else:
                players[actual_player].columns[2] = ['bowling/bowling-0', 'image']
                self.display.play_sound('bowling-miss')

        if players[actual_player].spare :
                players[actual_player].columns[2] = ['bowling/bowling-spare', 'image']

        ###  test bonus - tour 10
        # Affiche ce qui a ete touche avec la fleche2 dans la colonne 4
        if self.fleche4 >= 1 and self.fleche4 <= 9:
                players[actual_player].columns[3] = [f'bowling/bowling-{self.fleche4}', 'image']

        if self.fleche4 == 10 :
                print('ligne 750')
                players[actual_player].columns[3] = ['bowling/bowling-strike', 'image']

        if self.fleche4 == 0 and actual_round == self.max_round and player_launch > 3 :
                players[actual_player].columns[3] = ['bowling/bowling-0', 'image']
                self.display.play_sound('bowling-miss')

        elif self.fleche4 == 0 and actual_round != self.max_round and player_launch != 4 :
                players[actual_player].columns[3] = ['', 'txt']

### pour determiner si on passe au joueur suivant selon ce qu on a touche
        return_code = self.next

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
        ### a faire
        #print('early - player_launch = ')
        #print(player_launch)
        print('early - self.fleche_jouee = ')
        print(self.fleche_jouee)

        if self.fleche_jouee in (0, 1):
            players[actual_player].columns[1] = ['bowling/bowling-0', 'image']
        if self.fleche_jouee in (0, 1, 2):
            players[actual_player].columns[2] = ['bowling/bowling-0', 'image']
            self.display.play_sound('Bowling-miss')

        self.display.message([self.display.lang.translate('Bowling-miss')], 1000, None, 'middle', 'big')
        return 1

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """

        if actual_round >= self.max_round and actual_player == len(players) - 1:
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
