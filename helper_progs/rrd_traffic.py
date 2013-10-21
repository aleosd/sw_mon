#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os.path
import sys
import datetime
import rrdtool

import secure
import switch
import snmp_oids

FILE_PATH = secure.RRDTRAF_FILE_PATH
FILE_NAME = secure.RRDTRAF_FILE_NAME
GRAPH_NAME = secure.RRDTRAF_GRAPH_NAME


def initialize():
    if os.path.isfile(FILE_PATH + FILE_NAME):
        logging.warning('The file is already exists, cannot overwrite!')
        sys.exit(1)

    logging.info('Initializing rrd database')
    rrdtool.create(FILE_PATH + FILE_NAME, '--step', '300',
                   'DS:traffic_megafon_in:COUNTER:600:U:U',
                   'DS:traffic_megafon_out:COUNTER:600:U:U',
                   'DS:traffic_ttk_in:COUNTER:600:U:U',
                   'DS:traffic_ttk_out:COUNTER:600:U:U',
                   'DS:traffic_rtk_in:COUNTER:600:U:U',
                   'DS:traffic_rtk_out:COUNTER:600:U:U',
                   'RRA:AVERAGE:0.5:1:288',    # one day of 5 min averages
                   'RRA:AVERAGE:0.5:6:336',    # one week of 30 min averages
                   'RRA:AVERAGE:0.5:24:732',   # two month of 2 hours averages
                   'RRA:AVERAGE:0.5:144:730',  # one year of 12 hours averages
                   )
    logging.info('RRD database successfully initialized')


def update():
    logging.info('Updating database')
    bgp_gateway = switch.Host(secure.BGP_SERVER)

    # 4 port - TTK
    # 5 port - Megafon
    # 6 port - RTK
    port_data = {4: {}, 5: {}, 6: {}}
    total_in = 0
    total_out = 0

    for port in port_data:
        in_bytes = int(bgp_gateway.snmpget(snmp_oids.IN_BYTES + str(port))[0][1])
        out_bytes = int(bgp_gateway.snmpget(snmp_oids.OUT_BYTES + str(port))[0][1])
        port_data[port]['in_bytes'] = in_bytes
        port_data[port]['out_bytes'] = out_bytes
        total_in += in_bytes
        total_out += out_bytes

    rrdtool.update(FILE_PATH + FILE_NAME, 'N:{}:{}:{}:{}:{}:{}'.format(
        port_data[5]['in_bytes'], port_data[5]['out_bytes'],
        port_data[4]['in_bytes'], port_data[4]['out_bytes'],
        port_data[6]['in_bytes'], port_data[6]['out_bytes']))


