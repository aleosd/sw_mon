#! /usr/bin/python3


import argparse
import Switch
import database_con as db


UPTIME = 1209600
switch_types = {
    1: Switch.Allied,
    2: Switch.Com3,
    3: Switch.Cisco,
    4: Switch.SNR,
    5: Switch.SNR,
    6: Switch.Unmanaged, # Passing this case
    7: Switch.SNR,
    8: Switch.DLink,
    9: Switch.SNR,
    10:Switch.AlliedL2,
    }


def get_switch_list():
    raw_data = db.fetchdata(all=True)
    switch_list = []
    for row in raw_data:
        sw = switch_types[int(row[5])](row[0], row[1], row[2], row[6],
                                       row[7], row[8], row[13],
                                       row[9], row[5])
        switch_list.append(sw)
    return switch_list

def can_reboot(sw):
    if ((sw.sw_enabled and sw.sw_uptime) and
        sw.sw_ping):
        return True
    return False

def can_backup(sw):
    if can_reboot(sw) and sw.sw_backup_conf:
        return True
    return False

def reboot(ip):
    switch_list = get_switch_list()
    for sw in switch_list:
        if ip == 'all':
            if can_reboot(sw) and sw.sw_uptime > UPTIME:
                sw.reboot()
        else:
            if can_reboot(sw) and sw.ip_addr == ip:
                sw.reboot()
            else:
                print('The switch is dasabled or not responding')

def backup(ip):
    print('calling backup with ip {}'.format(ip))
    switch_list = get_switch_list()
    for sw in switch_list:
        if ip == 'all':
            if can_backup(sw):
                try:
                    sw.backup()
                except Exception as e:
                    print('Error occured: {}'.format(e))
                    print(sw)
        else:
            if can_backup(sw) and sw.ip_addr == ip:
                print('switch found')
                try:
                    print('Starting backup for {}'.format(ip))
                    sw.backup()
                except Exception as e:
                    print('Error occured: {}'.format(e))
                    print(sw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for switch management')
    parser.add_argument('-r', '--reboot', nargs='?', default=None, const='all',
                        help='Reboot all switches, if no IP specified',
                        metavar='<ip-address>')
    parser.add_argument('-b', '--backup', help='''Backup given by ip switch.
                                     If IP omitted - backup all switches''',
                        metavar='<ip-address>', default=None, const='all',
                        nargs='?')
    args = parser.parse_args()

    if args.reboot:
        reboot(args.reboot)
    elif args.backup:
        print('backuping {}'.format(args.backup))
        backup(args.backup)
    else:
        parser.print_help()
