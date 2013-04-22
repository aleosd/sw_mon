from django.contrib import admin
from device.models import Device, Vendor, Series

class VendorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Vendor, VendorAdmin)

class DeviceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Device, DeviceAdmin)

class SeriesAdmin(admin.ModelAdmin):
    pass

admin.site.register(Series, SeriesAdmin)
