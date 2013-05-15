from django.contrib import admin
from blog.models import Category, Entry

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['title']}

admin.site.register(Category, CategoryAdmin)

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'pub_date',)
    prepopulated_fields = {'slug': ['title']}

admin.site.register(Entry, EntryAdmin)