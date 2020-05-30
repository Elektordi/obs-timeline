from django.contrib import admin

from .models import Show, Sequence


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']
    ordering = ['-date']


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'wait_signal', 'target', 'duration', 'lock_duration', 'show']
    ordering = ['show__date', 'target']
    list_filter = ['show']
