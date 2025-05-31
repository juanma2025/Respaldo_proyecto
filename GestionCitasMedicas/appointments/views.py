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
    DoctorUnavailabilitySerializer,DoctorUnavailability,
    AppointmentHistorySerializer,
    DoctorAvailabilitySerializer,
    AppointmentStatsSerializer
)
from datetime import datetime, timedelta, time
from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from datetime import timedelta

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

class PatientAppointmentListView(generics.ListAPIView):
    """
    Vista para que los pacientes vean todas sus citas
    Permite filtros por estado y fechas
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Verificar que sea un paciente
        if self.request.user.user_type != 'patient':
            raise PermissionDenied("Solo los pacientes pueden ver sus citas.")
        
        # Obtener el perfil del paciente
        patient_profile = get_object_or_404(PatientProfile, user=self.request.user)
        
        # Queryset base
        queryset = Appointment.objects.filter(patient=patient_profile)
        
        # Filtros opcionales desde query params
        status_filter = self.request.query_params.get('status', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        upcoming_only = self.request.query_params.get('upcoming', None)
        
        # Filtrar por estado
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtrar por rango de fechas
        if date_from:
            try:
                date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__gte=date_from)
            except ValueError:
                pass  # Ignorar formato inválido
        
        if date_to:
            try:
                date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(appointment_date__lte=date_to)
            except ValueError:
                pass  # Ignorar formato inválido
        
        # Solo citas futuras
        if upcoming_only and upcoming_only.lower() == 'true':
            queryset = queryset.filter(
                appointment_date__gte=timezone.now().date(),
                status__in=['scheduled', 'confirmed']
            )
        
        return queryset.order_by('-appointment_date', '-appointment_time')
    
    def list(self, request, *args, **kwargs):
        """
        Personaliza la respuesta para incluir estadísticas
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calcular estadísticas
        total_appointments = queryset.count()
        upcoming_appointments = queryset.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).count()
        
        # Próxima cita
        next_appointment = queryset.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).first()
        
        next_appointment_data = None
        if next_appointment:
            next_appointment_data = AppointmentSerializer(next_appointment).data
        
        return Response({
            'appointments': serializer.data,
            'statistics': {
                'total_appointments': total_appointments,
                'upcoming_appointments': upcoming_appointments,
                'next_appointment': next_appointment_data
            }
        })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def cancel_patient_appointment(request, appointment_id):
    """
    Vista para que los pacientes cancelen sus propias citas
    Con validación de 24 horas de anticipación
    """
    # Verificar que sea un paciente
    if request.user.user_type != 'patient':
        return Response(
            {'error': 'Solo los pacientes pueden cancelar sus citas.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Obtener la cita
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verificar que la cita pertenezca al paciente
    if appointment.patient.user != request.user:
        return Response(
            {'error': 'No tienes permisos para cancelar esta cita.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Verificar que la cita se pueda cancelar (estado)
    if not appointment.can_be_cancelled:
        return Response(
            {'error': f'No se puede cancelar una cita con estado "{appointment.get_status_display()}".'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar la regla de 24 horas
    appointment_datetime = timezone.datetime.combine(
        appointment.appointment_date, 
        appointment.appointment_time
    )
    appointment_datetime = timezone.make_aware(appointment_datetime)
    
    # Calcular 24 horas antes de la cita
    time_limit = appointment_datetime - timedelta(hours=24)
    current_time = timezone.now()
    
    if current_time >= time_limit:
        hours_remaining = (appointment_datetime - current_time).total_seconds() / 3600
        return Response({
            'error': 'No se puede cancelar la cita. Debe cancelarse con al menos 24 horas de anticipación.',
            'hours_remaining': round(hours_remaining, 1),
            'cancellation_deadline': time_limit.isoformat()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Obtener razón de cancelación (opcional)
    cancellation_reason = request.data.get('reason', 'Cancelada por el paciente')
    
    # Crear registro en el historial
    AppointmentHistory.objects.create(
        appointment=appointment,
        previous_status=appointment.status,
        new_status='cancelled',
        changed_by='patient',
        change_reason=cancellation_reason
    )
    
    # Actualizar el estado de la cita
    appointment.status = 'cancelled'
    appointment.save()
    
    # Serializar la cita actualizada
    serializer = AppointmentSerializer(appointment)
    
    return Response({
        'message': 'Cita cancelada exitosamente.',
        'appointment': serializer.data,
        'cancelled_at': timezone.now().isoformat()
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_appointment_detail(request, appointment_id):
    """
    Vista para ver los detalles de una cita específica del paciente
    """
    # Verificar que sea un paciente
    if request.user.user_type != 'patient':
        return Response(
            {'error': 'Solo los pacientes pueden ver sus citas.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Obtener la cita
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verificar que la cita pertenezca al paciente
    if appointment.patient.user != request.user:
        return Response(
            {'error': 'No tienes permisos para ver esta cita.'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Serializar la cita
    serializer = AppointmentSerializer(appointment)
    
    # Verificar si se puede cancelar (información adicional)
    can_cancel = False
    cancellation_info = {}
    
    if appointment.can_be_cancelled:
        appointment_datetime = timezone.datetime.combine(
            appointment.appointment_date, 
            appointment.appointment_time
        )
        appointment_datetime = timezone.make_aware(appointment_datetime)
        
        time_limit = appointment_datetime - timedelta(hours=24)
        current_time = timezone.now()
        
        if current_time < time_limit:
            can_cancel = True
            hours_until_limit = (time_limit - current_time).total_seconds() / 3600
            cancellation_info = {
                'can_cancel_until': time_limit.isoformat(),
                'hours_remaining_to_cancel': round(hours_until_limit, 1)
            }
        else:
            hours_until_appointment = (appointment_datetime - current_time).total_seconds() / 3600
            cancellation_info = {
                'cancellation_deadline_passed': True,
                'hours_until_appointment': round(hours_until_appointment, 1)
            }
    
    return Response({
        'appointment': serializer.data,
        'can_cancel': can_cancel,
        'cancellation_info': cancellation_info
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_doctors(request):
    """Lista todos los médicos disponibles con su información básica"""
    if request.user.user_type != 'patient':
        return Response({'error': 'Solo los pacientes pueden ver médicos disponibles.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    doctors = DoctorProfile.objects.filter(is_available=True)
    serializer = DoctorProfileSerializer(doctors, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Nueva vista para obtener detalles de una cita
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_detail(request, appointment_id):
    """Obtiene los detalles de una cita específica"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Verificar permisos
    if (request.user.user_type == 'patient' and appointment.patient.user != request.user) or \
       (request.user.user_type == 'doctor' and appointment.doctor.user != request.user):
        return Response({'error': 'No tiene permisos para ver esta cita.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    serializer = AppointmentSerializer(appointment)
    return Response(serializer.data, status=status.HTTP_200_OK)

# Vista mejorada para marcar indisponibilidad con rangos de fechas
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_unavailable_range(request):
    """Marca indisponibilidad para un rango de fechas"""
    if request.user.user_type != 'doctor':
        return Response({'error': 'Solo los médicos pueden marcar indisponibilidad.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    # Validar datos requeridos
    required_fields = ['start_date', 'end_date', 'start_time', 'end_time']
    for field in required_fields:
        if field not in request.data:
            return Response({'error': f'El campo {field} es requerido.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
    
    try:
        start_date = datetime.strptime(request.data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.data['end_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.data['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(request.data['end_time'], '%H:%M:%S').time()
    except ValueError:
        return Response({'error': 'Formato de fecha u hora inválido.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Validaciones básicas
    if start_date > end_date:
        return Response({'error': 'La fecha de inicio debe ser menor o igual a la fecha de fin.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if start_time >= end_time:
        return Response({'error': 'La hora de inicio debe ser menor a la hora de fin.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if start_date < timezone.now().date():
        return Response({'error': 'No puede marcar indisponibilidad en fechas pasadas.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Verificar citas existentes en el rango
    existing_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__range=[start_date, end_date],
        appointment_time__range=[start_time, end_time],
        status__in=['scheduled', 'confirmed']
    )
    
    warning_message = None
    if existing_appointments.exists():
        appointments_info = []
        for apt in existing_appointments:
            appointments_info.append({
                'date': apt.appointment_date,
                'time': apt.appointment_time,
                'patient': apt.patient.user.get_full_name() or apt.patient.user.username
            })
        
        # Si el usuario no confirmó que quiere proceder, enviar advertencia
        if not request.data.get('force_block', False):
            return Response({
                'warning': 'Existen citas programadas en este rango de horario.',
                'existing_appointments': appointments_info,
                'message': 'Para proceder, envíe la solicitud nuevamente con force_block=true'
            }, status=status.HTTP_409_CONFLICT)
        
        warning_message = f'Se bloqueó el horario pero hay {existing_appointments.count()} citas existentes que requerirán reprogramación.'
    
    # Crear indisponibilidades para cada día en el rango
    created_unavailabilities = []
    current_date = start_date
    
    try:
        with transaction.atomic():
            while current_date <= end_date:
                unavailability = DoctorUnavailability.objects.create(
                    doctor=doctor,
                    date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    reason=request.data.get('reason', '')
                )
                created_unavailabilities.append(unavailability)
                current_date += timedelta(days=1)
    except Exception as e:
        return Response({'error': f'Error al crear indisponibilidades: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    serializer = DoctorUnavailabilitySerializer(created_unavailabilities, many=True)
    response_data = {
        'message': 'Indisponibilidad marcada exitosamente.',
        'unavailabilities': serializer.data
    }
    
    if warning_message:
        response_data['warning'] = warning_message
    
    return Response(response_data, status=status.HTTP_201_CREATED)

# Vista para verificar conflictos antes de bloquear
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_unavailability_conflicts(request):
    """Verifica si hay conflictos con citas existentes antes de marcar indisponibilidad"""
    if request.user.user_type != 'doctor':
        return Response({'error': 'Solo los médicos pueden verificar conflictos.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    
    try:
        start_date = datetime.strptime(request.data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.data['end_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.data['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(request.data['end_time'], '%H:%M:%S').time()
    except (ValueError, KeyError):
        return Response({'error': 'Datos de fecha/hora inválidos o faltantes.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Buscar citas en conflicto
    conflicting_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__range=[start_date, end_date],
        appointment_time__range=[start_time, end_time],
        status__in=['scheduled', 'confirmed']
    ).select_related('patient__user')
    
    conflicts = []
    for apt in conflicting_appointments:
        conflicts.append({
            'id': apt.id,
            'date': apt.appointment_date,
            'time': apt.appointment_time,
            'patient_name': apt.patient.user.get_full_name() or apt.patient.user.username,
            'reason': apt.reason
        })
    
    return Response({
        'has_conflicts': len(conflicts) > 0,
        'conflicts_count': len(conflicts),
        'conflicting_appointments': conflicts
    }, status=status.HTTP_200_OK)

# Vista para actualizar estado de citas (confirmar, completar, etc.)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_appointment_status(request, appointment_id):
    """Actualiza el estado de una cita"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Solo médicos pueden cambiar estados (excepto cancelación que ya existe)
    if request.user.user_type != 'doctor' or appointment.doctor.user != request.user:
        return Response({'error': 'No tiene permisos para actualizar esta cita.'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    new_status = request.data.get('status')
    valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled']
    
    if new_status not in valid_statuses:
        return Response({'error': 'Estado inválido.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if appointment.status == new_status:
        return Response({'error': 'La cita ya tiene ese estado.'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Guardar historial
    AppointmentHistory.objects.create(
        appointment=appointment,
        previous_status=appointment.status,
        new_status=new_status,
        changed_by='doctor',
        change_reason=request.data.get('reason', '')
    )
    
    appointment.status = new_status
    appointment.save()
    
    serializer = AppointmentSerializer(appointment)
    return Response({
        'message': f'Estado de cita actualizado a {new_status}.',
        'appointment': serializer.data
    }, status=status.HTTP_200_OK)
