import re
import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django import forms
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.utils import timezone
from device.models import Device


def validate_build(value):
    allowed = re.template('[а-я0-9]')
    for letter in value:
        if not allowed.findall(letter):
            raise ValidationError('{} is not allowed build number'.format(value))


class SwitchType(models.Model):
    sw_type = models.CharField(max_length=100, verbose_name='switch type')

    def __str__(self):
        return self.sw_type


class Street(models.Model):
    street = models.CharField(max_length=100, verbose_name='street')

    class Meta:
        ordering = ('street',)

    def __str__(self):
        return self.street


class Switch(models.Model):
    ip_addr = models.IPAddressField(verbose_name='ip address', unique=True)
    districts = (
        ('mzv', 'Машзавод'),
        ('vkz', 'Вокзал'),
        ('szp', 'Северо-Запад'),
        ('ggn', 'Гагарина'))
    sw_district = models.CharField(max_length=3, choices=districts,
                                   verbose_name='District')
    sw_street = models.ForeignKey(Street, verbose_name='street')
    sw_build_num = models.CharField(max_length=4, validators=[validate_build],
                                    verbose_name='Building number')
    sw_type = models.ForeignKey(SwitchType, verbose_name='switch type')
    sw_id = models.IntegerField(unique=True)
    sw_enabled = models.BooleanField(default=True, verbose_name='Enabled')
    sw_ping = models.FloatField(blank=True, null=True, editable=False)
    sw_uptime = models.IntegerField(blank=True, null=True, editable=False)
    sw_uplink = models.CharField(max_length=200, blank=True, null=True,
                                 verbose_name='Uplink ports',
                                 help_text='Enter port numbers, separated with commas')
    sw_comment = models.CharField(max_length=500, blank=True, null=True,
                                  verbose_name='Comments')
    
    sw_device = models.ForeignKey(Device, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Switches"

    def __str__(self):
        return '{} - {}, {}'.format(self.ip_addr, self.sw_street,
                                    self.sw_build_num)

    def sw_addr(self):
        return '{}, {}'.format(self.sw_street, self.sw_build_num)
    sw_addr.admin_order_field = 'sw_street'

    def sw_type_colored(self):
        if str(self.sw_type) == 'Unmanaged':
            return '<span style="color: #%s;">%s</span>' % (980000, self.sw_type)
        return self.sw_type
    sw_type_colored.allow_tags = True
    sw_type_colored.admin_order_field = 'sw_type'

    def sw_uptime_str(self):
        return datetime.timedelta(seconds=self.sw_uptime)

    def get_absolute_url(self):
        return "/mon/edit/%i/" % self.id


class SwitchForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SwitchForm, self).__init__(*args, **kwargs)

        if self.instance.sw_device:
            print(self.instance.sw_device)
            self.fields['sw_device'].queryset = Device.objects.filter(pk=self.instance.sw_device_id)
            # self.sw_device = self.instance.sw_device
        else:
            self.fields['sw_device'].queryset = Device.objects.filter(dev_state=3)

    class Meta:
        model = Switch


class Event(models.Model):
    ev_datetime = models.DateTimeField(auto_now_add=True,
                                       verbose_name='Date and time')
    types = (('info', 'Info'),
            ('warn', 'Warning'),
            ('err', 'Error'))
    ev_type = models.CharField(max_length=4, choices=types,
                               verbose_name='Event type')
    ev_switch = models.ForeignKey(Switch)
    ev_event = models.CharField(max_length=500, verbose_name='Event')
    ev_comment = models.CharField(max_length=500, blank=True, null=True,
                                  verbose_name='Comments')

    class Meta:
        ordering = ['-ev_datetime']

    def ev_type_colored(self):
        if str(self.ev_type) == 'err':
            return '<span style="color: #%s;">%s</span>' % ('ff0000', 'Error')
        elif str(self.ev_type) == 'info':
            return '<span style="color: #%s;">%s</span>' % ('00ff33', 'Info')
        elif str(self.ev_type) == 'warn':
            return '<span style="color: #%s;">%s</span>' % ('ffcc33', 'Warning')
        return self.ev_type
    ev_type_colored.allow_tags = True
    ev_type_colored.admin_order_field = 'sw_type'


@receiver(post_save, sender=Switch)
def dev_changed(sender, **kwargs):
    '''Function called to change ForeignKey Device save method of Switch object.
    '''
    sw = kwargs['instance']
    if sw.sw_device:
        sw.sw_device.dev_state = 0
        sw.sw_device.dev_location = sw.sw_addr()
        sw.sw_device.save()
        print(sw.sw_addr())
        print(sender.sw_addr)
        print(sw.sw_device.dev_mac)
        print(sw.sw_device.dev_location)
    else:
        pass
