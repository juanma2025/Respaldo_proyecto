from django.urls import path
from . import views

urlpatterns = [
    # Registro y autenticación
    path('register/patient/', views.register_patient, name='register_patient'),
    path('register/doctor/', views.register_doctor, name='register_doctor'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('auth/verify-email/<str:token>/', views.verify_email_get, name='verify_email_get'),
    path('auth/resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # Perfil de usuario
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # Médicos y especialidades
    path('doctors/', views.get_doctors_by_specialty, name='get_doctors'),
    path('specialties/', views.get_specialties, name='get_specialties'),
    
    # Horarios de médicos
    path('schedules/', views.DoctorScheduleListCreate.as_view(), name='doctor_schedules'),
    path('schedules/<int:pk>/', views.DoctorScheduleDetail.as_view(), name='doctor_schedule_detail'),
]