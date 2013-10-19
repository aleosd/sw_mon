from django.db import models


# Create your models here.
class Graph(models.Model):
    path = models.FilePathField(path="/var/www/sw_mon/templates/static/img/", match=".*\.png$",
                                recursive=True)
    periods = (
        ('d', 'Daily'),
        ('w', 'Weekly'),
        ('m', 'Monthly'),
        ('y', 'Yearly'),
    )
    period = models.CharField(max_length=1, choices=periods,
                              verbose_name='Time period')

    isps = (
        ('ttk', 'TTK'),
        ('rtk', 'Rostelekom'),
        ('mgf', 'Megafon'),
        ('ttl', 'Total'),
    )
    isp = models.CharField(max_length=3, choices=isps,
                           verbose_name='ISP to filter traffic')
