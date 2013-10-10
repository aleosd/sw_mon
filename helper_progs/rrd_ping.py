#! /usr/bin/python3

import argparse
import logging
import os.path
import sys
import datetime

import secure
import rrdtool
import Switch

FILE_PATH = secure.RRDPING_FILE_PATH
FILE_NAME = secure.RRDPING_FILE_NAME
GRAPH_NAME = secure.RRDPING_GRAPH_NAME


def initialize():
    if os.path.isfile(FILE_PATH + FILE_NAME):
        logging.warning('The file is already exists, cannot overwrite!')
        sys.exit(1)

    logging.info('Initializing rrd database')
    rrdtool.create(FILE_PATH + FILE_NAME, '--step', '60',
                   'DS:pl:GAUGE:120:0:100',
                   'DS:gateway_ping:GAUGE:120:0:10000000',
                   'DS:yandex_ping:GAUGE:120:0:10000000',
                   'RRA:MAX:0.5:1:1500')
    logging.info('RRD database successfully initialized')


def update():
    logging.info('Updating rrd database')
    gateway_ping = Switch.Host('10.1.10.1').sys_ping(packet_count=8)
    yandex_ping = Switch.Host('ya.ru').sys_ping(packet_count=8)
    rrdtool.update(FILE_PATH + FILE_NAME,
                   'N:{}:{}:{}'.format(gateway_ping[1], gateway_ping[0], yandex_ping[0]))


def graph():
    logging.info('Drawing graph')
    time = datetime.datetime.today().ctime()
    rrdtool.graph(FILE_PATH + GRAPH_NAME,
                   '-w', '785', '-h', '120', '-a', 'PNG',
                   '--slope-mode',
                   '--logarithmic', '--units=si',
                   '--start', '-86400', '--end', 'now',
                   '--font', 'DEFAULT:7:',
                   '--title', 'Ping monitor',
                   '--watermark', time,
                   '--vertical-label', 'ping(ms)',
                   '--right-axis-label', 'ping(ms)',
                   '--lower-limit', '0.1',
                   '--right-axis', '1:0',
                   '--x-grid', 'MINUTE:10:HOUR:1:MINUTE:120:0:%R',
                   '--alt-y-grid', '--rigid',
                   'DEF:gtw_rtp={}{}:gateway_ping:MAX'.format(FILE_PATH, FILE_NAME),
                   'DEF:ydx_rtp={}{}:yandex_ping:MAX'.format(FILE_PATH, FILE_NAME),
                   'DEF:packetloss={}{}:pl:MAX'.format(FILE_PATH, FILE_NAME),
                   'CDEF:PLNone=packetloss,0,0,LIMIT,UN,UNKN,INF,IF',
                   'CDEF:PL10=packetloss,1,10,LIMIT,UN,UNKN,INF,IF',
                   'CDEF:PL25=packetloss,10,25,LIMIT,UN,UNKN,INF,IF',
                   'CDEF:PL50=packetloss,25,50,LIMIT,UN,UNKN,INF,IF',
                   'CDEF:PL100=packetloss,50,100,LIMIT,UN,UNKN,INF,IF',
                   'LINE1:ydx_rtp#FF0000:yndx_ping(ms)\t',
                   'GPRINT:ydx_rtp:LAST:Cur\: %5.2lf',
                   'GPRINT:ydx_rtp:AVERAGE:Avg\: %5.2lf',
                   'GPRINT:ydx_rtp:MAX:Max\: %5.2lf',
                   'GPRINT:ydx_rtp:MIN:Min\: %5.2lf\t\t\t\\n',
                   'LINE1:gtw_rtp#0000FF:gtw_ping(ms)\t',
                   'GPRINT:gtw_rtp:LAST:Cur\: %5.2lf',
                   'GPRINT:gtw_rtp:AVERAGE:Avg\: %5.2lf',
                   'GPRINT:gtw_rtp:MAX:Max\: %5.2lf',
                   'GPRINT:gtw_rtp:MIN:Min\: %5.2lf\t\t\t',
                   'COMMENT:pckt loss\:',
                   'AREA:PL10#FFFF00:1-10%:STACK',
                   'AREA:PL25#FFCC00:10-25%:STACK',
                   'AREA:PL50#FF8000:25-50%:STACK',
                   'AREA:PL100#FF0000:50-100%:STACK',
                   'COMMENT:\\n',
                   )


def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s:%(levelname)s:%(message)s')
    parser = argparse.ArgumentParser(description='Script for rrd_ping database manipulation')
    parser.add_argument('-i', '--initialize', action='store_true',
                        help='Initialize database')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update database')
    parser.add_argument('-g', '--graph', action='store_true',
                        help='Draw graph')
    args = parser.parse_args()

    if args.initialize:
        initialize()
    elif args.update:
        update()
    elif args.graph:
        graph()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
