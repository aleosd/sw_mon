from django.contrib import admin
from blog.models import Category, Entry
from django.db import models
from django.forms import Textarea

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ['title']}

admin.site.register(Category, CategoryAdmin)

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'pub_date',)
    prepopulated_fields = {'slug': ['title']}

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':20, 'cols':150})},
    }

admin.site.register(Entry, EntryAdmin)
