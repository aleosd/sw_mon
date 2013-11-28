from django.test import TestCase
from switches.models import Switch, Street, SwitchType


def create_street(**kwargs):
    defaults = {
        'street': 'new_street'
    }
    defaults.update(kwargs)
    return Street.objects.create(**defaults)


def create_switch_type(**kwargs):
    defaults = {
        'sw_type': 'new_switch_type'
    }
    defaults.update(kwargs)
    return SwitchType.objects.create(**defaults)


def create_switch(**kwargs):
    defaults = {
        'ip_addr': '192.168.1.254',
        'sw_district': 'mzv',
        'sw_street': create_street(),
        'sw_build_num': 13,
        'sw_type': create_switch_type(),
        'sw_id': 10000001,
        'sw_enabled': True,
        'sw_ping': 12.6,
        'sw_uptime': 50000000,
    }
    defaults.update(kwargs)
    return Switch.objects.create(**defaults)


class SwitchModelsTest(TestCase):
    def setUp(self):
        # creating user for auth simulation
        '''
        self.user = User.objects.create_user('test', 'test@test.com', 'testpass')
        self.user.save()
        self.client.login(username='test', password='testpass')
        '''

        self.switch1 = create_switch(
            ip_addr = '192.168.1.1',
            sw_street = create_street(street='my_street_1'),
            sw_type = create_switch_type(sw_type='type_1'),
            sw_id = 1000003,
            sw_district = 'ggn'
        )
        self.switch2 = create_switch(
            ip_addr = '192.168.1.2',
            sw_street=create_street(street='my_street_2'),
            sw_type=create_switch_type(sw_type='type_2'),
            sw_id = 1000002
        )

        # creating switch with bad uptime
        self.switch3 = create_switch(
            ip_addr = '192.168.1.3',
            sw_street = create_street(street='my_street3'),
            sw_type = create_switch_type(sw_type='type_3'),
            sw_id = 1000004,
            sw_uptime = 200
        )

        # creating not responding switch (set ping to none) and bad uptime
        self.switch4 = create_switch(
            ip_addr = '192.168.1.4',
            sw_street = create_street(),
            sw_type = create_switch_type(sw_type='type_3'),
            sw_id = 1000005,
            sw_uptime = 200,
            sw_ping = None
        )

        # disabled switch
        self.switch5 = create_switch(
            ip_addr = '192.168.1.5',
            sw_street = create_street(),
            sw_type = create_switch_type(),
            sw_id = 1000006,
            sw_uptime = 200,
            sw_ping = None,
            sw_enabled = False
        )

    def test_get_config_path(self):
        switch3_configs = self.switch3.get_config_path()
        self.assertEqual(switch3_configs,
                         'configs/{}.cfg'.format(self.switch3.sw_id))
        self.assertFalse(self.switch1.get_config_path())

    def test_get_absolute_url(self):
        switch1_url = self.switch1.get_absolute_url()
        self.assertEqual(switch1_url, '/mon/edit/1/')