from django.core.urlresolvers import resolve
# from django.template.loader import render_to_string
# from django.http import HttpRequest
from switches.views import index, edit
from django.test import TestCase
from django.contrib.auth.models import User
from switches.models import Switch, Street, SwitchType

print('test_views imported!')


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


class SwitchViewsTest(TestCase):
    def setUp(self):
        # creating user for auth simulation
        self.user = User.objects.create_user('test', 'test@test.com', 'testpass')
        self.client.login(username='test', password='testpass')

        self.switch1 = create_switch(
            ip_addr = '192.168.1.1',
            sw_street = create_street(street='my_street_1'),
            sw_type = create_switch_type(sw_type='type_1'),
            sw_id = 1000003
        )
        self.switch2 = create_switch(
            ip_addr = '192.168.1.2',
            sw_street=create_street(street='my_street_2'),
            sw_type=create_switch_type(sw_type='type_2'),
            sw_id = 1000002
        )

 
    # ----------------- SWITCHES PART TESTS ------------------
    def test_site_root_response_code(self):
        response = self.client.get('/mon/')
        view = resolve('/mon/')
        self.assertEqual(view.func, index)
        self.assertEqual(response.status_code, 200)

    def test_site_root_response_context(self):
        response = self.client.get('/mon/')
        self.assertTrue('switch_list' in response.context)
        self.assertEqual(len(response.context['switch_list']), 2)

    def test_site_root_with_two_switch_obj(self):
        response = self.client.get('/mon/')
        self.assertIn('192.168.1.2', response.content.decode('utf-8'))
        self.assertIn('192.168.1.1', response.content.decode('utf-8'))
        '''
        expected_html = render_to_string(
            'mon/index.html',
            {'switch_list': [self.switch1, self.switch2],
             'STATIC_URL': '/static/',
             'user': self.user,
             'bad_uptime': 0,
             'bad_ping': 0,
             'LANGUAGES': ('en',),
            }
        )
        self.assertEqual((response.content.decode('utf-8')).strip(), expected_html)
        '''

    def test_switch_edit_view(self):
        response1 = self.client.get('/mon/edit/{}/'.format(self.switch1.id))
        response2 = self.client.get('/mon/edit/{}/'.format(self.switch2.id))
        view = resolve('/mon/edit/{}/'.format(self.switch1.id))

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(view.func, edit)

        self.assertIn('192.168.1.1', response1.content.decode('utf-8'))
        self.assertIn('192.168.1.2', response2.content.decode('utf-8'))
        self.assertTemplateUsed(response1, 'mon/edit.html', 'base.html')


    def test_switch_view_view(self):
        response = self.client.get('/mon/view/{}/'.format(self.switch1.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.switch1.ip_addr, response.content.decode('utf-8'))

    def test_mon_status_views(self):
        response_warn = self.client.get('/mon/status/warnings/')
        response_err = self.client.get('/mon/status/errors/')
        self.assertEqual(response_warn.status_code, 200)
        self.assertEqual(response_err.status_code, 200)

    # ----------------- EVENTS PART TESTS -----------------
    def test_event_page_response_code(self):
        response = self.client.get('/mon/events/all/')
        self.assertEqual(response.status_code, 200)

    def test_event_error_page_response_code(self):
        response = self.client.get('/mon/events/errors/')
        self.assertEqual(response.status_code, 200)

    # ----------------- HOME PAGE PART TESTS --------------
    def test_home_page_response_code(self):
        response = self.client.get('/mon/home/')
        self.assertEqual(response.status_code, 200)
