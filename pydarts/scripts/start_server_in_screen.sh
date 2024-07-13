#!/bin/bash
##################################################################
# This script is intended to be run by a MasterServer only (advanced users).
# Please don't execute it if you don't know what you're doing and check the wiki instead :
# https://obilhaut.freeboxos.fr/pydarts-wiki
# To run your own server, you only need pydarts_server.sh and no MasterServer.sh
# Screen is a magic tool that launch commands in a detachable subshell
##################################################################

# Wait a few seconds that network iterface raise up and get an ip address
sleep_time=30

## To run it at startup, add the following lines to /etc/rc.local
## Start pyDarts server in screens
# su pi -c '/home/pi/scripts/start_server_in_screen.sh &'

sleep $sleep_time

# Starting server in a screen context
screen -dmS pyserver /bin/bash
screen -S pyserver -X stuff '/usr/local/share/pydarts_dev/pydarts_server.sh --debuglevel=1 \n'

# Starting server in a screen context
screen -dmS pymaster /bin/bash
screen -S pymaster -X stuff '/usr/local/share/pydarts_dev/MasterServer.sh --debuglevel=1 \n'
