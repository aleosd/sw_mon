#! /usr/bin/python3.2

import psycopg2
import datetime
import logging
import sys
import unittest
from threading import Lock
import secure


DBNAME = secure.DBNAME
USER = secure.USER
PASS = secure.PASS
HOST = secure.DB_SERVER

UPTIME = 1209600  # Value in seconds (2 weeks), if greater - switch need to be rebooted
lock = Lock()


class Database():
    def __init__(self, dbname, username, password, host='localhost'):
        self.dbname = dbname
        self.username = username
        self.password = password
        self.host = host

        # table name, to query from, changing to testing table when running tests.
        self.table_name = 'switches_switch'
        self.cursor = None

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
            data = c.fetchall()
        except Exception as e:
            logging.error('Error while executing query: {}'.format(e))
            return None
        finally:
            conn.close()
        return data

    def get_switch_list(self, ip=None, action=None):
        """Function for fetching info from the switches database. If all
        arguments omitted returns list of all switches in table.

        @param ip: ip-address of the switch, to fetch info
        @param action: flag, can take values reboot - fetches switch with
            uptime, greater then 2 weeks; backup - fetches switches with
            enabled backup_conf, ping - fetches enabled switches
        @return: List of Tuple
        """
        if ip:
            query = """SELECT * from {}
                    WHERE ip_addr=('{}')""".format(self.table_name, ip)
            data = self.execute_query(query)
        elif action == 'reboot':
            query = """SELECT * from {}
                    WHERE sw_uptime>('{}') AND sw_enabled""".format(self.table_name, UPTIME)
            data = self.execute_query(query)
        elif action == 'backup':
            query = """SELECT * from {}
                    WHERE sw_backup_conf""".format(self.table_name)
            data = self.execute_query(query)
        elif action == 'ping':
            query = """SELECT * FROM {}
                    WHERE sw_enabled""".format(self.table_name)
            data = self.execute_query(query)
        else:
            query = "SELECT * from {}".format(self.table_name)
            data = self.execute_query(query)
        return data

    def set_query_decorator(method):
        def wrapped_method(self, data_dict):
            conn = self.connect()
            self.cursor = conn.cursor()
            method(self, data_dict)
            self.cursor = None
            conn.commit()
            conn.close()

        return wrapped_method

    @set_query_decorator
    def set_ping(self, data_dict):
        for id_ in data_dict:
            self.cursor.execute("""UPDATE {} SET sw_ping=(%s) WHERE id=(%s)""".format(self.table_name),
                                (data_dict[id_], id_))

    @set_query_decorator
    def set_events(self, data_dict):
        for id_ in data_dict:
            self.cursor.execute("""INSERT INTO switches_event (ev_datetime, ev_type,
                                                               ev_switch_id, ev_event)
                                VALUES (%s, %s, %s, %s)""",
                                (datetime.datetime.now(), data_dict[id_]['ev_type'], id_,
                                 data_dict[id_]['ev_event']))

    @set_query_decorator
    def set_uptime(self, data_dict):
        for id_ in data_dict:
            self.cursor.execute("""UPDATE {} SET sw_uptime=(%s) WHERE id=(%s)""".format(self.table_name),
                                (data_dict[id_], id_))


