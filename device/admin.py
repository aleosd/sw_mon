from django.contrib import admin
from device.models import Device, Vendor, Series, Event

class VendorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Vendor, VendorAdmin)

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('dev_ven', 'dev_ser', 'dev_mac', 'id',)

admin.site.register(Device, DeviceAdmin)

class SeriesAdmin(admin.ModelAdmin):
    pass

admin.site.register(Series, SeriesAdmin)

class EventAdmin(admin.ModelAdmin):
    pass

admin.site.register(Event, EventAdmin)
