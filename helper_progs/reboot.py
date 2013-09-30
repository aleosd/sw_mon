#! /usr/bin/python3


import sys
import argparse
import logging
import Switch
import database_con as db


UPTIME = 1209600
switch_types = {
    1: Switch.Allied,
    2: Switch.Com3,
    3: Switch.Cisco,
    4: Switch.SNR,
    5: Switch.SNR,
    6: Switch.Unmanaged,  # Passing this case
    7: Switch.SNR,
    8: Switch.DLink,
    9: Switch.SNR,
    10: Switch.AlliedL2,
}


def get_switch_list(ip):
    # fetch all or given by ip switch info from db
    if ip == 'all':
        raw_data = db.fetchdata(all=True)
    else:
        query = """SELECT * from switches_switch
                   WHERE ip_addr=('{}')""".format(ip)
        raw_data = db.ex_query(query)

    if len(raw_data) == 0:
        logging.error('IP-address not found in the database')
        sys.exit(1)

    switch_list = []
    for row in raw_data:
        # fancy names, just for better look
        id_ = int(row[0])
        ip_addr = row[1]
        sw_district = row[2]
        sw_type_id = int(row[5])
        sw_id = row[6]
        sw_enabled = row[7]
        sw_ping = row[8]
        sw_uptime = row[9]
        sw_backup_conf = row[13]
        sw = switch_types[sw_type_id](id_, ip_addr, sw_district, sw_id,
                                      sw_enabled, sw_ping, sw_backup_conf,
                                      sw_uptime, sw_type_id)
        switch_list.append(sw)
    return switch_list


def can_reboot(sw):
    """Switch -> Bool

    Check if switch is alive and allowed to reboot.
    """
    if ((sw.sw_enabled and sw.sw_uptime) and
            sw.sw_ping):
        return True
    logging.warning('The switch cannot be rebooted: {}'.format(sw))
    return False


def can_backup(sw):
    if sw.isalive() and sw.sw_backup_conf:
        return True
    logging.warning('The switch cannot be backuped: {}'.format(sw))
    return False


def reboot(ip):
    logging.debug('Starting global reboot function with ip {}'.format(ip))
    switch_list = get_switch_list(ip)
    for sw in switch_list:
        if ip == 'all':
            if can_reboot(sw) and sw.sw_uptime > UPTIME:
                sw.reboot()
        else:
            if can_reboot(sw):
                sw.reboot()


def backup(ip):
    logging.debug('Starting global backup function with ip {}'.format(ip))
    switch_list = get_switch_list(ip)
    for sw in switch_list:
        if can_backup(sw):
            try:
                logging.debug('Trying backup for ip {}'.format(sw.ip_addr))
                sw.backup()
            except Exception as e:
                logging.error('Error occured: {} from {}'.format(e, sw.ip_addr))
                logging.info(sw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for switch management')

    # setting arguments for command-line args
    # const is used when flag added without parameter
    # default is used when flag is omitted
    parser.add_argument('-r', '--reboot', nargs='?', default=None, const='all',
                        help='Reboot all switches, if no IP specified',
                        metavar='<ip-address>')
    parser.add_argument('-b', '--backup', help='''Backup given by ip switch.
                                     If IP omitted - backup all switches''',
                        metavar='<ip-address>', default=None, const='all',
                        nargs='?')
    parser.add_argument('-l', '--log', help='Set the logging level',
                        metavar='log-level', default='WARNING',
                        const='INFO', nargs='?')
    args = parser.parse_args()

    if args.log:
        lvl = args.log.upper()
        loglevel = getattr(logging, lvl)
        logging.basicConfig(level=loglevel, format='%(asctime)s:%(levelname)s:%(message)s')

    if args.reboot:
        reboot(args.reboot)
    elif args.backup:
        backup(args.backup)
    else:
        parser.print_help()
