# -*- coding: utf-8 -*-
# Game by ... David !
########
import subprocess
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############
OPTIONS = {'theme': 'default', 'max_round': 20, 'master': False, 'reverse': False}
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Segment Per Round': 'ASC', 'Nb turns to win': 'DESC'}
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3  # Total darts the player has to play
# background image - relative to images folder - Name it like the game itself
LOGO = 'Pursuit.png'
# Columns headers - Better as a string
HEADERS = ['D1', 'D2', 'D3', '', '', '', 'SPR' ] # Columns headers - Must be a string
# couleur des joueurs
Colors = ["green","red","blue","orange"]
# sequences for the race order
ringSequence = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]
ringSequenceCCW = [20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10, 6, 13, 4, 18, 1, 20]
positions = [ # (posX,posY)
    (300,950), #1
    (757,308),
    (1250,449),
    (300,538),
    (1006,978),
    (235,156),
    (1497,117),
    (1696,402),
    (1588,952),
    (447,95), #10
    (1702,593),
    (1288,979),
    (296,336),
    (1749,783),
    (659,143),
    (1723,183),
    (957,483),
    (177,723),
    (1371,252),
    (681,978) #20
    ]


def check_players_allowed(nb_players):
    '''
    Return the player number max for a game.
    '''
    return nb_players <= 4

############
# Extend the basic player
############
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, config):
        super().__init__(ident, config)
        # Extend the basic players property with your own here
        self.color = 'orange'
        self.kart = 'w'
        self.trueScore = 0
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'


