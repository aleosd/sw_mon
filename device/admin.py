from django.contrib import admin
from device.models import Device, Vendor, Series, Event

class VendorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Vendor, VendorAdmin)

class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id','dev_location', 'dev_ser', 'dev_mac', 'dev_state',)
    list_display_links = ('dev_ser',)

    search_fields = ['dev_mac',]
    list_filter = ['dev_state', 'dev_ven']

admin.site.register(Device, DeviceAdmin)

class SeriesAdmin(admin.ModelAdmin):
    pass

admin.site.register(Series, SeriesAdmin)

class EventAdmin(admin.ModelAdmin):
    pass

admin.site.register(Event, EventAdmin)
