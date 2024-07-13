# -*- coding: utf-8 -*-
#!/usr/bin/env python
#########################
# Sys requirements check
#########################
#from config import *

import sys
import json
from threading import Thread # New threading module. Compatible python 2 and 3. Object oriented. Replace the deprecated _thread module

import socket
from include import CNetGames
import select
import time
import signal
from copy import deepcopy
import random # Randomize player names

class CServer():
    def __init__(self, config, logs):
        self.Games = [] # Init Local Games array
        self.MsgQueue = [] # Queue of Message Dict
        self.colorlist = [color for color in range(31,39)] # First color will be red, and then green, yellow, blue, rose, cyan, grey, and back to first color.
        self.Config = config
        Self.logs=logs
        self.delim='|'
        self.send_timeout = 10 # Time after what a client is considered as disconnected

    def Listen(self,NetIp,NetPort):
        self.TCP_IP = NetIp
        self.TCP_PORT = NetPort
        self.BUFFER_SIZE = 256  # Usually 1024, but we want fast response - unit is char in this case
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(20) # Max number of clients
        #self.s.setblocking(1)


#
# Main loop (listen for client and create a thread for each client)
#
    def __main__(self):
        i=0 # Black shell color
        self.color = {}

        while True:
            conn, addr = self.s.accept()
            userid="{}-{}".format(addr[0],addr[1])
            Self.logs.log("WARNING","{} client joined server on port {}.".format(addr[0],addr[1]))
            self.color[userid] = self.colorlist[i]
            #print self.color
            #-_thread version_-thread.start_new_thread(self.client_thread,(conn,addr)) #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            T={}
            T[i] = Thread(target=self.client_thread, args=(conn,addr))
            T[i].daemon = True # Permit CTRL-C
            T[i].start() # Start Thread
            i+=1
            if i==8:
                i=0

#
# Client thread (one per client) - started from main
#
    def client_thread(self, conn, addr):
        userid="{}-{}".format(addr[0],addr[1])
        i=0
        gamename=""
        #infinite loop so that function do not terminate and thread do not end.
        while True:
            """
            data=""
            ready = select.select([conn], [], [], 0)
            if ready:
               try:
                  #conn.settimeout(timeout) # Set timeout
                  #time.sleep(0.2) # To avoid getting all the cpu. Tried 0.1, now passed to 0.2 to slow down again
                  #data = conn.recv(self.BUFFER_SIZE) # Buffer_size stands for bytes of data to be received
                  #data=str(data.decode('UTF-8'))
                  conn.settimeout(None) # Reset timeout
               except:
                  Self.logs.log("FATAL","Bad data received or timeout ({}) has been reached for connection with {}. Aborting.".format(timeout,userid))
                  sys.exit(2)
               if data=="":
                  Self.logs.log("DEBUG","Closing connection or bad data received with {}. Aborting.".format(userid))
                  sys.exit(3)
            """
            # Receive data
            data=self.rcv(conn,userid)
            # Print data for debug
            Self.logs.log("DEBUG","\033[{}mReceived from client {} : {}\033[0m".format(self.color[userid],userid,data))
            # Interpretation of the client message
            self.CheckMessage2(conn,data,addr)

#
# Receive Data and be sure that end of message has been reached
#
    def rcv(self,conn,userid,delim='|'):
        buf = ''
        data=""
        timeout = 3600
        ready = select.select([conn], [], [], 0)
        if ready:
            try:
                while True:
                    time.sleep(0.2) # Avoid consuming all cpu. Was 0.1, now I prefer 0.2 to reduce cpu again
                    data = conn.recv(self.BUFFER_SIZE)
                    buf += data.decode('utf-8') # Convert received bytes to unicode
                    found = buf.find(delim)
                    if found != -1:
                        msg = buf.split(delim, 1)
                        #print("Returning {} because we found {} in buffer ({}) : {}".format(data,delim,found,buf))
                        return str(msg[0])
            except Exception as e:
                Self.logs.log("DEBUG","Received {} and error was {}".format(data,e))
                Self.logs.log("FATAL","Bad data received or timeout ({}) has been reached for connection with {}. Aborting.".format(timeout,userid))
                sys.exit(2)
            if data=="":
                Self.logs.log("DEBUG","Closing connection or bad data received with {}. Aborting.".format(userid))
                sys.exit(3)
        #return data

