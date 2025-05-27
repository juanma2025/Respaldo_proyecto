from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

class User(AbstractUser):
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    email = models.EmailField(unique=True) # Hacer el email el campo único principal
    # USERNAME_FIELD = 'email' # Si quieres loguear con email
    # REQUIRED_FIELDS = ['username'] # Ajustar si cambias USERNAME_FIELD

    # Campos comunes
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    # Para la activación de cuenta del paciente
    email_confirmed = models.BooleanField(default=False)
    confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    # Campos adicionales específicos del paciente si los hubiera

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)
    professional_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Availability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False) # Para saber si este slot ya fue tomado

    class Meta:
        unique_together = ('doctor', 'date', 'start_time') # Un doctor no puede tener el mismo slot dos veces
        verbose_name_plural = "Availabilities"

    def __str__(self):
        return f"Dr. {self.doctor.user.last_name} - {self.date} de {self.start_time} a {self.end_time}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Agendada'),
        ('CANCELLED_PATIENT', 'Cancelada por Paciente'),
        ('CANCELLED_DOCTOR', 'Cancelada por Médico'),
        ('COMPLETED', 'Completada'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    availability = models.OneToOneField(Availability, on_delete=models.SET_NULL, null=True, blank=True, help_text="Slot de disponibilidad asociado") # Opcional, si quieres ligarlo directamente
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cita: {self.patient} con Dr. {self.doctor.user.last_name} - {self.appointment_date} {self.appointment_time}"
