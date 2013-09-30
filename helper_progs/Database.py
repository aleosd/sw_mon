#! /usr/bin/python3.2

import psycopg2
import datetime
import logging
import sys
import unittest
import secure


DBNAME = secure.DBNAME
USER = secure.USER
PASS = secure.PASS
HOST = '10.1.7.204'

UPTIME = 1209600

class Database():
    def __init__(self, dbname, username, password, host='localhost'):
        self.dbname = dbname
        self.username = username
        self.password = password
        self.host = host

    def connect(self):
        try:
            conn = psycopg2.connect(database=self.dbname,
                                    user=self.username,
                                    password=self.password,
                                    host=self.host)
            return conn
        except Exception as e:
            logging.error('Error while connecting to database: {}'.format(e))
            sys.exit(1)

    def execute_query(self, query):
        """Function for execution custom queries. Takes one parameter - query.
        Returns result in tuple
        """
        conn = self.connect()
        c = conn.cursor()
        try:
            c.execute(query)
        except Exception as e:
            logging.error('Error while executing query: {}'.format(e))
            return None
        data = c.fetchall()
        return data

    def get_switch_list(self, ip=None, reboot=False, backup=False):
        """Function for fetching info from the switches database. If all
        arguments omitted returns list of all switches in table.

        @param ip: ip-addres of the switch, to fetch info
        @param reboot: flag, to fetch switches with uptime greater then UPTIME
        @param backup: flag, to fetch switches with enabled backup
        @return: List of Tuples
        """
        if ip:
            query = """SELECT * from switches_switch
                    WHERE ip_addr=('{}')""".format(ip)
            data = self.execute_query(query)
            return data
        elif reboot:
            query = """SELECT * from switches_switch
                    WHERE sw_uptime>('{}') AND sw_enabled""".format(UPTIME)
            data = self.execute_query(query)
            return data
        elif backup:
            query = """SELECT * from switches_switch
                    WHERE sw_backup_conf"""
            data = self.execute_query(query)
            return data
        else:
            query = "SELECT * from switches_switch"
            data = self.execute_query(query)
            return data

    # TODO: data storing to database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(DBNAME, USER, PASS, HOST)

    def test_connect(self):
        self.assertIsNotNone(self.db.connect())

    def test_get_switch_list(self):
        self.assertIsNotNone(self.db.get_switch_list(ip='10.1.0.98'))
        self.assertEqual(len(self.db.get_switch_list(ip='10.1.0.98')), 1)
        self.assertIsNotNone(self.db.get_switch_list(reboot=True))
        self.assertIsNotNone(self.db.get_switch_list(backup=True))
        self.assertIsNotNone(self.db.get_switch_list())

if __name__ == '__main__':
    unittest.main()