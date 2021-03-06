# Create your views here.
import os
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.servers.basehttp import FileWrapper
from switches.models import Switch, SwitchForm, Event
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, Http404, HttpResponseNotAllowed
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from helper_progs import switch as hp_switch
from helper_progs import reboot


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
    warning_switch_list = [switch for switch in enabled_switch_list if (switch.sw_ping and
                            (not switch.sw_uptime or switch.sw_uptime < 86400))]
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
@permission_required('switches.change_switch')
def edit(request, id=None):
    if not id:
        return render(request, 'mon/edit.html', {'form': SwitchForm()})
    else:
        events = Event.objects.filter(ev_switch=id)[:20].select_related()
        switch = Switch.objects.select_related().get(id=id)
        form = SwitchForm(instance=switch)
        request.session['instance'] = switch
        return render(request, 'mon/edit.html', {'form': form, 'events': events})


@login_required
@permission_required('switches.add_switch')
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
    t = Event.objects.filter(ev_datetime__gte=timezone.now() - timedelta(days=1)).count()
    # events_all = Event.objects.all()

    if status == "all":
        event_list = Event.objects.select_related().all().order_by('-id')
    elif status == "warnings":
        event_list = Event.objects.select_related().filter(ev_type='warn')
    elif status == "errors":
        event_list = Event.objects.select_related().filter(ev_type='err')
    else:
        raise Http404

    paginator = Paginator(event_list, 50)
    page = request.GET.get('page')

    try:
        event_list = paginator.page(page)
    except PageNotAnInteger:
        event_list = paginator.page(1)
    except EmptyPage:
        event_list = paginator.page(paginator.num_pages)

    return render(request, 'mon/history.html', {'event_list': event_list,
                                                'status': status,
                                                'events_per_day': t})


@login_required
@permission_required('switches.change_switch')
def clear_history(request):
    if request.method == 'POST':
        id = request.POST['id']
        try:
            Event.objects.filter(ev_switch=id).delete()
            clear_event = Event()
            clear_event.ev_switch = Switch.objects.get(id=id)
            clear_event.ev_type = 'warn'
            clear_event.ev_event = 'History was cleaned manually'
            clear_event.save()
        except ObjectDoesNotExist:
            raise Http404
        return HttpResponse(content_type="text/html")
    else:
        return HttpResponseNotAllowed(['POST'])


@login_required
def home_view(request):
    total_switches = Switch.objects.all().select_related()
    disabled_switches = len([ sw for sw in total_switches if not sw.sw_enabled])
    error_switches = [sw for sw in total_switches if (not sw.sw_ping and sw.sw_enabled)]
    warning_switches = len([sw for sw in total_switches if sw.sw_uptime and sw.sw_uptime < 86400])
    events_per_day = Event.objects.filter(ev_datetime__gte=timezone.now() - timedelta(days=1)) # .select_related()
    last_events = [ev for ev in events_per_day][:4]
    return render(request, 'mon/home.html',
        {'total_switches': len(total_switches),
         'disabled_switches': disabled_switches,
         'error_switches': error_switches,
         'warning_switches': warning_switches,
         'events_per_day': len(events_per_day),
         'last_events': last_events})


@login_required
def switch_view(request, id):
    try:
        switch = Switch.objects.select_related().get(id=id)
    except ObjectDoesNotExist:
        raise Http404
    events = Event.objects.filter(ev_switch=id)[:30].select_related()
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
        return HttpResponseNotAllowed(['POST'])
    return render(request, 'mon/ping_view.html', {'return_data': return_data})


@login_required()
@permission_required('switches.change_switch')
def reboot_view(request):
    if request.method == 'POST':
        id = request.POST['id']
        try:
            switch = Switch.objects.select_related().get(id=id)
            reboot.reboot(switch.ip_addr)
            return_data = 'Successfully processed with reboot. Check uptime in 5 minutes'
        except ObjectDoesNotExist:
            return_data = 'No such switch in the database'
    else:
        return HttpResponseNotAllowed(['POST'])
    return render(request, 'mon/reboot_view.html', {'return_data': return_data})


@login_required()
def by_district(request, district):
    if district not in [distr[0] for distr in Switch.districts]:
        raise Http404
    switch_list = Switch.objects.select_related(
        'sw_street',
        'sw_type',
        'sw_device',
        'sw_device__dev_ven',
        'sw_device__dev_ser',
        'sw_device__dev_ser__ser_ven',
    ).filter(sw_district=district)
    return render(request, 'mon/index.html', {'switch_list': switch_list})


@login_required()
def config_download(request, file_name):
    file_path = settings.MEDIA_ROOT + 'configs/' + file_name
    if not os.path.isfile(file_path):
        raise Http404
    wrapper = FileWrapper(open(file_path, 'r'))
    response = HttpResponse(wrapper, mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)
    response['Content-Length'] = os.path.getsize(file_path)
    response['X-Sendfile'] = file_path
    return response
