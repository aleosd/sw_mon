# Create your views here.
from django.shortcuts import render
from switches.models import Switch, Street, SwitchType
from django.contrib.auth.decorators import login_required

@login_required
def index(request, status=None):
    if not status:
        switch_list = Switch.objects.all()
    if status == 'errors':
        switch_list = Switch.objects.filter(sw_ping=None)
    if status == 'warnings':
        switch_list = Switch.objects.filter(sw_uptime__lt=86400)

    street_list = Street.objects.all()
    street_dic = {}
    for street in street_list:
        street_dic[street.id] = street.street

    sw_type_list = SwitchType.objects.all()
    sw_type_dic = {}
    for sw_type in sw_type_list:
        sw_type_dic[sw_type.id] = sw_type.sw_type

    render_dict = {}
    for switch in switch_list:
        render_dict[switch.id] = {'sw_id': switch.sw_id,
                                  'sw_street': street_dic[switch.sw_street_id],
                                  'sw_build_num': switch.sw_build_num,
                                  'ip_addr': switch.ip_addr,
                                  'sw_ping': switch.sw_ping,
                                  'sw_uptime': switch.sw_uptime_str,
                                  'sw_type': sw_type_dic[switch.sw_type_id],
        }
    print(render_dict)
    return render(request, 'index.html',
                  {'switch_list': switch_list, 'status': status, 'render_dict': render_dict,})
