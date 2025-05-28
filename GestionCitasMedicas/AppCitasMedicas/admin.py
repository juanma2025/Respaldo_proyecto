from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, DoctorProfile, DoctorSchedule, DoctorUnavailability

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'user_type', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_email_verified', 'is_active', 'date_joined')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('full_name', 'phone_number')}),
        ('Permisos', {'fields': ('user_type', 'is_email_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'emergency_contact', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__full_name', 'user__email', 'emergency_contact')
    raw_id_fields = ('user',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'professional_license', 'is_available', 'created_at')
    list_filter = ('specialty', 'is_available', 'created_at')
    search_fields = ('user__full_name', 'user__email', 'professional_license')
    raw_id_fields = ('user',)

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_weekday_display', 'start_time', 'end_time', 'is_available')
    list_filter = ('weekday', 'is_available')
    search_fields = ('doctor__user__full_name',)

@admin.register(DoctorUnavailability)
class DoctorUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'reason')
    list_filter = ('date',)
    search_fields = ('doctor__user__full_name', 'reason')

admin.site.register(User, UserAdmin)