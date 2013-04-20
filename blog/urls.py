from django.conf.urls import patterns, url


urlpatterns = patterns('blog.views',
    url(r'^$', 'entries_index'),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{2})/(?P<slug>[-\d\w]+)/$',
        'entry_detail'),
)
