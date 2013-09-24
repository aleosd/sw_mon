import sys
import os
import socket
import libssh2
import termios
import tty
import telnetlib


class Connection():
    def __init__(self, ip_addr):
        self.ip_addr = ip_addr
        self.TIMEOUT = 5


class TelnetConnection(Connection):
    def connect(self):
        tn = telnetlib.Telnet(self.ip_addr, timeout=self.TIMEOUT)
        print(self.ip_addr)
        return tn


class SSHConnection(Connection):
    def connect(self):
        '''(ipaddress, switch_id, password, DEBUG) -> function
       
        Function for rebooting switches via ssh. 
        SNR-S2940-8G, SNR-S2940-24G and SNR-S2940-48G.

        '''

        # Create and connect a new socket.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            sock.connect((self.ip_addr, 22))
        except Exception as e:
            print('Error while connecting to {}, {}'.format(self.ip_addr, e)) 
            sys.exit(1)
        TTY = os.isatty(sys.stdin.fileno())
                 
        # Create a new SSH session using that socket and login
        # using basic password authentication.
        print('Connecting to {}...'.format(self.ip_addr))

        def channel_maker(user, password):
            session = libssh2.Session()
            session.startup(sock)
            session.userauth_password(user, password)
             
            # Put the session into non-blocking mode.
            channel = session.channel()
            channel.request_pty('vt100')
            channel.shell()
            session.blocking = False
            if TTY:
                attrs = termios.tcgetattr(sys.stdin)
            else:
                attrs = sys.stdin.readline().rstrip()
            try:
                # Put terminal attached to stdin into raw mode.
                if TTY:
                    tty.setraw(sys.stdin)
                return channel, sock
            except Exception as e:
                print('Error getting channel: {}'.format(e))

        return channel_maker
