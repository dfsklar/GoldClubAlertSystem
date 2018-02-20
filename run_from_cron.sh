cd /home/dfsklar/GoldClubAlertSystem/
find ./logs  -name '*.out' -empty -print -exec /bin/rm {} \;
find ./logs  -name '*.out' -mtime 14  -print -exec /bin/rm {} \;
python main.py > logs/$$.out 2>&1