def graph(period):
    logging.info('Drawing graph')
    time_now = datetime.datetime.today().ctime()

    # draw common graph, full page length
    if period is None:
            rrdtool.graph(FILE_PATH + GRAPH_NAME,
                  '-w', '785', '-h', '120', '-a', 'PNG',
                  '--slope-mode',
                  '--start', '-1d', '--end', 'now',
                  '--font', 'DEFAULT:7:',
                  '--title', 'Traffic monitor - Daily',
                  '--watermark', time_now,
                  '--vertical-label', 'Mb/sec',
                  '--right-axis-label', 'Mb/sec',
                  '--lower-limit', '0',
                  '--right-axis', '1:0',
                  '--x-grid', 'MINUTE:10:HOUR:1:MINUTE:120:0:%R',
                  '--alt-y-grid', '--rigid',
                  'DEF:tot_ttk_in={}{}:traffic_ttk_in:AVERAGE'.format(FILE_PATH, FILE_NAME),
                  'DEF:tot_megafon_in={}{}:traffic_megafon_in:AVERAGE'.format(FILE_PATH, FILE_NAME),
                  'DEF:tot_rtk_in={}{}:traffic_rtk_in:AVERAGE'.format(FILE_PATH, FILE_NAME),
                  'DEF:tot_ttk_out={}{}:traffic_ttk_out:AVERAGE'.format(FILE_PATH, FILE_NAME),
                  'DEF:tot_megafon_out={}{}:traffic_megafon_out:AVERAGE'.format(FILE_PATH, FILE_NAME),
                  'DEF:tot_rtk_out={}{}:traffic_rtk_out:AVERAGE'.format(FILE_PATH, FILE_NAME),
                  'CDEF:total_in=tot_ttk_in,tot_megafon_in,+,tot_rtk_in,+,8,*,1000000,/',
                  'CDEF:total_out=tot_ttk_out,tot_megafon_out,+,tot_rtk_out,+,8,*,1000000,/',
                  'AREA:total_in#00FF00:In traffic (Mbps)\t',
                  'GPRINT:total_in:LAST:Cur\: %5.2lf',
                  'GPRINT:total_in:AVERAGE:Avg\: %5.2lf',
                  'GPRINT:total_in:MAX:Max\: %5.2lf',
                  'GPRINT:total_in:MIN:Min\: %5.2lf\t\t\t\\n',
                  'LINE1:total_out#0000FF:Out traffic (Mbps)\t',
                  'GPRINT:total_out:LAST:Cur\: %5.2lf',
                  'GPRINT:total_out:AVERAGE:Avg\: %5.2lf',
                  'GPRINT:total_out:MAX:Max\: %5.2lf',
                  'GPRINT:total_out:MIN:Min\: %5.2lf\t\t\t\\n')

    # draw particular graphs, length according to sidebar menu
    else:
        settings = {'d': {'filename': secure.RRDTRAF_D_GRAPH_NAME,
                          'x-grid': 'MINUTE:10:HOUR:1:MINUTE:120:0:%R',
                          'title': 'DAILY'},
                    'w': {'filename': secure.RRDTRAF_W_GRAPH_NAME,
                          'x-grid': 'HOUR:2:DAY:1:DAY:1:86400:%A',
                          'title': 'WEEKLY'},
                    'm': {'filename': secure.RRDTRAF_M_GRAPH_NAME,
                          'x-grid': 'HOUR:12:DAY:1:WEEK:1:0:%d, %m',
                          'title': 'MONTHLY'},
                    'y': {'filename': secure.RRDTRAF_Y_GRAPH_NAME,
                          'x-grid': 'WEEK:1:WEEK:2:MONTH:1:0:%b',
                          'title': 'YEARLY'}}

        isps = {'ttk': {'CDEF_IN': 'CDEF:ttk_in_ps=tot_ttk_in,8,*,1000000,/',
                        'VAR_IN': 'ttk_in_ps',
                        'CDEF_OUT': 'CDEF:ttk_out_ps=tot_ttk_out,8,*,1000000,/',
                        'VAR_OUT': 'ttk_out_ps'},
               'rtk': {'CDEF_IN': 'CDEF:rtk_in_ps=tot_rtk_in,8,*,1000000,/',
                        'VAR_IN': 'rtk_in_ps',
                        'CDEF_OUT': 'CDEF:ttk_out_ps=tot_rtk_out,8,*,1000000,/',
                        'VAR_OUT': 'rtk_out_ps'},
               'mgf': {'CDEF_IN': 'CDEF:mgf_in_ps=tot_megafon_in,8,*,1000000,/',
                        'VAR_IN': 'mgf_in_ps',
                        'CDEF_OUT': 'CDEF:mgf_out_ps=tot_megafon_out,8,*,1000000,/',
                        'VAR_OUT': 'mgf_out_ps'},
               'total': {'CDEF_IN': '',
                        'VAR_IN': 'total_in',
                        'CDEF_OUT': '',
                        'VAR_OUT': 'total_out'}}

        for isp in isps:
            rrdtool.graph(FILE_PATH + isp + settings[period]['filename'],
                          '-w', '700', '-h', '158', '-a', 'PNG',
                          '--slope-mode',
                          '--start', '-1{}'.format(period), '--end', 'now',
                          '--font', 'DEFAULT:7:',
                          '--title', 'Traffic monitor - {} {}'.format(isp. settings[period]['title']),
                          '--watermark', time_now,
                          '--vertical-label', 'Mb/sec',
                          '--right-axis-label', 'Mb/sec',
                          '--lower-limit', '0',
                          '--right-axis', '1:0',
                          '--x-grid', settings[period]['x-grid'],
                          '--alt-y-grid', '--rigid',
                          'DEF:tot_ttk_in={}{}:traffic_ttk_in:AVERAGE'.format(FILE_PATH, FILE_NAME),
                          'DEF:tot_megafon_in={}{}:traffic_megafon_in:AVERAGE'.format(FILE_PATH, FILE_NAME),
                          'DEF:tot_rtk_in={}{}:traffic_rtk_in:AVERAGE'.format(FILE_PATH, FILE_NAME),
                          'DEF:tot_ttk_out={}{}:traffic_ttk_out:AVERAGE'.format(FILE_PATH, FILE_NAME),
                          'DEF:tot_megafon_out={}{}:traffic_megafon_out:AVERAGE'.format(FILE_PATH, FILE_NAME),
                          'DEF:tot_rtk_out={}{}:traffic_rtk_out:AVERAGE'.format(FILE_PATH, FILE_NAME),
                          'CDEF:total_in=tot_ttk_in,tot_megafon_in,+,tot_rtk_in,+,8,*,1000000,/',
                          'CDEF:total_out=tot_ttk_out,tot_megafon_out,+,tot_rtk_out,+,8,*,1000000,/',
                          isps['isp']['CDEF_IN'],
                          isps['isp']['CDEF_OUT'],
                          'LINE1:total_in#FF0000:In traffic (Mbps)\t',
                          'AREA:{}#00FF00:In traffic (Mbps)\t'.format(isps['isp']['VAR_IN']),
                          'GPRINT:{}:LAST:Cur\: %5.2lf'.format(isps['isp']['VAR_IN']),
                          'GPRINT:{}:AVERAGE:Avg\: %5.2lf'.format(isps['isp']['VAR_IN']),
                          'GPRINT:{}:MAX:Max\: %5.2lf'.format(isps['isp']['VAR_IN']),
                          'GPRINT:{}:MIN:Min\: %5.2lf\t\t\t\\n'.format(isps['isp']['VAR_IN']),
                          'LINE1:{}#0000FF:Out traffic (Mbps)\t'.format(isps['isp']['VAR_OUT']),
                          'GPRINT:{}:LAST:Cur\: %5.2lf'.format(isps['isp']['VAR_OUT']),
                          'GPRINT:{}:AVERAGE:Avg\: %5.2lf'.format(isps['isp']['VAR_OUT']),
                          'GPRINT:{}:MAX:Max\: %5.2lf'.format(isps['isp']['VAR_OUT']),
                          'GPRINT:{]:MIN:Min\: %5.2lf\t\t\t\\n'.format(isps['isp']['VAR_OUT']),
                         )


def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s:%(levelname)s:%(message)s')
    parser = argparse.ArgumentParser(description='Script for rrd_ping database manipulation')
    parser.add_argument('-i', '--initialize', action='store_true',
                        help='Initialize database')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update database')
    parser.add_argument('-g', '--graph', nargs='?', default=None, const=None, metavar='<period>',
                        help='''Draw graph for given period. Possible parameters:
                                    d - day,
                                    w - week,
                                    m - month,
                                    y - year.
                                By default draw big graph for main page,daily total traffic usage.''')
    args = parser.parse_args()

    if args.initialize:
        initialize()
    elif args.update:
        update()
    elif args.graph:
        graph(args.graph)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
