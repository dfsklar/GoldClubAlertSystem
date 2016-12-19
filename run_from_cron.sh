cd /root/GoldClubAlertSystem/
# find logs -name '*.out'  -empty  -print -exec /bin/rm '{}' \;
python main.py > logs/$$.out 2>&1
