from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from AppCitasMedicas.models import PatientProfile, DoctorProfile

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
        ('no_show', 'No se presentó'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    reason = models.TextField(help_text="Motivo de la consulta")
    notes = models.TextField(blank=True, help_text="Notas del médico")
    duration_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'appointment_date', 'appointment_time']
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"{self.patient.user.full_name} - Dr. {self.doctor.user.full_name} ({self.appointment_date} {self.appointment_time})"
    
    def clean(self):
        # Validar que la cita sea en el futuro
        appointment_datetime = timezone.datetime.combine(
            self.appointment_date, 
            self.appointment_time
        )
        appointment_datetime = timezone.make_aware(appointment_datetime)
        
        if appointment_datetime <= timezone.now():
            raise ValidationError("La cita debe ser programada para una fecha y hora futura.")
        
        # Validar que no haya conflictos de horario
        conflicting_appointments = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
            status__in=['scheduled', 'confirmed']
        ).exclude(pk=self.pk)
        
        if conflicting_appointments.exists():
            raise ValidationError("Ya existe una cita programada para este horario.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def can_be_cancelled(self):
        """Permite cancelar la cita si está programada o confirmada"""
        return self.status in ['scheduled', 'confirmed']
    
    @property
    def is_upcoming(self):
        """Verifica si la cita es próxima (dentro de las próximas 24 horas)"""
        appointment_datetime = timezone.datetime.combine(
            self.appointment_date, 
            self.appointment_time
        )
        appointment_datetime = timezone.make_aware(appointment_datetime)
        
        now = timezone.now()
        return now <= appointment_datetime <= now + timezone.timedelta(hours=24)

class AppointmentHistory(models.Model):
    """Historial de cambios en las citas"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='history')
    previous_status = models.CharField(max_length=15)
    new_status = models.CharField(max_length=15)
    changed_by = models.CharField(max_length=100)  # patient or doctor
    change_reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.appointment} - {self.previous_status} → {self.new_status}"