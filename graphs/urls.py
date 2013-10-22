from django.conf.urls import patterns, url


urlpatterns = patterns('graphs.views',
    url(r'^$', 'graph_by_query', {'query': 'ttl', 'type_': 'isp'}),
    url(r'^isp/(?P<query>\w+)', 'graph_by_query', {'type_': 'isp'}),
    url(r'^period/(?P<query>\w+)', 'graph_by_query', {'type_': 'period'}),
    )
