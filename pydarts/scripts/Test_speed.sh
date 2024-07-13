
echo 
echo "Test ecriture fichier 100 M"
dd if=/dev/zero of=/tmp/test1.img bs=100M count=1 oflag=dsync

echo 
echo "Test lecture fichier 100 M"
dd if=/tmp/test1.img of=/dev/zero bs=100M count=1

rm -f /tmp/test1.img
