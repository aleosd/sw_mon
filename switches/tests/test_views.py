from django.core.urlresolvers import resolve
# from django.template.loader import render_to_string
# from django.http import HttpRequest
from switches.views import index, edit
from django.test import TestCase
from django.contrib.auth.models import User, Permission
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


class SwitchViewsTest(TestCase):
    def setUp(self):
        # creating user for auth simulation
        self.user = User.objects.create_user('test', 'test@test.com', 'testpass')
        self.user.save()
        self.client.login(username='test', password='testpass')

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
    # ----------------- SWITCHES PART TESTS ------------------
    def test_site_root_response_code(self):
        response = self.client.get('/mon/')
        view = resolve('/mon/')
        self.assertEqual(view.func, index)
        self.assertEqual(response.status_code, 200)

    def test_site_root_response_context(self):
        response = self.client.get('/mon/')
        self.assertTrue('switch_list' in response.context)
        self.assertEqual(len(response.context['switch_list']), 5)

    def test_site_root_with_two_switch_obj(self):
        response = self.client.get('/mon/')
        self.assertIn('192.168.1.2', response.content.decode('utf-8'))
        self.assertIn('192.168.1.1', response.content.decode('utf-8'))

    def test_new_switch(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_switch'))
        response = self.client.get('/new/')
        self.assertEqual(response.status_code, 200)

        self.user.user_permissions.remove(Permission.objects.get(codename='change_switch'))

    def test_wrong_permissions(self):
        response_edit = self.client.get('/mon/edit/{}/'.format(self.switch1.id))
        response_reboot_post = self.client.post('/mon/reboot/', {'id': 2222})
        response_clear_post = self.client.post('/mon/clear/', {'id': 2})
        response_new_switch = self.client.get('/new/')

        self.assertEqual(response_edit.status_code, 302)
        self.assertEqual(response_reboot_post.status_code, 302)
        self.assertEqual(response_clear_post.status_code, 302)
        self.assertEqual(response_new_switch.status_code, 302)

    def test_switch_edit_view(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_switch'))
        response1 = self.client.get('/mon/edit/{}/'.format(self.switch1.id))
        response2 = self.client.get('/mon/edit/{}/'.format(self.switch2.id))
        view = resolve('/mon/edit/{}/'.format(self.switch1.id))

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(view.func, edit)

        self.assertIn('192.168.1.1', response1.content.decode('utf-8'))
        self.assertIn('192.168.1.2', response2.content.decode('utf-8'))
        self.assertTemplateUsed(response1, 'mon/edit.html', 'base.html')

        self.user.user_permissions.remove(Permission.objects.get(codename='change_switch'))

    def test_switch_view_view(self):
        response = self.client.get('/mon/view/{}/'.format(self.switch1.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.switch1.ip_addr, response.content.decode('utf-8'))

    def test_mon_status_views_status_code(self):
        response_warn = self.client.get('/mon/status/warnings/')
        response_err = self.client.get('/mon/status/errors/')
        response_disabled = self.client.get('/mon/status/disabled/')
        self.assertEqual(response_warn.status_code, 200)
        self.assertEqual(response_err.status_code, 200)
        self.assertEqual(response_disabled.status_code, 200)

    def test_mon_warning_status_page_response(self):
        response_warn = self.client.get('/mon/status/warnings/')
        self.assertEqual(response_warn.context['sw_all'], 5)
        self.assertEqual(response_warn.context['sw_warning'], 1)
        self.assertEqual(response_warn.context['sw_disabled'], 1)
        self.assertEqual(response_warn.context['sw_error'], 1)
        self.assertEqual(len(response_warn.context['switch_list']), 1)

    def test_mon_error_status_page_response(self):
        response_warn = self.client.get('/mon/status/errors/')
        self.assertEqual(response_warn.context['sw_all'], 5)
        self.assertEqual(response_warn.context['sw_warning'], 1)
        self.assertEqual(response_warn.context['sw_disabled'], 1)
        self.assertEqual(response_warn.context['sw_error'], 1)
        self.assertEqual(len(response_warn.context['switch_list']), 1)

    def test_mon_disabled_status_page_response(self):
        response_warn = self.client.get('/mon/status/disabled/')
        self.assertEqual(response_warn.context['sw_all'], 5)
        self.assertEqual(response_warn.context['sw_warning'], 1)
        self.assertEqual(response_warn.context['sw_disabled'], 1)
        self.assertEqual(response_warn.context['sw_error'], 1)
        self.assertEqual(len(response_warn.context['switch_list']), 1)

    # ----------------- DISTRICT VIEWS TESTS --------------
    def test_district_views_response_code(self):
        response_mzv = self.client.get('/mon/district/mzv/')
        response_ggn = self.client.get('/mon/district/ggn/')
        response_vkz = self.client.get('/mon/district/vkz/')
        response_szp = self.client.get('/mon/district/szp/')

        self.assertEqual(response_mzv.status_code, 200)
        self.assertEqual(response_ggn.status_code, 200)
        self.assertEqual(response_vkz.status_code, 200)
        self.assertEqual(response_szp.status_code, 200)

    def test_district_views_switch_count(self):
        response_mzv = self.client.get('/mon/district/mzv/')
        response_ggn = self.client.get('/mon/district/ggn/')

        self.assertEqual(len(response_mzv.context['switch_list']), 4)
        self.assertEqual(len(response_ggn.context['switch_list']), 1)

    # ----------------- EVENTS PART TESTS -----------------
    def test_event_page_response_code(self):
        response = self.client.get('/mon/events/all/')
        self.assertEqual(response.status_code, 200)

    def test_event_error_page_response_code(self):
        response = self.client.get('/mon/events/errors/')
        self.assertEqual(response.status_code, 200)

    def test_event_warning_page_response_code(self):
        response = self.client.get('/mon/events/warnings/')
        self.assertEqual(response.status_code, 200)

    def test_event_wrong_url_page_response_code(self):
        response = self.client.get('/mon/events/some_event/')
        self.assertEqual(response.status_code, 404)

    # ----------------- HOME PAGE PART TESTS --------------
    def test_home_page_response_code(self):
        response = self.client.get('/mon/home/')
        self.assertEqual(response.status_code, 200)

    def test_home_page_response_context(self):
        response = self.client.get('/mon/home/')

        self.assertEqual(response.context['total_switches'], 5)
        self.assertEqual(response.context['disabled_switches'], 1)
        self.assertEqual(len(response.context['error_switches']), 1)
        self.assertEqual(response.context['warning_switches'], 3)

    # ----------------- HELPER VIEWS TESTS ----------------
    def test_ping_view_response_code(self):
        response_get = self.client.get('/mon/ping/')
        response_post = self.client.post('/mon/ping/', {'id': 1})

        self.assertEqual(response_get.status_code, 400)
        self.assertEqual(response_post.status_code, 200)

    def test_reboot_view_response_code(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_switch'))
        response_get = self.client.get('/mon/reboot/')
        response_post = self.client.post('/mon/reboot/', {'id': 2222})

        self.assertEqual(response_get.status_code, 400)
        self.assertEqual(response_post.status_code, 200)
        self.user.user_permissions.remove(Permission.objects.get(codename='change_switch'))

    def test_clear_view_response_code(self):
        self.user.user_permissions.add(Permission.objects.get(codename='change_switch'))
        response_get = self.client.get('/mon/clear/')
        response_post = self.client.post('/mon/clear/', {'id': 2})

        self.assertEqual(response_get.status_code, 400)
        self.assertEqual(response_post.status_code, 404)
        self.user.user_permissions.remove(Permission.objects.get(codename='change_switch'))