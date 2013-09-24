import time
import Connection
import secure


class Switch():
    '''
    Basic class for switch representation. On initialization takes n
    arguments:
        id_ - unic number in database, 'id';
        ip_addr - ip address of this switch;
        sw_district - location;
        sw_id - universal id for dividing switches on districts;
        sw_enabled - enabled for checking;
        sw_ping - data form last ping test, float;
        sw_backup_conf - enabled for configuration backup;
        sw_uptime - uptime of the switch, in seconds;
        username, password - data for makling telnet or ssh connections;
        sw_type_id - id of the switch type, used for proper reboot command;
    '''

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
                Uptime: {} sec;
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


class SNR(Switch):
    def reboot(self):
        conn = Connection.SSHConnection(self.ip_addr)
        sh = conn.connect()
        channel, sock = sh(self.username, self.password)
        channel.write('reload\r\n'.encode())
        channel.write('Y\r\n'.encode())
        sock.close()


class Allied(Switch):
    def __init__(self, *args, **kw):
        super(Allied, self).__init__(*args, **kw)
        self.username = secure.allied_user

    def reboot(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"login: ")
        tn.write(secure.allied_user.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\n")
        tn.write(b"restart reboot\n")
        # debug_info = tn.read_all().decode('ascii')
        tn.close()


class DLink(Switch):
    def reboot(self):
        conn = Connection.SSHConnection(self.ip_addr)
        sh = conn.connect()
        channel, sock = sh(self.username, self.password)
        channel.write('reboot\r\n'.encode())
        time.sleep(1)
        channel.write('y\r\n'.encode())
        sock.close()


class Com3(Switch):
    def reboot(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        print('Rebooting 3com, ip: {}'.format(self.ip_addr))
        tn.read_until(b"Login: ")
        tn.write(secure.user.encode('ascii') + b"\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\r\n")
        tn.write(b"\r\n")   # in case of some alerts, to pass them
        tn.write(b"system\r\n")
        tn.write(b"control\r\n")
        tn.write(b"reboot\r\n")
        time.sleep(1)
        tn.write(b"yes\r\n")
        # for future success chek, or history/log records
        debug_info = tn.read_all().decode('ascii')
        # print(debug_info)
        tn.close()
        print('Rebooted 3com, ip: {}'.format(self.ip_addr))


class Cisco(Switch):
    def reboot(self):
        conn = Connection.TelnetConnection(self.ip_addr)
        tn = conn.connect()
        tn.read_until(b"Username: ")
        tn.write(b"admin\r\n")
        tn.read_until(b"Password: ")
        tn.write(self.password.encode('ascii') + b"\n")
        tn.write(b"reload\n")
        tn.write(b"\n")
        debug_info = tn.read_all().decode('ascii')
        # print(debug_info)
        tn.close()


class Unmanaged(Switch):
    def __init__(self, *args, **kw):
        self.sw_enabled = False

    def __str__(self):
        return 'The switch is unmanaged, cannot operate it.'
