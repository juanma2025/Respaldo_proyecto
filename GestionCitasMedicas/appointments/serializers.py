from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, AppointmentHistory
from AppCitasMedicas.models import DoctorProfile, PatientProfile, DoctorUnavailability
from AppCitasMedicas.serializers import DoctorProfileSerializer, PatientProfileSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_info = DoctorProfileSerializer(source='doctor', read_only=True)
    patient_info = PatientProfileSerializer(source='patient', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    can_cancel = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_can_cancel(self, obj):
        return obj.can_be_cancelled
    
    def get_is_upcoming(self, obj):
        return obj.is_upcoming
    
    def validate(self, data):
        # Validar que la fecha sea futura
        appointment_datetime = timezone.datetime.combine(
            data['appointment_date'], 
            data['appointment_time']
        )
        appointment_datetime = timezone.make_aware(appointment_datetime)
        
        if appointment_datetime <= timezone.now():
            raise serializers.ValidationError("La cita debe ser programada para una fecha y hora futura.")
        
        # Validar disponibilidad del médico
        doctor = data['doctor']
        appointment_date = data['appointment_date']
        appointment_time = data['appointment_time']
        
        # Verificar si el médico tiene horario disponible ese día
        weekday = appointment_date.weekday()
        doctor_schedules = doctor.schedules.filter(
            weekday=weekday,
            is_available=True,
            start_time__lte=appointment_time,
            end_time__gt=appointment_time
        )
        
        if not doctor_schedules.exists():
            raise serializers.ValidationError("El médico no tiene horario disponible en ese día y hora.")
        
        # Verificar que no haya una cita ya programada
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['scheduled', 'confirmed']
        )
        
        if self.instance:
            existing_appointment = existing_appointment.exclude(pk=self.instance.pk)
        
        if existing_appointment.exists():
            raise serializers.ValidationError("Ya existe una cita programada para este horario.")
        
        # Verificar que el médico no tenga una indisponibilidad marcada
        unavailabilities = DoctorUnavailability.objects.filter(
            doctor=doctor,
            date=appointment_date,
            start_time__lte=appointment_time,
            end_time__gt=appointment_time
        )
        
        if unavailabilities.exists():
            raise serializers.ValidationError("El médico no está disponible en ese horario.")
        
        return data

class CreateAppointmentSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField()
    
    class Meta:
        model = Appointment
        fields = ['doctor_id', 'appointment_date', 'appointment_time', 'reason', 'duration_minutes']
    
    def create(self, validated_data):
        doctor_id = validated_data.pop('doctor_id')
        doctor = DoctorProfile.objects.get(id=doctor_id)
        patient = self.context['request'].user.patient_profile
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            **validated_data
        )
        
        return appointment
    
    def validate_doctor_id(self, value):
        try:
            doctor = DoctorProfile.objects.get(id=value, is_available=True)
            return value
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError("Médico no encontrado o no disponible.")

class DoctorUnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorUnavailability
        fields = '__all__'
        read_only_fields = ['doctor', 'created_at']
    
    def validate(self, data):
        # Validar que la fecha sea futura o actual
        if data['date'] < timezone.now().date():
            raise serializers.ValidationError("No puede marcar indisponibilidad en fechas pasadas.")
        
        # Validar que la hora de inicio sea menor a la hora de fin
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("La hora de inicio debe ser menor a la hora de fin.")
        
        return data

class AppointmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentHistory
        fields = '__all__'

class DoctorAvailabilitySerializer(serializers.Serializer):
    date = serializers.DateField()
    available_times = serializers.ListField(child=serializers.TimeField(), read_only=True)

class AppointmentStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de citas"""
    total_appointments = serializers.IntegerField()
    scheduled_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()