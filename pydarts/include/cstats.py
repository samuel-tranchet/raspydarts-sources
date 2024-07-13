
"""
Stats class
"""
import os
import sys
import csv
# Patch for ConfigParser
if sys.version[:1]=='2':
    import ConfigParser as configparser
elif sys.version[:1]=='3':
    import configparser
#
class Stats:
    def __init__(self, game, logs):
        """
        Stats class
        """
        self.logs = logs
        self.userpath = os.path.expanduser('~')
        self.pathdir = f'{self.userpath}/.pydarts'
        self.pathfile = f'{self.pathdir}/playerstats.csv'
        self.player_stats = {}
        #
        self.game = game
        self.check_stats_file()
        self.write_dict()

    def check_stats_file(self):
        """
        Check Stat File existence. Create it if necessary
        """
        # Playerstats.csv
        # 0:CricketMarks,1:CricketThrows,2:CricketMPR,3:01Throws,4:01Points,5:01PPR,6:01PPD
        if not os.path.isfile(self.pathfile):
            self.logs.log("WARNING", f"Stats file {self.pathfile} doesn't exists. Creating...")
        if not os.path.exists(self.pathdir):
            os.makedirs(self.pathdir)
        self.write_csv()

    def write_dict(self):
        """
        write to dict
        """
        with open(self.pathfile,'r') as infile:
            reader = csv.reader(infile)
            for row in reader:
                key = row[0]
                if key in self.player_stats:
                    self.logs.log("WARNING","This name is duplicated in the file! Skipping!")
                pass
                self.player_stats[key] = row[1:]

    def write_csv(self):
        """
        write to csv
        """
        with open(self.pathfile,'w') as f:
            for key, values in self.player_stats.items():
                f.write(str.join(',', [key]+[str(i) for i in values])+'\n')
#
    def mpr(self,player):
        marks = float(self.player_stats[player][0])
        throws = float(self.player_stats[player][1])
        totl = float((marks/throws)*3)
        self.logs.log("DEBUG", f"Marks:{marks}, Throws:{throws} , mpr:{totl}")
        self.player_stats[player][2] = str(round(totl,6))

    def ppd(self,player):
        """
        Points per dart
        """
        throws = int(self.player_stats[player][3])
        totalscore = int(self.player_stats[player][4])
        try:
            totl = float(totalscore/throws)
        except:
            totl = 0
        self.player_stats[player][6] = str(round(totl,2))

    def PPR(self,player):
        """
        Points per round
        """
        throws = int(self.player_stats[player][3])
        totalscore = int(self.player_stats[player][4])
        try:
            totl = float((totalscore/throws)*3)
        except:
            totl = 0
        self.player_stats[player][5] = str(round(totl,2))

    def Increase01Points(self,player,totalscore):
        """
        Increase points
        """
        points = int(self.player_stats[player][4])
        points += totalscore
        self.player_stats[player][4] = str(points)

    def Increase01Throws(self, player, increase):
        """
        Increase throws
        """
        throws = int(self.player_stats[player][3])
        throws += increase
        self.player_stats[player][3] = str(throws)
