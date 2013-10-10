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


def initialize():
    pass

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
