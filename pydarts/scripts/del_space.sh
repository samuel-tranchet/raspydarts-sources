
find . -name '* *' \
| while read line
do
	new="`expr \"$line\"  | sed -e 's/ /_/g'`"
	new="`expr \"$new\"  | sed -e \"s/'/_/g\"`"
	mv "$line" $new
done

