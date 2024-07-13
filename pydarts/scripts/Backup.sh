#!/bin/sh

exec 2> /pydarts/logs/backup.log
set -uevx

RASPYDARTS_HOME=/pydarts
BACKUP_DIR=backup
LOGS_DIR=logs
NB_BACKUP=3
BASH_MODE=false
BACKUP_HOME=true

Usage(){
	echo ""
	echo "Backup.sh [-0][-p] b|r|l|c [filename]"
	echo ""
	echo "	b : Backup data"
	echo "	r : Restore data"
	echo "	l : List backup files"
	echo "		-0 : bash mode - 1 file per line"
	echo "		-p : No backup of ~/.pydarts directory"
	echo "	c : Clean old backups (keep 3 last versions)"
	echo ""
	echo "	[filename]	Archive name to create or restore."
	echo "			Backup :"
	echo "				Default : \e[97mraspydarts_\e[96mVx.y.z\e[97m_\e[95mYYYYMMDDHHmm\e[97m.tgz\e[39m"
	echo "			 	\e[96mVx.y.Z\e[39m : Raspydarts version"
	echo "				\e[95mYYYYMMDHHmm\e[39m : Date and hour of the backup"
	echo ""
	echo "			Restore :"
	echo "				Restore the last file : Last version, last date"
	echo ""
	echo "		/\e[33m!\\ Filename must respect ont of the following naming conventions :"
	echo "			\e[97mraspydarts_\e[96mVx.y.z\e[97m_\e[95mYYYYMMDDHHmm\e[97m.tgz\e[39m"
	echo "			\e[97mupdate_\e[96mVx.y.z\e[97m_\e[95mYYYYMMDDHHmm\e[97m.tgz\e[39m"
	echo ""
}

Error(){
	Usage
	echo ""
	echo "$1"
	echo
}


