"""
Player class
"""
import operator

class Player:
    """
    Standard player class
    """
    def __init__(self, ident, nb_columns, interior=False):
        self.ident = ident
        self.nb_columns = nb_columns
        self.color = None
        self.position = None
        self.interior = interior    # Manage interioir and exterior simple segments

        # Init value of each column for this player
        self.columns = []
        for _ in range(0, self.nb_columns + 1):
            self.columns.append(('', 'txt', None))
        # Init Player name
        self.name = f"Player {self.ident + 1}"
        # Stats table
        self.stats = {}

        # Still in game
        self.alive = True
        self.lives = 0
        # Number of sets win
        self.sets = 0

        ############################
        #### Player Computer
        ############################
        # Fake player
        self.computer = False
        # Level of computer player
        self.level = 0

        ############################
        #### Player Properties (Please use them)
        ############################
        # For sudden death's mode
        # 1st dead => last position, ...
        self.position = None
        # Team number
        self.team = 1 + (self.ident % 2)
        # Score is the value displayed in the last column. "Current"
        self.score = 0
        # points is the total count of point accumulated by the player,
        # even if it is not equal to score
        self.points = 0
        # Count how many valid hits the player reached for the whoel game
        self.hits = 0
        # Count how many valid hits the player reached in this round
        self.roundhits = 0
        # Count the points accumulated in current round
        self.round_points = 0
        # Count total of dart thrown. In some games it could differents from max_round*3.
        self.darts_thrown = 0
        # Touches of the round
        self.darts = []
        # All touched
        self.all_darts = {}

        for key in ['MISS','SB','DB'] + \
                [f"{mult}{num}" for mult in ('S', 'D', 'T') for num in range(1,21)]:
            # Nb touche, pct
            self.all_darts[key] = [0, 0, 0, 0]
        if self.interior:
            for key in [f's{num}' for num in range(1,21)]:
                self.all_darts[key] = [0, 0, 0, 0]

    def print(self):
        """
        Print player's informations
        """
        return f"{self.ident}/{self.name}/{self.hits}/{self.darts_thrown}/{self.score}"

    def reset(self):
        """
        Reset previous game data
        """
        self.score = 0
        self.points = 0
        self.hits = 0
        self.roundhits = 0
        self.round_points = 0
        self.darts_thrown = 0
        self.darts = []
        self.stats = {}
        self.alive = True
        self.lives = 0
        self.sets = 0
        self.columns = []
        for _ in range(0, self.nb_columns + 1):
            self.columns.append(('', 'txt', None))

        self.all_darts = {}
        for hit in ['MISS', 'SB', 'DB'] + \
                [f"{mult}{num}" for mult in ('S','D','T') for num in range(1,21)]:
            self.all_darts[hit] = [0, 0, 0, 0]
        if self.interior:
            for key in [f's{num}' for num in range(1,21)]:
                self.all_darts[key] = [0, 0, 0, 0]

    def new_set(self):
        """
        Reset data for new set
        """
        self.score = 0
        self.points = 0
        self.darts_thrown = 0
        self.alive = True
        self.lives = 0
        self.columns = []
        for _ in range(0, self.nb_columns + 1):
            self.columns.append(('', 'txt', None))

    def add_histo(self, hit):
        """
        Add dart to history
        """
        if hit in self.all_darts:
            self.all_darts[hit][0] += 1

    def get_stat_position(self, stats, hit):
        """
        Get statitic's position
        """
        i = 0
        flag = False
        for stat in stats:
            if stats[stat][0] == stats[hit][0] and i == 0:
                return i
            if stats[stat][0] == stats[hit][0]:
                flag = True
            elif flag:
                return i
            i += 1
        return None

    def get_histo(self):
        """
        Get history
        """
        total1 = 0
        total2 = 0
        total3 = 0
        simple = 0
        double = 0
        triple = 0
        missed = 0

        # Compute totals
        # total1 : Number of darts throwed
        # total2 : Number of segments hit
        # total3 : Number of differents segments hit
        old = 0
        for hit, values in self.all_darts.items():
            if values[0] > 0:
                total1 += values[0]
                total2 += 1
            if values[1] != old:
                total3 +=1
                old = values[1]

        for hit in self.all_darts:
            # Percent of hits
            self.all_darts[hit][1] = int(self.all_darts[hit][0] / total1 * 100)
            # Percent of target hits
            self.all_darts[hit][2] = int(1 / total2 * 100)

        sorted_stats = dict(sorted(self.all_darts.items(), key=operator.itemgetter(1), \
                reverse=True))

        for hit in self.all_darts:
            pos = self.get_stat_position(sorted_stats, hit)
            sorted_stats[hit][3] = pos
            if hit[:1] in ('s', 'S') and sorted_stats[hit][0] > 0:
                simple += sorted_stats[hit][0]
            elif hit[:1] == 'D' and sorted_stats[hit][0] > 0:
                double += sorted_stats[hit][0]
            elif hit[:1] == 'T' and sorted_stats[hit][0] > 0:
                triple += sorted_stats[hit][0]
            elif hit[:1] == 'M' and sorted_stats[hit][0] > 0:
                missed += sorted_stats[hit][0]

        percent_simple = int(100 * simple / (simple + double + triple + missed))
        percent_double = int(100 * double / (simple + double + triple + missed))
        percent_triple = int(100 * triple / (simple + double + triple + missed))
        percent_missed = int(100 * missed / (simple + double + triple + missed))

        return (sorted_stats, total2, (simple, percent_simple), (double, percent_double), \
                (triple, percent_triple), (missed, percent_missed), total3)

    def add_dart(self, actual_round, launch, hit, score=None, check=None, final_check=None, hit_value=None):
        """
        Add dart to the round
        """
        self.darts[launch - 1] = hit
        self.rounds[actual_round - 1][launch - 1] = hit
        if score is not None:
            self.scores[actual_round - 1][launch - 1] = hit
            self.scores[actual_round - 1][3] += score
        if check is not None:
            self.checks[actual_round - 1][launch - 1] = check
        if final_check is not None:
            self.checks[actual_round - 1][3] = final_check
        if hit_value is None:
            self.increment_hits(hit)
        else:
            self.increment_hits(hit_value)

    def reset_rounds(self, nb_rounds):
        """
        Initialize self.rounds : All darts of the game
        """

        # Dart1, Dart2, Dart3 : S12/S5/D6
        self.rounds = [[None, None, None] for _ in range(nb_rounds)]
        # Dart1, Dart2, Dart3, round score : 12/10/12/34
        self.scores = [[None, None, None, 0] for _ in range(nb_rounds)]
        # Dart1, Dart2, Dart3 : check/check/check/final check
        self.checks = [[None, None, None, None] for _ in range(nb_rounds)]

    def reset_darts(self):
        """
        Reset darts of round
        """
        self.darts = [None, None, None]

    def init_color(self, color):
        """
        Init player's color
        """
        self.color = color

    def get_position(self):
        """
        return position of player's line
        """
        return self.position

    def get_color(self):
        """
        return player's color
        """
        return self.color

    def get_col_value(self, col):
        """
        Return column value
        """
        if self.columns[col][1] == 'int':
            return int(self.columns[col][0])
        return self.columns[col][0]

    def increment_column_touch(self, column, increment=1):
        """
        Increment column touch
        """
        if self.columns[column][1] in ('int', 'leds') :
            data = int(self.columns[column][0]) + increment
            datatype = self.columns[column][1]
            color = self.columns[column][2]
            self.columns[column] = (data, datatype, color)

    def increment_hits(self, hit=1):
        """
        If a touch given, Increment with correponding value, else, add touch value
        """
        if str(hit)[:1] in ('s', 'S'):
            self.hits += 1
        elif str(hit)[:1] == 'D':
            self.hits += 2
        elif str(hit)[:1] == 'T':
            self.hits += 3
        elif hit != 'MISSDART':
            self.hits += hit
        self.darts_thrown += 1

    def increment_column(self, value, column):
        """
        Increment a column value (if int)
        """
        if self.columns[column][1] == 'int':
            color = self.columns[column][2]
            old_value = self.columns[column][0]
            self.columns[column] = (old_value + value, 'int', color)

    def decrement_column(self, value, column):
        """
        Decrement a column value (if int)
        """
        if self.columns[column][1] == 'int':
            color = self.columns[column][2]
            old_value = self.columns[column][0]
            self.columns[column] = (old_value - value, 'int', color)

    def get_touch_type(self, touch):
        """
        Find if a touch is a Simple, Double, Triple
        """
        if touch[:1] in ('s', 'S'):
            value = "Simple "
        elif touch[:1] == 'D':
            value = "Double "
        elif touch[:1] == 'T':
            value = "Triple "

        if touch[1:] == "B":
            return f'{value} Bull'
        return f'{value} {touch[1:]}'

    def get_touch_unit(self, touch):
        """
        Return touch unit (1 for simple, 2 for double, and 3 for triple)
        """
        if touch[:1] in ('s', 'S'):
            return 1
        if touch[:1] == 'D':
            return 2
        if touch[:1] == 'T':
            return 3
        return 0

    def get_total_hit(self):
        """
        Return total number of hits
        """
        return self.hits

    def add_score(self, value):
        """
        Add point to players' score
        """
        self.score += value
        return self.score

    def set_score(self, value):
        """
        Set player's score
        """
        self.score = value
        return self.score

    def get_score(self):
        """
        Return player's score
        """
        return int(self.score)

    def get_previous_id(self, nbplayers):
        """
        Return is of previous player
        """
        if self.ident > 0:
            return self.ident - 1
        return nbplayers - 1

    def show_mpr(self):
        """
        Return MPR ((hits/darts thrown)*3) (sems to be official calculation method)
        Marks per round.
        Simple = 1 / Double = 2 / Triple = 3
        3 * Sum of 3 darts / number of darts
        """
        try:
            mpr = round((float(self.hits) / float(self.darts_thrown)) * 3, 2)
        except: # pylint: disable=bare-except
            mpr = 0.00
        return mpr

    def show_ppd(self):
        """
        Return points per dart
        """
        try:
            ppd = round(float(self.points) / float(self.darts_thrown), 2)
        except: # pylint: disable=bare-except
            ppd = 0.00
        return ppd

    def show_ppr(self):
        """
        Return points per round
        """
        try:
            ppr = round((float(self.points) / self.darts_thrown) * 3, 2)
        except: # pylint: disable=bare-except
            ppr = 0.00
        return ppr

    def avg(self, actual_round):
        """
        Return Average points per round
        """
        return round((float(self.points) / actual_round), 2)

    def score_per_round(self, actual_round):
        """
        return average score per round
        """
        return round(float(self.score) / float(actual_round), 2)

    def hits_per_round(self, actual_round):
        """
        Return average hits per round
        """
        return round(float(self.hits) / float(actual_round), 2)