#
# NEW JSON CheckMessage implementation
#
    def CheckMessage2(self,conn,data,addr):
        try:
            d=json.loads(data)
        except:
            Self.logs.log("DEBUG","Error : Unable to load Json data from : {}".format(data))
            return False
        if d:
            gamename=d['GAMENAME']
            req=d['REQUEST']
            # Send first a ACK to notify of good reception
            ack={'REQUEST':'ACK'}
            self.SendMessage2(conn,gamename,addr,ack)
            # Case Management
            if req=='GETVERSION':
                self.SendVersion(conn,gamename,addr)
            if req=='JOIN':
                self.JoinGame2(conn,gamename,addr)
            if req=="CLIENTWAIT4GAMEREADY":
                while not self.CheckGameReady(gamename):
                    time.sleep(0.2) # To avoid getting all the cpu
                    pass
                d={'GAMENAME':gamename,'REQUEST':'GAMEISREADY'}
                self.SendMessage2(conn,gamename,addr,d)
            if req=="HEREISCHOOSEDGAME":
                self.SetChoosedGame(gamename,d['CHOOSEDGAME'])
            if req=="GETCHOOSEDGAME":
                self.SendGame(conn,gamename,addr)
            if req=="HEREAREPLAYERNAMES":
                self.AddPlayerNames2(gamename,d['PLAYERNAMES'])
                self.SetGameReady(gamename) # Game is ready when no more data to receive from Master
            if req=="HEREAREGAMEOPTS":
                self.AddOpts(gamename,d['GAMEOPTS'],d['nb_darts'])
            if req=="GAMEOPTS":
                self.SendOpts(conn,gamename,addr)
            if req=="PLAYERNAMES":
                self.SendPlayers(conn,gamename,addr)
            if req=="READY" and 'NBLOCALPLAYERS' in d:
                self.SetReady(gamename,d['NBLOCALPLAYERS'])
            if req=="READY" and 'PLAYERSNAMES' in d:
                self.SetReady2(conn,gamename,addr,d['PLAYERSNAMES'])
            if req=="LAUNCH":
                self.Launch(gamename)
            if req=="SHUFFLE":
                self.Shuffle(gamename)
            if req=="LEAVE" and 'PLAYERSNAMES' in d:
                self.SomeoneLeaving(addr,gamename,d['PLAYERSNAMES'],d['NETSTATUS'])
            if req=="ISEVERYBODYREADY":
                self.SendStatus(conn,gamename,addr)
            if req=="HEREARERANDOMVALUES":
                self.StoreRamdom(gamename,d['RANDOMVALUES'],d['actual_round'],d['actual_player'],d['player_launch'])
            if req=="RANDOMVALUES":
                self.SendRandom(conn,gamename,addr,d['actual_round'],d['actual_player'],d['player_launch'])
            if req=="PLAY":
                self.Play(gamename,d['PLAY'],d['actual_round'],d['actual_player'],d['player_launch'])
            if req=="WAIT4PLAYER":
                if 'WAITFOR' in d:
                    self.SendHit(conn,gamename,addr,d['actual_round'],d['actual_player'],d['player_launch'],d['WAITFOR'])
                else:
                    self.SendHit(conn,gamename,addr,d['actual_round'],d['actual_player'],d['player_launch'])
            if req=="EXIT":
                self.LeaveGame(addr,gamename)

#
# New implementation of SendMessage in JSON
#
    def SendMessage2(self,conn,gamename,addr,msg):
        # Try to determine color
        try:
            MsgColor = self.color[userid]
        except:
            MsgColor = '31' # FallBaaaack to Blaaaaaack
        #Self.logs.log("DEBUG","\033[{}m[{}][{}-{}] Sending : {}\033[0m".format(MsgColor,gamename,addr[0],addr[1],msg))
        #conn.send(msg)
        # Print Debug
        # Try to send or timeout
        old_timeout = conn.gettimeout() # Save old timeout settings
        conn.settimeout(self.send_timeout) # Enable timeout for this request
        try:
            msg = json.dumps(msg)
            #msg = msg.encode('UTF-8')# No need anymore since python3 ! See : https://medium.com/better-programming/strings-unicode-and-bytes-in-python-3-everything-you-always-wanted-to-know-27dc02ff2686
            msg = str(msg) + str(self.delim)
            Self.logs.log("DEBUG","\033[{}m[{}][{}-{}] Sending : {}\033[0m".format(MsgColor,gamename,addr[0],addr[1],msg))
            #msg = msg.decode('UTF-8')
            msg = msg.encode('UTF-8') # Convert unicode to bytes
            conn.send(msg)
        except Exception as e: # If timeout reached
            Self.logs.log("DEBUG","Error is {}".format(e))
            Self.logs.log("ERROR","Error or timeout ({}) has been reached for connection with client {}. Killing thread.".format(self.send_timeout,addr))
            sys.exit(2)
        conn.settimeout(old_timeout) # Restore previous timeout

