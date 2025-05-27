from rest_framework import serializers
from .models import Appointment, AppointmentHistory
from apps.users.serializers import PatientProfileSerializer, DoctorProfileSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientProfileSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'date', 'start_time', 'end_time',
            'status', 'status_display', 'reason', 'notes', 'duration_minutes',
            'created_at', 'updated_at'
        ]

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'start_time', 'end_time', 'reason']
    
    def validate(self, attrs):
        from datetime import datetime, date
        
        # Validar que la fecha no sea en el pasado
        if attrs['date'] < date.today():
            raise serializers.ValidationError("No se pueden agendar citas en fechas pasadas")
        
        # Validar que start_time sea antes que end_time
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError("La hora de inicio debe ser anterior a la hora de fin")
        
        # Validar duración mínima de 30 minutos
        start_datetime = datetime.combine(attrs['date'], attrs['start_time'])
        end_datetime = datetime.combine(attrs['date'], attrs['end_time'])
        duration = (end_datetime - start_datetime).total_seconds() / 60
        
        if duration < 30:
            raise serializers.ValidationError("La duración mínima de una cita es de 30 minutos")
        
        if duration > 120:
            raise serializers.ValidationError("La duración máxima de una cita es de 2 horas")
        
        return attrs

class AppointmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentHistory
        fields = ['id', 'previous_status', 'new_status', 'changed_by', 'reason', 'timestamp']