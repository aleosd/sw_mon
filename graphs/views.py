from django.shortcuts import render
from graphs.models import Graph
from django.db.models import Q
from django.http import Http404


def graph_by_query(request, query):
    imgs = Graph.objects.filter(Q(isp=query) | Q(period=query))
    if len(imgs) == 0:
        raise Http404
    return render(request, 'traf/graph_list.html', {'imgs': imgs})