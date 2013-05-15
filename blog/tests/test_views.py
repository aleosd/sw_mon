from django.test import TestCase
from django.contrib.auth.models import User


print ('blog/test/test_views.py imported')


class BlogViewsTest(TestCase):
    def setUp(self):
        User.objects.create_user('test', 'test@test.com', 'testpass')
        user = self.client.login(username='test', password='testpass')

    def test_blog_root_page_response_code(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)

    def test_blog_root_page_context(self):
        response = self.client.get('/blog/')
        self.assertTrue('entry_list' in response.context)
        self.assertTrue('category_list' in response.context)
