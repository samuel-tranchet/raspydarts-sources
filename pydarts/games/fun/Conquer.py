# -*- coding: utf-8 -*-
"""
Game by David !
"""
######
import random
import subprocess
import pygame
from copy import deepcopy
from include import cplayer
from include import cgame
# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': 20, 'max_territory': 7}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Conquer.png'  # background image
# Columns headers - Better as a string
HEADERS = ['#', 'PTS']  # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3  # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round': 'DESC'}


def check_players_allowed(nb_players):
    """
    Return the player number max for a game.
    """
    return nb_players <= 4

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

class Game(cgame.Game):
    """
    Conquer class game
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

        # couleurs segment des joueurs
        self.colors = ['green', 'blue', 'red', 'yellow']

        # records is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS

        self.max_round = int(options['max_round'])
        self.max_territory = int(options['max_territory'])

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

        # random hex
        hits = [x for x in range(1, 21)]
        for i in range(0, 20):
            h = random.randint(0, len(hits) - 1)
            # segment, player, strengh
            self.grid.append((str(hits[h]), -1, -1))
            hits.pop(h)

        # add extra hex for bull
        self.grid.append(('B', -1, 0))  # segment, player, strengh

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
            for Player in players:
                # Init score
                Player.score = 0

            # change background
            self.display.specialbg = 'bg_conquer'
            self.display.display_background(image='bg_conquer.jpg')

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

        neighbors = self.find_neighbors(actual_player)
        for segment in neighbors:
            if neighbors[segment] == 1:
                light_segments.append(segment)
            else:
                strobe_segments.append(segment)

        self.rpi.set_target_leds('|'.join(f"{mult}{segment}#{self.colors[actual_player]}" for mult in (
            'S', 'D', 'T') for segment in light_segments))
        self.rpi.set_target_leds_blink('|'.join(f"{mult}{segment}#{self.colors[actual_player]}" for mult in (
            'S', 'D', 'T') for segment in strobe_segments))

        return 0

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        handler = self.init_handler()

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].segments[player_launch-1] = hit

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D':
            multi = 2
        if hit[:1] == 'T':
            multi = 3

        for k, v in enumerate(self.grid):
            if v[0] == hit[1:]:
                if v[1] < 0:  # cas de prise directe
                    self.grid[k] = (v[0], actual_player, multi - 1)
                    handler['sound'] = 'conquer_first'
                elif v[1] != actual_player:
                    niv = v[2] - multi
                    if niv < 0:
                        # capture du territoire
                        self.grid[k] = (v[0], actual_player, -niv - 1)
                        handler['sound'] = 'conquer_fight'
                    else:
                        # reduction des troupes adverses
                        self.grid[k] = (v[0], v[1], niv)
                        handler['sound'] = 'conquer_down'
                else:
                    niv = v[2] + multi
                    if niv > self.maxSrength:
                        niv = self.maxSrength
                    # augmentation des troupes
                    self.grid[k] = (v[0], v[1], niv)
                    handler['sound'] = 'conquer_up'

                self.blink_box(k)
                self.draw_box(k)
                #self.display.update_screen()

                if hit[1:] == 'B':
                    handler['video'] = 'conquer/conquer_bull'

                # test for a winner
                kingdom = self.findLink(actual_player, hit[1:], [hit[1:]], [])
                if self.grid[k][1] == actual_player and len(kingdom[0]) >= self.max_territory:
                    self.winner = players[actual_player].ident

                    kingdoms = [0, 0, 0, 0]
                    for c in self.grid:
                        if c[1] >= 0:
                            # pondération des troupes pour les égalités en nombre de cases
                            kingdoms[c[1]] = kingdoms[c[1]] + 1000 + c[2]

                    for player in players:
                        player.score = kingdoms[player.ident]

                    bestscore = kingdoms[actual_player]
                    bestscoreid = player.ident
                    handler['return_code'] = 3
                else:
                    # end game because end of rounds
                    if actual_round >= self.max_round and actual_player == self.nb_players - 1:
                        kingdoms = [0, 0, 0, 0]
                        for c in self.grid:
                            if c[1] >= 0:
                                # pondération des troupes pour les égalités en nombre de cases
                                kingdoms[c[1]] = kingdoms[c[1]] + 1000 + c[2]

                        bestscore = 0
                        for player in players:
                            player.score = kingdoms[player.ident]
                            if kingdoms[player.ident] > bestscore:
                                bestscore = kingdoms[player.ident]
                                bestscoreid = player.ident
                        self.winner = bestscoreid
                        handler['return_code'] = 3

        return handler

    def find_neighbors(self, actual_player):
        """
        Methode pour trouver les segments voisins des segments du joueur
        """

        player_segments = [
            f'{element[0]}' for element in self.grid if element[1] == actual_player]
        neighbors = {}
        for segment in player_segments:
            case = self.getCaseFromSegment(segment)
            if case == 21:
                cases_voisines = self.link['B']
            else:
                cases_voisines = self.link[f'{case}']
            for neighbor in [self.grid[20 if case == 'B' else int(case) - 1][0] for case in cases_voisines]:
                if self.getCaseFromSegment(neighbor) == 'B':
                    index = 20
                else:
                    index = int(self.getCaseFromSegment(neighbor)) - 1

                if self.grid[index][1] != actual_player and self.grid[index][1] > -1:
                    # Occupied by other
                    neighbors[neighbor] = 3
                elif segment not in neighbors and neighbor in neighbors:
                    # Neighbor of 2 segments
                    neighbors[neighbor] = 2
                elif neighbor not in neighbors:
                    neighbors[neighbor] = 1
        return neighbors

    def findLink(self, actual_player, segment, linkedHex, linkedHexTotal):
        """
        Methode recursive pour trouver les cases connectées
        """
        for k in self.link['B' if segment == 'B' else str(self.getCaseFromSegment(segment))]:
            seg = 'B' if k == 'B' else self.grid[int(k)-1][0]
            if seg not in linkedHex and self.grid[20 if k == 'B' else int(k) - 1][1] == actual_player:
                linkedHex.append(seg)
                linkedHex2 = self.findLink(
                    actual_player, seg, linkedHex, linkedHexTotal)
                for i in linkedHex2[0]:
                    if i not in linkedHex:
                        linkedHex.append(i)
            if seg not in linkedHexTotal:
                # on compte avec les non pris pour les leds des segments adjacente
                linkedHexTotal.append(seg)

        return (linkedHex, linkedHexTotal)

    ###############
    # Methode pour retrouver les segments adjacents aux territoires d'un joueur
    def findPlayerNeighbor(self, player_id):
        maxZone = ([], [])
        allSeg = []
        for k, v in enumerate(self.grid):
            if v[0] not in allSeg and v[1] == player_id:
                zone = self.findLink(player_id, v[0], [v[0]], [])
                if len(zone[0]) > len(maxZone[0]):
                    maxZone = zone
                for seg in zone[0]:  # optimisation pour éviter les boucles
                    if seg not in allSeg:
                        allSeg.append(seg)

        # on determine les voisins en retirant les cases déjà prises
        neighbor = []
        for v in maxZone[1]:
            if v not in maxZone[0]:
                neighbor.append(v)
        return neighbor

    ###############
    # Récupération de la case correspondante au segment
    def getCaseFromSegment(self, segment):
        for k, v in enumerate(self.grid):
            if segment == v[0]:
                return k + 1

    def display_segment(self):
        return False

     ###############
    # Refresh In-game screen
    #
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       # do not show the table scores
        ClickZones = {}

        sx = 43 * self.scale

        # Clear
        self.display.screen.fill((0, 0, 0))
        # background image

        self.display.display_image(self.display.file_class.get_full_filename(
            'conquer/conquer_back.png', 'images'), 0, 0, self.display.res['x'], self.display.res['y'], True, False, False)

        # draw playernames
        yp1 = 180 * self.scale
        stepy = 182 * self.scale
        for player in Players:
            self.display.display_image(self.display.file_class.get_full_filename(
                f'conquer/conquer_j{player.ident + 1}.png', 'images'), sx, yp1+player.ident*stepy, 525 * self.scale, 105 * self.scale, True, False, False)
            self.display.blit_text(player.name, sx, yp1+player.ident*stepy+5 * self.scale, 525 * self.scale,
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
            return ClickZones

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
                f'conquer/conquer_{case + 1}_{i + 1}.png', 'images')
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
                f'conquer/conquer_{case + 1}_{v[1] + 1}.png', 'images'), 0, 0, self.display.res['x'], self.display.res['y'], True, False, False, UseCache=False)

            # draw strength logos
            stepx = 50 * self.scale
            for i in range(0, v[2]):
                self.display.display_image(self.display.file_class.get_full_filename('conquer/conquer_strength.png', 'images'), stepx*i +
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
