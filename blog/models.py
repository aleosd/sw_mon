from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from markdown import markdown

# Create your models here.
class Category(models.Model):
    title = models.CharField(max_length=250, help_text='Maximum 250 characters')
    slug = models.SlugField(unique=True,
                            help_text='Generated from title. Must be unique')
    description = models.TextField()

    class Meta:
        ordering = ['title']
        verbose_name_plural = "Categories"

    def get_absolute_url(self):
        return "/blog/categories/{}/".format(self.slug)

    def __str__(self):
        return self.title

class Entry(models.Model):
    title = models.CharField(max_length=250)
    excerpt = models.TextField(blank=True)
    body = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(unique_for_date='pub_date')
    author = models.ForeignKey(User)
    enable_comments = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)

    # for future searching
    keywords = models.CharField(max_length=250, blank=True)

    LIVE_STATUS = 1
    DRAFT_STATUS = 2
    HIDDEN_STATUS = 3
    STATUS_CHOICES = (
        (LIVE_STATUS, 'Live'),
        (DRAFT_STATUS, 'Draft'),
        (HIDDEN_STATUS, 'Hidden'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=LIVE_STATUS)
    categories = models.ManyToManyField(Category)

    excerpt_html = models.TextField(editable=False, blank=True)
    body_html = models.TextField(editable=False, blank=True)

    def save(self, force_insert=False, force_update=False):
        self.body_html = markdown(self.body)
        if self.excerpt:
            self.excerpt_html = markdown(self.excerpt)
        super(Entry, self).save(force_insert, force_update)

    def make_tag_list(self):
        return self.keywords.replace(' ', '').split(',')

    class Meta:
        verbose_name_plural = "Entries"
        ordering = ['-pub_date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return "/blog/{}/{}/".format(self.pub_date.strftime("%Y/%b/%d").lower(),
                                    self.slug)
