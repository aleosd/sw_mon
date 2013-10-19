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
<<<<<<< HEAD
=======

    def get_web_url(self):
        return self.path.split('static/')[-1]
>>>>>>> 8be2ca203834b64c7937ae933541abe71a26379a
