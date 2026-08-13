from django.contrib import admin

# Register your models here.
from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "age")
    list_filter = ("age",)
    search_fields = ("first_name", "last_name")