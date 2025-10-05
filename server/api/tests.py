from django.test import TestCase

# Create your tests here.

import os
import tempfile
from datetime import date, timedelta
import pandas as pd
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import (
    School, Staff, Student, ClassList, 
    AcademicSession, Term, Subject, User
)

# Test media root for file uploads
MEDIA_ROOT = tempfile.mkdtemp()


def create_test_user(role="admin", school=None, **kwargs):
    """Helper function to create a test user with the given role."""
    user_data = {
        'username': f'test_{role}@example.com',
        'email': f'test_{role}@example.com',
        'password': 'testpass123',
        'first_name': f'Test {role.title()}',
        'last_name': 'User',
        'role': role,
        'is_active': True,
    }
    user_data.update(kwargs)
    
    user = get_user_model().objects.create_user(**user_data)
    if school:
        user.school = school
        user.save()
    return user


def get_tokens_for_user(user):
    """Generate JWT tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AuthenticationTests(APITestCase):
    """Test authentication endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user(role="admin")
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
    
    def test_login_success(self):
        """Test user can log in and get tokens."""
        data = {
            'username': 'test_admin@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_refresh_token(self):
        """Test token refresh works."""
        tokens = get_tokens_for_user(self.user)
        response = self.client.post(
            self.refresh_url, 
            {'refresh': tokens['refresh']}, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class SchoolAPITests(APITestCase):
    """Test School API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_user(role="admin")
        self.client.force_authenticate(user=self.admin)
        self.school_data = {
            'name': 'Test School',
            'address': '123 Test St',
            'phone': '1234567890',
            'email': 'school@example.com',
            'motto': 'Test Motto',
            'about': 'Test About',
            'short_name': 'TS',
            'is_active': True
        }
        self.school = School.objects.create(**self.school_data, owner=self.admin)
    
    def test_create_school(self):
        """Test creating a new school."""
        url = reverse('schools-list')
        response = self.client.post(url, self.school_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(School.objects.count(), 2)  # 1 from setUp + new one
    
    def test_retrieve_school(self):
        """Test retrieving a school."""
        url = reverse('schools-detail', args=[self.school.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.school.name)
    
    def test_update_school(self):
        """Test updating a school."""
        url = reverse('schools-detail', args=[self.school.id])
        updated_data = self.school_data.copy()
        updated_data['name'] = 'Updated School Name'
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Updated School Name')


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AcademicSessionAPITests(APITestCase):
    """Test Academic Session API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_user(role="admin")
        self.client.force_authenticate(user=self.admin)
        
        # Create a school for the test
        self.school = School.objects.create(
            name='Test School', 
            owner=self.admin,
            email='test@example.com',
            address='123 Test St',
            phone='1234567890'
        )
        
        # Create test data
        self.session_data = {
            'name': '2023/2024',
            'start_date': '2023-09-01',
            'end_date': '2024-06-30',
            'is_current': True,
            'school': self.school.id
        }
    
    def test_create_academic_session(self):
        """Test creating an academic session."""
        url = reverse('academic_session-list')
        response = self.client.post(url, self.session_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AcademicSession.objects.count(), 1)
    
    def test_create_terms_for_session(self):
        """Test creating terms for an academic session."""
        # First create the session
        session = AcademicSession.objects.create(
            name='2023/2024',
            start_date='2023-09-01',
            end_date='2024-06-30',
            is_current=True,
            school=self.school
        )
        
        # Now create terms for this session
        url = reverse('academic-session-create-terms', args=[session.id])
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify 3 terms were created
        self.assertEqual(Term.objects.filter(academic_session=session).count(), 3)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class StaffAPITests(APITestCase):
    """Test Staff API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_user(role="admin")
        self.client.force_authenticate(user=self.admin)
        
        # Create a school
        self.school = School.objects.create(
            name='Test School',
            owner=self.admin,
            email='test@example.com',
            address='123 Test St',
            phone='1234567890'
        )
        
        # Create test staff data
        self.staff_data = {
            'user': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'password': 'testpass123',
                'role': 'staff',
                'is_active': True
            },
            'department': 'Mathematics',
            'is_teaching_staff': True
        }
    
    def test_create_staff(self):
        """Test creating a new staff member."""
        url = reverse('staff-list')
        response = self.client.post(url, self.staff_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Staff.objects.count(), 1)
        self.assertEqual(User.objects.filter(role='staff').count(), 2)  # 1 from setup + new staff
    
    def test_import_staff(self):
        """Test importing staff from a CSV file."""
        # Create a test CSV file
        import csv
        from io import StringIO
        
        csv_data = StringIO()
        fieldnames = ['first_name', 'last_name', 'email', 'department', 'is_teaching_staff']
        writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'department': 'Science',
            'is_teaching_staff': 'True'
        })
        
        # Create a test file
        test_file = SimpleUploadedFile(
            'test_staff_import.csv',
            csv_data.getvalue().encode('utf-8'),
            content_type='text/csv'
        )
        
        # Make the request
        url = reverse('staff-import-staff')
        response = self.client.post(url, {'file': test_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Staff.objects.count(), 1)
        self.assertTrue(User.objects.filter(email='jane.smith@example.com').exists())


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class StudentAPITests(APITestCase):
    """Test Student API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = create_test_user(role="admin")
        self.client.force_authenticate(user=self.admin)
        
        # Create a school
        self.school = School.objects.create(
            name='Test School',
            owner=self.admin,
            email='test@example.com',
            address='123 Test St',
            phone='1234567890'
        )
        
        # Create an academic session
        self.session = AcademicSession.objects.create(
            name='2023/2024',
            start_date='2023-09-01',
            end_date='2024-06-30',
            is_current=True,
            school=self.school
        )
        
        # Create a class
        self.school_class = ClassList.objects.create(
            name='Primary 1',
            academic_session=self.session,
            school=self.school
        )
        
        # Create test student data
        self.student_data = {
            'user': {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@example.com',
                'password': 'testpass123',
                'role': 'student',
                'is_active': True
            },
            'date_of_birth': '2015-05-15',
            'admission_number': 'STD001',
            'class_id': self.school_class.id
        }
    
    def test_create_student(self):
        """Test creating a new student."""
        url = reverse('students-list')
        response = self.client.post(url, self.student_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(User.objects.filter(role='student').count(), 1)
    
    def test_import_students(self):
        """Test importing students from a CSV file."""
        # Create a test CSV file
        import csv
        from io import StringIO
        
        csv_data = StringIO()
        fieldnames = ['first_name', 'last_name', 'email', 'admission_number', 'class_name', 'date_of_birth']
        writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            'first_name': 'Bob',
            'last_name': 'Wilson',
            'email': 'bob.wilson@example.com',
            'admission_number': 'STD002',
            'class_name': 'Primary 1',
            'date_of_birth': '2015-07-20'
        })
        
        # Create a test file
        test_file = SimpleUploadedFile(
            'test_students_import.csv',
            csv_data.getvalue().encode('utf-8'),
            content_type='text/csv'
        )
        
        # Make the request
        url = reverse('students-import-students')
        response = self.client.post(url, {'file': test_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Student.objects.count(), 1)
        self.assertTrue(User.objects.filter(email='bob.wilson@example.com').exists())


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class DashboardAPITests(APITestCase):
    """Test Dashboard API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create an admin user
        self.admin = create_test_user(role="admin")
        
        # Create a school
        self.school = School.objects.create(
            name='Test School',
            owner=self.admin,
            email='test@example.com',
            address='123 Test St',
            phone='1234567890'
        )
        
        # Create an academic session
        self.session = AcademicSession.objects.create(
            name='2023/2024',
            start_date='2023-09-01',
            end_date='2024-06-30',
            is_current=True,
            school=self.school
        )
        
        # Create a class
        self.school_class = ClassList.objects.create(
            name='Primary 1',
            academic_session=self.session,
            school=self.school
        )
        
        # Create a staff member
        self.staff_user = create_test_user(
            username='staff@example.com',
            email='staff@example.com',
            role='staff',
            school=self.school
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            department='Mathematics',
            is_teaching_staff=True
        )
        
        # Create a student
        self.student_user = create_test_user(
            username='student@example.com',
            email='student@example.com',
            role='student',
            school=self.school
        )
        self.student = Student.objects.create(
            user=self.student_user,
            date_of_birth='2015-05-15',
            admission_number='STD001'
        )
    
    def test_admin_dashboard(self):
        """Test admin dashboard data retrieval."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_students', response.data)
        self.assertIn('total_staff', response.data)
        self.assertIn('total_classes', response.data)
        self.assertIn('total_subjects', response.data)
    
    def test_staff_dashboard(self):
        """Test staff dashboard data retrieval."""
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add more assertions based on staff dashboard data structure
    
    def test_student_dashboard(self):
        """Test student dashboard data retrieval."""
        # Enroll the student in a class
        from main.models import StudentEnrollment
        StudentEnrollment.objects.create(
            student=self.student,
            class_list=self.school_class,
            academic_session=self.session,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.student_user)
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add more assertions based on student dashboard data structure
