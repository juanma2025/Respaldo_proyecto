from django.test import TestCase
from django.core import mail
from django.conf import settings
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import User, PatientProfile, DoctorProfile, DoctorSchedule
from .serializers import (
    PatientRegistrationSerializer,
    EmailVerificationSerializer,
    DoctorRegistrationSerializer,
    LoginSerializer,
    UserProfileSerializer,
    PatientProfileSerializer,
    DoctorProfileSerializer,
    DoctorScheduleSerializer,
)

UserModel = get_user_model()

class PatientRegistrationSerializerTest(TestCase):
    def test_valid_registration(self):
        data = {
            "email": "testpatient@example.com",
            "full_name": "Test Patient",
            "phone_number": "+12345678901",
            "password": "supersecret",
            "password_confirm": "supersecret"
        }
        with patch("AppCitasMedicas.serializers.send_mail") as mock_send_mail, \
             patch.object(User, "generate_verification_token", return_value="token123"):
            serializer = PatientRegistrationSerializer(data=data)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            user = serializer.save()
            self.assertEqual(user.email, data["email"])
            self.assertFalse(user.is_email_verified)
            self.assertEqual(PatientProfile.objects.filter(user=user).count(), 1)
            mock_send_mail.assert_called_once()

    def test_email_already_exists(self):
        User.objects.create_user(email="testpatient@example.com", username="testpatient@example.com", password="pass")
        data = {
            "email": "testpatient@example.com",
            "full_name": "Test Patient",
            "phone_number": "+12345678901",
            "password": "supersecret",
            "password_confirm": "supersecret"
        }
        serializer = PatientRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_phone_format_invalid(self):
        data = {
            "email": "test2@example.com",
            "full_name": "Test Patient",
            "phone_number": "123",  # Invalid
            "password": "supersecret",
            "password_confirm": "supersecret"
        }
        serializer = PatientRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_passwords_do_not_match(self):
        data = {
            "email": "test3@example.com",
            "full_name": "Test Patient",
            "phone_number": "+12345678901",
            "password": "supersecret",
            "password_confirm": "othersecret"
        }
        serializer = PatientRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

class EmailVerificationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="verifyme@example.com",
            username="verifyme@example.com",
            password="pass",
            is_email_verified=False,
            email_verification_token="tokentest"
        )

    def test_valid_token(self):
        serializer = EmailVerificationSerializer(data={"token": "tokentest"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_token(self):
        serializer = EmailVerificationSerializer(data={"token": "invalid"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("token", serializer.errors)

class DoctorRegistrationSerializerTest(TestCase):
    def test_valid_registration(self):
        data = {
            "email": "doctor@example.com",
            "full_name": "Dr. Who",
            "specialty": "Cardiology",
            "professional_license": "ABC123"
        }
        with patch("AppCitasMedicas.serializers.send_mail") as mock_send_mail, \
             patch.object(DoctorProfile, "generate_random_password", return_value="randompass"):
            serializer = DoctorRegistrationSerializer(data=data)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            user = serializer.save()
            self.assertEqual(user.email, data["email"])
            self.assertTrue(user.is_email_verified)
            self.assertEqual(DoctorProfile.objects.filter(user=user).count(), 1)
            mock_send_mail.assert_called_once()

    def test_email_already_exists(self):
        User.objects.create_user(email="doctor@example.com", username="doctor@example.com", password="pass")
        data = {
            "email": "doctor@example.com",
            "full_name": "Dr. Who",
            "specialty": "Cardiology",
            "professional_license": "ABC123"
        }
        serializer = DoctorRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_license_already_exists(self):
        user = User.objects.create_user(email="otherdoc@example.com", username="otherdoc@example.com", password="pass")
        DoctorProfile.objects.create(user=user, specialty="Cardiology", professional_license="ABC123")
        data = {
            "email": "doctor2@example.com",
            "full_name": "Dr. Who",
            "specialty": "Cardiology",
            "professional_license": "ABC123"
        }
        serializer = DoctorRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("professional_license", serializer.errors)

class LoginSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com",
            username="login@example.com",
            password="pass",
            is_email_verified=True
        )

    def test_valid_login(self):
        serializer = LoginSerializer(data={"email": "login@example.com", "password": "pass"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_invalid_login(self):
        serializer = LoginSerializer(data={"email": "login@example.com", "password": "wrong"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_unverified_email(self):
        self.user.is_email_verified = False
        self.user.save()
        serializer = LoginSerializer(data={"email": "login@example.com", "password": "pass"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

class UserProfileSerializerTest(TestCase):
    def test_fields(self):
        user = User.objects.create_user(
            email="profile@example.com",
            username="profile@example.com",
            password="pass",
            full_name="Profile User",
            phone_number="+12345678901",
            user_type="patient"
        )
        serializer = UserProfileSerializer(user)
        self.assertEqual(serializer.data["email"], "profile@example.com")
        self.assertEqual(serializer.data["full_name"], "Profile User")
        self.assertEqual(serializer.data["user_type"], "patient")

class PatientProfileSerializerTest(TestCase):
    def test_fields(self):
        user = User.objects.create_user(
            email="patprofile@example.com",
            username="patprofile@example.com",
            password="pass",
            full_name="Patient User",
            phone_number="+12345678901",
            user_type="patient"
        )
        patient = PatientProfile.objects.create(user=user)
        serializer = PatientProfileSerializer(patient)
        self.assertEqual(serializer.data["user"]["email"], "patprofile@example.com")

class DoctorProfileSerializerTest(TestCase):
    def test_fields(self):
        user = User.objects.create_user(
            email="docprofile@example.com",
            username="docprofile@example.com",
            password="pass",
            full_name="Doctor User",
            phone_number="+12345678901",
            user_type="doctor"
        )
        doctor = DoctorProfile.objects.create(user=user, specialty="Cardiology", professional_license="XYZ123")
        serializer = DoctorProfileSerializer(doctor)
        self.assertEqual(serializer.data["user"]["email"], "docprofile@example.com")
        self.assertEqual(serializer.data["specialty"], "Cardiology")

class DoctorScheduleSerializerTest(TestCase):
    def test_fields(self):
        user = User.objects.create_user(
            email="docsch@example.com",
            username="docsch@example.com",
            password="pass",
            full_name="Doctor User",
            phone_number="+12345678901",
            user_type="doctor"
        )
        doctor = DoctorProfile.objects.create(user=user, specialty="Cardiology", professional_license="SCH123")
        schedule = DoctorSchedule.objects.create(
            doctor=doctor,
            weekday=1,
            start_time="08:00",
            end_time="12:00"
        )
        serializer = DoctorScheduleSerializer(schedule)
        self.assertEqual(serializer.data["doctor"], doctor.id)
        self.assertEqual(serializer.data["weekday"], 1)