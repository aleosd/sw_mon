#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import subprocess
import datetime
from pysnmp.entity.rfc3413.oneliner import cmdgen
import pysnmp
import snmp_oids
import unittest

import secure


class Snmp():
    def __init__(self, ip_addr):
        self.ip_addr = ip_addr

    def snmpget(self, oid):
        cg = cmdgen.CommandGenerator()
        comm_data = cmdgen.CommunityData('my-manager', 'public', 0)
        transport = cmdgen.UdpTransportTarget((self.ip_addr, 161))
        err_indication, err_status, err_index, result = cg.getCmd(comm_data, transport, oid)

        if err_indication:
            logging.error('Error while snmp query from {}: {}'.format(self.ip_addr, err_indication))
            return None
        else:
            if err_status:
                logging.error('{} at {}'.format(err_status.prettyPrint(),
                                                err_indication and result[int(err_indication)-1] or '?'))
                return None
        return result

    def sys_snmpget(self, oid):
        p = subprocess.Popen(['snmpwalk', '-v', '1', '-c', 'public', '-On',
                             self.ip_addr, oid],
                             stdout = subprocess.PIPE)
        result = p.communicate()
        print(result)
        return 0

    def snmpget_test(self, oid):
        cg = cmdgen.CommandGenerator()
        comm_data = cmdgen.CommunityData('public')
        transport = cmdgen.UdpTransportTarget((self.ip_addr, 161))
        err_indication, err_status, err_index, result = cg.getCmd(comm_data, transport, oid)

        if err_indication:
            logging.error('Error while snmp query from {}: {}'.format(self.ip_addr, err_indication))
            return None
        else:
            if err_status:
                logging.error('{} at {}'.format(err_status.prettyPrint(),
                                                err_indication and result[int(err_indication)-1] or '?'))
                return None
        return result



class TestSnmp(unittest.TestCase):
    def setUp(self):
        self.snmp_test = Snmp('10.1.10.8')
        self.snmp_test_unk = Snmp('10.1.0.6')
        self.snmp_test_fail = Snmp('1.1.1.1')
        self.snmp_test_bgp = Snmp(secure.BGP_SERVER)

    def test_snmpget(self):
        raw_uptime = self.snmp_test.snmpget(snmp_oids.UPTIME)
        self.assertIsNotNone(raw_uptime)
        self.assertIsInstance(raw_uptime[0][1], pysnmp.proto.rfc1902.TimeTicks)
        self.assertIsNone(self.snmp_test_fail.snmpget(snmp_oids.UPTIME))
        self.assertIsNotNone(self.snmp_test_bgp.snmpget(snmp_oids.UPTIME))

    def test_sys_snmpget(self):
        raw_uptime = self.snmp_test.sys_snmpget(snmp_oids.UPTIME)
        self.assertIsNotNone(raw_uptime)

if __name__ == '__main__':
    unittest.main()
