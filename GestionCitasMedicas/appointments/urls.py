from django.urls import path
from . import views

urlpatterns = [
    # Gestión de citas para pacientes
    path('create/', views.create_appointment, name='create_appointment'),
    path('patient/', views.patient_appointments, name='patient_appointments'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    # Gestión de citas para médicos
    path('doctor/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/calendar/', views.doctor_calendar, name='doctor_calendar'),
    
    # Disponibilidad del médico
    path('availability/<int:doctor_id>/', views.doctor_availability, name='doctor_availability'),
    
    # Indisponibilidades del médico (originales)
    path('unavailable/', views.mark_unavailable, name='mark_unavailable'),
    path('unavailable/list/', views.doctor_unavailabilities, name='doctor_unavailabilities'),
    path('unavailable/<int:unavailability_id>/', views.remove_unavailability, name='remove_unavailability'),
    
    # Estadísticas
    path('stats/', views.appointment_stats, name='appointment_stats'),
    
    # NUEVAS URLs
    path('doctors/', views.available_doctors, name='available_doctors'),
    path('detail/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('unavailable/range/', views.mark_unavailable_range, name='mark_unavailable_range'),
    path('unavailable/check-conflicts/', views.check_unavailability_conflicts, name='check_unavailability_conflicts'),
    path('update-status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
]