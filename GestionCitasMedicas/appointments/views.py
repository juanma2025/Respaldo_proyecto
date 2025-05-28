from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta, time
from .models import Appointment, AppointmentHistory
from AppCitasMedicas.models import DoctorProfile, PatientProfile, DoctorSchedule
from .serializers import (
    AppointmentSerializer,
    CreateAppointmentSerializer,
    DoctorUnavailabilitySerializer,
    AppointmentHistorySerializer,
    DoctorAvailabilitySerializer,
    AppointmentStatsSerializer
)

# Vistas para pacientes
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_appointment(request):
    if request.user.user_type != 'patient':
        return Response({'error': 'Solo los pacientes pueden agendar citas.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    serializer = CreateAppointmentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        appointment = serializer.save()
        response_serializer = AppointmentSerializer(appointment)
        return Response({
            'message': 'Cita agendada exitosamente.',
            'appointment': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_appointments(request):
    if request.user.user_type != 'patient':
        return Response({'error': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
    
    patient = get_object_or_404(PatientProfile, user=request.user)
    
    # Filtros opcionales
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    appointments = Appointment.objects.filter(patient=patient)
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verificar permisos
    if (request.user.user_type == 'patient' and appointment.patient.user != request.user) or \
       (request.user.user_type == 'doctor' and appointment.doctor.user != request.user):
        return Response({'error': 'No tiene permisos para cancelar esta cita.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    if not appointment.can_be_cancelled:
        return Response({'error': 'Esta cita no puede ser cancelada.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Guardar historial
    AppointmentHistory.objects.create(
        appointment=appointment,
        previous_status=appointment.status,
        new_status='cancelled',
        changed_by=request.user.user_type,
        change_reason=request.data.get('reason', '')
    )
    
    appointment.status = 'cancelled'
    appointment.save()
    
    serializer = AppointmentSerializer(appointment)
    return Response({
        'message': 'Cita cancelada exitosamente.',
        'appointment': serializer.data
    }, status=status.HTTP_200_OK)

# Vistas para médicos
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_appointments(request):
    if request.user.user_type != 'doctor':
        return Response({'error': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    # Filtros opcionales
    date_from = request.GET.get('date_from', timezone.now().date())
    date_to = request.GET.get('date_to')
    status_filter = request.GET.get('status')
    
    appointments = Appointment.objects.filter(doctor=doctor)
    
    if date_from:
        appointments = appointments.filter(appointment_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(appointment_date__lte=date_to)
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    appointments = appointments.order_by('appointment_date', 'appointment_time')
    
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_calendar(request):
    if request.user.user_type != 'doctor':
        return Response({'error': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    # Obtener citas de la próxima semana
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    
    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__range=[today, next_week],
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')
    
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_unavailable(request):
    if request.user.user_type != 'doctor':
        return Response({'error': 'Solo los médicos pueden marcar indisponibilidad.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    serializer = DoctorUnavailabilitySerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save(doctor=doctor)
        return Response({
            'message': 'Indisponibilidad marcada exitosamente.',
            'unavailability': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_unavailabilities(request):
    if request.user.user_type != 'doctor':
        return Response({'error': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    unavailabilities = DoctorUnavailability.objects.filter(
        doctor=doctor,
        date__gte=timezone.now().date()
    ).order_by('date', 'start_time')
    
    serializer = DoctorUnavailabilitySerializer(unavailabilities, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_unavailability(request, unavailability_id):
    if request.user.user_type != 'doctor':
        return Response({'error': 'Acceso denegado.'}, status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    unavailability = get_object_or_404(DoctorUnavailability, id=unavailability_id, doctor=doctor)
    
    unavailability.delete()
    return Response({'message': 'Indisponibilidad eliminada exitosamente.'}, 
                   status=status.HTTP_200_OK)

# Vistas de utilidad
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_availability(request, doctor_id):
    """Obtiene los horarios disponibles de un médico para una fecha específica"""
    date_str = request.GET.get('date')
    if not date_str:
        return Response({'error': 'Debe proporcionar una fecha.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if date <= timezone.now().date():
        return Response({'error': 'No se pueden agendar citas en fechas pasadas.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    doctor = get_object_or_404(DoctorProfile, id=doctor_id, is_available=True)
    weekday = date.weekday()
    
    # Obtener horarios del médico para ese día
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        weekday=weekday,
        is_available=True
    )
    
    if not schedules.exists():
        return Response({
            'date': date,
            'available_times': []
        }, status=status.HTTP_200_OK)
    
    available_times = []
    
    for schedule in schedules:
        # Generar slots de 30 minutos
        current_time = schedule.start_time
        while current_time < schedule.end_time:
            # Verificar si no hay cita programada
            appointment_exists = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                appointment_time=current_time,
                status__in=['scheduled', 'confirmed']
            ).exists()
            
            # Verificar si no hay indisponibilidad marcada
            unavailable = DoctorUnavailability.objects.filter(
                doctor=doctor,
                date=date,
                start_time__lte=current_time,
                end_time__gt=current_time
            ).exists()
            
            if not appointment_exists and not unavailable:
                available_times.append(current_time)
            
            # Agregar 30 minutos
            current_datetime = datetime.combine(date, current_time)
            current_datetime += timedelta(minutes=30)
            current_time = current_datetime.time()
    
    return Response({
        'date': date,
        'available_times': available_times
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_stats(request):
    """Obtiene estadísticas de citas para el usuario actual"""
    user = request.user
    
    if user.user_type == 'patient':
        patient = get_object_or_404(PatientProfile, user=user)
        appointments = Appointment.objects.filter(patient=patient)
    elif user.user_type == 'doctor':
        doctor = get_object_or_404(DoctorProfile, user=user)
        appointments = Appointment.objects.filter(doctor=doctor)
    else:
        return Response({'error': 'Tipo de usuario inválido.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    stats = {
        'total_appointments': appointments.count(),
        'scheduled_appointments': appointments.filter(status='scheduled').count(),
        'completed_appointments': appointments.filter(status='completed').count(),
        'cancelled_appointments': appointments.filter(status='cancelled').count(),
        'upcoming_appointments': appointments.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).count()
    }
    
    serializer = AppointmentStatsSerializer(stats)
    return Response(serializer.data, status=status.HTTP_200_OK)