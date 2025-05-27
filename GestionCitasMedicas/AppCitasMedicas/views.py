from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import User, Patient, Doctor, DoctorSchedule, DoctorUnavailability
from .serializers import (
    PatientRegistrationSerializer, DoctorRegistrationSerializer, 
    LoginSerializer, PatientProfileSerializer, DoctorProfileSerializer,
    DoctorScheduleSerializer, DoctorUnavailabilitySerializer,
    DoctorPublicSerializer
)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_patient(request):
    serializer = PatientRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Enviar email de verificación
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}"
        subject = 'Verifica tu cuenta - Sistema de Citas Médicas'
        message = f"""
        Hola {user.first_name},
        
        Gracias por registrarte en nuestro sistema de citas médicas.
        
        Para activar tu cuenta, haz clic en el siguiente enlace:
        {verification_url}
        
        Si no solicitaste esta cuenta, puedes ignorar este mensaje.
        
        Saludos,
        Equipo de Citas Médicas
        """
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            return Response({
                'message': 'Cuenta creada exitosamente. Revisa tu correo para verificar la cuenta.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'message': 'Cuenta creada pero hubo un error enviando el email de verificación.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_doctor(request):
    serializer = DoctorRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Enviar credenciales por email
        subject = 'Bienvenido - Credenciales de acceso al Sistema de Citas Médicas'
        message = f"""
        Hola Dr. {user.first_name} {user.last_name},
        
        Tu cuenta ha sido creada exitosamente en nuestro sistema de citas médicas.
        
        Tus credenciales de acceso son:
        Email: {user.email}
        Contraseña: {user.temp_password}
        
        Por favor, cambia tu contraseña después del primer inicio de sesión.
        
        Puedes acceder al sistema en: {settings.FRONTEND_URL}/login
        
        Saludos,
        Equipo de Citas Médicas
        """
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            return Response({
                'message': 'Cuenta de médico creada exitosamente. Las credenciales han sido enviadas por correo.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'message': 'Cuenta creada pero hubo un error enviando las credenciales por email.',
                'email': user.email
            }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()
        
        return Response({
            'message': 'Email verificado exitosamente. Ya puedes iniciar sesión.'
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'Token de verificación inválido.'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_type': user.user_type,
            'user_id': str(user.id),
            'name': f"{user.first_name} {user.last_name}"
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = PatientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(Patient, user=self.request.user)

class DoctorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(Doctor, user=self.request.user)

class DoctorListView(generics.ListAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorPublicSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Doctor.objects.all()
        specialty = self.request.query_params.get('specialty', None)
        if specialty:
            queryset = queryset.filter(specialty=specialty)
        return queryset

class DoctorScheduleView(generics.ListCreateAPIView):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        doctor = get_object_or_404(Doctor, user=self.request.user)
        return DoctorSchedule.objects.filter(doctor=doctor)
    
    def perform_create(self, serializer):
        doctor = get_object_or_404(Doctor, user=self.request.user)
        serializer.save(doctor=doctor)

class DoctorUnavailabilityView(generics.ListCreateAPIView):
    serializer_class = DoctorUnavailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        doctor = get_object_or_404(Doctor, user=self.request.user)
        return DoctorUnavailability.objects.filter(doctor=doctor)
    
    def perform_create(self, serializer):
        doctor = get_object_or_404(Doctor, user=self.request.user)
        serializer.save(doctor=doctor)

@api_view(['DELETE'])
def delete_unavailability(request, unavailability_id):
    doctor = get_object_or_404(Doctor, user=request.user)
    unavailability = get_object_or_404(DoctorUnavailability, id=unavailability_id, doctor=doctor)
    unavailability.delete()
    return Response({'message': 'Horario eliminado exitosamente'}, status=status.HTTP_200_OK)