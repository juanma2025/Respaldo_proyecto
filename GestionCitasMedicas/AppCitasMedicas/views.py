from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from django.shortcuts import get_object_or_404
from .models import User, PatientProfile, DoctorProfile, DoctorSchedule
from .serializers import (
    PatientRegistrationSerializer, 
    DoctorRegistrationSerializer,
    LoginSerializer,
    UserProfileSerializer,
    PatientProfileSerializer,
    DoctorProfileSerializer,
    DoctorScheduleSerializer
)
from django.utils import timezone
from rest_framework import status
from .serializers import EmailVerificationSerializer
from django.contrib.auth import authenticate
from django .shortcuts import render




@api_view(['POST'])
@permission_classes([AllowAny])
def register_patient(request):
    serializer = PatientRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'Paciente registrado exitosamente. Por favor, revisa tu correo para verificar tu cuenta.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_doctor(request):
    serializer = DoctorRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'Médico registrado exitosamente. Las credenciales han sido enviadas por correo.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = ''
        user.save()
        return Response({
            'message': 'Correo verificado exitosamente. Ya puedes iniciar sesión.'
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'Token de verificación inválido.'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user.user_type
            }
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Vista de login que verifica si el email está confirmado
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'success': False,
            'message': 'Email y contraseña son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Autenticar usuario
    user = authenticate(username=email, password=password)
    
    if user:
        # Verificar si el email está confirmado
        if not user.is_email_verified:
            return Response({
                'success': False,
                'message': 'Debes verificar tu email antes de iniciar sesión. Revisa tu bandeja de entrada.',
                'email_verified': False,
                'can_resend': True
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        return Response({
            'success': True,
            'message': 'Login exitoso',
            'tokens': {
                'access': access_token,
                'refresh': str(refresh)
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user.user_type,
                'is_email_verified': user.is_email_verified
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Credenciales inválidas'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    refresh_token = request.data.get("refresh_token")

    if not refresh_token:
        return Response({'error': 'Falta el token de refresco.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Sesión cerrada exitosamente.'}, status=status.HTTP_200_OK)
    except TokenError:
        return Response({'error': 'Token inválido o ya fue usado.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    if user.user_type == 'patient':
        profile = get_object_or_404(PatientProfile, user=user)
        serializer = PatientProfileSerializer(profile)
    else:
        profile = get_object_or_404(DoctorProfile, user=user)
        serializer = DoctorProfileSerializer(profile)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    
    # Actualizar datos del usuario
    user_serializer = UserProfileSerializer(user, data=request.data, partial=True)
    if user_serializer.is_valid():
        user_serializer.save()
        
        # Actualizar perfil específico
        if user.user_type == 'patient':
            profile = get_object_or_404(PatientProfile, user=user)
            profile_serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
        else:
            profile = get_object_or_404(DoctorProfile, user=user)
            profile_serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
        
        if profile_serializer.is_valid():
            profile_serializer.save()
            return Response({
                'message': 'Perfil actualizado exitosamente.',
                'user': user_serializer.data,
                'profile': profile_serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_doctors_by_specialty(request):
    specialty = request.GET.get('specialty')
    if specialty:
        doctors = DoctorProfile.objects.filter(
            specialty=specialty, 
            is_available=True,
            user__is_email_verified=True
        )
    else:
        doctors = DoctorProfile.objects.filter(
            is_available=True,
            user__is_email_verified=True
        )
    
    serializer = DoctorProfileSerializer(doctors, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_specialties(request):
    """Obtiene todas las especialidades disponibles"""
    specialties = [{'value': choice[0], 'label': choice[1]} 
                  for choice in DoctorProfile.SPECIALTY_CHOICES]
    return Response(specialties, status=status.HTTP_200_OK)

# Vistas para horarios de médicos
class DoctorScheduleListCreate(generics.ListCreateAPIView):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'doctor':
            doctor_profile = get_object_or_404(DoctorProfile, user=self.request.user)
            return DoctorSchedule.objects.filter(doctor=doctor_profile)
        return DoctorSchedule.objects.none()
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'doctor':
            raise PermissionDenied("Solo los médicos pueden crear horarios.")
        
        doctor_profile = get_object_or_404(DoctorProfile, user=self.request.user)
        serializer.save(doctor=doctor_profile)
        
class DoctorScheduleDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Solo permitir acceso a los propios horarios del médico
        if self.request.user.user_type == 'doctor':
            doctor_profile = get_object_or_404(DoctorProfile, user=self.request.user)
            return DoctorSchedule.objects.filter(doctor=doctor_profile)
        return DoctorSchedule.objects.none()
    
    def get_object(self):
        """
        Obtiene el objeto específico del horario verificando permisos
        """
        queryset = self.get_queryset()
        schedule_id = self.kwargs.get('pk')
        
        schedule = get_object_or_404(queryset, pk=schedule_id)
        
        # Verificar que el médico solo puede acceder a sus propios horarios
        if schedule.doctor.user != self.request.user:
            raise PermissionDenied("No tiene permisos para acceder a este horario.")
        
        return schedule
    
    def perform_update(self, serializer):
        """
        Validaciones adicionales antes de actualizar
        """
        if self.request.user.user_type != 'doctor':
            raise PermissionDenied("Solo los médicos pueden modificar horarios.")
        
        # Verificar que no haya citas programadas en este horario antes de modificarlo
        schedule = self.get_object()
        
        # Si se está cambiando la disponibilidad a False, verificar citas existentes
        if not serializer.validated_data.get('is_available', True):
            from .models import Appointment
            
            upcoming_appointments = Appointment.objects.filter(
                doctor=schedule.doctor,
                appointment_date__gte=timezone.now().date(),
                status__in=['scheduled', 'confirmed']
            )
            
            # Filtrar citas que caigan en este horario
            conflicting_appointments = []
            for appointment in upcoming_appointments:
                appointment_weekday = appointment.appointment_date.weekday()
                if (appointment_weekday == schedule.weekday and 
                    schedule.start_time <= appointment.appointment_time < schedule.end_time):
                    conflicting_appointments.append(appointment)
            
            if conflicting_appointments:
                raise ValidationError({
                    'non_field_errors': [
                        f'No se puede desactivar este horario. Tiene {len(conflicting_appointments)} cita(s) programada(s).'
                    ]
                })
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Validaciones antes de eliminar un horario
        """
        if self.request.user.user_type != 'doctor':
            raise PermissionDenied("Solo los médicos pueden eliminar horarios.")
        
        # Verificar que no haya citas programadas en este horario
        from .models import Appointment
        
        upcoming_appointments = Appointment.objects.filter(
            doctor=instance.doctor,
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        )
        
        # Filtrar citas que caigan en este horario
        conflicting_appointments = []
        for appointment in upcoming_appointments:
            appointment_weekday = appointment.appointment_date.weekday()
            if (appointment_weekday == instance.weekday and 
                instance.start_time <= appointment.appointment_time < instance.end_time):
                conflicting_appointments.append(appointment)
        
        if conflicting_appointments:
            raise ValidationError(
                f'No se puede eliminar este horario. Tiene {len(conflicting_appointments)} cita(s) programada(s).'
            )
        
        instance.delete()

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verifica el email del usuario usando el token enviado por correo
    """
    serializer = EmailVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'success': True,
            'message': 'Email verificado exitosamente. Ya puedes iniciar sesión.',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'is_email_verified': user.is_email_verified
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email_get(request, token):
    """
    Verifica el email usando GET (para cuando el usuario hace clic en el enlace)
    """
    try:
        user = User.objects.get(
            email_verification_token=token,
            is_email_verified=False
        )
        user.verify_email()
        
        return Response({
            'success': True,
            'message': f'¡Cuenta verificada exitosamente! Bienvenido {user.full_name}',
            'redirect_url': 'http://localhost:5173/login?verified=true'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Token de verificación inválido o ya usado.',
            'redirect_url': 'http://localhost:5173/verification-error'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Reenvía el email de verificación
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email, is_email_verified=False)
        
        # Generar nuevo token
        token = user.generate_verification_token()
        
        # Reenviar email (usar el mismo método del serializer)
        serializer = PatientRegistrationSerializer()
        serializer.send_verification_email(user, token)
        
        return Response({
            'success': True,
            'message': 'Email de verificación reenviado exitosamente'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado o ya verificado'
        }, status=status.HTTP_404_NOT_FOUND)
    
def index(request):
    return render(request, 'index.html')