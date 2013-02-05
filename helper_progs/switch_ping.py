#! /usr/bin/python3

import subprocess
import datetime
import psycopg2
import re
from threading import Thread, Lock
import secure
import database_con as db


"""  Program for parsing ping information.
Working on *nix only. Return ip address of
tested host, avg delay, and ping status
(ping_bad == True if packet loss more 60%)

Modification for usage with django-project
switch-monitoring.
"""

DBNAME = secure.DBNAME
USER = secure.USER
PASS = secure.PASS
PING_DIC = {}
EVENT_DIC = {}

def makeconnection():
    try:
        conn = psycopg2.connect("dbname={} user={} password={}".format(DBNAME,
                                                                       USER,
                                                                       PASS))
        return conn
    except Exception as e:
        print('Error: ', e)

lock = Lock()

def fetchdata():
    conn = makeconnection()
    c = conn.cursor()
    c.execute("""SELECT ip_addr, sw_enabled, sw_type_id,
              sw_id, sw_uptime, sw_ping, id FROM switches_switch""")
    data = c.fetchall()
    data_list = []
    for row in data:
        data_list.append(row)
    conn.close()
    return data_list

def setdata(avg_ping, ip_addr, data='ping', db_data = []):
    '''Format of db_data: db_data[0] -> event type
                          db_date[1] -> switch_id (ForeignKey)
                          db_date[2] -> event description
                          db_date[3] -> comment (optional)
    '''
    conn = makeconnection()
    c = conn.cursor()
    if data=='ping':
        c.execute("""UPDATE switches_switch SET sw_ping=(%s) WHERE ip_addr=(%s)""",
                  (avg_ping, ip_addr))
    elif data == 'uptime':
        c.execute("""UPDATE switches_switch SET sw_uptime=(%s) WHERE ip_addr=(%s)""",
                  (avg_ping, ip_addr))
    elif data == 'event':
        c.execute("""INSERT INTO switches_event VALUES (%s)""",
                  (datetime.datetime.now(), db_data[0], db_data[1], db_data[2],
                   db_data[3]))
    conn.commit()
    conn.close()

def ping_st(ip, old_ping, id, *args):
    p = subprocess.Popen(["ping", "-c", "3", ip], stdout=subprocess.PIPE)
    result = p.communicate()
    pclst = 0
    ping_bad = 'Good'
    PING_DIC[id] = {}
    PING_DIC[id]['old_ping'] = old_ping
    for line in result:
        if line != None:
            line = line.decode()
            m1 = re.search('(.*)% packet loss', line)
            if m1:
                pclst = int((m1.group(1)).split()[5])
                if pclst > 60: ping_bad = 'Bad'
            m2 = re.search('rtt min/avg/max/mdev = (.*) ms', line)
            if m2:
                avgtime = m2.group(1).split('/')[1]
                PING_DIC[id]['ping'] = float(avgtime)
            else:
                avgtime = None
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

    # Create event record in dic if switch not responding
    for id in PING_DIC:
        if PING_DIC[id]['old_ping'] and not PING_DIC[id]['ping']:
            print('Switch not responding!')
            EVENT_DIC[id] = {}
            EVENT_DIC[id]['ev_type'] = "err"
            EVENT_DIC[id]['ev_event'] = "Switch is not responding"
            EVENT_DIC[id]['ev_comment'] = " "

    # If at least one record, updating database
    if len(EVENT_DIC) > 0:
        lock.acquire()
        print("Adding new event")
        db.setdata(EVENT_DIC, data='event')
        lock.release()

if __name__ == '__main__':
    main()
