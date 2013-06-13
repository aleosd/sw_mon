from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    url(r'^new/$', 'switches.views.edit'),
    url(r'^create/', 'switches.views.create_switch'),
    url(r'^logout/', 'django.contrib.auth.views.logout', {'next_page': '/login/'}),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += i18n_patterns('',
    url(r'^$', 'switches.views.home_view'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^blog/', include('blog.urls')),
    url(r'^mon/', include('switches.urls')),
)
