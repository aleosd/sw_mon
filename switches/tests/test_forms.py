from django.test import TestCase

from switches.models import Switch

print('test_forms imported!\n')


class SwitchTest(TestCase):

    def test_switch1(self):
        self.assertEqual(1, 1)
