#! /usr/bin/python3

import subprocess
import psycopg2
import re
from threading import Thread, Lock


"""  Program for parsing ping information.
Working on *nix only. Return ip address of
tested host, avg delay, and ping status
(ping_bad == True if packet loss more 60%)

Modification for usage with django-project
switch-monitoring.
"""

DBNAME = 'sw_mon'
USER = 'sw_mon'
PASS = 'monitor'

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
    c.execute("SELECT ip_addr, sw_enabled FROM switches_switch")
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
            else:
                avgtime = None
    lock.acquire()
    setdata(avgtime, ip, 'ping')
    lock.release()
    return ip, avgtime, ping_bad

def main():
    data_list = fetchdata()
    for item in data_list:
        if item[1]:
            Thread(target=ping_st, args=(item[0],)).start()
        else:
            setdata(0, item[0], 'ping')

if __name__ == '__main__':
    main()
