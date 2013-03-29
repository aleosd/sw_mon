#! /usr/bin/python3
'''Program for rebooting switches in LAN via telnet. Login data 
   is stored in 'secure.py' file, ip and device id are stored in
   database.'''

import telnetlib
import secure
import switch_ping
import database_con as db


TIMEOUT = 5

def pass_chooser(sw_id):
    if sw_id < 2000000:             # choosing proper password
        password = secure.mzv_pass
    else:
        password = secure.vkz_pass
    return password



def reboot_cisco(ip):
    tn = telnetlib.Telnet(ip)
    tn.read_until(b"Username: ")
    tn.write(secure.user.encode('ascii') + b"\n")
    tn.read_until(b"Password: ")
    tn.write(secure.mzv_pass.encode('ascii') + b"\n")
    tn.write(b"pwd\n")
    tn.write(b"exit\n")
    print(tn.read_all().decode('ascii'))
    tn.close()

def reboot_snr(ip, sw_id):
    '''Function for rebooting SNR devicec via telnet. Takes an ip and
    device_id as argument, login/pass imports from secure.py.'''

    password = pass_chooser(sw_id)

    try:
        tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
        tn.read_until(b"login:")
        tn.write(b"admin\r\n")
        tn.read_until(b"Password:")
        tn.write(password.encode('ascii') + b"\r\n")
        tn.write(b"reload\r\n")
        tn.read_until(b"Process with reboot? [Y/N] ")
        tn.write(b"Y\r\n")
        # for future check, or history/log records
        debug_info = tn.read_all().decode('ascii')
        tn.close()
    except Exception as e:
        print("Error: {}".format(e))

def reboot_3com(ip, sw_id):
    '''Function for reboting 3com devices via telnet. Takes ip addres
    as argument, user/pass imports from secure.py'''

    password = pass_chooser(sw_id)

    try:
        tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
        tn.read_until(b"Login: ")
        tn.write(secure.user.encode('ascii') + b"\r\n")
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\r\n")
        tn.write(b"system\r\n")
        tn.write(b"control\r\n")
        tn.write(b"reboot\r\n")
        tn.write(b"yes\r\n")
        # for future success chek, or history/log records
        debug_info = tn.read_all().decode('ascii')
        tn.close()
    except Exception as e:
        print("{} reported Error: {}".format(ip, e))

def reboot_telesyn(ip, sw_id):
    '''Function for rebooting allied-telesyn devices via telnet.
    Takes ip addres and switch_id as arguments.'''

    password = pass_chooser(sw_id)

    try:
        tn = telnetlib.Telnet(ip, timeout=5)
        tn.read_until(b"login: ")
        tn.write(secure.allied_user.encode('ascii') + b"\n")
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\n")
        tn.write(b"restart reboot\n")
        debug_info = tn.read_all().decode('ascii')
        tn.close()
    except Exception as e:
        print("{} reported Error: {}".format(ip, e))


def reg_reboot():
    data_list = db.fetchdata()
    for row in data_list:
        # row[2] - switch type, row[4] - uptime
        if row[4]:
            if row[2] in (5,4) and row[4] > 1209600:    # looking for 'SNR' devices
                reboot_snr(row[0], row[3])              # rebooting them
            elif row[2] == 2 and row[4] > 1209600:      # looking for '3com'
                print('Rebooting 3com at {}, {}'.format(row[0], row[3]))
                reboot_3com(row[0], row[3])
            elif row[2] == 1 and row[4] > 1209600:      # looking for 'Allied'
                reboot_telesyn(row[0], row[3])

if __name__=='__main__':
    reg_reboot()
