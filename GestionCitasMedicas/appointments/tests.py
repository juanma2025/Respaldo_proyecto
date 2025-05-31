from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from AppCitasMedicas.models import PatientProfile, DoctorProfile
from appointments.models import Appointment
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, time, timedelta

User = get_user_model()

class AppointmentTests(APITestCase):
    def setUp(self):
        # Crear paciente
        self.patient_user = User.objects.create_user(
            username='paciente1',
            email='paciente@example.com',
            password='paciente123',
            full_name='Paciente Uno',
            user_type='patient',
            phone_number='123456789'
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            date_of_birth='1995-01-01'
        )
        self.patient_token = str(RefreshToken.for_user(self.patient_user).access_token)

        # Crear doctor
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor@example.com',
            password='doctor123',
            full_name='Doctor Uno',
            user_type='doctor',
            phone_number='987654321'
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty='general'
        )
        self.doctor_token = str(RefreshToken.for_user(self.doctor_user).access_token)

    def test_create_appointment_as_patient(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        url = reverse('create-appointment')
        data = {
            "doctor_id": self.doctor_profile.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "10:00",
            "reason": "Consulta general",
            "duration_minutes": 30
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_create_appointment_as_doctor_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.doctor_token}')
        url = reverse('create-appointment')
        data = {
            "doctor_id": self.doctor_profile.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "10:00",
            "reason": "Consulta general",
            "duration_minutes": 30
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_patient_appointments(self):
        # Crear una cita directamente en la base de datos
        Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment_date=date.today() + timedelta(days=2),
            appointment_time=time(10,0),
            reason="Chequeo",
            duration_minutes=30,
            status='scheduled'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        url = reverse('patient-appointments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('appointments', response.data)
        self.assertGreaterEqual(len(response.data['appointments']), 1)

    def test_get_appointments_as_doctor_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.doctor_token}')
        url = reverse('patient-appointments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_appointment_detail(self):
        appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment_date=date.today() + timedelta(days=3),
            appointment_time=time(12, 0),
            reason="Revisión",
            duration_minutes=30,
            status='scheduled'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        url = reverse('patient-appointment-detail', args=[appointment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('appointment', response.data)

    def test_patient_cannot_see_others_appointment_detail(self):
        # Otro paciente
        other_user = User.objects.create_user(
            username='paciente2',
            email='paciente2@example.com',
            password='paciente123',
            full_name='Paciente Dos',
            user_type='patient',
            phone_number='111222333'
        )
        other_profile = PatientProfile.objects.create(
            user=other_user,
            date_of_birth='1990-01-01'
        )
        appointment = Appointment.objects.create(
            patient=other_profile,
            doctor=self.doctor_profile,
            appointment_date=date.today() + timedelta(days=4),
            appointment_time=time(13, 0),
            reason="Otro",
            duration_minutes=30,
            status='scheduled'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        url = reverse('patient-appointment-detail', args=[appointment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_appointment(self):
        appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment_date=date.today() + timedelta(days=5),
            appointment_time=time(14, 0),
            reason="Cancelar",
            duration_minutes=30,
            status='scheduled'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        url = reverse('cancel-appointment', args=[appointment.id])
        response = self.client.post(url, {"reason": "Ya no puedo asistir"})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')
