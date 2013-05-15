from django.test import TestCase
from django.contrib.auth.models import User
from switches.models import Switch

print('test_views imported!')


class SwitchViewsTest(TestCase):
    def setUp(self):
        # creating user for auth simulation
        User.objects.create_user('test', 'test@test.com', 'testpass')
        user = self.client.login(username='test', password='testpass')

    def test_site_root_response_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_site_root_response_context(self):
        response = self.client.get('/')
        self.assertTrue('switch_list' in response.context)

    # ----------------- EVENTS PART TESTS -----------------
    def test_event_page_response_code(self):
        response = self.client.get('/mon/events/all/')
        self.assertEqual(response.status_code, 200)

    def test_event_error_page_response_code(self):
        response = self.client.get('/mon/events/errors/')
        self.assertEqual(response.status_code, 200)
