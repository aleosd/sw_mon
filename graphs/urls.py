from django.conf.urls import patterns, url
from django.views.generic import RedirectView


urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='isp/ttl/')),
    url(r'^isp/(?P<query>\w+)', 'graphs.views.graph_by_query', {'type_': 'isp'}),
    url(r'^period/(?P<query>\w+)', 'graphs.views.graph_by_query', {'type_': 'period'}),
    )
