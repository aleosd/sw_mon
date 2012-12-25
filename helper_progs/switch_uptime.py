#! /usr/bin/python3

from threading import Thread
from pysnmp.entity.rfc3413.oneliner import cmdgen
import switch_ping


COMMUNITYRO = 'public'
PORT = 161
OID = '1.3.6.1.2.1.1.3.0'


def check_uptime(ip, oid=OID):
    oid = tuple([int(i) for i in oid.split('.')])
    cg = cmdgen.CommandGenerator()
    comm_data = cmdgen.CommunityData('my-manager', COMMUNITYRO, 0)
    transport = cmdgen.UdpTransportTarget((ip, PORT))
    try:
        errInd, errStatus, errIdx, result = cg.getCmd(comm_data, transport, oid)
        sec = int(str(result[0][1])[:-2])
        switch_ping.lock.acquire()
        switch_ping.setdata(sec, ip, 'uptime')
        switch_ping.lock.release()
    except Exception as e:
        switch_ping.lock.acquire()
        switch_ping.setdata(None, ip, 'uptime')
        switch_ping.lock.release()
        print('Error', e)

if __name__=='__main__':
    data_list = switch_ping.fetchdata()
    for item in data_list:
        if item[1]:
            Thread(target=check_uptime, args=(item[0],)).start()
        else:
            switch_ping.setdata(0, item[0])
