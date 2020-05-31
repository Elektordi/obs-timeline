from django.contrib import admin

from .models import Show, Sequence, Live


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['name', 'date']
    ordering = ['-date']
    actions = ["go_live"]

    def go_live(self, request, queryset):
        if queryset.count() != 1:
            return
        live = Live.get()
        live.active_show = queryset.first()
        live.active_sequence = None
        live.save()


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'wait_signal', 'target', 'duration', 'lock_duration', 'show']
    ordering = ['show__date', 'target']
    list_filter = ['show']
