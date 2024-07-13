#!/bin/sh


PYDARTS_HOME=$HOME/.pydarts
PYDARTS_VIDEO=/pydarts/videos

if [ -d $PYDARTS_HOME/videos/intro -a `find $PYDARTS_HOME/videos/intro \( -iname \*.mp4 -o -iname \*.mkv \) -type f | wc -l` -ge 1 ]
then
	video="`find $PYDARTS_HOME/videos/intro \( -iname \*.mp4 -o -iname \*.mkv \) -type f | shuf -n 1`"
elif [ -s $PYDARTS_HOME/videos/intro.mkv ]
then
	video=$PYDARTS_HOME/videos/intro.mkv
elif [ -s $PYDARTS_HOME/videos/intro.mp4 ]
then
	video=$PYDARTS_HOME/videos/intro.mp4
elif [ -s $PYDARTS_VIDEO/intro.mkv ]
then
	video=$PYDARTS_VIDEO/intro.mkv
elif [ -s $PYDARTS_VIDEO/intro.mp4 ]
then
	video=$PYDARTS_VIDEO/intro.mp4
else
	exit 0
fi
#cvlc $video  -f --no-video-title-show --mouse-hide-timeout 0 -A alsa,none --alsa-audio-device default  --play-and-exit
omxplayer --vol -1500 -o hdmi "$video"

