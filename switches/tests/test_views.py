from django.core.urlresolvers import resolve
from django.template.loader import render_to_string
from django.http import HttpRequest
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
    }
    defaults.update(kwargs)
    return Switch.objects.create(**defaults)


class SwitchViewsTest(TestCase):
    def setUp(self):
        # creating user for auth simulation
        User.objects.create_user('test', 'test@test.com', 'testpass')
        user = self.client.login(username='test', password='testpass')

        switch1 = create_switch(
            ip_addr = '192.168.1.1',
            sw_street = create_street(street='my_street_1'),
            sw_type = create_switch_type(sw_type='type_1'),
            sw_id = 1000003
        )
        switch2 = create_switch(
            ip_addr = '192.168.1.2',
            sw_street=create_street(street='my_street_2'),
            sw_type=create_switch_type(sw_type='type_2'),
            sw_id = 1000002
        )

 
    # ----------------- SWITCHES PART TESTS ------------------
    def test_site_root_response_code(self):
        response = self.client.get('/')
        view = resolve('/')
        self.assertEqual(view.func, index)
        self.assertEqual(response.status_code, 200)

    def test_site_root_response_context(self):
        response = self.client.get('/')
        self.assertTrue('switch_list' in response.context)
        self.assertEqual(len(response.context['switch_list']), 2)

    def test_site_root_with_switch_obj(self):
        response = self.client.get('/')
        self.assertIn('192.168.1.2', response.content.decode('utf-8'))
        # expected_html = render_to_string('mon/index.html')
        # self.assertEqual(response.content.decode('utf-8'), expected_html)

    def test_switch_edit_view(self):
        response = self.client.get('/edit/1/')
        view = resolve('/edit/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(view.func, edit)
        self.assertIn('192.168.1.1', response.content.decode('utf-8'))

    # ----------------- EVENTS PART TESTS -----------------
    def test_event_page_response_code(self):
        response = self.client.get('/mon/events/all/')
        self.assertEqual(response.status_code, 200)

    def test_event_error_page_response_code(self):
        response = self.client.get('/mon/events/errors/')
        self.assertEqual(response.status_code, 200)
