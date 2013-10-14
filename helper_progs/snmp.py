#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging

from pysnmp.entity.rfc3413.oneliner import cmdgen
import pysnmp
import snmp_oids
import unittest


class Snmp():
    def __init__(self, ip_addr):
        self.ip_addr = ip_addr

    def snmpget(self, oid):
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
        self.snmp_test_fail = Snmp('1.1.1.1')

    def test_snmpget(self):
        raw_uptime = self.snmp_test.snmpget(snmp_oids.UPTIME)
        self.assertIsNotNone(raw_uptime)
        self.assertIsInstance(raw_uptime[0][1], pysnmp.proto.rfc1902.TimeTicks)
        self.assertIsNone(self.snmp_test_fail.snmpget(snmp_oids.UPTIME))


if __name__ == '__main__':
    unittest.main()