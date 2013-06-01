from django.test import TestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from blog.models import Category, Entry


print ('blog/test/test_views.py imported')


class BlogViewsTest(TestCase):
    def create_category(self, **kwargs):
        defaults = {
            'title': 'test_category1',
            'description': 'category description',
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)


    def create_entry(self, **kwargs):
        defaults = {
            'title': 'Test entry1',
            'body': 'Entry body',
            'keywords': 'test, entry',
            # 'categories': self.create_category(),
        }
        defaults.update(kwargs)
        entry = Entry(**defaults)
        entry.slug = slugify(entry.title)
        entry.save()
        category = self.create_category()
        entry.categories.add(category)
        return entry

    def setUp(self):
        author = User.objects.create_user('test', 'test@test.com', 'testpass')
        self.user = self.client.login(username='test', password='testpass')
        self.entry1 = self.create_entry(author = author)

    # ------------------- ENTRIES TESTS ------------------------
    def test_blog_root_page_response_code(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)

    def test_blog_root_page_context(self):
        response = self.client.get('/blog/')
        self.assertTrue('entry_list' in response.context)
        self.assertTrue('category_list' in response.context)

    def test_entry_page_response_code(self):
        response = self.client.get(self.entry1.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry1.title, response.content.decode('utf-8'))
