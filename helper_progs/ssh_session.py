#! /usr/bin/python3.2


import getpass
import sys
import socket
import select
import libssh2
import termios
import tty

if len(sys.argv) != 2:
    print("Usage: ssh_session.py <ip>")
    sys.exit(1)
else:
    ip = sys.argv[1]

# Create and connect a new socket.
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
try:
    sock.connect((ip, 22))
             
    # Create a new SSH session using that socket and login
    # using basic password authentication.
    session = libssh2.Session()
    session.startup(sock)
    user = input("Enter username: ")
    password = getpass.getpass(prompt="Password: ")
    session.userauth_password(user, password)
except Exception as e:
    print("Error:", e)
    sys.exit(1)
 
# Put the session into non-blocking mode.
 
channel = session.channel()
channel.request_pty('vt100')
channel.shell()
session.blocking = False

attrs = termios.tcgetattr(sys.stdin)
  
try:
    # Put terminal attached to stdin into raw mode.
    tty.setraw(sys.stdin)
               
    # Forward data from the channel to stdout and data from
    # stdin to the channel, until an EOF request is received.
    while not channel.eof:
        session.blocking = True
        rlist, wlist, xlist = select.select([sock, sys.stdin], [], [], 0.1)
                             
        if sock in rlist:
            data = channel.read(1024)
                                                                 
            if data is None:
                break
                                                         
            sys.stdout.write(data.decode('utf-8'))
            sys.stdout.flush()
                                                                                                                       
        if sys.stdin in rlist:
            data = sys.stdin.read(1)
            try:
                data = "".join(i for i in data if ord(i) < 128)
                data = data.replace('\n', '\r\n').encode()
            except Exception as e:
                print('Error: ', e) 
            channel.write(data)

finally:
    # Restore attributes of terminal attached to stdin.
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, attrs)
