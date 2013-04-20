from django.conf.urls import patterns, url


urlpatterns = patterns('switches.views',
    url(r'^events/(?P<status>\w+)/$', 'history'),
    url(r'^(?P<status>\w+)/$', 'index'), 
) 
