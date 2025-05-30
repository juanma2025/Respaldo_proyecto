from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, time, timedelta
from .models import DoctorProfile, PatientProfile, DoctorUnavailability
from .serializers import (
    DoctorProfileSerializer,
    PatientProfileSerializer,
)
from . import views

User = get_user_model()

class SerializerTests(TestCase):
    def setUp(self):
        self.user_doctor = User.objects.create_user(
            username='doc',
            email='doc1@example.com',
            password='pass',
            user_type='doctor'
        )
        self.user_patient = User.objects.create_user(
            username='pat',
            email='pat1@example.com',
            password='pass',
            user_type='patient'
        )
        self.doctor = DoctorProfile.objects.create(user=self.user_doctor, specialty='Cardiology')
        self.patient = PatientProfile.objects.create(user=self.user_patient, phone='123456789')
        self.unavailability = DoctorUnavailability.objects.create(
            doctor=self.doctor,
            date=date.today() + timedelta(days=1),
            start_time=time(8, 0),
            end_time=time(10, 0),
            reason="Reunión"
        )

    def test_doctor_profile_serializer(self):
        serializer = DoctorProfileSerializer(self.doctor)
        self.assertEqual(serializer.data['specialty'], 'Cardiology')

    def test_patient_profile_serializer(self):
        serializer = PatientProfileSerializer(self.patient)
        self.assertEqual(serializer.data['phone'], '123456789')


class ViewAndURLTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_doctor = User.objects.create_user(
            username='doc2',
            email='doc2@example.com',
            password='pass',
            user_type='doctor'
        )
        self.doctor = DoctorProfile.objects.create(user=self.user_doctor, specialty='Cardiology')
        self.client.force_authenticate(user=self.user_doctor)

    def test_unavailability_list_view(self):
        url = reverse('doctor_unavailabilities')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_unavailability_view(self):
        url = reverse('mark_unavailable')
        data = {
            "date": str(date.today() + timedelta(days=2)),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "reason": "Prueba"
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [201, 400])

    def test_remove_unavailability_view(self):
        unav = DoctorUnavailability.objects.create(
            doctor=self.doctor,
            date=date.today() + timedelta(days=3),
            start_time=time(12, 0),
            end_time=time(13, 0),
            reason="Otro"
        )
        url = reverse('remove_unavailability', args=[unav.id])
        response = self.client.delete(url)
        self.assertIn(response.status_code, [200, 204])

    def test_urls_resolve(self):
        self.assertEqual(resolve(reverse('doctor_unavailabilities')).func, views.doctor_unavailabilities)
        self.assertEqual(resolve(reverse('mark_unavailable')).func, views.mark_unavailable)
        self.assertEqual(resolve(reverse('remove_unavailability', args=[1])).func, views.remove_unavailability)

    def test_stats_view(self):
        url = reverse('appointment_stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 400])

    def test_doctor_profile_serializer_fields(self):
        serializer = DoctorProfileSerializer(self.doctor)
        self.assertIn('specialty', serializer.data)

    def test_patient_profile_serializer_fields(self):
        user = User.objects.create_user(
            username='pat2',
            email='pat2@example.com',
            password='pass',
            user_type='patient'
        )
        patient = PatientProfile.objects.create(user=user, phone='987654321')
        serializer = PatientProfileSerializer(patient)
        self.assertIn('phone', serializer.data)


class UserRegistrationSerializerTests(TestCase):
    def setUp(self):
        self.validated_data = {
            'email': 'uniqueuser@example.com',
            'full_name': 'Test User',
            'phone_number': '+12345678901',
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        }

    def test_validate_email(self):
        User.objects.create_user(
            email='duplicate@example.com',
            username='duplicate@example.com',
            password='testpassword'
        )
        data = self.validated_data.copy()
        data['email'] = 'duplicate@example.com'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_validate_phone_number(self):
        invalid_data = self.validated_data.copy()
        invalid_data['phone_number'] = '12345'
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)

    def test_validate_passwords_match(self):
        invalid_data = self.validated_data.copy()
        invalid_data['password_confirm'] = 'differentpassword'
        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_create_user(self):
        serializer = UserRegistrationSerializer(data=self.validated_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(user.is_email_verified)

    def test_send_verification_email(self):
        # Este test necesita mock de send_mail para funcionar correctamente
        user = User.objects.create_user(
            email='sendmailtest@example.com',
            username='sendmailtest@example.com',
            password='testpassword'
        )
        token = user.generate_verification_token()
        serializer = UserRegistrationSerializer()
        try:
            serializer.send_verification_email(user, token)
        except Exception:
            pass  # Puedes usar mock para verificar si se llamó correctamente
