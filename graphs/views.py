from django.shortcuts import render
from graphs.models import Graph
from django.http import Http404
from django.contrib.auth.decorators import login_required


@login_required
def graph_by_query(request, query, type_):
    if type_ == 'isp':
        imgs = Graph.objects.filter(isp=query)
    elif type_ == 'period':
        pd = {'daily': 'd',
              'weekly': 'w',
              'monthly': 'm',
              'yearly': 'y'}
        imgs = Graph.objects.filter(period=pd[query])
    if len(imgs) == 0:
        raise Http404
    return render(request, 'traf/graph_list.html', {'imgs': imgs})
