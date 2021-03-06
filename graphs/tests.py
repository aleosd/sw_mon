from django.test import TestCase
from graphs.models import Graph
from django.contrib.auth.models import User



def create_graph(**kwargs):
    defaults = {'path': "/var/www/sw_mon/templates/static/img/total.png",
        'period': 'd',
        'isp': 'ttl'}
    defaults.update(kwargs)
    return Graph.objects.create(**defaults)


class SimpleTest(TestCase):
    def setUp(self):
        self.graph_total_d = create_graph()
        self.graph_total_w = create_graph(period='w')

        self.graph_ttk_d = create_graph(isp='ttk')
        self.graph_ttk_y = create_graph(isp='ttk', period='y')

        User.objects.create_user('test', 'test@test.com', 'testpass')
        self.user = self.client.login(username='test', password='testpass')

    # ----------------- MODEL TESTS -------------------
    def test_graph_get_web_url(self):
        self.assertEqual(self.graph_total_d.get_web_url(), 'img/total.png')

    # ----------------- VIEW TESTS --------------------
    def test_traf_page_response_code(self):
        response = self.client.get('/traf/')
        self.assertEqual(response.status_code, 301)

    def test_traf_isp_pages_response_code(self):
        response_ttl = self.client.get('/traf/isp/ttl/')
        response_ttk = self.client.get('/traf/isp/ttk/')

        self.assertEqual(response_ttl.status_code, 200)
        self.assertEqual(response_ttk.status_code, 200)

    def test_traf_page_wrong_url(self):
        response = self.client.get('/traf/very_wrong_url')
        self.assertEqual(response.status_code, 404)