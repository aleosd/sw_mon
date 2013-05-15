DBNAME = 'sw_mon'
USER = 'sw_mon'
PASS = 'monitor'

allied_user = 'manager'
user = 'admin'
mzv_pass = 'e2t0k1'
vkz_pass = '2g7+ksm(6'

ssh_password = '1kak6)m6'

def pass_chooser(sw_id):
    if sw_id < 2000000:             # choosing proper password
        password = mzv_pass
    else:
        password = vkz_pass
    return password
