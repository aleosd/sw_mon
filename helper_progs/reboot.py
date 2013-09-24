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
    }

def reboot():
    raw_data = db.fetchdata(all=True)
    switch_list = []
    for row in raw_data:
        sw = switch_types[int(row[5])](row[0], row[1], row[2], row[6],
                                       row[7], row[8], row[13],
                                       row[9], row[5])
        switch_list.append(sw)
        if sw.sw_enabled and sw.sw_uptime > UPTIME:
            print(sw)
            sw.reboot()

reboot()
