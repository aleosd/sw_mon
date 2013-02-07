# Create your views here.
from django.shortcuts import render
from switches.models import Switch, Street, SwitchType, SwitchForm, Event
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect

@login_required
def index(request, status=None):
    if not status:
        switch_list = Switch.objects.all()
    if status == 'errors':
        switch_list = Switch.objects.filter(sw_ping=None)
    if status == 'warnings':
        switch_list = Switch.objects.filter(
            Q(sw_uptime__lt=86400) | Q(sw_uptime=None)
        )

    street_list = Street.objects.all()
    street_dic = {}
    for street in street_list:
        street_dic[street.id] = street.street

    sw_type_list = SwitchType.objects.all()
    sw_type_dic = {}
    for sw_type in sw_type_list:
        sw_type_dic[sw_type.id] = sw_type.sw_type

    render_dict = {}
    bad_uptime = 0
    bad_ping = 0
    for switch in switch_list:
        if switch.sw_enabled:
            if switch.sw_uptime == None or switch.sw_uptime < 86400:
                bad_uptime += 1
            if not switch.sw_ping:
                bad_ping += 1
            render_dict[switch.id] = {'id': switch.id,
                                      'sw_id': switch.sw_id,
                                      'sw_street': street_dic[switch.sw_street_id],
                                      'sw_build_num': switch.sw_build_num,
                                      'ip_addr': switch.ip_addr,
                                      'sw_ping': switch.sw_ping,
                                      'sw_uptime': switch.sw_uptime_str,
                                      'sw_uptime_sec': switch.sw_uptime,
                                      'sw_type': sw_type_dic[switch.sw_type_id],
                                      'sw_comment': switch.sw_comment,
            }
    return render(request, 'index.html',
                  {'status': status, 'render_dict': render_dict,
                   'bad_uptime': bad_uptime, 'bad_ping': bad_ping})

def edit(request, id=None):
    if not id:
        return render(request, 'edit.html', {'form': SwitchForm()})
    else:
        switch = Switch.objects.get(id=id)
        form = SwitchForm(instance=switch)
        request.session['instance'] = switch
        return render(request, 'edit.html', {'form': form})


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
            return render(request, 'edit.html', {'form': form})

def history(request, status=None):
    event_list = Event.objects.select_related().all().order_by('-id')[:30]
    render_dict = {}
    for event in event_list:
        render_dict[event.id] = {'ev_datetime': event.ev_datetime,
                                'ev_type': event.ev_type,
                                'ev_switch_id': event.ev_switch_id,
                                'ev_event': event.ev_event,
                                'ev_comment': event.ev_comment}
    # return render(request, 'history.html', {'render_dict': render_dict})
    return render(request, 'history.html', {'event_list': event_list})
