from django.test import TestCase
from switches.models import Switch

print('test_models imported!\n')


class SwitchModelsTest(TestCase):

    def test_switch2(self):
        self.assertEqual(1, 1)
