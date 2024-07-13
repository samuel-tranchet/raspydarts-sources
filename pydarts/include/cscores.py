
import sqlite3
import os
#

class Scores:
    """
    Scores' class
    """
    def __init__(self, config, logs):
        self.config = config
        self.logs = logs
        self.userpath = os.path.expanduser('~')
        self.pathdir = f'{self.userpath}/.pydarts'
        self.db = f'{self.pathdir}/scores.db'
        self.DBChecks()
        self.game_name = ''
        self.game_options = None
        self.nb_players = None
        self.game_id = ''

    def connect(self):
        """
        Create a database connection to the SQLite database
           specified by the db_file
           :param db_file: database file
           :return: Connection object or None
        """
        try:
            self.cx = sqlite3.connect(self.db)
        except Exception as exception:
            self.logs.log("ERROR", f"{exception}")

    def DBChecks(self):
        """
        Check db
        """
        if not os.path.exists(self.pathdir):
            os.makedirs(self.pathdir)
        # Connect to db
        self.connect()
        # Purge if requested
        if self.config.get_value('SectionAdvanced', 'clear-local-db'):
            self.logs.log("WARNING", f"Squeezing any existing table in {self.db}")
            sql='DROP table scores'
            cur = self.cx.cursor()
            cur.execute(sql)
            sql='DROP table games'
            cur = self.cx.cursor()
            cur.execute(sql)
           # Create structure if needed
        sql = """
              CREATE TABLE IF NOT EXISTS scores
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              game_id INTEGER,
              scorename TEXT,
              score FLOAT,
              playername TEXT)
              """
        cur = self.cx.cursor()
        cur.execute(sql)
        self.cx.commit()


        sql = """
           CREATE TABLE IF NOT EXISTS games
           (  id INTEGER PRIMARY KEY AUTOINCREMENT,
              date DATETIME,
              gamename TEXT,
              gameoptions TEXT,
              nbplayers INT
           )
           """
        cur = self.cx.cursor()
        cur.execute(sql)
        self.cx.commit()

        if self.cx:
            self.cx.close()

    def add_game(self, data):
        """
        Add new game
        """
        self.game_name = data['game_name']
        self.game_options = data['game_options']
        self.nb_players = data['nb_players']
        self.connect()
        # Replaced CURRENT_TIMESTAMP by datetime('now','localtime'),
        sql = f"""
              INSERT INTO games (
              date,
              gamename,
              gameoptions,
              nbplayers)
              VALUES (
              datetime('now','localtime'),
              '{self.game_name}',
              '{self.game_options}',
              {self.nb_players}
              )
              """;

        # Get cursor
        cur = self.cx.cursor()
        # Exsecute query
        cur.execute(sql)
        # Get last inserted id
        game_id = cur.lastrowid
        # Commit changes
        self.cx.commit()
        # Close cx if its still open
        if self.cx:
            self.cx.close()
        self.game_id = game_id
        return game_id

    def add_score(self, data):
        """
        add score
        """
        score_name = data['score_name']
        score = data['score']
        player_name = data['player_name']

        sql = f"""
              INSERT INTO scores (
              game_id,
              scorename,
              score,
              playername)
              VALUES (
              '{self.game_id}',
              '{score_name}',
              '{score}',
              '{player_name}'
              )
              """;

        self.connect()
        # Get cursor
        cur = self.cx.cursor()
        # Exsecute query
        cur.execute(sql)
        # Commit changes
        self.cx.commit()
        # Close cx if its still open
        if self.cx:
            self.cx.close()

    def get_score_table(self, score_name, orderby, current=False):
        """
        return scores' table
        """
        self.connect()
        #
        if current:
            sql_this_game_only = f"AND games.id='{self.game_id}'"
        else:
            sql_this_game_only = ""
        #
        sql = f"""
              SELECT
                 CASE games.id
                    WHEN '{self.game_id}' THEN 1
                    ELSE 0
                 END hiscore,
                 date,
                 playername,
                 score
              FROM scores
              LEFT JOIN games on scores.game_id=games.id
              WHERE gameoptions = '{self.game_options}'
              AND gamename = '{self.game_name}'
              AND scorename = '{score_name}'
              {sql_this_game_only}
              ORDER BY score {orderby}
              LIMIT 12
              """;

        # Get cursor
        cur = self.cx.cursor()
        # Exsecute query
        cur.execute(sql)
        # Get rows
        rows = cur.fetchall()

        return rows
