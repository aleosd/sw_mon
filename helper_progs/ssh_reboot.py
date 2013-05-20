#! /usr/bin/python3


import sys
import socket
import libssh2
import termios
import tty
import secure
import database_con as db


def ssh_reboot(ip, sw_id, password=None, DEBUG=False): # pass args: ip, type, user, passwd
    # Create and connect a new socket.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, 22))
             
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

    attrs = termios.tcgetattr(sys.stdin)
      
    try:
        # Put terminal attached to stdin into raw mode.
        tty.setraw(sys.stdin)
        session.blocking = True

        try:
            channel.write('reload\n'.replace('\n', '\r\n').encode())
            channel.write('Y\n'.replace('\n', '\r\n').encode())
        except Exception:
            print('\n {} Rebooted\n'.format(ip))

    finally:
        # Restore attributes of terminal attached to stdin.
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, attrs)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('{0} usage: {0} <ip_addr>'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(2)

    query = "SELECT sw_id from switches_switch WHERE ip_addr=('{}')".format(str(sys.argv[1]))
    raw_result = db.ex_query(query)
    sw_id = raw_result[0][0]
    
    ssh_reboot(sys.argv[1], sw_id, DEBUG=True)
