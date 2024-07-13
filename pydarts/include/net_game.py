#!/usr/bin/env python
"""
Class ... ofr online games
"""

class NetGame():
    """
    Class ... ofr online games
    """
    def __init__(self, game_name):
        self.game_name = game_name
        self.members_id = []

        # Store the choosed game
        self.choosed_game = None

        # Store the Game Options Dict
        self.choosed_options = {} # Deprecated
        self.options = {}
        self.nb_darts = None # Total darts each player is allowed to throw in this game

        # RandomValues will be a key/value array with a unique combination of
        # Round/Player/Launch as key
        self.random_values = {} # New list of max x round

        # HitValues will be a key/value array with a unique combination of
        # Round/Player/Launch as key
        self.hit_values = {} #

        # Store all the players names
        self.players_names = []

        # Players properties
        self.player = []

        # Is game ready to launch
        self.launch = False

        # Is game aborted by Master Player
        self.aborted = False
