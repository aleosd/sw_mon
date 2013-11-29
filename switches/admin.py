from django.contrib import admin
from switches.models import Switch, SwitchType, Street, Event


class SwitchAdmin(admin.ModelAdmin):
    list_display = ('ip_addr', 'sw_street', 'sw_build_num',
                    'sw_district', 'sw_type_colored', 'sw_enabled')

    fieldsets = [
        ('Basics', {'fields': ['ip_addr', 'sw_type', 'sw_id']}),
        ('Address', {'fields': ['sw_district', 'sw_street', 'sw_build_num']}),
        ('Other', {'fields': ['sw_enabled', 'sw_backup_conf', 'sw_uplink',
                              'sw_comment', 'sw_device', 'sw_uptime_to_reboot'],
                   'classes': ['collapse']})
    ]

    search_fields = ['sw_street__street', 'sw_district', 'sw_type__sw_type']
    list_filter = ('sw_district', 'sw_enabled')
    actions = ['disable', 'enable']

    def disable(self, request, queryset):
        sw_updated = queryset.update(sw_enabled=False)
        if sw_updated == 1:
            self.message_user(request, "1 switch was successfully disabled")
        else:
            self.message_user(request,
                              "{} switches were disabled".format(sw_updated))
    disable.short_description = "Disable selected switch check"

    def enable(self, request, queryset):
        sw_updated = queryset.update(sw_enabled=True)
        if sw_updated == 1:
            self.message_user(request, "1 switch was successfully enabled")
        else:
            self.message_user(request,
                              "{} switches were enabled".format(sw_updated))
    enable.short_description = "Enable selected switch check"

admin.site.register(Switch, SwitchAdmin)
admin.site.register(SwitchType)

class StreetAdmin(admin.ModelAdmin):
    list_display = ('street',)


admin.site.register(Street, StreetAdmin)

class EventAdmin(admin.ModelAdmin):
    list_display = ('ev_switch', 'ev_type', 'ev_datetime')

admin.site.register(Event, EventAdmin)