class TestDatabase(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.CRITICAL)

        self.db = Database(DBNAME, USER, PASS, HOST)
        conn = self.db.connect()
        c = conn.cursor()

        # Creating test table
        c.execute("""CREATE TABLE "switches_switch_test" (
                                  "id" serial NOT NULL PRIMARY KEY,
                                  "ip_addr" inet NOT NULL UNIQUE,
                                  "sw_district" varchar(3) NOT NULL,
                                  "sw_street_id" integer NOT NULL,
                                  "sw_build_num" varchar(4) NOT NULL,
                                  "sw_type_id" integer NOT NULL,
                                  "sw_id" integer NOT NULL UNIQUE,
                                  "sw_enabled" boolean NOT NULL,
                                  "sw_backup_conf" boolean NOT NULL,
                                  "sw_ping" double precision,
                                  "sw_uptime" integer,
                                  "sw_uplink" varchar(200),
                                  "sw_comment" varchar(500),
                                  "sw_device_id" integer);""")

        # Adding disabled switch
        c.execute("""INSERT INTO switches_switch_test VALUES (
                        1, '192.168.1.1', 'mzv', 1, '26а', 3,
                        100068, FALSE, FALSE, 4.56, 3200, '24,',
                        'com', 2);""")

        # Adding enabled switch with uptime = 1h
        c.execute("""INSERT INTO switches_switch_test VALUES (
                        2, '192.168.1.2', 'vkz', 3, '13', 3,
                        100069, TRUE, TRUE, 4.2, 3600, '24,',
                        'com', 3);""")

        # Adding switch with uptime > 2 weeks
        c.execute("""INSERT INTO switches_switch_test VALUES (
                        3, '192.168.1.3', 'sz', 35, '125', 3,
                        100070, TRUE, TRUE, 0.1, 1209601, '9,',
                        'com', 3);""")

        conn.commit()
        conn.close()

        # Setting table name, which will be used in tests, to test tale
        self.db.table_name = 'switches_switch_test'

    def tearDown(self):
        conn = self.db.connect()
        c = conn.cursor()
        c.execute("""DROP TABLE switches_switch_test;""")
        conn.commit()
        conn.close()

    def test_connect(self):
        self.assertIsNotNone(self.db.connect())

    def test_get_switch_list_all(self):
        all_query_result = self.db.get_switch_list()

        self.assertIsNotNone(all_query_result)
        self.assertEqual(len(all_query_result), 3)
        self.assertTrue('192.168.1.1' in i for i in all_query_result)

    def test_get_switch_list_ip(self):
        ip_query_result = self.db.get_switch_list(ip='192.168.1.1')

        self.assertIsNotNone(ip_query_result)
        self.assertEqual(len(ip_query_result), 1)
        self.assertTrue('192.168.1.1' in i for i in ip_query_result)
        self.assertEqual(len(self.db.get_switch_list(ip='192.168.1.255')), 0)
        self.assertIsNone(self.db.get_switch_list(ip='wrong.ip.address'))

    def test_get_switch_list_reboot(self):
        reboot_query_result = self.db.get_switch_list(action='reboot')

        self.assertIsNotNone(reboot_query_result)
        self.assertEqual(len(reboot_query_result), 1)
        self.assertTrue('192.168.1.3' in i for i in reboot_query_result)

    def test_get_switch_list_backup(self):
        backup_query_result = self.db.get_switch_list(action='backup')

        self.assertIsNotNone(backup_query_result)
        self.assertEqual(len(backup_query_result), 2)
        self.assertTrue('192.168.1.2' in i for i in backup_query_result)

    def test_get_switch_list_ping(self):
        ping_query_result = self.db.get_switch_list(action='ping')

        self.assertIsNotNone(ping_query_result)
        self.assertEqual(len(ping_query_result), 2)
        self.assertTrue('192.168.1.2' in i for i in ping_query_result)

    def test_set_ping(self):
        # checking old ping value
        old_pig = self.db.get_switch_list(ip='192.168.1.3')
        self.assertEqual(old_pig[0][9], 0.1)

        # setting new ping value and checking that it correctly changed
        self.db.set_ping({3: 0.9})
        new_ping = self.db.get_switch_list(ip='192.168.1.3')
        self.assertEqual(new_ping[0][9], 0.9)

    def test_set_uptime(self):
        # checking old uptime value
        old_uptime = self.db.get_switch_list(ip='192.168.1.2')[0][10]
        self.assertEqual(old_uptime, 3600)

        # setting new uptime value and checking that it correctly changed
        self.db.set_uptime({2: 3700})
        new_uptime = self.db.get_switch_list(ip='192.168.1.2')[0][10]
        self.assertEqual(new_uptime, 3700)


if __name__ == '__main__':
    unittest.main()