if [ $# -lt 1 -o $# -gt 2 ]
then
	Usage
	exit 0
else
	cd $RASPYDARTS_HOME

	if [ "$1" = '-0' ]
	then
		BASH_MODE=true
		shift
	fi

	if [ "$1" = '-p' ]
	then
		BACKUP_HOME=false
		shift
	fi

	case "$1" in 
		'b' )	MODE=BACKUP ;;
		'r' )	MODE=RESTORE ;;
		'l' )	MODE=LIST ;;
		'c' )	MODE=CLEAN ;;
		* )	Error "Unknown $1 parameter"
			exit 9
			;;
	esac
	shift

	if [ $# -eq 1 ]
	then
		f=`basename $1`
		if [ `expr "$f" : '^raspydarts_V[0-9]\.[0-9]\.[0-9]_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9].*\.tgz'` -eq 35 ]
		then
			FileName="$f"
		elif [ `expr "$f" : '^update_V[0-9]\.[0-9]\.[0-9]_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9].*\.tgz'` -eq 31 ]
		then
			FileName="$f"
		else
			Error "Provided filename (\e[91m$1\e[39m) doesn't respect naming convention"
			exit 10
		fi
	else
		FileName=""
	fi

fi

case "$MODE" in
	"CLEAN" )	# Clean old versions

		if $BASH_MODE
		then
			ls -1 $BACKUP_DIR/raspydarts*tgz | head -n -$NB_BACKUP
		else
			NbFiles=`ls -1 $BACKUP_DIR/raspydarts*tgz $BACKUP_DIR/update*tgz| wc -l`
			echo ""
			if [ $NbFiles -lt $NB_BACKUP ]
			then
				echo "Only $NbFiles available bkacups"
				echo "No need to clean"
				echo ""
				exit 0
			else
				echo "    Filename                        | Version |    Timestamp "
				echo "------------------------------------+---------+------------------"

				for f in `ls -1 $BACKUP_DIR/raspydarts*tgz $BACKUP_DIR/update*tgz| head -n -$NB_BACKUP`
				do
					Version=`echo $f | cut -d'_' -f2`
					Date="`echo $f | cut -d'_' -f3-4 | sed -e 's/^\([0-9][0-9][0-9][0-9]\)\([0-9][0-9]\)\([0-9][0-9]\)_\([0-9][0-9]\)\([0-9][0-9]\).*$/\3\/\2\/\1 \4:\5/'`"

					echo "$f |  \e[96m$Version\e[39m   | \e[95m$Date\e[39m"
					rm -f $f
				done
				echo ""

			fi
		fi
	;;

	"LIST" )	# List availables backups
		if $BASH_MODE
		then
			ls -1 $BACKUP_DIR/raspydarts*tgz $BACKUP_DIR/update*tgz
		else
			NbFiles=`ls -1 $BACKUP_DIR/raspydarts*tgz $BACKUP_DIR/update*tgz | wc -l`
			echo ""
			if [ $NbFiles -gt 0 ]
			then
				echo "    Filename                        |  Version  | Type |    Timestamp "
				echo "------------------------------------+-----------+------+------------------"

				echo -n '\e[92m'

				i=1
				for f in `ls -r1 $BACKUP_DIR/raspydarts*tgz $BACKUP_DIR/update*tgz | sort  -k2r,3r -t_ | sed -e "s/$BACKUP_DIR\///g" `
				do
					Version=`echo $f | cut -d'_' -f2`
					Date="`echo $f | cut -d'_' -f3-4 | sed -e 's/^\([0-9][0-9][0-9][0-9]\)\([0-9][0-9]\)\([0-9][0-9]\)_\([0-9][0-9]\)\([0-9][0-9]\).*$/\3\/\2\/\1 \4:\5/'`"

					if [ `expr "$f" : '^update_V[0-9]\.[0-9]\.[0-9]_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9].*\.tgz'` -eq 31 ]
					then
						echo "$f\e[39m     |  \e[96m$Version\e[39m   | Màj  | \e[95m$Date\e[39m"
					else
						echo "$f\e[39m |  \e[96m$Version\e[39m   | Full | \e[95m$Date\e[39m"
					fi
					if [ $i -ge $NB_BACKUP ]
					then
						echo -n '\e[93m'
					else
						echo -n '\e[97m'
					fi
					i=`expr $i + 1`

				done
				echo ""
			else
				echo ""
				echo "	/\e[33m!\\ No backups available.\e[39m"
				echo "	Launch ./Backup.sh b to generate"
				echo ""
				exit 0
			fi
		fi
	;;

	"BACKUP" )	# Backup mode
		if [ -z "$FileName" ]
		then
			Date=`date +%Y%m%d_%H%M`
			Version=
			test -s /pydarts/VERSION && Version=`cat /pydarts/VERSION | cut -d'_' -f1`

			Backup=$RASPYDARTS_HOME/$BACKUP_DIR/raspydarts_${Version}_${Date}.tgz
		fi

		if $BASH_MODE
		then
			if $BACKUP_HOME
			then
				tar -zcvf $Backup --exclude $BACKUP_DIR --exclude $LOGS_DIR $RASPYDARTS_HOME ~/.pydarts >> /pydarts/logs/backup.log
			else
				tar -zcvf $Backup --exclude $BACKUP_DIR --exclude $LOGS_DIR $RASPYDARTS_HOME >> /pydarts/logs/backup.log
			fi
		else
			echo ""
			echo "	Generating \e[92m$Backup\e[39m"
			echo ""
			if $BACKUP_HOME
			then
				echo "tar -zcvf $Backup --exclude='__init__.py' --exclude='__pycache__' --exclude='*.tgz' --exclude='*.log' --exclude $BACKUP_DIR --exclude $LOGS_DIR $RASPYDARTS_HOME ~/.pydarts >> /pydarts/logs/backup.log"
				tar -zcvf $Backup --exclude='__init__.py' --exclude='__pycache__' --exclude='*.tgz' --exclude='*.log' --exclude $BACKUP_DIR --exclude $LOGS_DIR $RASPYDARTS_HOME ~/.pydarts >> /pydarts/logs/backup.log
			else
				echo "tar -zcvf $Backup --exclude='__init__.py' --exclude='__pycache__' --exclude='*.tgz' --exclude='*.log' --exclude $BACKUP_DIR --exclude $LOGS_DIR $RASPYDARTS_HOME >> /pydarts/logs/backup.log"
				tar -zcvf $Backup --exclude='__init__.py' --exclude='__pycache__' --exclude='*.tgz' --exclude='*.log' --exclude $BACKUP_DIR --exclude $LOGS_DIR $RASPYDARTS_HOME >> /pydarts/logs/backup.log
			fi
			echo ""
			echo "	\e[92mCorrect end\e[39m"
			echo
		fi
	;;

	"RESTORE" )	# Restore data
		if [ -z "$FileName" ]
		then
			FileName="`basename \`ls -1 $RASPYDARTS_HOME/$BACKUP_DIR/raspydarts*tgz | tail -1\``"
		fi

		if [ -z "$FileName" ]
		then
			Error "No backup to restore"
			echo ""
			exit 11
		elif [ ! -s "$RASPYDARTS_HOME/$BACKUP_DIR/$FileName" ]
		then
			Error "File \e[91m$FileName\e[39m is missing"
			echo ""
			exit 12
		else
			echo ""
			echo "Restore \e[92m$FileName\e[39m ..."
			echo ""
			echo "tar xvf $RASPYDARTS_HOME/$BACKUP_DIR/$FileName -C/ --overwrite >> /pydarts/logs/backup.log"
			tar xvf "$RASPYDARTS_HOME/$BACKUP_DIR/$FileName" -C/ --overwrite >> /pydarts/logs/backup.log
			echo ""
			echo "\e[92mDone\e[39m"
			echo
		fi
	;;

esac

