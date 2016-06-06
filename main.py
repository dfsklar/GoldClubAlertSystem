import re
import mechanize
import pickle

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

    # We really don't want the default "show all" page
    br.open("https://www.theaterclub.com/ny/upcoming/new")
    html = br.response().read()

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
                    title = the_match.group(1)
                    available_titles.append(title)
                else:
                    raise Exception("Change in format detected: series-title did not presage actual title two lines later")

    return sorted(available_titles)


def fetch_previous_available_titles():
    with open("avail_titles.pkl") as f:
        return pickle.load(f)


def titlelist_abbrev(arr_titles):
    return str(map(lambda t: t[0:15], arr_titles))

# This differ Would be much nicer as a lambda use of filter() -- good exercise for Matt
def differ(old, new):
    new_offerings = []
    for x in new:
        if x not in old:
            new_offerings.append(x)
    return new_offerings


prev_avail = None
try:
    prev_avail = fetch_previous_available_titles()
except:
    prev_avail = []

new_avail = fetch_fresh_available_titles(login_and_grab_roster())

new_offerings = differ(prev_avail, new_avail)
if new_offerings:
    import subprocess
    retval = subprocess.call(['/bin/sh', './report_new_offerings.sh', titlelist_abbrev(new_offerings), credentials.SMSEMAIL])
    print("Return value from the email-alert launch: " + str(retval))

with open("avail_titles.pkl", "w") as f:
    pickle.dump(new_avail, f)
