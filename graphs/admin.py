from django.contrib import admin
from graphs.models import Graph


class GraphAdmin(admin.ModelAdmin):
    list_display = ('path', 'isp', 'period')


admin.site.register(Graph, GraphAdmin)