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
    port_nums = {4: None, 5: None, 6: None}
    bgp_gateway = Switch.Host(secure.BGP_SERVER)
    for port in port_nums:
        in_bytes = bgp_gateway.snmpget(snmp_oids.IN_BYTES + str(port))
        out_bytes = bgp_gateway.snmpget(snmp_oids.OUT_BYTES + str(port))
        print(in_bytes, out_bytes)

def graph():
    pass

if __name__ == '__main__':
    update()