############
# Extend the common Game class
############
class Game(cgame.Game):

    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)

        ##############
        # VAR
        ##############
        # Dictionary of options in STRING format.
        # You can use any numeric value or 'True' or 'False', but in string format.
        # Don't put more than 10 options per game or you will experience display issues
        self.options = options
        # Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in descending
        # order)
        self.game_records = GAME_RECORDS
        # How many darts per player and per round ? Yes ! this is a feature :)
        self.nb_darts = NB_DARTS  # Total darts the player has to play
        # background image - relative to images folder - Name it like the game itself
        self.logo = 'pursuit_cw.png'
        # Columns headers - Better as a string
        self.headers = HEADERS
        # self.score_map.update({'SB':50})
        #  Get the maximum round number
        self.max_round = int(options['max_round'])
        # Mode master : have to finish exactly on the concurrent case
        self.master = options['master']
        #set mode reverse when bull hited
        self.reverse = options['reverse']
        # For rpi
        self.rpi = rpi
        #current Schema order
        self.sequence = ringSequence

        self.loosePosition = 0

        # scale of Karts img 231 * 145 for a fullHd res
        self.scaleX = self.display.res['x'] * 231 / 1920
        self.scaleY = self.display.res['y'] * 145 / 1080

    # Actions done before each dart throw - for example, check if the player is allowed to play
    def pre_dart_check(self,players,actual_round,actual_player,player_launch):
        return_code = 0

        # gestion de l'affichage du segment
        self.show_hit = True

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.log("ERROR","Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0
                Player.trueScore = 0

            if not self.intro_done:
                self.display.play_sound('pursuit_intro')
                self.video_player.play_video(self.display.file_class.get_full_filename('pursuit/pursuit_intro', 'videos'))
                self.intro_done = True

            # nombre de départ du premier joueur choisi au hasard
            value = random.randint(1,20)
            step = 10
            if len(players) == 3 :
                step = 7
                self.display.line_height = self.display.line_height * 2 / 3
            elif len(players) > 3:
                step = 5
            else :
                step = 10
            for i, player in enumerate(players):
                player.score = value
                player.color = Colors[i]
                if player.color == 'orange' :
                    player.kart = 'w'
                else :
                    player.kart = player.color[0]
                for j in range(0, step):
                    value = self.sequence[self.sequence.index(value) + 1]

            #change background
            self.display.display_background('pursuit_back')

        # Each new player
        if player_launch == 1:

            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 7):
                players[actual_player].columns.append(['', 'str'])

        if players[actual_player].score > 0:
            # Display stats
            if actual_round == 1 and player_launch == 1:
                #players[actual_player].columns[5] = (0.0,'int')
                players[actual_player].columns[6] = (0.0, 'int')
            else:
                #players[actual_player].columns[5] = (players[actual_player].show_ppd(),'int')
                players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')

            # Clean next boxes
            for index in range(player_launch - 1, self.nb_darts):
                players[actual_player].columns[index] = ('', 'str')

            # Display target color of player
            segments = {}
            for player in players :
                if player.score>0 :
                    segments[f'S{player.score}'] = str(player.color)
                    segments[f'D{player.score}'] = str(player.color)
                    segments[f'T{player.score}'] = str(player.color)
                    #segments['T'+str(self.sequence[self.sequence.index(p.score)+1])]=str(p.color)

            segmentsAsStr = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
            self.rpi.set_target_leds(segmentsAsStr)
        else:
            # this player is game over
            return_code  = 4

        # Print debug output
        self.logs.log("DEBUG",self.infos)
        return return_code

    ###############
    # Function run after each dart throw - for example, add points to player
    def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        return_code = 0

        self.display.sound_for_touch(hit) # Touched !

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)

        # stock the segment hitted
        players[actual_player].columns[player_launch-1] = (hit[1:],'int')

        # test DB to change orientation
        if hit[1:] == 'B' :
            if self.reverse=='True' :
                self.show_hit = False
                self.display.play_sound('pursuit_reverse')
                if self.sequence == ringSequenceCCW:
                    self.sequence=ringSequence
                    self.logo = 'pursuit_cw.png'
                    self.video_player.play_video(self.display.file_class.get_full_filename('pursuit/pursuit_cw', 'videos'))
                else:
                    self.sequence=ringSequenceCCW
                    self.logo = 'pursuit_ccw.png'
                    self.video_player.play_video(self.display.file_class.get_full_filename('pursuit/pursuit_ccw', 'videos'))
                # Change segment to hit for keep Kart position on the track (for all players)
                for p in players:
                    if p.score>0:
                        p.score = self.sequence[self.sequence.index(p.score)+1]
                        p.score = self.sequence[self.sequence.index(p.score)+1]
        else :
            # increment segment if the player hit his segment (score)
            segment=int(hit[1:])
            if players[actual_player].score == segment:
                self.show_hit = False
                # forward to the next segment to hit !
                segmentPass = [self.sequence[self.sequence.index(segment)+1]]
                players[actual_player].score = self.sequence[self.sequence.index(segment)+1]
                if hit[:1] == 'D' or hit[:1] == 'T'  :
                    players[actual_player].score = self.sequence[self.sequence.index(players[actual_player].score)+1]
                    segmentPass.append(players[actual_player].score)
                if hit[:1] == 'T'  :
                    players[actual_player].score = self.sequence[self.sequence.index(players[actual_player].score)+1]
                    segmentPass.append(players[actual_player].score)

                # for the stat 'Nb segment hitted per round'
                players[actual_player].points += 1

                # Refresh stats
                players[actual_player].columns[6] = (players[actual_player].avg(actual_round),'int')
                self.refresh_stats(players,actual_round)

                # check if a player pass an opponent
                forward=True
                for i,p in enumerate(players):
                    if i!= actual_player and p.score in segmentPass :
                        killed = False
                        if self.master == 'True' :
                            if p.score == segmentPass[0] and hit[:1] == 'S' :
                                killed = True
                            elif len(segmentPass)>1 and p.score == segmentPass[1] and hit[:1] == 'D' :
                                killed = True
                            elif len(segmentPass)>2 and p.score == segmentPass[2] and hit[:1] == 'T' :
                                killed = True
                        else :
                            killed = True

                        if killed:
                            self.display.play_sound('pursuit_pass')
                            self.video_player.play_video(self.display.file_class.get_full_filename('pursuit/pursuit_pass', 'videos'))
                            forward=False
                            p.score=0 # game over for this player
                            p.trueScore = self.loosePosition
                            self.loosePosition +=1

                # play video for forward
                if forward:
                    self.display.play_sound('pursuit_forward')
                    self.video_player.play_video(self.display.file_class.get_full_filename('pursuit/pursuit_move', 'videos'))

                # Check for end of game (no more rounds to play or only on player is in game)
                NbPlayerInGame=0
                for i,p in enumerate(players):
                    if p.score>0:
                        NbPlayerInGame+=1

                if player_launch == self.nb_darts and actual_round >= self.max_round and actual_player == len(players)-1:
                    for player in players:
                        if player.trueScore <=0 :
                            player.trueScore = self.loosePosition
                        player.score = player.trueScore

                    return_code = 2
                elif NbPlayerInGame==1:
                    players[actual_player].trueScore = self.loosePosition
                    for player in players:
                        player.score = player.trueScore
                    self.winner =  players[actual_player].ident
                    return_code = 3
                    self.display.play_sound('pursuit_win')
                    self.video_player.play_video(self.display.file_class.get_full_filename('pursuit/pursuit_win', 'videos'))

        return return_code

    def early_player_button(self,players,actual_player,actual_round):
        # Jump to next player by default
        return_code=1

        # darts_thrown for missing target
        players[actual_player].darts_thrown += (self.nb_darts - self.nb_dartsHitInTurn)

        # Refresh stats
        players[actual_player].columns[6] = (players[actual_player].avg(actual_round), 'int')
        self.refresh_stats(players,actual_round)

        if actual_round >= self.max_round and actual_player == self.nb_players - 1:
            return_code = 2

        return return_code


    ###############
    # Set if a message is shown to indicate the segment hitted !
    #
    def display_segment(self):
       return self.show_hit

    ###############
    # Method to refresh player.stat - Adapt to the stats you want.
    # They represent mathematical formulas used to calculate stats. Refreshed after every launch
    ###############
    def refresh_stats(self, players, actual_round):
        for player in players:
            player.stats['Segment Per Round'] = player.avg(actual_round)
            player.stats['Nb turns to win'] = actual_round

    ###############
    # Refresh In-game screen
    #
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        ClickZones={}

        # Clear
        self.display.screen.fill((0,0,0))
        # background image
        self.display.display_background('pursuit_back')

        # Game Logo
        self.display_logo(logo)

        # Show players Karts
        for p in Players :
            if p.score>0 :
                if self.sequence == ringSequence :
                    segment = ringSequenceCCW[ringSequenceCCW.index(p.score)+1]
                else :
                    segment = ringSequence[ringSequence.index(p.score)+1]
                self.logs.log("DEBUG",'segment show {} for score {}'.format(segment,p.score))
                pos=positions[segment-1] # position sur la case d'avant pour faciliter le visuel
                x=pos[0]*self.display.res['x']/1920-self.scaleX/2
                y=pos[1]*self.display.res['y']/1080-self.scaleY/2
                self.display.display_image(self.display.file_class.get_full_filename(f'pursuit_k{p.kart}_{self.get_direction(segment)}', 'images'),x, y, self.scaleX, self.scaleY, True)

        #sho< players names
        self.display_player_name(self.display,self.display.res['x']/2-self.display.pn_size, self.display.res['y']/2+self.display.line_height/2, actual_player, Players[0])
        if len(Players)>1 :
            self.display_player_name(self.display,self.display.res['x']/2, self.display.res['y']/2+self.display.line_height/2, actual_player, Players[1])
        if len(Players)>2 :
            self.display_player_name(self.display,self.display.res['x']/2-self.display.pn_size, self.display.res['y']/2+self.display.line_height*3/2, actual_player, Players[2])
        if len(Players)>3 :
            self.display_player_name(self.display,self.display.res['x']/2, self.display.res['y']/2+self.display.line_height*3/2, actual_player, Players[3])

        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
            return ClickZones

        self.display.update_screen()

        self.logs.log("DEBUG", f"ClickZones={ClickZones}")
        self.logs.log("DEBUG", f"end_of_game={end_of_game}")

        return [ClickZones]

    ################
    # define the direction of kart by the orientation and position of this
    #
    def get_direction(self,segment) :
        direction = 'l'
        if self.sequence == ringSequence :
            if segment in [18,4,13,6,10,15,2,17,3,19,7,16] :
                direction = 'r' # right orientation of the Kart
        else :
            if segment in [18,1,20,5,12,9,14,13,4] :
                direction = 'r' # right orientation of the Kart
        return direction

    # Display name of the player if given, Player X otherwise
    #
    def display_player_name(self, display, pos_x, pos_y, actual_player, player):
        playername = player.name
        if playername is None:
            playername = f'Player {player.ident}'

        if player.color == 'orange':
            txtcolor = (255, 255, 0) #orange
        elif player.color == 'blue':
            txtcolor = (0, 0, 255) #blue
        elif player.color == 'red':
            txtcolor = (255, 0, 0) # red
        else:
            txtcolor = (0, 255, 0) # green
        #  Player name size depends of player name number of char (dynamic size)
        scaled = self.display.scale_text(playername, self.display.pn_size - 2 * self.display.margin, self.display.line_height)
        font = self.display.get_font(scaled[0])

        #display rect
        background_color = (150,150,150,100)
        if player.ident == actual_player :
            background_color = (245, 245, 245)
        self.display.blit_rect(pos_x, pos_y, self.display.pn_size - self.display.margin, self.display.line_height - self.display.margin, background_color)

        # Render the text. "True" means anti-aliased text.
        playername_x = pos_x + self.display.margin * 2 + scaled[1]
        playername_y = pos_y + scaled[2]
        text = font.render(playername, True, txtcolor)
        self.display.screen.blit(text, [playername_x, playername_y])

    #
    # Display an image on the middle top of the screen
    #
    def display_logo(self, logoimage=False):
        # Local Constants

        pos_x = self.display.res['x'] / 2 + self.display.pn_size
        pos_y = self.display.res['y'] / 2 + self.display.line_height / 2
        width = self.display.box_width * (int(self.display.config.get_value('SectionGlobals', 'nbcol')) + 1) - self.display.margin
        height = self.display.box_height - self.display.line_height - self.display.top_space - self.display.margin
        # Display LOGO
        self.display.display_image(self.display.file_class.get_full_filename(logoimage, 'images'), pos_x, pos_y, width, height, False, False)
