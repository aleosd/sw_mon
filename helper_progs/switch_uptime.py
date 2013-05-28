#! /usr/bin/python3

import subprocess
import re
from threading import Thread
import queue
import time
# from pysnmp.entity.rfc3413.oneliner import cmdgen

from tendo import singleton

import switch_ping
import database_con as db


COMMUNITYRO = 'public'
PORT = 161
OID = '1.3.6.1.2.1.1.3'
UPTIME_DIC = {}
MAX_THREADS = 5


# chek if another insnatce of process is still running
me = singleton.SingleInstance()

def check_uptime(id, ip, oid=OID):
    UPTIME_DIC[id] = {}
    oid = tuple([int(i) for i in oid.split('.')])
#    cg = cmdgen.CommandGenerator()
#    comm_data = cmdgen.CommunityData('my-manager', COMMUNITYRO, 0)
#    transport = cmdgen.UdpTransportTarget((ip, PORT))
#    try:
#        errInd, errStatus, errIdx, result = cg.getCmd(comm_data, transport, oid)
#        # in case of strange error in python3.2 with snmp and cisco
#        if result == ():
    try:
        p = subprocess.Popen(['snmpwalk', '-v', '1', '-c',
                              'public', '-On', ip,
                              '1.3.6.1.2.1.1.3', '2>/dev/null'],
                              stdout=subprocess.PIPE)
        result = p.communicate()
        # looks like this approach alittle bit faster:
        sec = result[0].decode('UTF-8')[33:].split(')')[0][:-2]
        # seconds = re.search("(\(\d+\))", result[0].decode('UTF-8'))
        # sec = int(seconds.group()[1:-3])
        if sec:
            UPTIME_DIC[id]['sw_uptime'] = sec
        else:
            UPTIME_DIC[id]['sw_uptime'] = None
    except Exception:
        UPTIME_DIC[id]['sw_uptime'] = None
#        else:
#            # normal work with pysnmp
#            sec = int(str(result[0][1])[:-2])
#            UPTIME_DIC[id]['sw_uptime'] = sec
#    except Exception as e:
#        UPTIME_DIC[id]['sw_uptime'] = None
#        # print('Error', e)
#

# helper function for queue, limiting threads count to MAX_THREADS
def worker():
    all_done = 0
    while not all_done:
        try:
            item = q.get(0)
            check_uptime(item[6], item[0],)
            # q.task_done()
        except queue.Empty:
            all_done = 1


if __name__=='__main__':
    start_time = time.time()
    q = queue.Queue()
    data_list = db.fetchdata()
    threads = []

    for item in data_list:
        # cheking if tests are enabled for device
        if item[1]:
            '''
            t = Thread(target=check_uptime, args=(item[6], item[0],))
            threads.append(t)
            '''
            q.put(item)
        else:
            UPTIME_DIC[item[6]] = {}
            UPTIME_DIC[item[6]]['sw_uptime'] = None

    for i in range(MAX_THREADS):
        t = Thread(target=worker)
        threads.append(t)
        t.start()
    '''
    for thread in threads: # starting all threads
        thread.start()
    '''

    for thread in threads: # wait for all threads
        thread.join()      # to finish

    # writing to database
    switch_ping.lock.acquire()
    db.setdata(UPTIME_DIC, 'uptime')
    switch_ping.lock.release()

    print(time.time() - start_time, "seconds")
