#! /usr/bin/python3

import sys
import os
import time
import socket
import libssh2
import termios
import tty
import secure
import database_con as db


def ssh_rebooter(reboot_function):
    '''(function) -> (function)
    Decorator for making individual reboot functions, for
    different switches.

    reboot_function must take 'channel' as arg, and make 'channel.write(data)'
    calls to make reboot of switch.
    '''

    def wrapper(ip, sw_id, password=None, DEBUG=False):
        '''(ipaddress, switch_id, password, DEBUG) -> function
       
        Function wrapper for rebooting switches via ssh. 
        SNR-S2940-8G, SNR-S2940-24G and SNR-S2940-48G.

        '''

        # Create and connect a new socket.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            sock.connect((ip, 22))
        except Exception as e:
            print('Error while connecting to {}, {}'.format(ip, e)) 
            sys.exit(1)
        TTY = os.isatty(sys.stdin.fileno())
                 
        # Create a new SSH session using that socket and login
        # using basic password authentication.
        print('Connecting to {}...'.format(ip))
        if not password:
            password = secure.pass_chooser(sw_id)
        user = secure.user
        if DEBUG:
            print('Using username', user)
            print('Using password', password)
        session = libssh2.Session()
        session.startup(sock)
        session.userauth_password(user, password)
         
        # Put the session into non-blocking mode.
        channel = session.channel()
        channel.request_pty('vt100')
        channel.shell()
        session.blocking = False

        if DEBUG:
            print('Getting attrs from stdin')

        if TTY:
            attrs = termios.tcgetattr(sys.stdin)
        else:
            attrs = sys.stdin.readline().rstrip()
        try:
            # Put terminal attached to stdin into raw mode.
            if TTY:
                tty.setraw(sys.stdin)
            try:
                # session.blocking = True
                reboot_function(channel)
            except Exception as e:
                print('\n {} reported\n'.format(ip, e))
        finally:
            # Restore attributes of terminal attached to stdin.
            sock.close()
            if TTY:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, attrs)

    return wrapper


@ssh_rebooter
def ssh_reboot_dlink(channel):
    '''Function for rebooting dlink switches with ssh.
    Used with decorator, calling this func with channel arg.

    Tested with D-Link DES-3200-28F
    '''

    channel.write('reboot\r\n'.encode())
    time.sleep(1)
    channel.write('y\r\n'.encode())


@ssh_rebooter
def ssh_reboot_snr(channel):
    '''Function for rebooting dlink switches with ssh.
    Used with decorator, calling this func with channel arg.

    Tested with SNR-S2940-8G
    '''
    channel.write('reload\r\n'.encode())
    channel.write('Y\r\n'.encode())


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('{0} usage: {0} <ip_addr>'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)

    query = """SELECT sw_id, sw_type_id from switches_switch 
               WHERE ip_addr=('{}')""".format(str(sys.argv[1]))

    raw_result = db.ex_query(query)
    sw_id = raw_result[0][0]
    sw_type = raw_result[0][1]

    type_to_func = {
        5: ssh_reboot_snr,
        4: ssh_reboot_snr,
        7: ssh_reboot_snr,
        8: ssh_reboot_dlink,    
    }

    try:
        type_to_func[sw_type](sys.argv[1], sw_id, password=secure.ssh_password,
                              DEBUG=True)
    except KeyError as e:
        print('No ssh_reboot implemented for switch type id:', e)
    except Exception as e:
        print(e)
