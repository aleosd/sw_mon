from django.conf.urls import patterns, url


urlpatterns = patterns('switches.views',
    url(r'^$', 'index'),
    url(r'^home/$', 'home_view'),
    url(r'^edit/(?P<id>\d+)/$', 'edit', name='edit'),
    url(r'^events/(?P<status>\w+)/$', 'history'),
    url(r'^view/(?P<id>\d+)/$', 'switch_view', name='view'),
    url(r'^status/(?P<status>\w+)/$', 'index'),
    url(r'^ping/$', 'ping_view'),
    url(r'^reboot/$', 'reboot_view'),
    url(r'^district/(?P<district>\w+)/$', 'by_district'),
    url(r'^clear/$', 'clear_history'),
)
