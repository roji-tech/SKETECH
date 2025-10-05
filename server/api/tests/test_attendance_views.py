import json
from datetime import datetime, time, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from employee.models import Employee
from attendance.models import Attendance, AttendanceActivity, AttendanceOverTime
from django.contrib.auth.models import Permission

User = get_user_model()


class AttendanceAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.hr_user = User.objects.create_user(
            username='hr_user',
            email='hr@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.manager_user = User.objects.create_user(
            username='manager_user',
            email='manager@example.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Create employee records
        self.hr_employee = Employee.objects.create(
            employee_first_name='HR',
            employee_last_name='User',
            employee_user=self.hr_user
        )
        
        self.manager_employee = Employee.objects.create(
            employee_first_name='Manager',
            employee_last_name='User',
            employee_user=self.manager_user
        )
        
        self.regular_employee = Employee.objects.create(
            employee_first_name='Regular',
            employee_last_name='User',
            employee_user=self.regular_user,
            employee_work_info__reporting_manager=self.manager_employee
        )
        
        # Add permissions
        view_perm = Permission.objects.get(codename='view_attendance')
        add_perm = Permission.objects.get(codename='add_attendance')
        change_perm = Permission.objects.get(codename='change_attendance')
        
        self.hr_user.user_permissions.add(view_perm, add_perm, change_perm)
        
        # Create test attendance records
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Regular user's attendance
        self.regular_attendance = Attendance.objects.create(
            employee_id=self.regular_employee,
            attendance_date=yesterday,
            attendance_clock_in=time(9, 0),
            attendance_clock_out=time(17, 0),
            status='present'
        )
        
        # Manager's attendance
        self.manager_attendance = Attendance.objects.create(
            employee_id=self.manager_employee,
            attendance_date=yesterday,
            attendance_clock_in=time(8, 30),
            attendance_clock_out=time(17, 30),
            status='present'
        )
        
        # Set up clients
        self.hr_client = APIClient()
        self.hr_client.force_authenticate(user=self.hr_user)
        
        self.manager_client = APIClient()
        self.manager_client.force_authenticate(user=self.manager_user)
        
        self.regular_client = APIClient()
        self.regular_client.force_authenticate(user=self.regular_user)
    
    def test_hr_can_view_all_attendance(self):
        """Test that HR can view all attendance records"""
        url = reverse('attendance-list')
        response = self.hr_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Should see both records
    
    def test_manager_can_view_team_attendance(self):
        """Test that managers can view their team's attendance"""
        url = reverse('attendance-list')
        response = self.manager_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see the regular user's attendance (their direct report)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['employee_id'], self.regular_employee.id)
    
    def test_employee_can_view_own_attendance(self):
        """Test that employees can only view their own attendance"""
        url = reverse('attendance-list')
        response = self.regular_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see their own attendance
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['employee_id'], self.regular_employee.id)
    
    def test_check_in(self):
        """Test the check-in functionality"""
        url = reverse('attendance-check-in')
        data = {
            'employee_id': self.regular_employee.id,
            'notes': 'Test check-in',
            'location': 'Office'
        }
        
        response = self.regular_client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the attendance record was created
        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            employee_id=self.regular_employee,
            attendance_date=today
        ).first()
        self.assertIsNotNone(attendance)
        self.assertIsNotNone(attendance.attendance_clock_in)
    
    def test_check_out(self):
        """Test the check-out functionality"""
        # First, check in
        check_in_url = reverse('attendance-check-in')
        check_in_data = {'employee_id': self.regular_employee.id}
        self.regular_client.post(check_in_url, check_in_data, format='json')
        
        # Now check out
        check_out_url = reverse('attendance-check-out')
        check_out_data = {'employee_id': self.regular_employee.id}
        
        response = self.regular_client.post(check_out_url, check_out_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the attendance record was updated
        today = timezone.now().date()
        attendance = Attendance.objects.get(
            employee_id=self.regular_employee,
            attendance_date=today
        )
        self.assertIsNotNone(attendance.attendance_clock_out)
    
    def test_attendance_report(self):
        """Test the attendance report generation"""
        url = '/api/reports/attendance/'
        
        # Test HR can see all reports
        response = self.hr_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should see both records
        
        # Test manager can only see team reports
        response = self.manager_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only regular user's record
        self.assertEqual(response.data[0]['employee_id'], self.regular_employee.id)
        
        # Test date filtering
        yesterday = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.hr_client.get(f"{url}?start_date={yesterday}&end_date={yesterday}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both records are from yesterday
    
    def test_overtime_approval(self):
        """Test overtime approval workflow"""
        # Create an overtime record
        overtime = AttendanceOverTime.objects.create(
            employee_id=self.regular_employee,
            month=timezone.now().month,
            year=timezone.now().year,
            overtime_second=7200,  # 2 hours
            status='pending'
        )
        
        # Regular user shouldn't be able to approve
        url = reverse('overtime-approve', kwargs={'pk': overtime.id})
        response = self.regular_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Manager can approve
        response = self.manager_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the status was updated
        overtime.refresh_from_db()
        self.assertEqual(overtime.status, 'approved')
    
    def test_attendance_validation(self):
        """Test attendance validation by HR/Managers"""
        # Create an unvalidated attendance record
        attendance = Attendance.objects.create(
            employee_id=self.regular_employee,
            attendance_date=timezone.now().date(),
            attendance_clock_in=time(9, 0),
            attendance_clock_out=time(17, 0),
            attendance_validated=False
        )
        
        url = reverse('attendance-validate-attendance', kwargs={'pk': attendance.id})
        
        # Regular user shouldn't be able to validate
        response = self.regular_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Manager can validate
        response = self.manager_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the attendance was validated
        attendance.refresh_from_db()
        self.assertTrue(attendance.attendance_validated)
