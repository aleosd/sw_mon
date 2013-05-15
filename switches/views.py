# Create your views here.
from datetime import datetime, timedelta
from django.shortcuts import render
from switches.models import Switch, Street, SwitchType, SwitchForm, Event
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone

@login_required
def index(request, status=None):
    if not status:
        switch_list = Switch.objects.select_related().filter(sw_enabled=True)
    if status == 'errors':
        switch_list = Switch.objects.select_related().filter(sw_ping=None)
    if status == 'warnings':
        switch_list = Switch.objects.select_related().filter(
            Q(sw_uptime__lt=86400) | Q(sw_uptime=None)
        )

    bad_uptime = 0
    bad_ping = 0
    for switch in switch_list:
        if switch.sw_enabled:
            if switch.sw_uptime == None or switch.sw_uptime < 86400:
                bad_uptime += 1
            if not switch.sw_ping:
                bad_ping += 1

    try:
        del request.session['instance']
    except:
        pass

    return render(request, 'mon/index.html',
                  {'status': status,
                   'bad_uptime': bad_uptime, 'bad_ping': bad_ping,
                   'switch_list': switch_list})

@login_required
def edit(request, id=None):
    if not id:
        return render(request, 'mon/edit.html', {'form': SwitchForm()})
    else:
        events = Event.objects.filter(ev_switch=id)[:10]
        switch = Switch.objects.get(id=id)
        form = SwitchForm(instance=switch)
        request.session['instance'] = switch
        return render(request, 'mon/edit.html', {'form': form, 'events': events})


@login_required
def create_switch(request):
    if request.method == 'POST':
        try:
            form = SwitchForm(request.POST, instance=request.session['instance'])
        except Exception:
            form = SwitchForm(request.POST)
        if form.is_valid():
            form.save()
            try:
                del request.session['instance']
            except:
                pass
            return HttpResponseRedirect('/')
        else:
            return render(request, 'mon/edit.html', {'form': form})

@login_required
def history(request, status=None):
    t = Event.objects.filter(ev_datetime__gte=timezone.now() - timedelta(days=1))
    # events_all = Event.objects.all()

    if status == "all":
        event_list = Event.objects.select_related().all().order_by('-id')
    elif status == "warnings":
        event_list = Event.objects.select_related().filter(ev_type='warn')[:30]
    elif status == "errors":
        event_list = Event.objects.select_related().filter(ev_type='err')

    paginator = Paginator(event_list, 50)
    page = request.GET.get('page')

    try:
        event_list = paginator.page(page)
    except PageNotAnInteger:
        event_list = paginator.page(1)
    except EmptyPage:
        event_list = paginator(paginator.num_pages)

    return render(request, 'mon/history.html', {'event_list': event_list,
                                            'status' : status,
                                            'events_per_day' : t})

