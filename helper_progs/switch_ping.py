#! /usr/bin/python3

import subprocess
import psycopg2
import re
from threading import Thread, Lock
import secure


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
              sw_id, sw_uptime FROM switches_switch""")
    data = c.fetchall()
    data_list = []
    for row in data:
        data_list.append(row)
    conn.close()
    return data_list

def setdata(avg_ping, ip_addr, data='ping'):
    conn = makeconnection()
    c = conn.cursor()
    if data=='ping':
        c.execute("""UPDATE switches_switch SET sw_ping=(%s) WHERE ip_addr=(%s)""",
                  (avg_ping, ip_addr))
    elif data == 'uptime':
        c.execute("""UPDATE switches_switch SET sw_uptime=(%s) WHERE ip_addr=(%s)""",
                  (avg_ping, ip_addr))
    conn.commit()
    conn.close()

def ping_st(ip, *args):
    p = subprocess.Popen(
        ["ping", "-c", "3", ip],
	stdout=subprocess.PIPE
	)
    result = p.communicate()
    pclst = 0
    ping_bad = 'Good'
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
                PING_DIC[ip] = avgtime
            else:
                avgtime = None
                PING_DIC[ip] = None

def main():
    data_list = fetchdata()
    threads = []
    for item in data_list:
        # checking if tests are enabled for device
        if item[1]:
            t = Thread(target=ping_st, args=(item[0],))
            threads.append(t)
        else:
            PING_DIC[item[0]] = 0
            setdata(0, item[0], 'ping')

    for thread in threads:
        thread.start()

    for thread in threads: # waiting all threads to finish
        thread.join()

    lock.acquire()
    for ip, ping in PING_DIC.items():
        setdata(ping, ip, 'ping')
    lock.release()

if __name__ == '__main__':
    main()
