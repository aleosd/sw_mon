from django.test import TestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from blog.models import Category, Entry


def create_category(**kwargs):
    defaults = {
        'title': 'test_category1',
        'description': 'category description',
    }
    defaults.update(kwargs)
    return Category.objects.create(**defaults)


def create_entry(**kwargs):
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
    category = create_category()
    entry.categories.add(category)
    return entry

class BlogViewsTest(TestCase):
    def setUp(self):
        author = User.objects.create_user('test', 'test@test.com', 'testpass')
        self.user = self.client.login(username='test', password='testpass')
        self.entry1 = create_entry(author = author)
        self.category = create_category(title='my', slug='my_category')

    # ------------------- ENTRIES TESTS ------------------------
    def test_blog_root_page(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('entry_list' in response.context)
        self.assertTrue('category_list' in response.context)
        self.assertEqual(len(response.context['entry_list']), 1)
        self.assertEqual(len(response.context['category_list']), 2)
        self.assertIn(self.entry1.title, response.content.decode('utf-8'))

    def test_entry_page_response_code(self):
        response = self.client.get(self.entry1.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.entry1.title, response.content.decode('utf-8'))

    def test_bad_entry_url(self):
        response = self.client.get('/blog/2013/jun/12/bad_url/')
        self.assertEqual(response.status_code, 404)

    def test_category(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['entry_list']), 0)
        self.assertEqual(len(response.context['category_list']), 2)

        self.entry1.categories.add(self.category)
        response_with_entry = self.client.get(self.category.get_absolute_url())
        self.assertEqual(len(response_with_entry.context['entry_list']), 1)
        self.assertEqual(len(response_with_entry.context['category_list']), 2)
        self.assertIn(self.entry1.title, response_with_entry.content.decode('utf-8'))

        response_bad_category = self.client.get('/blog/categories/wrong/')
        self.assertEqual(response_bad_category.status_code, 404)

    def test_tag_view(self):
        response = self.client.get('/blog/tag/{}/'.format(self.entry1.make_tag_list()[0]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['results']), 1)

        response_404 = self.client.get('/blog/tag/t/')
        self.assertEqual(response_404.status_code, 404)