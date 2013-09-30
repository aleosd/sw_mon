import re
import logging
import subprocess
import time
import datetime
import Connection
import secure
import unittest
import sys


class Switch():
    """
    Basic class for switch representation. On initialization takes n
    arguments:
        id_ - unique number in database, 'id';
        ip_addr - ip address of this switch;
        sw_district - location;
        sw_id - universal id for dividing switches on districts;
        sw_enabled - enabled for checking;
        sw_ping - data form last ping test, float;
        sw_backup_conf - enabled for configuration backup;
        sw_uptime - uptime of the switch, in seconds;
        username, password - data for making telnet or ssh connections;
        sw_type_id - id of the switch type, used for proper reboot command;
    """

    def __init__(self, id_, ip_addr, sw_district, sw_id, sw_enabled, sw_ping,
                 sw_backup_conf, sw_uptime, sw_type_id):
        self.id_ = id_
        self.ip_addr = ip_addr
        self.sw_district = sw_district
        self.sw_id = sw_id
        self.sw_enabled = sw_enabled
        self.sw_ping = sw_ping
        self.sw_backup_conf = sw_backup_conf
        self.sw_uptime = sw_uptime
        self.sw_type_id = sw_type_id
        self.username = secure.user
        self.password = self.pass_chooser()

    def isalive(self):
        p = subprocess.Popen(["fping", self.ip_addr],stdout=subprocess.PIPE)
        result = p.communicate()
        logging.debug("The raw result is: {}".format(result))
        result = result[0].decode()
        if result:
            alive = re.search('alive', result)
            if alive:
                return True

    def ping(self):
        p = subprocess.Popen(["ping", "-c", "3", "-i", "0.2", self.ip_addr], stdout=subprocess.PIPE)
        result = p.communicate()
        result = result[0].decode()
        if result:
            m2 = re.search('rtt min/avg/max/mdev = (.*) ms', result)
            if m2:
                avgtime = m2.group(1).split('/')[1]
                return float(avgtime)
        else:
            return None

    def reboot(self):
        print('Function must be implemented in subclasses')

    def backup(self):
        print('function must be implemented in subclasses')

    def __str__(self):
        return """
                The switch id {},
                IP-address: {},
                Cheking is enabled: {},
                Backup is enabled: {},
                Ping: {} ms,
                Uptime: {};
                Username: {}.
                Password: {}.
               """.format(str(self.sw_id), self.ip_addr, str(self.sw_enabled),
                          str(self.sw_backup_conf), str(self.sw_ping),
                          str(self.sw_uptime), self.username, self.password)

    def pass_chooser(self):
        if self.sw_id < 2000000:             # choosing proper password
            password = secure.mzv_pass
        else:
            password = secure.vkz_pass
        return password

    def make_uptime(self):
        if self.sw_uptime:
            return str(datetime.timedelta(seconds=self.sw_uptime))
        return 'Unknown'


class SNR(Switch):
    def reboot(self):
        logging.info('Starting reboot for SNR {}'.format(self.ip_addr))
        conn = Connection.SSHConnection(self.ip_addr)
        sh = conn.connect()
        channel, sock, attrs = sh(self.username, self.password)
        channel.write('reload\r\n'.encode())
        channel.write('Y\r\n'.encode())
        sock.close()


class Allied(Switch):
    def __init__(self, *args, **kw):
        super(Allied, self).__init__(*args, **kw)
        self.username = secure.allied_user

    def login(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"login: ")
        tn.write(secure.allied_user.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\n")
        return tn
 
    def reboot(self):
        logging.info('Started reboot for L3 Allied {}'.format(self.ip_addr))
        tn = self.login()
        tn.write(b"restart reboot\n")
        debug_info = tn.read_all().decode('ascii')
        logging.debug(debug_info)
        tn.close()

    def backup(self):
        logging.info('Started backup for Allied {}'.format(self.ip_addr))
        tn = self.login()
        command = "upload server=10.1.7.204 file=boot.cfg method=tftp destfile={}.cfg\n".format(self.sw_id)
        tn.write(command.encode('ascii'))
        tn.close()


class DLink(Switch):
    def login(self):
        conn = Connection.SSHConnection(self.ip_addr)
        sh = conn.connect()
        channel, sock = sh(self.username, self.password)
        return channel, sock

    def reboot(self):
        logging.debug('Starting reboot for DLink {}'.format(self.ip_addr))
        channel, sock = self.login() 
        channel.write('reboot\r\n'.encode())
        time.sleep(1)
        channel.write('y\r\n'.encode())
        sock.close()


class Com3(Switch):
    def login(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"Login: ")
        tn.write(secure.user.encode('ascii') + b"\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\r\n")
        tn.write(b"\r\n") # in case of some alerts, to pass them
        return tn

    def reboot(self):
        logging.info('Starting reboot for 3Com {}'.format(self.ip_addr))
        tn = self.login()
        tn.write(b"system\r\n")
        tn.write(b"control\r\n")
        tn.write(b"reboot\r\n")
        time.sleep(1)
        tn.write(b"yes\r\n")
        try:
            debug_info = tn.read_all().decode('ascii')
            logging.debug(debug_info)
        except Exception as e:
            logging.warning('Error while reading info from {}: {}'.format(self.ip_addr, e))
        finally:
            tn.close()
            logging.info('Rebooted 3com, ip: {}'.format(self.ip_addr))

    def backup(self):
        logging.info('Starting backup for 3com {}'.format(self.ip_addr))
        tn = self.login()
        tn.write(b"system\r\n")
        tn.write(b"backupConfig\r\n")
        tn.write(b"save\r\n")
        time.sleep(1)
        tn.write(b"10.1.7.204\r\n")
        tn.write(str(self.sw_id).encode('ascii') + b".cfg\r\n")
        time.sleep(1)
        tn.write(b"\r\n")
        tn.read_until(b"Select menu option (system/backupConfig): ")
        time.sleep(1)
        debug_info = tn.read_all().decode('ascii')
        logging.debug(debug_info)
        tn.close()


class Cisco(Switch):
    def reboot(self):
        logging.info('Starting reboot for Cisco {}'.format(self.ip_addr))
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"Username: ")
        tn.write(b"admin\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\n")
        tn.write(b"reload\n")
        tn.write(b"\n")
        debug_info = tn.read_all().decode('ascii')
        logging.debug(debug_info)
        tn.close()


class AlliedL2(Switch):
    def reboot(self):
        print('To be implemented')

    def backup(self):
        print('Implement later')

class Unmanaged(Switch):
    def __init__(self, *args, **kw):
        self.sw_enabled = False

    def __str__(self):
        return 'The switch is unmanaged, cannot operate it.'

class TestSwitch(unittest.TestCase):

    def setUp(self):
        self.google_dns = Switch(1, "8.8.8.8", 2, 100000, True, 236, False, 592, 2)
        self.error_device = Switch(1, "1.1.1.1", 2, 200000, True, 237, False, None, 2)

    def test_is_alive(self):
        self.assertTrue(self.google_dns.isalive())
        self.assertFalse(self.error_device.isalive())

    def test_ping(self):
        self.assertIsInstance(self.google_dns.ping(), float)
        self.assertIsNone(self.error_device.ping())

    def test_make_uptime(self):
        self.assertEqual(self.google_dns.make_uptime(), "0:09:52")
        self.assertEqual(self.error_device.make_uptime(), "Unknown")

if __name__ == '__main__':
    unittest.main()
