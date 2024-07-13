# Handicaps
class Handicap:
    def __init__(self, gamename, config, logs):
        self.Config = config
        self.logs = logs
        self.GameName = gamename
        self.LSThandimarks = []
        self.LSTHandiPoints = []
        self.LSTteammpr = []
        self.maxid = 0

    def findcrickethandicap(self, lstmpr):
        handicol = 0
        # Get team average MPR
        self.LSTteammpr.append(round((float(lstmpr[0]) + float(lstmpr[2])) / 2, 2))
        self.LSTteammpr.append(round((float(lstmpr[1]) + float(lstmpr[3])) / 2, 2))
        self.logs.log("DEBUG", "List mpr: {}, self.LSTteammpr: {}".format(lstmpr, self.LSTteammpr))
        for i in self.LSTteammpr:
            if i <= 1.99:
                handicol += 0.5
            elif 2.0 <= i <= 2.99:
                handicol += 1
            elif i >= 3.0:
                handicol += 1.5
        self.logs.log("DEBUG", "Handicap col: {}".format(handicol))
        # figure out difference in MPR between both teams
        maxval = max(self.LSTteammpr)
        self.maxid = self.LSTteammpr.index(maxval)
        minval = min(self.LSTteammpr)
        diff = maxval - minval
        self.logs.log("DEBUG", "maxval: {}. minval: {}, maxid: {}, diff: {}".format(maxval, minval, self.maxid, diff))
        # Load new marks into a list
        if handicol < 1.5:
            if 0.10 <= diff <= 0.19:
                self.LSThandimarks = [1, 0, 0, 0, 0, 0, 0]
            elif 0.20 <= diff <= 0.29:
                self.LSThandimarks = [1, 0, 0, 0, 0, 0, 1]
            elif 0.30 <= diff <= 0.39:
                self.LSThandimarks = [1, 1, 0, 0, 0, 0, 1]
            elif 0.40 <= diff <= 0.49:
                self.LSThandimarks = [1, 1, 1, 0, 0, 0, 1]
            elif 0.50 <= diff <= 0.59:
                self.LSThandimarks = [1, 1, 1, 1, 0, 0, 1]
            elif 0.60 <= diff <= 0.69:
                self.LSThandimarks = [1, 1, 1, 1, 1, 0, 1]
            elif 0.70 <= diff <= 0.79:
                self.LSThandimarks = [1, 1, 1, 1, 1, 1, 1]
            elif 0.80 <= diff <= 0.89:
                self.LSThandimarks = [2, 1, 1, 1, 1, 1, 1]
            elif 0.90 <= diff <= 0.99:
                self.LSThandimarks = [2, 2, 1, 1, 1, 1, 1]
            elif 1.00 <= diff <= 1.09:
                self.LSThandimarks = [2, 2, 2, 1, 1, 1, 1]
            elif 1.10 <= diff <= 1.19:
                self.LSThandimarks = [2, 2, 2, 2, 1, 1, 1]
            elif 1.20 <= diff <= 1.29:
                self.LSThandimarks = [2, 2, 2, 2, 2, 1, 1]
            elif 1.30 <= diff <= 1.39:
                self.LSThandimarks = [2, 2, 2, 2, 2, 2, 1]
            elif diff >= 1.40:
                self.LSThandimarks = [2, 2, 2, 2, 2, 2, 2]
            else:
                self.LSThandimarks = [0, 0, 0, 0, 0, 0, 0]
        elif 1.5 <= handicol < 3.0:
            if 0.10 <= diff <= 0.29:
                self.LSThandimarks = [1, 0, 0, 0, 0, 0, 0]
            elif 0.30 <= diff <= 0.39:
                self.LSThandimarks = [1, 0, 0, 0, 0, 0, 1]
            elif 0.40 <= diff <= 0.59:
                self.LSThandimarks = [1, 1, 0, 0, 0, 0, 1]
            elif 0.60 <= diff <= 0.69:
                self.LSThandimarks = [1, 1, 1, 0, 0, 0, 1]
            elif 0.70 <= diff <= 0.89:
                self.LSThandimarks = [1, 1, 1, 1, 0, 0, 1]
            elif 0.90 <= diff <= 0.99:
                self.LSThandimarks = [1, 1, 1, 1, 1, 0, 1]
            elif 1.00 <= diff <= 1.19:
                self.LSThandimarks = [1, 1, 1, 1, 1, 1, 1]
            elif 1.20 <= diff <= 1.29:
                self.LSThandimarks = [2, 1, 1, 1, 1, 1, 1]
            elif 1.30 <= diff <= 1.49:
                self.LSThandimarks = [2, 2, 1, 1, 1, 1, 1]
            elif 1.50 <= diff <= 1.59:
                self.LSThandimarks = [2, 2, 2, 1, 1, 1, 1]
            elif 1.60 <= diff <= 1.79:
                self.LSThandimarks = [2, 2, 2, 2, 1, 1, 1]
            elif 1.80 <= diff <= 1.89:
                self.LSThandimarks = [2, 2, 2, 2, 2, 1, 1]
            elif 1.90 <= diff <= 2.09:
                self.LSThandimarks = [2, 2, 2, 2, 2, 2, 1]
            elif diff >= 2.10:
                self.LSThandimarks = [2, 2, 2, 2, 2, 2, 2]
            else:
                self.LSThandimarks = [0, 0, 0, 0, 0, 0, 0]
        elif handicol >= 3.0:
            if 0.20 <= diff <= 0.39:
                self.LSThandimarks = [1, 0, 0, 0, 0, 0, 0]
            elif 0.40 <= diff <= 0.59:
                self.LSThandimarks = [1, 0, 0, 0, 0, 0, 1]
            elif 0.60 <= diff <= 0.79:
                self.LSThandimarks = [1, 1, 0, 0, 0, 0, 1]
            elif 0.80 <= diff <= 0.99:
                self.LSThandimarks = [1, 1, 1, 0, 0, 0, 1]
            elif 1.00 <= diff <= 1.19:
                self.LSThandimarks = [1, 1, 1, 1, 0, 0, 1]
            elif 1.20 <= diff <= 1.39:
                self.LSThandimarks = [1, 1, 1, 1, 1, 0, 1]
            elif 1.40 <= diff <= 1.59:
                self.LSThandimarks = [1, 1, 1, 1, 1, 1, 1]
            elif 1.60 <= diff <= 1.79:
                self.LSThandimarks = [2, 1, 1, 1, 1, 1, 1]
            elif 1.80 <= diff <= 1.99:
                self.LSThandimarks = [2, 2, 1, 1, 1, 1, 1]
            elif 2.00 <= diff <= 2.19:
                self.LSThandimarks = [2, 2, 2, 1, 1, 1, 1]
            elif 2.20 <= diff <= 2.39:
                self.LSThandimarks = [2, 2, 2, 2, 1, 1, 1]
            elif 2.40 <= diff <= 2.59:
                self.LSThandimarks = [2, 2, 2, 2, 2, 1, 1]
            elif 2.60 <= diff <= 2.79:
                self.LSThandimarks = [2, 2, 2, 2, 2, 2, 1]
            elif diff >= 2.80:
                self.LSThandimarks = [2, 2, 2, 2, 2, 2, 2]
            else:
                self.LSThandimarks = [0, 0, 0, 0, 0, 0, 0]
        return self.LSThandimarks

    def returnmaxid(self):
        return self.maxid

    def hoonehandicap(self, lstppd, ogstartscore, players):
        team1avg = (lstppd[0] + lstppd[2]) / 2
        team2avg = (lstppd[1] + lstppd[3]) / 2
        pointsperdart = [team1avg, team2avg]
        # Sets lowest score of starting score (default is .40 which in 301 is 121)
        startpercent = float(self.Config.get_value('SectionGlobals', 'startpercent'))
        # Calculates and stores lowest possible starting score
        minstartscore = int(((int(ogstartscore) - 1) * startpercent) + 1)
        # Stores highest PPD into variable to use for calculations
        maxval = max(pointsperdart)
        # Stores id number of highest PPD
        self.maxid = pointsperdart.index(maxval)
        for idx, val in enumerate(pointsperdart):
            playerstartscore = 0
            if idx != self.maxid:
                if val == 0:
                    # If no PPD or PPD is zero, start with original score
                    self.LSTHandiPoints.append(int(ogstartscore))
                elif val != 0:
                    # Otherwise determine player start score based off of best player's PPD
                    playerstartscore = int(float(ogstartscore) * (float(val) / float(maxval)) + .5)
                    if playerstartscore >= minstartscore:
                        # If playerstartscore is equal to or higher than minimum, use that
                        self.LSTHandiPoints.append(playerstartscore)
                    elif playerstartscore < minstartscore:
                        # Otherwise, start with minimum start score
                        self.LSTHandiPoints.append(minstartscore)
                else:
                    # Something went way wrong
                    self.logs.log("ERROR", "The value for setting the 01 start score is throwing an error!")
            elif idx == self.maxid:
                # If player has the highest PPD, they start at original start score
                self.LSTHandiPoints.append(int(ogstartscore))
                playerstartscore = ogstartscore
            self.logs.log("DEBUG", "Team {} start score: {}, ogstartscore: {}, val: {}, maxval: {}".format(
                idx + 1, playerstartscore, ogstartscore, val, maxval))
        return self.LSTHandiPoints
