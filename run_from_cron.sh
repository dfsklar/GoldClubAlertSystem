cd /root/GoldClubAlertSystem/
python main.py > logs/$$.out 2>&1
find logs -atime 20 -name '*.out' -print -exec /bin/rm {} \;

