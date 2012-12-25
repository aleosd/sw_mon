# Create your views here.
from django.shortcuts import render
from switches.models import Switch
from django.contrib.auth.decorators import login_required

@login_required
def index(request, status=None):
    if not status:
        switch_list = Switch.objects.all()
    if status == 'errors':
        switch_list = Switch.objects.filter(sw_ping=None)
    if status == 'warnings':
        switch_list = Switch.objects.filter(sw_uptime__lt=86400)
    return render(request, 'switches/index.html', 
                  {'switch_list': switch_list, 'status': status})