#
# Set Launch flag to True (game is ready to go - new version) - Trigger send of LAUNCH to clients via SetReady2
#
    def Launch(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.Launch=True

#
# Randomize Player names
#
    def Shuffle(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                random.shuffle(LstGames.PlayersNames)

#
# Handle someone who leave the game
#

    def SomeoneLeaving(self,addr,gamename,Pl,NetStatus):
        userid = "{}-{}".format(addr[0],addr[1])
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                if NetStatus=='YOUAREMASTER':
                    LstGames.Aborted=True
                for P in Pl:
                    try:
                        LstGames.PlayersNames.remove(P) # Remove players if they are ready
                    except:
                        pass # When there is still noone in the game (nobody's ready)
                Self.logs.log("DEBUG","Some has left. Remaining in game {} : {}".format(gamename,LstGames.PlayersNames))
                self.LeaveGame(userid,gamename)

#
# Send Server version
#

    def SendVersion(self,conn,gamename,addr):
        d={'GAMENAME':gamename,'REQUEST':'VERSION','VERSION':self.Config.pyDartsVersion}
        self.SendMessage2(conn,gamename,addr,d)

# PLAYERS NAMES
# Add players names to list (sent by master server - will be sent
#

    def AddPlayerNames2(self,gamename,playernames):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                for player in playernames:
                    Self.logs.log("DEBUG","Adding player {} to game {}".format(player,gamename))
                    LstGames.PlayersNames.append(player)

#
# Add players names in queue for a specific user
#
    def SendPlayers(self,conn,gamename,addr): #JSON
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                d={'GAMENAME':gamename,'REQUEST':'PLAYERNAMES','PLAYERNAMES':LstGames.PlayersNames}
                self.SendMessage2(conn,gamename,addr,d)

# GAME OPTIONS
# Add game options if they are received from master client
#
    def AddOpts(self,gamename,Opts,nb_darts): #JSON
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.Opts=Opts
                LstGames.nb_darts = nb_darts

    def SendOpts(self,conn,gamename,addr): # JSON
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                d={'GAMENAME':gamename,'REQUEST':'GAMEOPTS','GAMEOPTS':LstGames.Opts,'nb_darts':LstGames.nb_darts}
                self.SendMessage2(conn,gamename,addr,d)
# CHOOSED GAME
# Set Choosed game as server want
#
    def SetChoosedGame(self,gamename,ChoosedGame):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.ChoosedGame = ChoosedGame
                Self.logs.log("DEBUG","Setting choosed game for {} : {}".format(gamename,LstGames.ChoosedGame))

    def SendGame(self,conn,gamename,addr): # JSON Version
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                d={'GAMENAME':gamename,'CHOOSEDGAME':LstGames.ChoosedGame}
                self.SendMessage2(conn,gamename,addr,d)

#
# Create or Join a game
#
    def JoinGame2(self,conn,gamename,addr):
        userid = "{}-{}".format(addr[0],addr[1])
        availablegamename = True
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                Self.logs.log("WARNING","There is already a running game with the name {}. We will join this guy to it.".format(gamename))
                availablegamename = False
                ClientStatus = "YOUARESLAVE"
        if availablegamename:
            Self.logs.log("WARNING","\033[{}m Creating a game with the name {}\033[0m".format(self.color[userid],gamename))
            self.Games.append(CNetGames.CNetGames(gamename))
            ClientStatus = "YOUAREMASTER"
        Self.logs.log("DEBUG","\033[{}mJoining game {}\033[0m".format(self.color[userid],gamename))
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                LstGames.MembersId.append(userid)
        # Return to client if its a Master or a Slave
        d={'GAMENAME':gamename,'REQUEST':'NETSTATUS','NETSTATUS':ClientStatus}
        self.SendMessage2(conn,gamename,addr,d)


#
#  Increment the number of ready players and tell everybody that everybody's ready
#

    def SetReady2(self,conn,gamename,addr,Players):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                for P in Players:
                    if P not in LstGames.PlayersNames:
                        LstGames.PlayersNames.append(P)
                #LstGames.PlayersNames.extend(Players)
                Self.logs.log("DEBUG","Players in this game : {} ".format(LstGames.PlayersNames))
                # If the game has been aborted by master player
                if LstGames.Aborted==True:
                    d={'REQUEST':'ABORT','PLAYERSNAMES':[],'GAMENAME':gamename}
                # If the Master Player has not decided to launch game yet, we refresh player list
                elif LstGames.Launch==False:
                    d={'REQUEST':'PLAYERSNAMES','PLAYERSNAMES':LstGames.PlayersNames,'GAMENAME':gamename}
                # Else, that means that the game if ready to go, then go ! Send all players names anyway for a last refreshing :)
                else:
                    d={'REQUEST':'LAUNCH','GAMENAME':gamename,'PLAYERSNAMES':LstGames.PlayersNames}
                self.SendMessage2(conn,gamename,addr,d)

    def SendStatus(self,conn,gamename,addr):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                while LstGames.PlayersReady != len(LstGames.PlayersNames):
                    time.sleep(0.1) # To avoid getting all the cpu
                    pass
                d={'GAMENAME':gamename,'REQUEST':'EVERYBODYISREADY'}
                self.SendMessage2(conn,gamename,addr,d)
#
# Check if master client has sent all information to server (if true, send them to clients)
#
    def CheckGameReady(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                if LstGames.GameReady:
                    return True
                else:
                    return False
#
# If all data has been received by the server, set the game setup readyu to be downloaded
#
    def SetGameReady(self,gamename):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                Self.logs.log("DEBUG","{} is now complete. No more options to receive from server.".format(gamename))
                LstGames.GameReady = True # All data has been received by server

#
# Random values
#

    def StoreRamdom(self,gamename,rand,actual_round,actual_player,player_launch):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                # Delete any previously stored value
                LstGames.RandomValues={}
                # Store new values
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                LstGames.RandomValues[hitkey] = rand


    def SendRandom(self,conn,gamename,addr,actual_round,actual_player,player_launch):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                while hitkey not in LstGames.RandomValues:
                    time.sleep(0.1) # To avoid getting all the cpu
                    pass
                rand=LstGames.RandomValues[hitkey]
                d={'GAMENAME':gamename,'REQUEST':'RANDOMVALUES','RANDOMVALUES':rand,'actual_player':actual_player,'actual_round':actual_round,'player_launch':player_launch}
                self.SendMessage2(conn,gamename,addr,d)


#
# Play
#

    def Play(self,gamename,hit,actual_round,actual_player,player_launch):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                # Delete any stored values
                LstGames.HitValues={}
                # In any case, store actual hit
                Self.logs.log("DEBUG","Storing hit {} for round {}, player {}, launch {} and game {}".format(hit,actual_round,actual_player,player_launch,gamename))
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                LstGames.HitValues[hitkey]=hit

    def SendHit(self,conn,gamename,addr,actual_round,actual_player,player_launch,waitfor=False):
        for LstGames in self.Games:
            if LstGames.GameName == gamename:
                hitkey="{}{}{}".format(actual_round,actual_player,player_launch)
                if waitfor==False:
                    while hitkey not in LstGames.HitValues:
                        time.sleep(0.1) # To avoid getting all the cpu
                        pass
                    hit=LstGames.HitValues[hitkey]
                    d={'GAMENAME':gamename,'REQUEST':'SOMEONEPLAYED','PLAY':hit,'actual_round':actual_round,'player_launch':player_launch,'actual_player':actual_player}
                else:
                    while hitkey not in LstGames.HitValues or LstGames.HitValues[hitkey]!=waitfor:
                        time.sleep(0.1) # To avoid getting all the cpu
                        pass
                    d={'GAMENAME':gamename,'REQUEST':'SOMEONEPLAYED','PLAY':waitfor,'actual_round':actual_round,'player_launch':player_launch,'actual_player':actual_player}
                hit=LstGames.HitValues[hitkey]
                self.SendMessage2(conn,gamename,addr,d)



#
# Leave a game
#
    def LeaveGame(self,addr,gamename=None):
        # Remove user from Members
        userid = "{}-{}".format(addr[0],addr[1])
        for LstGames in self.Games:
            if (gamename!=None and LstGames.GameName == gamename) or gamename == None:
                if userid in LstGames.MembersId:
                    Self.logs.log("DEBUG","Removing {} from members of game named {}".format(addr,LstGames.GameName))
                    #filter(lambda a: a != userid, self.Games[gamename].MembersId)
                    LstGames.MembersId.remove(userid)
        # Remove color from color list (try/except is here if there is multiple connection from same ip address it will remove all of them)
        try:
            del self.color[userid]
        except:
            pass
        # Remove game if no more members
        index2del = -1
        for key,val in enumerate(self.Games):
            if len(self.Games[key].MembersId) == 0:
                index2del = key
        if index2del >= 0:
            Self.logs.log("WARNING","No more members in this game : {}. Removing.".format(self.Games[index2del].GameName))
            del self.Games[index2del]

#
# Close connection method
#
    def closecx(self):
        self.conn.close()
