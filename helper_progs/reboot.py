#! /usr/bin/python3


import sys
import argparse
import logging
from threading import Thread

try:
    from . import switch
    from . import snmp
    from . import database
    from . import secure
    from . import snmp_oids
except ValueError:
    import switch
    import snmp
    import database
    import secure
    import snmp_oids
    # from timer import Timer


switch_types = {
    1: switch.Allied,
    2: switch.Com3,
    3: switch.Cisco,
    4: switch.SNR,
    5: switch.SNR,
    6: switch.Unmanaged,  # Passing this case
    7: switch.SNR,
    8: switch.DLink,
    9: switch.SNR,
    10: switch.AlliedL2,
}


def get_switch_list(flag):
    # fetch all or given by ip switch info from db
    db = database.Database(secure.DBNAME, secure.USER,
                           secure.PASS, secure.DB_SERVER)
    if flag == 'backup':
        raw_data = db.get_switch_list(action='backup')
    elif flag == 'reboot':
        raw_data = db.get_switch_list(action='reboot')
    elif flag == 'ping':
        raw_data = db.get_switch_list(action='ping')
    else:
        raw_data = db.get_switch_list(ip=flag)

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


def reboot(ip):
    logging.debug('Starting global reboot function with ip {}'.format(ip))
    switch_list = get_switch_list(ip)
    event_dict = {}
    for sw in switch_list:
        if sw.can_reboot():
            event_dict[sw.id_] = {}
            event_dict[sw.id_]['ev_type'] = 'warn'
            try:
                logging.debug('Trying reboot the switch {}'.format(sw.ip_addr))
                sw.reboot()
                event_dict[sw.id_]['ev_event'] = 'Switch is rebooted manually'
            except Exception as e:
                logging.error('Error while rebooting switch {}: {}'.format(sw,
                                                                           e))
                event_dict[sw.id_]['ev_event'] = 'Switch rebooted with errors'
        else:
            logging.warning('The switch cannot be rebooted: {}'.format(sw))

    if len(event_dict) > 0:
        with database.lock:
            logging.debug("Writing reboot events to database.")
            db = database.Database(secure.DBNAME, secure.USER,
                                   secure.PASS, secure.DB_SERVER)
            db.set_events(event_dict)

def ping():
    logging.debug('Starting global ping function')
    switch_list = get_switch_list('ping')
    threads = []
    ping_dict = {}
    event_dict = {}

    def ping_worker(sw):
        avg = sw.ping()[0]
        ping_dict[sw.id_] = avg

        if sw.sw_ping and not avg:
            event_dict[sw.id_] = {}
            event_dict[sw.id_]['ev_type'] = 'err'
            event_dict[sw.id_]['ev_event'] = 'Switch is not responding'
        elif avg and not sw.sw_ping:
            event_dict[sw.id_] = {}
            event_dict[sw.id_]['ev_type'] = 'info'
            event_dict[sw.id_]['ev_event'] = 'Switch is up and running'

    logging.debug('Adding threads')
    for sw in switch_list:
        t = Thread(target=ping_worker, args=(sw,))
        threads.append(t)

    logging.debug('Starting threads')
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    logging.info('Starting database update...')
    logging.debug(ping_dict)

    with database.lock:
        db = database.Database(secure.DBNAME, secure.USER,
                               secure.PASS, secure.DB_SERVER)
        db.set_ping(ping_dict)
        if len(event_dict) > 0:
            db.set_events(event_dict)


def uptime():
    logging.debug('Starting global uptime function')
    switch_list = get_switch_list('ping')
    s = snmp.Snmp()
    result_dict = s.asyn_snmpget(switch_list, snmp_oids.UPTIME)

    uptime_dict = {}
    for send_rh in result_dict:
        uptime_ = result_dict[send_rh]['uptime']
        if uptime_:
            uptime_ = int(int(uptime_)/100)
        uptime_dict[result_dict[send_rh]['id']] = uptime_

    logging.info('Starting database update')
    logging.debug(uptime_dict)

    with database.lock:
        db = database.Database(secure.DBNAME, secure.USER,
                               secure.PASS, secure.DB_SERVER)
        db.set_uptime(uptime_dict)


def backup(ip):
    logging.debug('Starting global backup function with ip {}'.format(ip))
    switch_list = get_switch_list(ip)
    event_dict = {}
    for sw in switch_list:
        if sw.can_backup():
            event_dict[sw.id_] = {}
            event_dict[sw.id_]['ev_type'] = 'warn'
            try:
                logging.debug('Trying backup for ip {}'.format(sw.ip_addr))
                sw.backup()

                event_dict[sw.id_]['ev_event'] = ('Switch configuration '
                                                  'backup successful')
            except Exception as e:
                msg = ('Error occurred while making '
                        'config backup: {} from {}'.format(e, sw.ip_addr))
                logging.error(msg)
                event_dict[sw.id_]['ev_event'] = ('Switch configuration backup'
                                                  ' raised error')
                logging.info(sw)
        else:
            logging.warning('The switch cannot be backuped: {}'.format(sw))

    if len(event_dict) > 0:
        with database.lock:
            logging.debug("Writing reboot events to database.")
            db = database.Database(secure.DBNAME, secure.USER,
                                   secure.PASS, secure.DB_SERVER)
            db.set_events(event_dict)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for switch management')

    # setting arguments for command-line args
    # const is used when flag added without parameter
    # default is used when flag is omitted
    parser.add_argument('-r', '--reboot', default=None, const='reboot',
                        help='Reboot all switches, if no IP specified',
                        metavar='<ip-address>', nargs='?')
    parser.add_argument('-b', '--backup', help='''Backup given by ip switch.
                                     If IP omitted - backup all switches''',
                        metavar='<ip-address>', default=None, const='backup',
                        nargs='?')
    parser.add_argument('-l', '--log', help='Set the logging level',
                        metavar='log-level', default='WARNING',
                        const='INFO', nargs='?')
    parser.add_argument('-p', '--ping', action='store_true',
                        help='Ping all enabled switches')
    parser.add_argument('-u', '--uptime', action='store_true',
                        help='Check uptime of all enabled switches')
    args = parser.parse_args()

    if args.log:
        lvl = args.log.upper()
        loglevel = getattr(logging, lvl)
        logging.basicConfig(level=loglevel,
                            format='%(asctime)s:%(levelname)s:%(message)s')

    if args.ping:
        ping()
    elif args.uptime:
        uptime()
    elif args.backup:
        backup(args.backup)
    elif args.reboot:
        reboot(args.reboot)
    else:
        parser.print_help()