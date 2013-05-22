#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import argparse
from pysnmp.entity.rfc3413.oneliner import cmdgen
from threading import Thread

import database_con as db


SHOW_UPLINKS = False
IP_PORT_DICT = {}


def hex_to_decimal(mac):
    macDecimal = '.'.join([str(int(s, 16)) for s in mac.split(':')])
    return macDecimal


def get_port(ip, mac):
    '''Get port, where given mac is listetd, if any.
    '''

    port = 161
    cg = cmdgen.CommandGenerator()
    comm_data = cmdgen.CommunityData('my-manager', 'public', 0)
    transport = cmdgen.UdpTransportTarget((ip[0], port))
    oid = '1.3.6.1.2.1.17.4.3.1.2.' + mac
    oid_tuple = tuple([int(i) for i in oid.split('.')])
    errInd, errStatus, errIdx, result = cg.getCmd(comm_data, transport,
                                                  oid_tuple)
    if not errInd and not errStatus:
        port_num = str(result[0][1])
        IP_PORT_DICT[ip[0]] = port_num
        port_list = ip[1].split(',')
        for port in port_list:
            if port and port_num != port.strip():
                print('{}, uplink on {}, queryed mac on port {}'.format(ip[0], ip[1].split(','), port_num))
            elif SHOW_UPLINKS and port:
                print('{}, uplink on {}, queryed mac on port {}'.format(ip[0], ip[1].split(','), port_num))


def get_switches():
    '''Function for parsing switches from the database.
        None -> List
    '''

    raw_switch_list = db.fetchdata()
    switch_list = []
    for switch in raw_switch_list:
        if switch[1]:
            switch_list.append((switch[0],switch[7]))
    return switch_list


def add_uplink_ports():
    '''Use only once, to automaticaly add all uplinks, where
    default gateway mac-address is listed.
    '''

    gateway_mac = '00:25:90:69:ED:EA'

    switches_query(gateway_mac)
    db.setdata(data_dic=IP_PORT_DICT, data='uplink')


def switches_query(mac=None):
    '''Queryies database for all switches, then parses
    all of them.
    '''

    switch_list = get_switches()
    if not mac:
        decimal_mac = hex_to_decimal(sys.argv[1])
    else:
        decimal_mac = hex_to_decimal(mac)
    threads = []
    for ip in switch_list:
        t = Thread(target=get_port, args=(ip, decimal_mac))
        threads.append(t)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def main():
    parser = argparse.ArgumentParser(description='''
        Search switch and port number, where given MAC-address is connected.
                                     ''')
    parser.add_argument('mac', metavar='MAC-address', type=str,
                        help='mac address to search for')
    parser.add_argument('-u', action="store_true", 
                        help='set this to see all ports, where given mac is listed')
    args = parser.parse_args()

    # uncomment this to add uplinks to database!
    # add_uplink_ports()
    if args.u:
        global SHOW_UPLINKS
        SHOW_UPLINKS = True
    switches_query(args.mac)


if __name__ == '__main__':
    main()
