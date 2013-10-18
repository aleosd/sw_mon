import sys
import os
import socket
try:
    import libssh2
except ImportError:
    from . import libssh2
import termios
import tty
import telnetlib
import logging


class Connection():
    def __init__(self, ip_addr):
        self.ip_addr = ip_addr
        self.TIMEOUT = 10


class TelnetConnection(Connection):
    def connect(self):
        tn = telnetlib.Telnet(self.ip_addr, timeout=self.TIMEOUT)
        return tn


class SSHConnection(Connection):
    def __init__(self, ip_addr):
        super(SSHConnection, self).__init__(ip_addr)
        self.socket = None
        self.attrs = None
        self.channel = None
        self.TTY = None

    def connect(self):
        '''(Connection) -> function
       
        Function for connecting to switches via ssh.
        SNR-S2940-8G, SNR-S2940-24G and SNR-S2940-48G.
        '''

        # Create and connect a new socket.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3)
        try:
            self.sock.connect((self.ip_addr, 22))
        except Exception as e:
            logging.error('Error while connecting to {}, {}'.format(self.ip_addr, e))
            sys.exit(1)
        self.TTY = os.isatty(sys.stdin.fileno())
                 
        # Create a new SSH session using that socket and login
        # using basic password authentication.
        logging.info('Connecting to {}...'.format(self.ip_addr))

        def channel_maker(user, password):
            session = libssh2.Session()
            session.startup(self.sock)
            session.userauth_password(user, password)
             
            # Put the session into non-blocking mode.
            self.channel = session.channel()
            self.channel.request_pty('vt100')
            self.channel.shell()
            session.blocking = True
            if self.TTY:
                self.attrs = termios.tcgetattr(sys.stdin)
            else:
                self.attrs = sys.stdin.readline().rstrip()
            try:
                # Put terminal attached to stdin into raw mode.
                if self.TTY:
                    tty.setraw(sys.stdin)
                return self.channel
            except Exception as e:
                logging.error('Error getting channel: {}'.format(e))
        return channel_maker

    def close(self):
        self.sock.close()
        if self.TTY:
            # reset terminal (console) to it's basic state
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.attrs)

    def read_until(self, word):
        if self.channel == None:
            logging.error('Cannot read on empty channel')
            return None
        raw_data = self.channel.read(1024)
        while not (word in raw_data.decode()):
            raw_data = self.channel.read(1024)
