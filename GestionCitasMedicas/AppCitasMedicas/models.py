from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import secrets
import string

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('patient', 'Paciente'),
        ('doctor', 'Médico'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, default='Sin nombre')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')],
        blank=True
    )
    is_email_verified = models.BooleanField(default=False)

    email_verification_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default=None
    )
    
    #USERNAME_FIELD = 'email'
    #REQUIRED_FIELDS = ['username', 'full_name']
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def generate_verification_token(self):
        self.email_verification_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(50))
        self.save()
        return self.email_verification_token

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Paciente: {self.user.full_name}"

class DoctorProfile(models.Model):
    SPECIALTY_CHOICES = [
        ('cardiologia', 'Cardiología'),
        ('dermatologia', 'Dermatología'),
        ('endocrinologia', 'Endocrinología'),
        ('gastroenterologia', 'Gastroenterología'),
        ('ginecologia', 'Ginecología'),
        ('neurologia', 'Neurología'),
        ('oftalmologia', 'Oftalmología'),
        ('ortopedia', 'Ortopedia'),
        ('pediatria', 'Pediatría'),
        ('psiquiatria', 'Psiquiatría'),
        ('medicina_general', 'Medicina General'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=50, choices=SPECIALTY_CHOICES)
    professional_license = models.CharField(max_length=20, unique=True)
    years_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    biography = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.user.full_name} - {self.get_specialty_display()}"
    
    @staticmethod
    def generate_random_password():
        """Genera una contraseña aleatoria para el médico"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

class DoctorSchedule(models.Model):
    class WEEKDAY_CHOICES(models.IntegerChoices):
        MONDAY = 0, 'Lunes'
        TUESDAY = 1, 'Martes'
        WEDNESDAY = 2, 'Miércoles'
        THURSDAY = 3, 'Jueves'
        FRIDAY = 4, 'Viernes'
        SATURDAY = 5, 'Sábado'
        SUNDAY = 6, 'Domingo'
    
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES.choices,
        default=WEEKDAY_CHOICES.MONDAY
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'weekday', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.user.full_name} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"

class DoctorUnavailability(models.Model):
    """Permite al médico cerrar espacios específicos en su horario"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='unavailabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.CharField(
        max_length=255, 
        default='No especificado'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.doctor.user.full_name} - No disponible {self.date} {self.start_time}-{self.end_time}"