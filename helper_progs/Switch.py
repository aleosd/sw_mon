import re
import logging
import subprocess
import time
import datetime
import unittest
import Connection
import secure


class Host():
    def __init__(self, ip_addr):
        self.ip_addr = ip_addr

    def ping(self, packet_count = 3):
        """func(int) -> [float, int]

        Method for host ping. Returns list of two items:
        - average round trip time
        - packet loss
        If host is not responding, avg rtt is None.
        """
        global avgtime
        p = subprocess.Popen(["ping", "-c", str(packet_count), "-i", "0.2", self.ip_addr], stdout=subprocess.PIPE)
        result = p.communicate()
        result = result[0].decode()
        pl = None
        avg = None
        if result:
            avg = re.search('rtt min/avg/max/mdev = (.*) ms', result)
            pl = re.search('[0-9]+% packet loss', result)
            if pl:
                pl = int(pl.group(0).split('%')[0])
            if avg:
                avg = float(avg.group(1).split('/')[1])
            return avg, pl

        return avg, pl


# TODO: Add try-except clauses to all network functions
class Switch(Host):
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
        super(Switch, self).__init__(ip_addr)
        self.id_ = id_
        # self.ip_addr = ip_addr
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
        p = subprocess.Popen(["fping", self.ip_addr], stdout=subprocess.PIPE)
        result = p.communicate()
        logging.debug("The raw result is: {}".format(result))
        result = result[0].decode()
        if result:
            alive = re.search('alive', result)
            if alive:
                return True


    def can_backup(self):
        return self.sw_backup_conf and self.isalive()

    def can_reboot(self):
        return self.sw_enabled and self.isalive()

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
                          self.make_uptime(), self.username, self.password)

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
    def pass_chooser(self):
        return secure.ssh_password

    def login(self):
        conn = Connection.SSHConnection(self.ip_addr)
        sh = conn.connect()
        channel = sh(self.username, self.password)
        return channel, conn

    def reboot(self):
        logging.info('Starting reboot for SNR {}'.format(self.ip_addr))
        channel, conn = self.login()
        try:
            channel.write('reload\r\n'.encode())
            channel.write('Y\r\n'.encode())
        except Exception as e:
            logging.error("Error {} while rebooting SNR switch: {}".format(e, self.ip_addr))
        finally:
            conn.close()

    def backup(self):
        logging.info('Starting backup for SNR {}'.format(self.ip_addr))
        channel, conn = self.login()
        logging.debug('Connected to {} with ssh'.format(self.ip_addr))
        command = 'copy running-config tftp://{}/{}.cfg\r\n'.format(secure.TFTP_SERVER, self.sw_id)
        channel.write(command.encode())
        channel.write('Y\r\n'.encode('ascii'))
        # waiting for success message
        raw_data = channel.read(1024)
        i = 0
        while not ('close tftp client' in raw_data.decode()):
            raw_data = channel.read(1024)
            i += 1
            # in case of error, to escape infinite loop
            if i > 10:
                break
        conn.close()


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
        command = "upload server={} file=boot.cfg method=tftp destfile={}.cfg\n".format(secure.TFTP_SERVER, self.sw_id)
        tn.write(command.encode('ascii'))
        tn.close()


class DLink(Switch):
    def pass_chooser(self):
        return secure.ssh_password

    def login(self):
        conn = Connection.SSHConnection(self.ip_addr)
        sh = conn.connect()
        channel = sh(self.username, self.password)
        return channel, conn

    def reboot(self):
        logging.debug('Starting reboot for DLink {}'.format(self.ip_addr))
        channel, conn = self.login()
        try:
            channel.write('reboot\r\n'.encode())
            time.sleep(1)
            channel.write('y\r\n'.encode())
        except Exception as e:
            logging.error('Error while rebooting DLink switch {}: {}'.format(self.ip_addr, e))
        finally:
            conn.close()

    def backup(self):
        logging.info('Starting backup for Dlink switch {}'.format(self.ip_addr))
        channel, conn = self.login()
        try:
            command = 'upload cfg_toTFTP {} dest_file {}.cfg\r\n'.format(secure.TFTP_SERVER, self.sw_id)
            channel.write(command.encode())
            conn.read_until('Success')
            channel.write('logout\r\n'.encode())
        except Exception as e:
            logging.error('Error while backuping DLink switch {}: {}'.format(self.ip_addr, e))
        finally:
            conn.close()

class Com3(Switch):
    def login(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"Login: ")
        tn.write(secure.user.encode('ascii') + b"\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\r\n")
        tn.write(b"\r\n")  # in case of some alerts, to pass them
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
        command = '{}\r\n'.format(secure.TFTP_SERVER)
        tn.write(command)
        tn.write(str(self.sw_id).encode('ascii') + b".cfg\r\n")
        time.sleep(1)
        tn.write(b"\r\n")
        tn.read_until(b"Select menu option (system/backupConfig): ")
        time.sleep(1)
        debug_info = tn.read_all().decode('ascii')
        logging.debug(debug_info)
        tn.close()


class Cisco(Switch):
    def login(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"Username: ")
        tn.write(b"admin\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\n")
        return tn

    def reboot(self):
        logging.info('Starting reboot for Cisco {}'.format(self.ip_addr))
        tn = self.login()
        tn.write(b"reload\n")
        tn.write(b"\n")
        debug_info = tn.read_all().decode('ascii')
        logging.debug(debug_info)
        tn.close()


class AlliedL2(Switch):
    def __init__(self, *args, **kw):
        super(AlliedL2, self).__init__(*args, **kw)
        self.username = secure.allied_user

    def login(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"Login: ")
        tn.write(secure.allied_user.encode('ascii') + b"\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\r\n")
        logging.debug('Successfully logged in to {}'.format(self.ip_addr))
        return tn

    def reboot(self):
        logging.warning("Telnet misfunction on switch, reboot disabled")
        '''
        logging.info("Starting reboot for Allied L2 {}".format(self.ip_addr))
        tn = self.login()
        tn.write(b"C\r\n")
        tn.write(b"restart switch\r\n")
        tn.write(b"Y\r\n")
        tn.close()
        '''

    def backup(self):
        print('Implement later')


class Unmanaged(Switch):
    def __init__(self, *args, **kw):
        self.sw_enabled = False
        self.sw_backup_conf = False

    def __str__(self):
        return 'The switch is unmanaged, cannot operate it.'


class TestSwitch(unittest.TestCase):

    def setUp(self):
        self.google_dns = Switch(1, "8.8.8.8", 2, 100000, True, 236, True, 592, 2)
        self.error_device = Switch(1, "1.1.1.1", 2, 200000, False, 237, False, None, 2)

    def test_is_alive(self):
        self.assertTrue(self.google_dns.isalive())
        self.assertFalse(self.error_device.isalive())

    def test_ping(self):
        self.assertIsInstance(self.google_dns.ping()[0], float)
        self.assertIsInstance(self.google_dns.ping()[1], int)
        self.assertIsNone(self.error_device.ping()[0])
        self.assertEqual(self.error_device.ping()[1], 100)

    def test_make_uptime(self):
        self.assertEqual(self.google_dns.make_uptime(), "0:09:52")
        self.assertEqual(self.error_device.make_uptime(), "Unknown")

    def test_can_backup(self):
        self.assertTrue(self.google_dns.can_backup())
        self.assertFalse(self.error_device.can_backup())

    def test_can_reboot(self):
        self.assertTrue(self.google_dns.can_reboot())
        self.assertFalse(self.error_device.can_reboot())

if __name__ == '__main__':
    unittest.main()
