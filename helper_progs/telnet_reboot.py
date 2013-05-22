#! /usr/bin/python3
'''Program for rebooting switches in LAN via telnet. Login data 
   is stored in 'secure.py' file, ip and device id are stored in
   database.'''

import telnetlib
import secure
import database_con as db
import ssh_reboot


TIMEOUT = 5
DEBUG = True # be carefull!!! This prints out username/password to console


def reboot_cisco(ip, sw_id):
    password = secure.pass_chooser(sw_id)

    try:
        tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
        tn.read_until(b"Username: ")
        tn.write(b"admin\r\n")
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\n")
        tn.write(b"reload\n")
        tn.write(b"\n")
        debug_info = tn.read_all().decode('ascii')
        print(debug_info)
        tn.close()
    except Exception as e:
        print("Error: ", e)

def reboot_snr(ip, sw_id):
    '''Function for rebooting SNR devicec via telnet. Takes an ip and
    device_id as argument, login/pass imports from secure.py.'''

    password = secure.pass_chooser(sw_id)

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

    password = secure.pass_chooser(sw_id)

    try:
        tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
        tn.read_until(b"Login: ")
        tn.write(secure.user.encode('ascii') + b"\r\n")
        tn.read_until(b"Password: ")
        tn.write(password.encode('ascii') + b"\r\n")
        tn.write(b"\r\n")   # in case of some alerts, to pass them
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

    password = secure.pass_chooser(sw_id)

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
            if row[2] in (5,4,7) and row[4] > 1209600:    # looking for 'SNR' devices
                try:
                    ssh_reboot.ssh_reboot(row[0], row[3], DEBUG=DEBUG) # trying to reboot with ssh
                except Exception as e:
                    if DEBUG:
                        print("{} reported error: {}".format(row[0], e))
                    # if exception, trying ssh_reboot with new password
                    try:
                        ssh_reboot.ssh_reboot(row[0], row[3],
                                              password=secure.ssh_password,
                                              DEBUG=DEBUG) 
                    except Exception as e:
                        if DEBUG:
                            print("{} reported another error: {}".format(row[0], e))
            elif row[2] == 2 and row[4] > 1209600:      # looking for '3com'
                reboot_3com(row[0], row[3])
            elif row[2] == 1 and row[4] > 1209600:      # looking for 'Allied'
                reboot_telesyn(row[0], row[3])
            elif row[2] == 3 and row[4] > 1209600:      # looking for 'Cisco'
                reboot_cisco(row[0], row[3])

if __name__=='__main__':
    reg_reboot()
