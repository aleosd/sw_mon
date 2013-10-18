#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import subprocess
from pysnmp.entity.rfc3413.oneliner import cmdgen
import pysnmp
import unittest

import secure
import snmp_oids


class Snmp():
    def __init__(self, ip_addr=None):
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
        if result:
            return result
        else:
            return None

    def asyn_snmpget(self, swl, oid):
        """Method mostly copy-pasted from official pysnmp web-page:
        http://pysnmp.sourceforge.net/docs/current/apps/async-command-generator.html
        """

        logging.debug("Starting syncronous snmpget call")
        result_dict = {}

        def cbFun(sendRequestHandle, errorIndication, errorStatus, errorIndex, varBinds, cbCtx):
            if errorIndication or errorStatus:
                result_dict[sendRequestHandle]['uptime'] = None
                return

            for oid, val in varBinds:
                result_dict[sendRequestHandle]['uptime'] = val

        cmdGen  = cmdgen.AsynCommandGenerator()

        for sw in swl:
            rhv = cmdGen.getCmd(
                cmdgen.CommunityData('my-manager', 'public', 0),
                cmdgen.UdpTransportTarget((sw.ip_addr, 161)),
                (oid,),
                (cbFun, None)
            )
            result_dict[rhv] = {}
            result_dict[rhv]['id'] = sw.id_

        cmdGen.snmpEngine.transportDispatcher.runDispatcher()
        return result_dict


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


if __name__ == '__main__':
    unittest.main()
