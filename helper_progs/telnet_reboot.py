#! /usr/bin/python3
'''Program for rebooting switches in LAN via telnet. Login data 
   is stored in 'secure.py' file, ip and device id are stored in
   database.'''

import sys
import telnetlib
import secure
import database_con as db
import ssh_reboot


TIMEOUT = 5
UPTIME = 1209600
DEBUG = False # be carefull!!! This prints out username/password to console


def telnet_rebooter(func):
    '''Decorator for making telnet-rebooting functions.
    Passed function takes three arguments: ip, password
    and active telnet socket, call to decorated function -
    only two: ip address and sw_id from database.
    '''

    def wrapper(ip, sw_id):
        password = secure.pass_chooser(sw_id)
        try:
            tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
            func(ip, password, tn)
        except Exception as e:
            print('Error while rebooting {}: {}'.format(ip, e))
    return wrapper


@telnet_rebooter
def reboot_cisco(ip, password, tn):
    tn.read_until(b"Username: ")
    tn.write(b"admin\r\n")
    tn.read_until(b"Password: ")
    tn.write(password.encode('ascii') + b"\n")
    tn.write(b"reload\n")
    tn.write(b"\n")
    # debug_info = tn.read_all().decode('ascii')
    # print(debug_info)
    tn.close()


@telnet_rebooter
def reboot_3com(ip, password, tn):
    print('Rebooting 3com')
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
    print(debug_info)
    tn.close()


@telnet_rebooter
def reboot_snr(ip, password, tn):
    tn = telnetlib.Telnet(ip, timeout=TIMEOUT)
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


@telnet_rebooter
def reboot_telesyn(ip, password, tn):
    tn = telnetlib.Telnet(ip, timeout=5)
    tn.read_until(b"login: ")
    tn.write(secure.allied_user.encode('ascii') + b"\n")
    tn.read_until(b"Password: ")
    tn.write(password.encode('ascii') + b"\n")
    tn.write(b"restart reboot\n")
    # debug_info = tn.read_all().decode('ascii')
    tn.close()


def reg_reboot():
    data_list = db.fetchdata()
    for row in data_list:
        # row[2] - switch type, row[4] - uptime
        if row[4]:
            if row[2] in (5,4,7) and row[4] > UPTIME:    # looking for 'SNR' devices
                try:
                    ssh_reboot.ssh_reboot_snr(row[0], row[3], DEBUG=DEBUG) # trying to reboot with ssh
                except Exception as e:
                    if DEBUG:
                        print("{} reported error: {}".format(row[0], e))
                    # if exception, trying ssh_reboot with new password
                    try:
                        ssh_reboot.ssh_reboot_snr(row[0], row[3],
                                              password=secure.ssh_password,
                                              DEBUG=DEBUG) 
                    except Exception as e:
                        if DEBUG:
                            print("{} reported another error: {}".format(row[0], e))
            elif row[2] == 2 and row[4] > UPTIME:      # looking for '3com'
                reboot_3com(row[0], row[3])
            elif row[2] == 1 and row[4] > UPTIME:      # looking for 'Allied'
                reboot_telesyn(row[0], row[3])
            elif row[2] == 3 and row[4] > UPTIME:      # looking for 'Cisco'
                reboot_cisco(row[0], row[3])
            elif row[2] == 8 and row[4] > UPTIME:
                ssh_reboot.ssh_reboot_dlink(row[0], row[3],
                                            password=secure.ssh_password)


if __name__=='__main__':
    if len(sys.argv) == 1:
        reg_reboot()
    elif len(sys.argv) == 2:
        query = """SELECT sw_id, sw_type_id from switches_switch 
                   WHERE ip_addr=('{}')""".format(str(sys.argv[1]))

        raw_result = db.ex_query(query)
        sw_id = raw_result[0][0]
        sw_type = raw_result[0][1]

        type_to_func = {
                1: reboot_telesyn,
                2: reboot_3com,
                3: reboot_cisco,
                5: reboot_snr,    
            }

        try:
            type_to_func[sw_type](sys.argv[1], sw_id)
        except KeyError as e:
            print('No ssh_reboot implemented for switch type id:', e)
        except Exception as e:
            print(e)

    else:
        print('''Usage {}:
                    '{}' to reboot all uptimed switches
                    '{} <ip_address>' to reboot particular switch
              '''.format(sys.argv[0]))
        sys.exit(2)
