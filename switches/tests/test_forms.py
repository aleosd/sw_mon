from django.test import TestCase

from switches.models import Switch


class SwitchTest(TestCase):

    def test_switch1(self):
        self.assertEqual(1, 1)
