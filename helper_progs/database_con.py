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

def fetchdata(all=False):
    conn = makeconnection()
    c = conn.cursor()
    if not all:
        c.execute("""SELECT ip_addr, sw_enabled, sw_type_id, sw_id, sw_uptime,
                  sw_ping, id, sw_uplink FROM switches_switch""")
    else:
        c.execute("""SELECT * FROM switches_switch""")
    data = c.fetchall()
    data_list = []
    for row in data:
        data_list.append(row)
    conn.close()
    return data_list


def ex_query(query):
    '''Function for execution custom queries. Takes one parameter - query.
    Returns result in tuple
    '''

    conn = makeconnection()
    c = conn.cursor()
    c.execute(query)
    data = c.fetchall()
    return data


def setdata(data_dic={}, data='ping'):
    '''Format of data_dic for event: db_data[0] -> event type
                                     db_date[1] -> switch_id (ForeignKey)
                                     db_date[2] -> event description
                                     db_date[3] -> comment (optional)
    '''
    conn = makeconnection()
    c = conn.cursor()
    if data=='ping':
        for id in data_dic:
            c.execute("""UPDATE switches_switch SET sw_ping=(%s) WHERE id=(%s)""",
                      (data_dic[id]['ping'], id))
    elif data == 'uptime':
        for id in data_dic:
            c.execute("""UPDATE switches_switch SET sw_uptime=(%s) WHERE id=(%s)""",
                      (data_dic[id]['sw_uptime'], id))
    elif data == 'event':
        for key in data_dic:
            c.execute("""INSERT INTO switches_event (ev_datetime, ev_type,
                                                     ev_switch_id, ev_event,
                                                     ev_comment) 
                      VALUES (%s, %s, %s, %s, %s)""",
                      (datetime.datetime.now(), data_dic[key]['ev_type'], key,
                       data_dic[key]['ev_event'], data_dic[key]['ev_comment']))
    elif data == 'uplink':
        for key in data_dic:
            c.execute("""UPDATE switches_switch SET sw_uplink=(%s) WHERE ip_addr=(%s)""",
                      (data_dic[key] + ',', key))
    conn.commit()
    conn.close()


