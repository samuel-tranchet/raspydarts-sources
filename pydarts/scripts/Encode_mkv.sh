
if [ $# -ne 1 ]
then
	echo "Usage : Encode_mkv.sh <file>"
	echo ""
	echo "It will encode file into mkv file"
	echo ""
	exit 0
fi

file2encode="$1"

mkvfile="`basename ${file2encode%.*}`.mkv"

ffmpeg -i "$file2encode" -r 30 "$mkvfile"

#ffmpeg-normalize  --sample-rate 44100 --video-codec h264_omx -e '"-vframes" "30" "-s" "1280x720"' /home/pi/.pydarts/themes/perso1/videos/big_score/killfleche1.mp4 -f -o killfleche1.mkv
#ffmpeg-normalize  --sample-rate 44100 --video-codec h264_omx -e '"-vframes" "30" "-s" "1280x720"' /home/pi/.pydarts/videos/S1.mp4 -o S1.mkv

