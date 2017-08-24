import re
import mechanize
import pickle
from difflib import SequenceMatcher

import credentials


# Returns the raw HTML of the roster page post-login
def login_and_grab_roster():
    br = mechanize.Browser()
    br.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:45.0) Gecko/20100101 Firefox/45.0')]
    br.open("https://www.theaterclub.com/user")

    br.select_form(nr=0)

    br.find_control(name="name").value = credentials.USERNAME
    br.find_control(name="pass").value = credentials.PASSWORD

    response_login = br.submit()

    html = response_login.get_data()
    #print html

    # We really don't want the default "show all" page
    br.open("https://www.theaterclub.com/ny/upcoming/new")
    html = br.response().read()
    #print "------------------"
    #print html

    return html


# Returns a sorted list of all available titles
def fetch_fresh_available_titles(html):
    available_titles = []

    regex_title_announce = re.compile('.*<h2 class=.series-title.*', re.IGNORECASE)
    regex_title = re.compile(' *(.*) *</a>.*', re.IGNORECASE)
    line_num = 999
    for line in html.splitlines():
        line_num += 1
        the_match = regex_title_announce.match(line)
        if the_match:
            line_num = 0
        else:
            if line_num == 2:
                the_match = regex_title.match(line)
                if the_match:
                    title = the_match.group(1).strip()
                    available_titles.append(title)
                else:
                    raise Exception("Change in format detected: series-title did not presage actual title two lines later")

    return sorted(available_titles)


def fetch_previous_available_titles():
    with open("avail_titles.pkl") as f:
        return pickle.load(f)


def titlelist_abbrev(arr_titles):
    return str(map(lambda t: t[0:45], arr_titles))


def differ(old, new):
    new_offerings = []
    for new_candidate in new:
        #print "======================"
        #print "Looking for match for " + new_candidate
        old_matching_entry = list(filter(lambda x: SequenceMatcher(None, x, new_candidate).ratio() > 0.8, old))
        if not old_matching_entry:
            new_offerings.append(new_candidate)
            #print "DIFFER IS SAYING THIS IS NEW:"
            #print new_candidate
            #print old
        #else:
            #print "Found match: "
            #print old_matching_entry
    return new_offerings


prev_avail = None
try:
    prev_avail = fetch_previous_available_titles()
except:
    prev_avail = []

new_avail = fetch_fresh_available_titles(login_and_grab_roster())

new_offerings = differ(prev_avail, new_avail)

if new_offerings:
    print "There are new offerings"
    import subprocess
    titles =  titlelist_abbrev(new_offerings).replace('\'','').replace('"','')
    retval = subprocess.call(['/bin/sh', './report_new_offerings.sh', titles, credentials.SMSEMAIL])
    print("Return value from the email-alert launch: " + str(retval))
    retval = subprocess.call([
        'curl',
        '-X',
        'POST',
        '--data-urlencode',
        'payload={"channel": "#general", "username": "webhookbot", "text": "GOLDCLUB %s", "icon_emoji": ":ghost:"}' % titles,
        'https://hooks.slack.com/services/%s' % credentials.SLACK
    ])
    print("Return value from the slack webhook launch: " + str(retval))


with open("avail_titles.pkl", "w") as f:
    pickle.dump(new_avail, f)
