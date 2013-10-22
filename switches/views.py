# Create your views here.
from datetime import timedelta
from django.shortcuts import render
from switches.models import Switch, SwitchForm, Event
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone

from helper_progs import switch as hp_switch


@login_required
def index(request, status='all'):
    switch_list = Switch.objects.select_related(
            'sw_street',
            'sw_type',
            'sw_device',
            'sw_device__dev_ven',
            'sw_device__dev_ser',
            'sw_device__dev_ser__ser_ven',
        )
    enabled_switch_list = [switch for switch in switch_list if switch.sw_enabled]
    sw_enabled = len(enabled_switch_list)
    warning_switch_list = [switch for switch in enabled_switch_list if (switch.sw_uptime and
                            (switch.sw_uptime < 86400 or not switch.sw_uptime))]
    sw_warning = len(warning_switch_list)
    error_switch_list = [switch for switch in enabled_switch_list if switch.sw_ping is None]
    sw_error = len(error_switch_list)
    disabled_switch_list = [switch for switch in switch_list if not switch.sw_enabled]
    sw_disabled = len(disabled_switch_list)

    if status == 'all':
        switch_list = switch_list
    elif status == 'errors':
        switch_list = error_switch_list
    elif status == 'warnings':
        switch_list = warning_switch_list
    elif status == 'disabled':
        switch_list = disabled_switch_list
    else:
        raise Http404

    if 'instance' in request.session:
        del request.session['instance']

    return render(request, 'mon/index.html',
                  {'status': status,
                   'sw_enabled': sw_enabled,
                   'sw_warning': sw_warning,
                   'sw_error': sw_error,
                   'switch_list': switch_list,
                   'sw_disabled': sw_disabled,
                   'sw_all': sw_enabled + sw_disabled})


@login_required
def edit(request, id=None):
    if not id:
        return render(request, 'mon/edit.html', {'form': SwitchForm()})
    else:
        events = Event.objects.filter(ev_switch=id)[:20]
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
            if 'instance' in request.session:
                del request.session['instance']
            return HttpResponseRedirect('/mon/')
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
                                                'status': status,
                                                'events_per_day': t})


@login_required
def home_view(request):
    total_switches = Switch.objects.all().count()
    disabled_switches = Switch.objects.filter(sw_enabled=False).count()
    error_switches = Switch.objects.filter(sw_ping=None, sw_enabled=True).count()
    warning_switches = Switch.objects.filter(sw_uptime__lt=86400).count()
    return render(request, 'mon/home.html',
        {'total_switches': total_switches,
         'disabled_switches': disabled_switches,
         'error_switches': error_switches,
         'warning_switches': warning_switches})


@login_required
def switch_view(request, id):
    events = Event.objects.filter(ev_switch=id)[:30]
    switch = Switch.objects.select_related().get(id=id)
    return render(request, 'mon/view.html', {'switch': switch,
                                             'events': events})


def ping_view(request):
    if request.method == 'POST':
        id = request.POST['id']
        switch = Switch.objects.select_related().get(id=id)
        host = hp_switch.Host(switch.ip_addr)
        return_data = host.sys_ping(packet_count=4, verbose=True)
        return_data = return_data.split('\n')
    else:
        return_data = None
    return render(request, 'mon/ping_view.html', {'return_data': return_data})
