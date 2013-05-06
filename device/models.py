import re
import datetime
from django.db import models
from django.core.exceptions import ValidationError
from smart_selects.db_fields import ChainedForeignKey
from django.db.models.signals import post_save, post_init, post_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


_NEW_DEVICE = False

def validate_mac(value):
    allowed = re.template('[\:A-Fa-f0-9]')
    for letter in value:
        if not allowed.findall(letter):
            raise ValidationError('{} is not allowed symbol for MAC'.format(value))


class Vendor(models.Model):
    ven = models.CharField(max_length=16)

    def __str__(self):
        return self.ven


class Series(models.Model):

    class Meta:
        verbose_name_plural='Serieses'

    ser = models.CharField(max_length=128)
    ser_ven = models.ForeignKey(Vendor)

    def __str__(self):
        return str(self.ser_ven) + '-' + self.ser

"""
class Type(models.Model):
    type_ven = models.CharField(max_length=16)
    type_models = models.TextField(help_text="Input models, separated \
                                    with semicolon")

    def model_list(self):
        '''Type -> list

        Returns models from type_models field, splitted and formatted
        as list.
        '''
        return [s.strip() for s in self.type_models.split(';')]

    def model_by_number(self, num):
        '''Type, int -> list

        Returns model from model_list by given index number.
        '''
        l = self.model_list()
        return l[num -1]
"""


class Device(models.Model):
    # Device info
    dev_mac = models.CharField(max_length=17, unique=True,
                               verbose_name = 'MAC-address',
                               help_text="MAC-address, separated by columns")
    dev_ven = models.ForeignKey(Vendor, verbose_name = 'Device Vendor')
    dev_ser = ChainedForeignKey(
        Series,
        chained_field="dev_ven",
        chained_model_field="ser_ven",
        show_all=False,
        auto_choose=True,
        verbose_name = 'Device Series',
    )

    # Device history
    dev_purchase_date = models.DateField()
    dev_comments = models.TextField(blank=True)

    # Device status
    WORKING = 0
    NEED_REPAIR = 1
    BROKEN = 2
    ON_STORE = 3
    STATUS_CHOICES = (
        (WORKING, 'Working'),
        (NEED_REPAIR, 'Need Repair'),
        (BROKEN, 'Broken'),
        (ON_STORE, 'On Store'),
    )
    dev_state = models.IntegerField(choices=STATUS_CHOICES, default=ON_STORE)

    def __str__(self):
        return '{}-{} ({})'.format(self.dev_ven, self.dev_ser, self.id)


class Event(models.Model):
    # Main fields
    ev_dtime = models.DateTimeField(default=datetime.datetime.now)
    ev_message = models.CharField(max_length=255)

    ev_device = models.ForeignKey(Device, blank=True, null=True)

    # Event types, for logging
    INFO = 0
    WARNING = 1
    ERROR = 2
    EVENT_TYPE = (
        (INFO, 'Info'),
        (WARNING, 'Warning'),
        (ERROR, 'Error')
    )
    ev_type = models.IntegerField(choices=EVENT_TYPE, default=INFO)

    def __str__(self):
        return "{} - {}, {}".format(self.get_ev_type_display(), self.ev_message,
                                    self.ev_device)


@receiver(post_save, sender=Device)
def dev_changed(sender, **kwargs):
    '''Function called to add new event after save method of Device object.
    According to global variable, text of event changes.
    '''
    global _NEW_DEVICE
    if _NEW_DEVICE:
        message_text = 'Added new device'
        type_num = 0
    else:
        message_text = 'Device modified'
        type_num = 1
    e = Event(
        ev_message=message_text,
        ev_type=type_num,
        ev_device=kwargs['instance']
    )
    e.save()
    _NEW_DEVICE = False

@receiver(post_init, sender=Device)
def dev_init(sender, **kwargs):
    '''Checking, if device new or existing modification. If new -
    setting global var to True, for correct event record.
    '''
    try:
        kwargs['instance'].dev_ven
    except ObjectDoesNotExist:
        global _NEW_DEVICE
        _NEW_DEVICE = True


@receiver(post_delete, sender=Device)
def dev_deleted(sender, **kwargs):
    '''Adding new event record on Device deletion.
    '''
    message_text = "Device {} was deleted from database".format(str(kwargs['instance']))
    e = Event(
        ev_message = message_text,
        ev_type=2,
        ev_device=None,
        )
    e.save()
