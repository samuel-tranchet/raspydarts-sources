#!/usr/bin/env python
import sys
from include import CServer
from include import CArgs
from include import CLogs # Import Clogs from path
from include import CConfig # Import Config Class to read config file


#####
# Create server instances
#####
Logs = CLogs.CLogs()
Args = CArgs.CArgs()
Config=CConfig.CConfig(Args,Logs)
ConfigGlobals=Config.ReadConfigFile("SectionGlobals") # Read config file for main configuration
ConfigAdvanced=Config.ReadConfigFile("SectionAdvanced") # Read config file for main configuration
ConfigServer=Config.ReadConfigFile("Server") # Read config file for server specific configuration

Logs.SetConfig(Config)

# Select either future or old version of pyDarts server
if Config.GetValue("Server",'server2'):
    Logs.Log("WARNING","Using future Server version. May be unstable now.")
    CServer = CServer.CServer2(Config,Logs)
else:
    Logs.Log("DEBUG","Starting stable version of pyDarts server.")
    CServer = CServer.CServer(Config,Logs)
Args.SetLogs(Logs)
#######
# Set verbosity if option given
#######
# Verbosity
debuglevel = int(Config.GetValue('SectionGlobals','debuglevel'))
if debuglevel>=1 and debuglevel<=4:
    Logs.UpdateFacility(debuglevel)

# Getting Interface or setting default
ServerInterface = Config.GetValue('SectionAdvanced','listen')

# Setting Ip from interface
ServerIp = Args.get_ip_address(ServerInterface)
if ServerIp==None:
    Logs.Log("FATAL","Unable to listen from {}. Use --help for a list of command line arguments.".format(ServerInterface))
    exit(1)
# Getting port or set default
ServerPort = int(Config.GetValue('SectionAdvanced','serverport'))
if ServerPort == False:
    ServerPort = 5005

Logs.Log("DEBUG","Starting server on interface {} ({}) on port {}".format(ServerInterface,ServerIp,ServerPort))

# Listen for connexions
CServer.Listen(ServerIp,ServerPort)
# Launch main
CServer.__main__()
