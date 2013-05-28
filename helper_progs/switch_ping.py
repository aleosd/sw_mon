#! /usr/bin/python3

import re
import subprocess
import time
from threading import Thread, Lock
from tendo import singleton
import sh
import database_con as db


"""  Program for parsing ping information.
Working on *nix only. Return ip address of
tested host, avg delay, and ping status
(ping_bad == True if packet loss more 60%)

Modification for usage with django-project
switch-monitoring.
"""

# chek if another insnatce of process is still running
me = singleton.SingleInstance()

PING_DIC = {}
EVENT_DIC = {}

lock = Lock()


def ping_st(ip, old_ping, id, manual_check=False, ping_type=2):
    # for subprocess usage
    if ping_type==2:
        p = subprocess.Popen(["ping", "-c", "3", "-i", "0.2", ip], stdout=subprocess.PIPE)
        result = p.communicate()
        result = result[0].decode()

    # for sh.py usage
    if ping_type==1:
        try:
            result = str(sh.ping("-c 3", "-i 0.2", ip, _bg=True))
        except sh.ErrorReturnCode_1:
            result = None

    if manual_check:
        return result

    PING_DIC[id] = {'old_ping': old_ping}
    if result:
        m2 = re.search('rtt min/avg/max/mdev = (.*) ms', result)
        if m2:
            avgtime = m2.group(1).split('/')[1]
            PING_DIC[id]['ping'] = float(avgtime)
        else:
            PING_DIC[id]['ping'] = None
    else:
        PING_DIC[id]['ping'] = None


def main():
    data_list = db.fetchdata()
    threads = []
    for item in data_list:
        # checking if tests are enabled for device
        if item[1]:
            t = Thread(target=ping_st, args=(item[0], item[5], item[6],))
            threads.append(t)
        # if disable, setting None
        else:
            PING_DIC[item[6]] = {}
            PING_DIC[item[6]]['ping'] = None
            PING_DIC[item[6]]['old_ping'] = None

    for thread in threads:
        thread.start()

    for thread in threads: # waiting all threads to finish
        thread.join()

    lock.acquire()
    db.setdata(PING_DIC, 'ping')
    lock.release()

    # Create event record in dic if switch is not responding
    for id in PING_DIC:
        if PING_DIC[id]['old_ping'] and not PING_DIC[id]['ping']:
            EVENT_DIC[id] = {}
            EVENT_DIC[id]['ev_type'] = "err"
            EVENT_DIC[id]['ev_event'] = "Switch is not responding"
            EVENT_DIC[id]['ev_comment'] = ""
        elif not PING_DIC[id]['old_ping'] and PING_DIC[id]['ping']:
            EVENT_DIC[id] = {}
            EVENT_DIC[id]['ev_type'] = "info"
            EVENT_DIC[id]['ev_event'] = "Switch is up and running"
            EVENT_DIC[id]['ev_comment'] = ""

    # If at least one record, updating database
    if len(EVENT_DIC) > 0:
        lock.acquire()
        db.setdata(EVENT_DIC, data='event')
        lock.release()


if __name__ == '__main__':
    main()
