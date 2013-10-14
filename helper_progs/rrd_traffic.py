#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os.path
import sys
import datetime
import time

import secure
import rrdtool
import switch
import snmp_oids

FILE_PATH = secure.RRDTRAF_FILE_PATH
FILE_NAME = secure.RRDTRAF_FILE_NAME
GRAPH_NAME = secure.RRDTRAF_GRAPH_NAME


def initialize():
    if os.path.isfile(FILE_PATH + FILE_NAME):
        logging.warning('The file is already exists, cannot overwrite!')
        sys.exit(1)

    logging.info('Initializing rrd database')
    rrdtool.create(FILE_PATH + FILE_NAME, '--step', '300',
                   'DS:traffic_total_in:COUNTER:600:U:U',
                   'DS:traffic_total_out:COUNTER:600:U:U',
                   'DS:traffic_megafon_in:COUNTER:600:U:U',
                   'DS:traffic_megafon_out:COUNTER:600:U:U',
                   'DS:traffic_ttk_in:COUNTER:600:U:U',
                   'DS:traffic_ttk_out:COUNTER:600:U:U',
                   'DS:traffic_rtk_in:COUNTER:600:U:U',
                   'DS:traffci_rtk_out:COUNTER:600:U:U',
                   'RRA:AVERAGE:0.5:1:288',    # one day of 5 min averages
                   'RRA:AVERAGE:0.5:6:336',    # one week of 30 min averages
                   'RRA:AVERAGE:0.5:24:732',   # two month of 2 hours averages
                   'RRA:AVERAGE:0.5:144:730',  # one year of 12 hours averages
                   )
    logging.info('RRD database successfully initialized')


def update():
    logging.info('Updating database')
    bgp_gateway = switch.Host(secure.BGP_SERVER)

    # 4 port - TTK
    # 5 port - Megafon
    # 6 port - RTK
    port_data = {4: {}, 5: {}, 6: {}}
    total_in = 0
    total_out = 0

    for port in port_data:
        in_bytes = int(bgp_gateway.snmpget(snmp_oids.IN_BYTES + str(port))[0][1])
        out_bytes = int(bgp_gateway.snmpget(snmp_oids.OUT_BYTES + str(port))[0][1])
        port_data[port]['in_bytes'] = in_bytes
        port_data[port]['out_bytes'] = out_bytes
        total_in += in_bytes
        total_out += out_bytes

    rrdtool.update(FILE_PATH + FILE_NAME, 'N:{}:{}:{}:{}:{}:{}:{}:{}'.format(
        total_in, total_out,
        port_data[5]['in_bytes'], port_data[5]['out_bytes'],
        port_data[4]['in_bytes'], port_data[4]['out_bytes'],
        port_data[6]['in_bytes'], port_data[6]['out_bytes']))


def graph():
    pass


def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s:%(levelname)s:%(message)s')
    parser = argparse.ArgumentParser(description='Script for rrd_ping database manipulation')
    parser.add_argument('-i', '--initialize', action='store_true',
                        help='Initialize database')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update database')
    parser.add_argument('-g', '--graph', action='store_true',
                        help='Draw graph')
    args = parser.parse_args()

    if args.initialize:
        initialize()
    elif args.update:
        update()
    elif args.graph:
        graph()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
