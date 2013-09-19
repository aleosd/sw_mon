import database_con as db

class Switch():
    '''
    Basic class for switch representation. On initialization takes n
    arguments:
        id_ - unic number in database, 'id';
        ip_addr - ip address of this switch;
        sw_district - location;
    '''

    def __init__(self, id_, ip_addr, sw_district, sw_id, sw_enabled, sw_ping,
                 sw_backup_conf, sw_uptime, sw_type_id):

        self.id_ = id_
        self.ip_addr = ip_addr
        self.sw_district = sw_district
        self.sw_id = sw_id
        self.sw_enabled = sw_enabled
        self.sw_ping = sw_ping
        self.sw_backup_conf = sw_backup_conf
        self.sw_uptime = sw_uptime
        self.sw_type_id = sw_type_id

    def __str__(self):
        return """
                The switch id {},
                IP-address: {},
                Cheking is enabled: {},
                Backup is enabled: {},
                Ping: {} ms,
                Uptime: {} sec.
               """.format(str(self.sw_id), self.ip_addr, str(self.sw_enabled),
                          str(self.sw_backup_conf), str(self.sw_ping),
                          str(self.sw_uptime))


def make_switch_list():
    raw_data = db.fetchdata(all=True)
    switch_list = []
    for row in raw_data:
        sw = Switch(row[0], row[1], row[2], row[6], row[7], row[8], row[13],
                    row[9], row[5])
        switch_list.append(sw)
        print(sw)


print('Switch imported')
make_switch_list()
