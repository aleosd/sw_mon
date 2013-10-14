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
import Switch
import snmp_oids

FILE_PATH = secure.RRDTRAF_FILE_PATH
FILE_NAME = secure.RRDTRAF_FILE_NAME
GRAPH_NAME = secure.RRDTRAF_GRAPH_NAME


def initialize():
    if os.path.isfile(FILE_PATH + FILE_NAME):
        logging.warning('The file is already exists, cannot overwrite!')
        sys.exit(1)

    logging.info('Initializing rrd database')
    rrdtool.create(FILE_PATH + FILE_NAME,)
    logging.info('RRD database successfully initialized')


def update():
    port_data = {4: {}, 5: {}, 6: {}}
    bgp_gateway = Switch.Host(secure.BGP_SERVER)

    for port in port_data:
        in_bytes = int(bgp_gateway.snmpget(snmp_oids.IN_BYTES + str(port))[0][1])
        out_bytes = int(bgp_gateway.snmpget(snmp_oids.OUT_BYTES + str(port))[0][1])
        port_data[port]['in_bytes'] = in_bytes
        port_data[port]['out_bytes'] = out_bytes

    print(port_data)


def graph():
    pass

if __name__ == '__main__':
    update()
