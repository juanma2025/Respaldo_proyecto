from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Patient, Doctor, DoctorSchedule, DoctorUnavailability
import secrets
import string

class PatientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Generar token de verificación
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        user = User.objects.create(
            username=validated_data['email'],
            user_type='patient',
            email_verification_token=token,
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        # Crear perfil de paciente
        Patient.objects.create(user=user)
        
        return user

class DoctorRegistrationSerializer(serializers.ModelSerializer):
    professional_license = serializers.CharField()
    specialty = serializers.CharField()
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'professional_license', 'specialty']
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado")
        return value
    
    def validate_professional_license(self, value):
        if Doctor.objects.filter(professional_license=value).exists():
            raise serializers.ValidationError("Esta cédula profesional ya está registrada")
        return value
    
    def create(self, validated_data):
        specialty = validated_data.pop('specialty')
        professional_license = validated_data.pop('professional_license')
        
        # Generar contraseña aleatoria
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        user = User.objects.create(
            username=validated_data['email'],
            user_type='doctor',
            is_email_verified=True,  # Los médicos se verifican automáticamente
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        # Crear perfil de médico
        Doctor.objects.create(
            user=user,
            specialty=specialty,
            professional_license=professional_license
        )
        
        # Guardar la contraseña para enviarla por email
        user.temp_password = password
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Credenciales incorrectas")
            if not user.is_email_verified:
                raise serializers.ValidationError("Debes verificar tu correo electrónico antes de iniciar sesión")
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError("Email y contraseña son requeridos")

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'user_type', 'is_email_verified']
        read_only_fields = ['id', 'email', 'user_type', 'is_email_verified']

class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()
    
    class Meta:
        model = Patient
        fields = ['user', 'birth_date', 'emergency_contact', 'medical_history']

class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['user', 'specialty', 'specialty_display', 'professional_license', 'consultation_fee', 'bio']

class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = ['id', 'day_of_week', 'day_display', 'start_time', 'end_time', 'is_available']

class DoctorUnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorUnavailability
        fields = ['id', 'date', 'start_time', 'end_time', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']

class DoctorPublicSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialty', 'specialty_display', 'consultation_fee', 'bio']