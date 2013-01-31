#! /usr/bin/python3.2

import psycopg2
import datetime
import secure


DBNAME = secure.DBNAME
USER = secure.USER
PASS = secure.PASS
PING_DIC = {}

def makeconnection():
    try:
        conn = psycopg2.connect("dbname={} user={} password={}".format(DBNAME,
                                                                       USER,
                                                                       PASS))
        return conn
    except Exception as e:
        print('Error: ', e)

# lock = Lock()

def fetchdata():
    conn = makeconnection()
    c = conn.cursor()
    c.execute("""SELECT ip_addr, sw_enabled, sw_type_id,
              sw_id, sw_uptime, sw_ping, id FROM switches_switch""")
    data = c.fetchall()
    data_list = []
    for row in data:
        data_list.append(row)
    conn.close()
    return data_list

def setdata(data_dic={}, data='ping'):
    '''Format of data_dic for event: db_data[0] -> event type
                                     db_date[1] -> switch_id (ForeignKey)
                                     db_date[2] -> event description
                                     db_date[3] -> comment (optional)
    '''
    conn = makeconnection()
    c = conn.cursor()
    if data=='ping':
        for key in data_dic:
            c.execute("""UPDATE switches_switch SET sw_ping=(%s) WHERE ip_addr=(%s)""",
                      (data_dic[key]['ping'], key))
    elif data == 'uptime':
        for key in data_dic:
            c.execute("""UPDATE switches_switch SET sw_uptime=(%s) WHERE ip_addr=(%s)""",
                      (data_dic[key]['sw_uptime'], data_dic[key]['ip_addr']))
    elif data == 'event':
        for key in data_dic:
            c.execute("""INSERT INTO switches_event VALUES (%s)""",
                      (datetime.datetime.now(), data_dic[key]['ev_type'], key,
                       data_dic[key]['ev_event'], data_dic[key]['ev_comment']))
    conn.commit()
    conn.close()


