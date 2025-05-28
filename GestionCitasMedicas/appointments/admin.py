from django.contrib import admin
from .models import Appointment, AppointmentHistory

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('status', 'appointment_date', 'created_at')
    search_fields = ('patient__user__full_name', 'doctor__user__full_name', 'reason')
    date_hierarchy = 'appointment_date'
    raw_id_fields = ('patient', 'doctor')
    
    fieldsets = (
        ('Información de la Cita', {
            'fields': ('patient', 'doctor', 'appointment_date', 'appointment_time', 'duration_minutes')
        }),
        ('Detalles', {
            'fields': ('reason', 'notes', 'status')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'previous_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('previous_status', 'new_status', 'changed_by', 'changed_at')
    search_fields = ('appointment__patient__user__full_name', 'appointment__doctor__user__full_name')
    readonly_fields = ('changed_at',)