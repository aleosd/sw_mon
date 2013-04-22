import re
from django.db import models
from django.core.exceptions import ValidationError
from smart_selects.db_fields import ChainedForeignKey


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
    ser = models.CharField(max_length=128)
    ser_ven = models.ForeignKey(Vendor)

    def __str__(self):
        return self.ser

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
    dev_mac = models.CharField(max_length=17,
                               help_text="MAC-address, separated by columns")
    dev_ven = models.ForeignKey(Vendor)
    dev_ser = ChainedForeignKey(
        Series,
        chained_field="dev_ven",
        chained_model_field="ser_ven",
        show_all=False,
        auto_choose=True
    )

    # Device history
    dev_purchase_date = models.DateField()

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
        return '{}-{}'.format(self.dev_ven, self.dev_ser)
