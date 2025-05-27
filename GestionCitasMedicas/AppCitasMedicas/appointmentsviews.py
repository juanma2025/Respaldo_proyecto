from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime, date, time, timedelta
from .models import Appointment, AppointmentHistory
from apps.users.models import Patient, Doctor, DoctorSchedule, DoctorUnavailability
from .serializers import AppointmentSerializer, AppointmentCreateSerializer, AppointmentHistorySerializer

class PatientAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            patient = Patient.objects.get(user=self.request.user)
            return Appointment.objects.filter(patient=patient).order_by('-date', '-start_time')
        except Patient.DoesNotExist:
            return Appointment.objects.none()

class DoctorAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            return Appointment.objects.filter(doctor=doctor).order_by('date', 'start_time')
        except Doctor.DoesNotExist:
            return Appointment.objects.none()

@api_view(['GET'])
def get_available_slots(request, doctor_id):
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response({'error': 'Fecha es requerida'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que la fecha no sea en el pasado
        if appointment_date < date.today():
            return Response({'available_slots': []}, status=status.HTTP_200_OK)
        
        # Obtener el día de la semana (0=lunes, 6=domingo)
        day_of_week = appointment_date.weekday()
        
        # Obtener horarios del médico para ese día
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            is_available=True
        )
        
        if not schedules:
            return Response({'available_slots': []}, status=status.HTTP_200_OK)
        
        # Obtener citas ya agendadas para ese día
        existing_appointments = Appointment.objects.filter(
            doctor=doctor,
            date=appointment_date,
            status__in=['scheduled', 'confirmed']
        )
        
        # Obtener horarios no disponibles para ese día
        unavailable_slots = DoctorUnavailability.objects.filter(
            doctor=doctor,
            date=appointment_date
        )
        
        available_slots = []
        
        for schedule in schedules:
            current_time = schedule.start_time
            end_time = schedule.end_time
            
            while current_time < end_time:
                slot_end_time = (datetime.combine(date.today(), current_time) + timedelta(minutes=30)).time()
                
                if slot_end_time > end_time:
                    break
                
                # Verificar si el slot está ocupado por una cita
                is_occupied = existing_appointments.filter(
                    start_time__lt=slot_end_time,
                    end_time__gt=current_time
                ).exists()
                
                # Verificar si el slot está marcado como no disponible
                is_unavailable = unavailable_slots.filter(
                    start_time__lt=slot_end_time,
                    end_time__gt=current_time
                ).exists()
                
                if not is_occupied and not is_unavailable:
                    available_slots.append({
                        'start_time': current_time.strftime('%H:%M'),
                        'end_time': slot_end_time.strftime('%H:%M')
                    })
                
                current_time = slot_end_time
        
        return Response({'available_slots': available_slots}, status=status.HTTP_200_OK)
    
    except Doctor.DoesNotExist:
        return Response({'error': 'Médico no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def create_appointment(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return Response({'error': 'Solo los pacientes pueden agendar citas'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AppointmentCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Verificar disponibilidad del slot
        doctor_id = serializer.validated_data['doctor']
        appointment_date = serializer.validated_data['date']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        
        # Verificar que no haya conflictos
        existing_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            date=appointment_date,
            status__in=['scheduled', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if existing_appointments.exists():
            return Response({'error': 'Este horario ya no está disponible'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar horarios no disponibles
        unavailable_slots = DoctorUnavailability.objects.filter(
            doctor_id=doctor_id,
            date=appointment_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if unavailable_slots.exists():
            return Response({'error': 'El médico no está disponible en este horario'}, status=status.HTTP_400_BAD_REQUEST)
        
        appointment = serializer.save(patient=patient)
        
        # Crear registro en el historial
        AppointmentHistory.objects.create(
            appointment=appointment,
            previous_status='',
            new_status='scheduled',
            changed_by=patient.user.email,
            reason='Cita creada por el paciente'
        )
        
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def cancel_appointment(request, appointment_id):
    try:
        patient = Patient.objects.get(user=request.user)
        appointment = Appointment.objects.get(id=appointment_id, patient=patient)
        
        if appointment.status in ['completed', 'cancelled']:
            return Response({'error': 'No se puede cancelar esta cita'}, status=status.HTTP_400_BAD_REQUEST)
        
        previous_status = appointment.status
        appointment.status = 'cancelled'
        appointment.save()
        
        # Crear registro en el historial
        AppointmentHistory.objects.create(
            appointment=appointment,
            previous_status=previous_status,
            new_status='cancelled',
            changed_by=patient.user.email,
            reason='Cita cancelada por el paciente'
        )
        
        return Response({'message': 'Cita cancelada exitosamente'}, status=status.HTTP_200_OK)
    
    except Patient.DoesNotExist:
        return Response({'error': 'Solo los pacientes pueden cancelar sus citas'}, status=status.HTTP_403_FORBIDDEN)
    except Appointment.DoesNotExist:
        return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
def update_appointment_status(request, appointment_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
        appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
        
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in ['confirmed', 'completed', 'cancelled', 'no_show']:
            return Response({'error': 'Estado inválido'}, status=status.HTTP_400_BAD_REQUEST)
        
        previous_status = appointment.status
        appointment.status = new_status
        if notes:
            appointment.notes = notes
        appointment.save()
        
        # Crear registro en el historial
        AppointmentHistory.objects.create(
            appointment=appointment,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=doctor.user.email,
            reason=f'Estado actualizado por el médico. Notas: {notes}'
        )
        
        return Response({'message': 'Estado de la cita actualizado exitosamente'}, status=status.HTTP_200_OK)
    
    except Doctor.DoesNotExist:
        return Response({'error': 'Solo los médicos pueden actualizar el estado de las citas'}, status=status.HTTP_403_FORBIDDEN)
    except Appointment.DoesNotExist:
        return Response({'error': 'Cita no encontrada'}, status=status.HTTP_404_NOT_FOUND)