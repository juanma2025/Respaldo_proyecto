from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from AppCitasMedicas.models import PatientProfile, DoctorProfile
from appointments.models import Appointment
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, time, timedelta
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from AppCitasMedicas.models import PatientProfile, DoctorProfile
from appointments.models import Appointment
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, timedelta, time
from django.utils import timezone


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
        url = reverse('create_appointment')
        data = {
            "doctor": self.doctor_profile.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "10:00"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('appointment', response.data)

    def test_create_appointment_as_doctor_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.doctor_token}')
        url = reverse('create_appointment')
        data = {
            "doctor": self.doctor_profile.id,
            "appointment_date": str(date.today() + timedelta(days=1)),
            "appointment_time": "10:00"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_patient_appointments(self):
        # Crear una cita directamente en la base de datos
        appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment_date=date.today() + timedelta(days=2),
            appointment_time=time(11, 0),
            status='pending'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        url = reverse('patient_appointments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_appointments_as_doctor_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.doctor_token}')
        url = reverse('patient_appointments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class PatientAppointmentListViewTests(APITestCase):
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
            date_of_birth='1990-01-01'
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

        # Crear citas
        self.today = date.today()
        self.appt1 = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment_date=self.today + timedelta(days=1),
            appointment_time=time(10, 0),
            status='scheduled'
        )
        self.appt2 = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            appointment_date=self.today - timedelta(days=2),
            appointment_time=time(11, 0),
            status='completed'
        )

        self.url = reverse('patient-appointments')  # URL para la vista PatientAppointmentListView

    def test_patient_can_view_appointments(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('appointments', response.data)
        self.assertIn('statistics', response.data)
        self.assertEqual(len(response.data['appointments']), 2)

    def test_only_patients_can_access(self):
        doctor_token = str(RefreshToken.for_user(self.doctor_user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {doctor_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_status(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        response = self.client.get(self.url, {'status': 'scheduled'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['appointments']), 1)
        self.assertEqual(response.data['appointments'][0]['status'], 'scheduled')

    def test_filter_by_date_range(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        date_from = (self.today - timedelta(days=3)).strftime('%Y-%m-%d')
        date_to = (self.today - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'date_from': date_from, 'date_to': date_to})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['appointments']), 1)
        self.assertEqual(response.data['appointments'][0]['status'], 'completed')

    def test_filter_upcoming(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        response = self.client.get(self.url, {'upcoming': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['appointments']), 1)
        self.assertEqual(response.data['appointments'][0]['status'], 'scheduled')

    def test_next_appointment_data_in_statistics(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.patient_token}')
        response = self.client.get(self.url)
        stats = response.data['statistics']
        self.assertEqual(stats['upcoming_appointments'], 1)
        self.assertIsNotNone(stats['next_appointment'])
        self.assertEqual(stats['next_appointment']['id'], self.appt1.id)

