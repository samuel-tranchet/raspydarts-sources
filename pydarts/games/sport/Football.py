# -*- coding: utf-8 -*-
"""
Game by ... @Poilou !
"""

from include import cplayer
from include import cgame

LOGO = 'Football.png'
HEADERS = ['1', '2', '3', 'Drib', '', '', 'Ball']
OPTIONS = {'theme': 'default', 'max_round': 100, 'master': False, 'goals': 3, 'defense': False}
NB_DARTS = 3
GAME_RECORDS = {'Score Per Round': 'DESC', 'Dribbles': 'DESC'}

def check_players_allowed(nb_players):
    """
    Only 2 players
    """
    return nb_players == 2

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Read the CJoueur class parameters, and add here yours if needed
        self.ball = False # Does the player has got the ball ?
        self.dribbles = 0 # How many time the players get the ball
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record]='0'

class Game(cgame.Game):
    """
    Football game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # GameRecords is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS
        # Import game settings
        self.logo = LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS
        self.options = options
        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        self.master = options['master']
        self.defense = options['defense']
        self.goals = int(options['goals'])
        # For rpi
        self.rpi = rpi

        self.winner = None
        self.infos = ''
        self.translate = self.display.lang.translate
        self.show_hit = True

    def pre_dart_check(self,  players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """

        self.show_hit = True
        return_code = 0
        # infos Can be used to create a per-player debug output
        self.infos += f"###### Player {actual_player} ######{self.lf}"
        # You will probably save the turn to be used in case of backup turn (each first launch) :
        if player_launch == 1:
            self.display.play_sound('whistle')
            self.video_player.play_video(self.display.file_class.get_full_filename('football/arbitre', 'videos'))
            # Clean actual_players' columns
            i = 0
            for column in players[actual_player].columns:
                players[actual_player].columns[i] = ['', 'txt']
                i += 1
        # Draw the balloon if a player has got the ball
        for player in players:
            if player.ball:
                self.infos += f"Player {player.name} has got the ball !{self.lf}"
                player.columns[6] = ['balloon','image']
            player.columns[3] = [player.dribbles, 'int']
        # Backuping scores
        self.save_turn(players)
        # Send debug output to log system. Use DEBUG or WARNING or ERROR or FATAL
        self.logs.log("DEBUG",self.infos)

        if players[actual_player].ball :
            doubles = [f'D{number}#{self.colors[0]}' for number in range(1,21)]
            triples = [f'T{number}#{self.colors[0]}' for number in range(1,21)]
            self.rpi.set_target_leds('|'.join(doubles + triples))
        elif self.master:
            self.rpi.set_target_leds(f'DB#{self.colors[0]}'.format(self.colors[0]))
        else :
            self.rpi.set_target_leds(f'SB#{self.colors[0]}|DB#{self.colors[0]}')

        return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """

        return_code = 0
        if ((hit[1:] == 'B' and not self.master) or (hit == 'DB' and self.master)) \
                and not players[actual_player].ball:
            self.video_player.play_video(self.display.file_class.get_full_filename('football/defense', 'videos'))
            # Remove balloon to other players
            for player in players:
                player.ball = False
                player.columns[6] = ['', 'txt']
            # Give the ballon to actual player (drible)
            self.infos += f"Player {players[actual_player].name} get the ball !{self.lf}"
            self.display.play_sound('youllneverwalkalone')
            players[actual_player].ball = True
            players[actual_player].dribbles += 1
            players[actual_player].columns[6] = ['balloon', 'image']
            players[actual_player].columns[3] = [players[actual_player].dribbles, 'int']
            
        # Else if the balloon holder score
        elif players[actual_player].ball and (hit[:1]== 'D' or hit[:1]== 'T'):
            self.show_hit = False
            scored = True
            if self.defense:
                self.dmd.send_text("Défense")
                opponent = players[(actual_player + 1) % len(players)].name

                self.display.message([
                    f"{opponent} : {self.translate('Football-defend')}",
                    f"{self.translate('Football-def2')} {hit} {self.translate('Football-def3')}"
                    ], 2000, None, 'middle', 'big')

                self.rpi.event.publish('blink', f"{hit}#{self.colors[0]}")

                # Opponent has to stop attack
                dart_stroke = self.rpi.listen_inputs([],
                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISSDART',
                      'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'single-click', 'escape', 'space', 'special'],
                      context='game')

                self.infos += f'{opponent} stroke {hit}{self.lf}'
                if dart_stroke == hit:
                    if not self.video_player.play_video(self.display.file_class.get_full_filename('football/gardien', 'videos')):
                        self.display.message([f"{self.translate('Football-stopped')}"], 2000, None, 'middle', 'big')
                        
                        
                    self.infos += f"Player {opponent} stopped the goal !"
                    scored = False
                    self.display.play_sound('football/supporters')
                    players[actual_player].ball = False
                    players[actual_player].columns[6] = ['', 'image']
                    players[(actual_player + 1) % len(players)].ball = True

            if scored:
                self.dmd.send_text("Goal", sens='flip')

                if not self.video_player.play_video(self.display.file_class.get_full_filename('football/goal', 'videos')):
                    self.display.play_sound('goal')
                    self.display.message([f"Gooooooaaaaaaaal !!!"], 2000, None, 'middle', 'big')
                self.infos += f"Player {players[actual_player].name} scored !"
                players[actual_player].score += 1

        # Display hit history
        players[actual_player].columns[player_launch - 1] = [hit, 'txt']

        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # If the actual player wins
        if int(players[actual_player].score) == self.goals:
            self.winner = players[actual_player].ident
            self.video_player.play_video(self.display.file_class.get_full_filename('football/victory', 'videos'))
            return_code = 3
        # Return code to main
        return return_code

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Score Per Round'] = player.score_per_round(actual_round)
            player.stats['Dribbles'] = player.dribbles

    def display_segment(self):
        """
        Display or not the hit segment
        """
        return self.show_hit

