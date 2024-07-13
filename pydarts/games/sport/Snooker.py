########## reste a faire
#
# changer la couleur #brun de la bille de couleur 4 par une autre ==> pour l instant c est #orange mais pas terrible


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
OPTIONS = {'theme': 'default', 'max_round': 20, 'rouge': 6, 'table1': True, 'alea': True}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 99  # Total darts the player has to play
LOGO = 'Snooker.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Rnd', 'PPD', 'PPR'] # Columns headers - Must be a string
COLORS = {'2': 'yellow', '3': 'green', '4': 'orange', '5': 'blue', '6': 'purple', '7': 'white'}

def check_players_allowed(nb_players):
   '''
   Return the player number max for a game.
   '''
   return nb_players < 6

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

        self.columns[6] = ['Snooker-rouge', 'image']
        self.character = 0


class Game(cgame.Game):
    """
    snooker game class
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
        self.leds = True
        self.couleur = False
        self.next = 0
        self.rouge = int(options['rouge'])

        self.liste_triee = ['2']

        self.headers[6] = 'CLR'
        self.headers[5] = "--"
        self.options = options
        self.message = 'Snooker-billerouge'
        self.video = 0

        self.alea = options['alea']
        self.table1 = options['table1']
        self.show_segment = False
        self.show_dmd = False

    def penalite(self, players, actual_player):
        self.logs.log('WARNING', 'ajout points aux advs car penalite (couelur) - boucle FOR')
        self.dmd.send_text("PENALITE", sens=None, iteration=None)
        self.display.message([self.display.lang.translate('Snooker-penalite')], 1000, None, 'middle', 'big')
        for player in players:
            if player.ident != actual_player:
                player.score += 4

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0

### INITIALISE LES LEDS (bille) POUR CHAQUE JOUEUR -- player.targets
        if self.leds:
                targets_rouge = []
                rouge = (21 - self.rouge) ##+ 1

                hits = [1, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                for _ in range (0, (21 - rouge)):
                    rouge_alea = random.randint(0, len(hits) - 1)
                    targets_rouge.append(hits[rouge_alea])
                    hits.pop(rouge_alea)

                for player in players:

                        if self.alea:
                                ### SI  ROUGE EST ALEATOIRE
                                hitsS = [f'S{number}#{self.colors[1]}' for number in targets_rouge]
                                hitsD = [f'D{number}#{self.colors[1]}' for number in targets_rouge]
                                hitsT = [f'T{number}#{self.colors[1]}' for number in targets_rouge]

                                Sbull = [f'SB#{self.colors[1]}']
                                Dbull = [f'DB#{self.colors[1]}']

                                couleurs = [f'S2#yellow' , 'S3#green','S4#orange','S5#blue', 'S6#purple','S7#white','D2#yellow' , 'D3#green','D4#orange','D5#blue', 'D6#purple','D7#white','T2#yellow' , 'T3#green','T4#orange','T5#blue', 'T6#purple','T7#white']

                                player.targets = hitsS + hitsD + hitsT + couleurs ##+ Sbull + Dbull

                                player.targets_couleur = couleurs

                                player.targets_rouge = hitsS + hitsD + hitsT ##+ Sbull + Dbull

                        if not self.alea:
                                ### SI ROUGE N EST PAS ALEATOIRE
                                hitsS = [f'S{number}#{self.colors[1]}' for number in range((rouge),21)]
                                hitsD = [f'D{number}#{self.colors[1]}' for number in range((rouge),21)]
                                hitsT = [f'T{number}#{self.colors[1]}' for number in range((rouge),21)]

                                couleurs = [f'S2#yellow' , 'S3#green','S4#orange','S5#blue', 'S6#purple','S7#white','D2#yellow' , 'D3#green','D4#orange','D5#blue', 'D6#purple','D7#white','T2#yellow' , 'T3#green','T4#orange','T5#blue', 'T6#purple','T7#white']

                                Sbull = [f'SB#{self.colors[1]}']
                                Dbull = [f'DB#{self.colors[1]}']

                                player.targets = hitsS + hitsD + hitsT + couleurs ##+ Sbull + Dbull

                                player.targets_couleur = couleurs

                                player.targets_rouge = hitsS + hitsD + hitsT ##+ Sbull + Dbull

                        ### INITIALISE LES VARIABLE UTILISEE SI ON JOUE SUR 1 TABLE (table1 = True)
                        self.TTT = player.targets
                        self.TTT_rouge = player.targets_rouge
                        self.TTT_couleur = player.targets_couleur

                        self.leds = False

        if player_launch == 1:
            players[actual_player].reset_darts()
            #### Utilise 1 table pour tout le monde (table1 = true)
            if self.table1:
                players[actual_player].targets = self.TTT
                players[actual_player].targets_rouge = self.TTT_rouge
                players[actual_player].targets_couleur = self.TTT_couleur

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
### DECLARATION DES VARIABLE PHASE ET COULEUR POUR CHAQUE JOUEUR
                player.phase = 1
                player.couleur = False
                player.allcouleur = False
                player.test = False

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

            ### ACTIVE LA PHASE 2 (qd il n y a plus de bille rouge a jouer)
            if players[actual_player].phase == 1 and len(players[actual_player].targets) == 18:
                    players[actual_player].phase = 2

            ### AFFICHE LA BONNE BILLE A JOUER
            if players[actual_player].phase == 1:
                    if not players[actual_player].couleur:
                            self.message = 'Snooker-billerouge'
                            players[actual_player].columns[6] = ['Snooker-rouge', 'image']
                    else:
                            self.message = 'Snooker-couleur'
                            players[actual_player].columns[6] = ['Snooker-couleur', 'image']

            ### ACTIVE ALLCOULEUR (qd il faut jouer la plus petite bille de couleur)
            if len(players[actual_player].targets) <= 18:
                    print('predart - force allcouleur et couleur a true')
                    players[actual_player].allcouleur = True
                    players[actual_player].couleur = True

                    ### TEST POUR QUE TOUT LES JOUEUR AIE COULEUR COMMUNE
                    if self.table1:
                        for player in players:
                            player.couleur = True

                    print(players[actual_player].allcouleur)
                    print(players[actual_player].couleur)
                    print ('la liste targets contient ==')
                    print(players[actual_player].targets)

            if players[actual_player].phase == 2:
                if not players[actual_player].allcouleur:
                    self.message = 'Snooker-couleur'
                    players[actual_player].columns[6] = ['Snooker-couleur', 'image']
                else:
                     if len(players[actual_player].targets) == 18 and players[actual_player].allcouleur:
                         players[actual_player].columns[6] = ['Snooker-jaune', 'image']
                         self.message = 'Snooker-jaune'
                     if len(players[actual_player].targets) == 15 and players[actual_player].allcouleur:
                         players[actual_player].columns[6] = ['Snooker-vert', 'image']
                         self.message = 'Snooker-vert'
                     if len(players[actual_player].targets) == 12 and players[actual_player].allcouleur:
                         players[actual_player].columns[6] = ['Snooker-brun', 'image']
                         self.message = 'Snooker-brun'
                     if len(players[actual_player].targets) == 9 and players[actual_player].allcouleur:
                         players[actual_player].columns[6] = ['Snooker-bleu', 'image']
                         self.message = 'Snooker-bleu'
                     if len(players[actual_player].targets) == 6 and players[actual_player].allcouleur:
                         players[actual_player].columns[6] = ['Snooker-rose', 'image']
                         self.message = 'Snooker-rose'
                     if len(players[actual_player].targets) == 3 and players[actual_player].allcouleur:
                         players[actual_player].columns[6] = ['Snooker-noir', 'image']
                         self.message = 'Snooker-noir'

        ### ACTIVE LA PHASE 2
        if players[actual_player].test:
            players[actual_player].phase = 2
            players[actual_player].couleur = True
            players[actual_player].allcouleur = True
            ### TEST POUR QUE TOUT LES JOUEUR AIE COULEUR COMMUNE
            if self.table1:
                for player in players:
                    player.phase = 2
                    player.couleur = True
                    player.allcouleur = True

            players[actual_player].columns[6] = ['Snooker-jaune', 'image']
            self.message = 'Snooker-jaune'
            players[actual_player].test = False

        ### CHECK SI PHASE 1 ou PHASE 2    ---  TESTER SANS CAR CA FAIT DOUBLON
        if len(players[actual_player].targets) == 18 and not players[actual_player].couleur:
            players[actual_player].phase = 2

        ### GESTION DES LEDS SELON CE QU ON DOIT JOUER
        if players[actual_player].couleur and not players[actual_player].allcouleur:
            ### couleur active, fait clignoter les leds couleurs
            self.rpi.set_target_leds ('')
            self.rpi.set_target_leds('|'.join(players[actual_player].targets_rouge))
            self.rpi.set_target_leds_blink ('')
            self.rpi.set_target_leds_blink('|'.join(players[actual_player].targets_couleur))
            self.dmd.send_text("BILLE DE COULEUR", sens=None, iteration=None)

        elif not players[actual_player].couleur:
            ### rouge active, fait clignoter les leds rouge
            self.rpi.set_target_leds ('')
            self.rpi.set_target_leds('|'.join(players[actual_player].targets_couleur))
            self.rpi.set_target_leds_blink ('')
            self.rpi.set_target_leds_blink('|'.join(players[actual_player].targets_rouge))
            self.dmd.send_text("BILLE ROUGE", sens=None, iteration=None)

        elif players[actual_player].couleur and players[actual_player].allcouleur:
                if self.message == 'Snooker-jaune':
                    self.rpi.set_target_leds ('')
                    leds = f'S3#green|D3#green|T3#green|S4#orange|D4#orange|T4#orange|S5#blue|D5#blue|T5#blue|S6#purple|D6#purple|T6#purple|S7#white|D7#white|T7#white'
                    self.rpi.set_target_leds(leds)
                    ### PLUS DE ROUGE, fait clignoter la plus petite bille de couleur (jaune)
                    self.rpi.set_target_leds_blink ('')
                    self.rpi.set_target_leds_blink('S2#yellow|D2#yellow|T2#yellow|SB#red|DB#red')
                    self.dmd.send_text("BILLE JAUNE", sens=None, iteration=None)

                elif self.message == 'Snooker-vert':
                    self.rpi.set_target_leds ('')
                    leds = f'S4#orange|D4#orange|T4#orange|S5#blue|D5#blue|T5#blue|S6#purple|D6#purple|T6#purple|S7#white|D7#white|T7#white'
                    self.rpi.set_target_leds(leds)
                    ### PLUS DE ROUGE, fait clignoter la plus petite bille de couleur (verte)
                    self.rpi.set_target_leds_blink ('')
                    self.rpi.set_target_leds_blink('S3#green|D3#green|T3#green|SB#red|DB#red')
                    self.dmd.send_text("BILLE VERTE", sens=None, iteration=None)

                elif self.message == 'Snooker-brun':
                    self.rpi.set_target_leds ('')
                    leds = f'S5#blue|D5#blue|T5#blue|S6#purple|D6#purple|T6#purple|S7#white|D7#white|T7#white'
                    self.rpi.set_target_leds(leds)
                    ### PLUS DE ROUGE, fait clignoter la plus petite bille de couleur (brune)
                    self.rpi.set_target_leds_blink ('')
                    self.rpi.set_target_leds_blink('S4#orange|D4#orange|T4#orange|SB#red|DB#red')
                    self.dmd.send_text("BILLE BRUNE", sens=None, iteration=None)

                elif self.message == 'Snooker-bleu':
                    self.rpi.set_target_leds ('')
                    leds = f'S6#purple|D6#purple|T6#purple|S7#white|D7#white|T7#white'
                    self.rpi.set_target_leds(leds)
                    ### PLUS DE ROUGE, fait clignoter la plus petite bille de couleur (bleue)
                    self.rpi.set_target_leds_blink ('')
                    self.rpi.set_target_leds_blink('S5#blue|D5#blue|T5#blue|SB#red|DB#red')
                    self.dmd.send_text("BILLE BLEUE", sens=None, iteration=None)

                elif self.message == 'Snooker-rose':
                    self.rpi.set_target_leds ('')
                    leds = f'S7#white|D7#white|T7#white'
                    self.rpi.set_target_leds(leds)
                    ### PLUS DE ROUGE, fait clignoter la plus petite bille de couleur (rose)
                    self.rpi.set_target_leds_blink ('')
                    self.rpi.set_target_leds_blink('S6#purple|D6#purple|T6#purple|SB#red|DB#red')
                    self.dmd.send_text("BILLE ROSE", sens=None, iteration=None)

                elif self.message == 'Snooker-noir':
                    self.rpi.set_target_leds ('')
                    ### PLUS DE ROUGE, fait clignoter la plus petite bille de couleur (noire)
                    self.rpi.set_target_leds_blink ('')
                    self.rpi.set_target_leds_blink('S7#white|D7#white|T7#white|SB#red|DB#red')
                    self.dmd.send_text("BILLE NOIRE", sens=None, iteration=None)

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

        ### retire le bandeau de ce qu on a touche
        self.show_segment = False

        # Play DMD animation
### PHASE 1 (joue bille rouge et couleur)
        if players[actual_player].phase == 1:
                if players[actual_player].couleur == False:
                        ### TOUCHE UNE BILLE ROUGE
                        if f'{hit}#red' in players[actual_player].targets:
                            try:
                                while True:
                                    players[actual_player].targets.remove('S'+hit[1:]+'#red')
                                    players[actual_player].targets_rouge.remove('S'+hit[1:]+'#red')
                                    players[actual_player].targets.remove('D'+hit[1:]+'#red')
                                    players[actual_player].targets_rouge.remove('D'+hit[1:]+'#red')
                                    players[actual_player].targets.remove('T'+hit[1:]+'#red')
                                    players[actual_player].targets_rouge.remove('T'+hit[1:]+'#red')
                            except:
                                pass

                            self.TTT = players[actual_player].targets
                            self.TTT_rouge = players[actual_player].targets_rouge

                            ### active la couleur
                            self.couleur = True
                            ### ajoute le score
                            score = 1
                            ### pour determiner si on passe au joueur suivant
                            self.next = 0

                            #joue video bille rouge
                            self.video_player.play_video(self.display.file_class.get_full_filename('snooker/rouge', 'videos'))

                        elif (hit+'#yellow') in players[actual_player].targets or (hit+'#green') in players[actual_player].targets or (hit+'#orange') in players[actual_player].targets or (hit+'#blue') in players[actual_player].targets or (hit+'#purple') in players[actual_player].targets or (hit+'#white') in players[actual_player].targets:

                            score = 0
                            self.penalite(players, actual_player)
                        else:
                            ### NE TOUCHE PAS UNE BILLE ROUGE
                            print('dans else touche pas de bille rouge et couleur')
                            self.penalite(players, actual_player)

                            ### ajoute le score
                            score = 0

                            ### desactive la couleur
                            self.couleur = False
                            self.message = 'Snooker-billerouge'

                            ### pour determiner si on passe au joueur suivant
                            self.next = 1

                if players[actual_player].couleur == True:
                        ### TOUCHE UNE BILLE DE COULEUR
                        if (hit+'#yellow') in players[actual_player].targets or (hit+'#green') in players[actual_player].targets or (hit+'#orange') in players[actual_player].targets or (hit+'#blue') in players[actual_player].targets or (hit+'#purple') in players[actual_player].targets or (hit+'#white') in players[actual_player].targets:

                                score = int(hit[1:])

                                ### desactive/active la couleur
                                if len(players[actual_player].targets) == 18:
                                        self.couleur = True
                                else:
                                        self.couleur = False

                                ### pour determiner si on passe au joueur suivant
                                self.next = 0

                                ### pour activer le ALLCOULEUR apres avoir touche une couleur apres la derniere rouge
                                if players[actual_player].phase == 1 and len(players[actual_player].targets) == 18:
                                        players[actual_player].test = True
                                else:
                                        players[actual_player].test = False

                                #player_launch -= 1
                                #joue video bille couleur
                                if int(hit[1:]) == 2:
                                    self.video_player.play_video(self.display.file_class.get_full_filename('snooker/couleur/jaune', 'videos'))
                                elif int(hit[1:]) == 3:
                                    self.video_player.play_video(self.display.file_class.get_full_filename('snooker/couleur/vert', 'videos'))
                                elif int(hit[1:]) == 4:
                                    self.video_player.play_video(self.display.file_class.get_full_filename('snooker/couleur/marron', 'videos'))
                                elif int(hit[1:]) == 5:
                                    self.video_player.play_video(self.display.file_class.get_full_filename('snooker/couleur/bleu', 'videos'))
                                elif int(hit[1:]) == 6:
                                    self.video_player.play_video(self.display.file_class.get_full_filename('snooker/couleur/rose', 'videos'))
                                elif int(hit[1:]) == 7:
                                    self.video_player.play_video(self.display.file_class.get_full_filename('snooker/couleur/noir', 'videos'))

                        else:
                            ### NE TOUCHE PAS UNE BILLE DE COULEUR
                            self.penalite(players, actual_player)

                            ### ajoute le score
                            score = 0

                            ### desactive la couleur
                            self.couleur = False
                            print(self.couleur)

                            self.message = 'Snooker-billerouge'

                            ### pour determiner si on passe au joueur suivant
                            self.next = 1

                ### active ou non la couleur selon ce qu on a touche
                players[actual_player].couleur = self.couleur

### PHASE 2 (plus de bille rouge)
        if players[actual_player].phase == 2:
                players[actual_player].couleur = True

                ### TEST POUR QUE TOUT LES JOUEUR AIE COULEUR COMMUNE
                if self.table1:
                    for player in players:
                        player.couleur = True

                ### creation d une nouvelle liste sans les 'S-D-T et les couleurs #green, #yellow, ....
                nouvelle_liste = []
                for val in players[actual_player].targets:
                        indexdiese = val.find('#')
                        nouvelle_liste.append(val[1:indexdiese])

                ### retire les doublons de la liste
                liste_doublon = list(set(nouvelle_liste))
                print('')

                ### trie la liste du plus petit au plus grand
                liste_triee = sorted(liste_doublon)

                ### test pour recuperer la liste pour les leds
                self.liste_triee = liste_triee

                players[actual_player].allcouleur = True

                ### affiche la bonne bille a jouer
                if players[actual_player].phase == 2:
                    if not players[actual_player].allcouleur:
                        self.message = 'Snooker-couleur'
                        players[actual_player].columns[6] = ['Snooker-couleur', 'image']
                    else:
                         if len(players[actual_player].targets) == 18 and players[actual_player].allcouleur:
                             players[actual_player].columns[6] = ['Snooker-jaune', 'image']
                             self.message = 'Snooker-jaune'
                         if len(players[actual_player].targets) == 15 and players[actual_player].allcouleur:
                             players[actual_player].columns[6] = ['Snooker-vert', 'image']
                             self.message = 'Snooker-vert'
                         if len(players[actual_player].targets) == 12 and players[actual_player].allcouleur:
                             players[actual_player].columns[6] = ['Snooker-brun', 'image']
                             self.message = 'Snooker-brun'
                         if len(players[actual_player].targets) == 9 and players[actual_player].allcouleur:
                             players[actual_player].columns[6] = ['Snooker-bleu', 'image']
                             self.message = 'Snooker-bleu'
                         if len(players[actual_player].targets) == 6 and players[actual_player].allcouleur:
                             players[actual_player].columns[6] = ['Snooker-rose', 'image']
                             self.message = 'Snooker-rose'
                         if len(players[actual_player].targets) == 3 and players[actual_player].allcouleur:
                             players[actual_player].columns[6] = ['Snooker-noir', 'image']
                             self.message = 'Snooker-noir'

                ### TOUCHE LA PLUS PETITE BILLE DE COULEUR
                if hit[1:2] == liste_triee[0]:
                    color = COLORS[liste_triee[0]]
                    score = int(liste_triee[0])
                    self.video = score
                    
                    try:
                        while True:
                            players[actual_player].targets.remove(f'S{hit[1:]}#{color}')
                            players[actual_player].targets.remove(f'D{hit[1:]}#{color}')
                            players[actual_player].targets.remove(f'T{hit[1:]}#{color}')

                            ### test pour supprimer les leds couleur clignotante
                            players[actual_player].targets_couleur.remove(f'S{hit[1:]}#{color}')
                            players[actual_player].targets_couleur.remove(f'D{hit[1:]}#{color}')
                            players[actual_player].targets_couleur.remove(f'T{hit[1:]}#{color}')
                    except:
                        pass
                    self.TTT = players[actual_player].targets
                    self.TTT_couleur = players[actual_player].targets_couleur

                    ### active la couleur
                    self.couleur = True

                    ### pour determiner si on passe au joueur suivant
                    self.next = 0

                    ### joue la video
                    if self.video == 2:
                        self.video_player.play_video(self.display.file_class.get_full_filename('snooker/jaune', 'videos'))
                    elif self.video == 3:
                        self.video_player.play_video(self.display.file_class.get_full_filename('snooker/vert', 'videos'))
                    elif self.video == 4:
                        self.video_player.play_video(self.display.file_class.get_full_filename('snooker/marron', 'videos'))
                    elif self.video == 5:
                        self.video_player.play_video(self.display.file_class.get_full_filename('snooker/bleu', 'videos'))
                    elif self.video == 6:
                        self.video_player.play_video(self.display.file_class.get_full_filename('snooker/rose', 'videos'))
                    elif self.video == 7:
                        self.video_player.play_video(self.display.file_class.get_full_filename('snooker/noir', 'videos'))

                    self.video = 0

                elif hit in ('SB', 'DB'):
                    self.message = 'Snooker-break'
                    self.display.message([self.display.lang.translate('Snooker-break')], 1000, None, 'middle', 'big')
                    print('BREAK - ajout points aux advs car SB ou DB TOUCHE -  boucle FOR')
                    self.dmd.send_text("BREAK", sens=None, iteration=None)
                    score = 4

                else:
                    ### NE TOUCHE PAS LA BILLE DE COULEUR LA PLUS PETITE
                    score = 0
                    self.penalite(players, actual_player)
                    self.next = 1

                ### AFFICHE LA BONNE BILLE
                if players[actual_player].phase == 2:
                    if not players[actual_player].allcouleur:
                        self.message = 'Snooker-couleur'
                        players[actual_player].columns[6] = ['Snooker-couleur', 'image']
                    else:
                        if len(players[actual_player].targets) == 18 and players[actual_player].allcouleur:
                            players[actual_player].columns[6] = ['Snooker-jaune', 'image']
                            self.message = 'Snooker-jaune'
                        if len(players[actual_player].targets) == 15 and players[actual_player].allcouleur:
                            players[actual_player].columns[6] = ['Snooker-vert', 'image']
                            self.message = 'Snooker-vert'
                        if len(players[actual_player].targets) == 12 and players[actual_player].allcouleur:
                            players[actual_player].columns[6] = ['Snooker-brun', 'image']
                            self.message = 'Snooker-brun'
                        if len(players[actual_player].targets) == 9 and players[actual_player].allcouleur:
                            players[actual_player].columns[6] = ['Snooker-bleu', 'image']
                            self.message = 'Snooker-bleu'
                        if len(players[actual_player].targets) == 6 and players[actual_player].allcouleur:
                            players[actual_player].columns[6] = ['Snooker-rose', 'image']
                            self.message = 'Snooker-rose'
                        if len(players[actual_player].targets) == 3 and players[actual_player].allcouleur:
                            players[actual_player].columns[6] = ['Snooker-noir', 'image']
                            self.message = 'Snooker-noir'

                players[actual_player].couleur = self.couleur

        ### pour determiner si on passe au joueur suivant selon ce qu on a touche
        return_code = self.next

        ### AFFICHE SI ON DOIT JOUER UNE ROUGE OU UNE COULEUR DANS LA COLONNE 6  --- A VOIR SI IL FAUT MODIFIER OU SUPPRIMER
        if players[actual_player].couleur and not players[actual_player].allcouleur:
            players[actual_player].columns[6] = ['Snooker-couleur', 'image']
            self.message = 'Snooker-couleur'
        elif players[actual_player].allcouleur:
            print('')
            #self.message = 'Snooker-toute couleur'
            players[actual_player].couleur = True
            ### TEST POUR QUE TOUT LES JOUEUR AIE COULEUR COMMUNE
            if self.table1:
                for player in players:
                    player.couleur = True
                    player.allcouleur = True

        else:
            self.message = 'Snooker-billerouge'
            players[actual_player].columns[6] = ['Snooker-rouge', 'image']

        #players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score

        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if (self.next == 1 or player_launch == self.nb_darts) and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner >= 0:
                self.winner = winner
                return_code = 3
            else:
                # No winner : last round reached
                return_code = 2

        ### GAGNE SI JOUEUR N A PLUS DE CIBLE A TOUCHER --- NE MARCHE PAS SI J1 A TERMINER ET PAS J2 --- 'mettre or avec condition'
        if len(players[actual_player].targets) == 0:
            winner = self.best_score(players)
            if winner >= 0:
                self.winner = winner
                return_code = 3
            else:
                # No winner : last round reached
                return_code = 2

        return return_code

    def early_player_button(self, players, actual_player, actual_round):
        #SI LE JOUEUR N A PAS NETTOYE LA TABLE ALORS PENALITE SI APPUI SUR NEXTPLAYER
        #if (len(players[actual_player].targets)) != 0:
        self.penalite(players, actual_player)

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2

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
