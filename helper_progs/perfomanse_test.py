#! /usr/bin/python3

import Switch
import Ping
import Database
import secure
import time
from threading import Thread
import cProfile
import pstats

DBNAME = secure.DBNAME
USER = secure.USER
PASS = secure.PASS
HOST = secure.DB_SERVER


class Timer():
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000
        if self.verbose:
            print('Running time {} ms'.format(self.msecs))

gtw1 = Switch.Host('10.1.10.1')
gtw2 = Ping.Ping('10.1.10.1')

db = Database.Database(DBNAME, USER, PASS, HOST)
switch_list = db.get_switch_list()
hosts = []

for sw in switch_list:
    if sw[7]:
        hosts.append(Switch.Host(sw[1]))


def ping_sub():
    threads = []
    for host in hosts:
        t = Thread(target=host.ping, args=())
        threads.append(t)

    for thread in threads:
        thread.start()

    for thread in threads: # waiting all threads to finish
        thread.join()

    #for host in hosts:
    #    host.ping()

def ping_pure():
    threads = []
    for host in hosts:
        # host_ping = Ping.Ping()
        t = Thread(target=Ping.Ping(host.ip_addr).pyng, args=())
        threads.append(t)

    for thread in threads:
        thread.start()

    for thread in threads: # waiting all threads to finish
        thread.join()

    #for host in hosts:
    #    Ping.Ping(host.ip_addr).pyng()


cProfile.run("ping_sub()", filename='ping_sub.profile')
print("finished ping_sub")
time.sleep(1)
cProfile.run("ping_pure()", filename='ping_pure.profile')
print("Done!\n\n")

p_sub = pstats.Stats('ping_sub.profile')
p_sub.sort_stats('time').print_stats(3)

p_pure = pstats.Stats('ping_pure.profile')
p_pure.sort_stats('time').print_stats(3)
