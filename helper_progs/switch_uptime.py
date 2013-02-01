#! /usr/bin/python3

import subprocess
import re
from threading import Thread
from pysnmp.entity.rfc3413.oneliner import cmdgen
import switch_ping
import database_con as db


COMMUNITYRO = 'public'
PORT = 161
OID = '1.3.6.1.2.1.1.3.0'
UPTIME_DIC = {}


def check_uptime(id, ip, oid=OID):
    UPTIME_DIC[id] = {}
    oid = tuple([int(i) for i in oid.split('.')])
    cg = cmdgen.CommandGenerator()
    comm_data = cmdgen.CommunityData('my-manager', COMMUNITYRO, 0)
    transport = cmdgen.UdpTransportTarget((ip, PORT))
    try:
        errInd, errStatus, errIdx, result = cg.getCmd(comm_data, transport, oid)
        # in case of strange error in python3.2 with snmp and cisco
        if result == ():
            try:
                p = subprocess.Popen(['snmpwalk', '-v', '1', '-c',
                                      'public', '-On', ip,
                                      '1.3.6.1.2.1.1.3', '2>/dev/null'], 
                                      stdout=subprocess.PIPE)
                result = p.communicate()
                seconds = re.search("(\(\d+\))", result[0].decode('UTF-8'))
                sec = int(seconds.group()[1:-3])
                UPTIME_DIC[id]['sw_uptime'] = sec
            except Exception:
                UPTIME_DIC[id]['sw_uptime'] = None
        else:
            # normal work with pysnmp
            sec = int(str(result[0][1])[:-2])
            UPTIME_DIC[id]['sw_uptime'] = sec
    except Exception as e:
        UPTIME_DIC[id]['sw_uptime'] = None
        # print('Error', e)


if __name__=='__main__':
    data_list = switch_ping.fetchdata()
    threads = []
    for item in data_list:
        # cheking if tests are enabled for device
        if item[1]:
            t = Thread(target=check_uptime, args=(item[6], item[0],))
            threads.append(t)
        else:
            UPTIME_DIC[item[6]] = {}
            UPTIME_DIC[item[6]]['sw_uptime'] = None 

    for thread in threads: # starting all threads
        thread.start()

    for thread in threads: # wait for all threads
        thread.join()      # to finish
    
    # writing to database
    switch_ping.lock.acquire()
    db.setdata(UPTIME_DIC, 'uptime')
    # for ip, uptime in UPTIME_DIC.items():
    #     switch_ping.setdata(uptime, ip, 'uptime')
    switch_ping.lock.release()
