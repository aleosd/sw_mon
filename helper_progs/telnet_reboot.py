#! /usr/bin/python3

import telnetlib
import secure
import switch_ping


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

    if sw_id < 2000000:             # choosing proper password
        password = secure.mzv_pass
    else:
        password = secure.vkz_pass

    tn = telnetlib.Telnet(ip, timeout=5)
    tn.read_until(b"login:")
    tn.write(b"admin\r\n")
    tn.read_until(b"Password:")
    tn.write(password.encode('ascii') + b"\r\n")
    tn.write(b"reload\r\n")
    tn.read_until(b"Process with reboot? [Y/N] ")
    tn.write(b"Y\r\n")
    # for future check, or history/log records
    # debug_info = tn.read_all().decode('ascii')
    tn.close()

def reboot_3com(ip):
    '''Function for reboting 3com devices via telnet. Takes ip addres
    as argument, user/pass imports from secure.py'''

    tn = telnetlib.Telnet(ip, timeout=5)
    tn.read_until(b"Login: ")
    tn.write(secure.user.encode('ascii') + b"\r\n")
    tn.read_until(b"Password: ")
    tn.write(secure.mzv_pass.encode('ascii') + b"\r\n")
    tn.write(b"system\r\n")
    tn.write(b"control\r\n")
    tn.write(b"reboot\r\n")
    tn.write(b"yes\r\n")
    # for future success chek, or history/log records
    # print(tn.read_all().decode('ascii'))
    tn.close()


def reg_reboot():
    data_list = switch_ping.fetchdata()
    for row in data_list:
        if row[2] in (5,4) and row[4] > 1209600:    # looking for 'SNR' devices
            reboot_snr(row[0], row[3])              # rebooting them

if __name__=='__main__':
    reg_reboot()
