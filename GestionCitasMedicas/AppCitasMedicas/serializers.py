from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import User, PatientProfile, DoctorProfile, DoctorSchedule
import re

class PatientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone_number', 'password', 'password_confirm']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value
    
    def validate_phone_number(self, value):
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Formato de teléfono inválido.")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            full_name=validated_data['full_name'],
            phone_number=validated_data['phone_number'],
            user_type='patient',
            is_email_verified=False  # IMPORTANTE: Email no verificado por defecto
        )
        user.set_password(password)
        user.save()
        
        # Crear perfil de paciente
        PatientProfile.objects.create(user=user)
        
        # Generar token de verificación y enviar email
        token = user.generate_verification_token()
        self.send_verification_email(user, token)
        
        return user
    
    def send_verification_email(self, user, token):
        subject = 'Confirma tu cuenta - Sistema de Citas Médicas'
        
        # URL para verificación por GET (cuando hacen clic)
        verification_url = f"http://127.0.0.1:8000/api/auth/verify-email/{token}/"
        
        message = f"""
        Hola {user.full_name},
        
        Gracias por registrarte en nuestro sistema de citas médicas.
        
        Para activar tu cuenta, haz clic en el siguiente enlace:
        {verification_url}
        
        O copia y pega este enlace en tu navegador.
        
        Si no te registraste en nuestro sistema, ignora este mensaje.
        
        Saludos,
        Equipo de Citas Médicas
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    
    def validate_token(self, value):
        try:
            user = User.objects.get(
                email_verification_token=value,
                is_email_verified=False
            )
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Token de verificación inválido o ya usado."
            )
    
    def save(self):
        token = self.validated_data['token']
        user = User.objects.get(email_verification_token=token)
        user.verify_email()
        return user
    
class DoctorRegistrationSerializer(serializers.ModelSerializer):
    specialty = serializers.CharField()
    professional_license = serializers.CharField()
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'specialty', 'professional_license']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value
    
    def validate_professional_license(self, value):
        if DoctorProfile.objects.filter(professional_license=value).exists():
            raise serializers.ValidationError("Esta cédula profesional ya está registrada.")
        return value
    
    def create(self, validated_data):
        specialty = validated_data.pop('specialty')
        professional_license = validated_data.pop('professional_license')
        
        # Generar contraseña aleatoria
        password = DoctorProfile.generate_random_password()
        
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            full_name=validated_data['full_name'],
            user_type='doctor',
            is_email_verified=True  # Los médicos se verifican automáticamente
        )
        user.set_password(password)
        user.save()
        
        # Crear perfil de médico
        DoctorProfile.objects.create(
            user=user,
            specialty=specialty,
            professional_license=professional_license
        )
        
        # Enviar credenciales por email
        self.send_credentials_email(user, password)
        
        return user
    
    def send_credentials_email(self, user, password):
        subject = 'Bienvenido - Credenciales de Acceso'
        message = f"""
        Estimado Dr. {user.full_name},
        
        Su cuenta médica ha sido creada exitosamente en nuestro sistema.
        
        Sus credenciales de acceso son:
        Email: {user.email}
        Contraseña: {password}
        
        Por favor, inicie sesión y cambie su contraseña lo antes posible.
        
        Enlace de acceso: http://localhost:5173/login
        
        Saludos,
        Administración del Sistema
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if not user.is_email_verified:
                    raise serializers.ValidationError("Debe verificar su correo electrónico antes de iniciar sesión.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Credenciales inválidas.")
        else:
            raise serializers.ValidationError("Debe proporcionar email y contraseña.")
        
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'user_type']
        read_only_fields = ['id', 'email', 'user_type']

class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = '__all__'

class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = '__all__'

class DoctorScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = '__all__'