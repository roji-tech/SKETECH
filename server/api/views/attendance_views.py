# from rest_framework import viewsets, status, permissions, mixins
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from django.utils import timezone
# from datetime import datetime, timedelta
# from django.db.models import Q, Sum, F
# from django.shortcuts import get_object_or_404

# from attendance.models import Attendance, AttendanceActivity, AttendanceOverTime
# from employee.models import Employee
# from api.permissions import IsAuthenticatedEmployee, IsHRAdmin, IsManagerOrHR
# from api.serializers.attendance_serializers import (
#     AttendanceSerializer, CheckInSerializer, CheckOutSerializer,
#     OvertimeSerializer, AttendanceReportSerializer, AttendanceActivitySerializer
# )


# class AttendanceViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows attendance records to be viewed or edited.
#     """
#     serializer_class = AttendanceSerializer
#     permission_classes = [IsAuthenticatedEmployee]
#     filterset_fields = ['employee_id', 'attendance_date', 'status']
#     search_fields = ['employee_id__employee_first_name', 'employee_id__employee_last_name']
#     ordering_fields = ['attendance_date', 'attendance_clock_in', 'attendance_clock_out']

#     def get_queryset(self):
#         # For HR/Admin, return all attendance records
#         if self.request.user.has_perm('attendance.view_attendance'):
#             return Attendance.objects.all()
#         # For managers, return attendance of their team members
#         elif hasattr(self.request.user, 'employee') and self.request.user.employee.employee_work_info.reporting_manager:
#             return Attendance.objects.filter(
#                 employee_id__employee_work_info__reporting_manager=self.request.user.employee
#             )
#         # For regular employees, return only their own attendance
#         return Attendance.objects.filter(employee_id__employee_user_id=self.request.user.id)

#     @action(detail=False, methods=['post'])
#     def check_in(self, request):
#         """
#         Handle employee check-in
#         """
#         serializer = CheckInSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             employee = serializer.validated_data['employee_id']
#             now = timezone.now()
#             today = now.date()
            
#             # Create or update attendance record
#             attendance, created = Attendance.objects.get_or_create(
#                 employee_id=employee,
#                 attendance_date=today,
#                 defaults={
#                     'attendance_clock_in': now.time(),
#                     'attendance_clock_in_date': today,
#                     'status': 'present'
#                 }
#             )
            
#             # Create attendance activity
#             AttendanceActivity.objects.create(
#                 employee_id=employee,
#                 attendance_date=today,
#                 clock_in_date=today,
#                 clock_in=now.time(),
#                 attendance_id=attendance,
#                 shift_day=attendance.shift_id.get_day_display() if attendance.shift_id else None,
#             )
            
#             return Response(
#                 {'status': 'success', 'message': 'Checked in successfully'},
#                 status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['post'])
#     def check_out(self, request):
#         """
#         Handle employee check-out
#         """
#         serializer = CheckOutSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             employee = serializer.validated_data['employee_id']
#             now = timezone.now()
#             today = now.date()
            
#             # Get today's attendance
#             attendance = get_object_or_404(
#                 Attendance,
#                 employee_id=employee,
#                 attendance_date=today,
#                 attendance_clock_in__isnull=False
#             )
            
#             if attendance.attendance_clock_out:
#                 return Response(
#                     {'status': 'error', 'message': 'Already checked out for today'},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Update attendance record
#             attendance.attendance_clock_out = now.time()
#             attendance.attendance_clock_out_date = today
#             attendance.save()
            
#             # Update the latest activity
#             activity = AttendanceActivity.objects.filter(
#                 attendance_id=attendance,
#                 clock_in__isnull=False,
#                 clock_out__isnull=True
#             ).order_by('-in_datetime').first()
            
#             if activity:
#                 activity.clock_out = now.time()
#                 activity.out_datetime = now
#                 activity.save()
            
#             return Response(
#                 {'status': 'success', 'message': 'Checked out successfully'},
#                 status=status.HTTP_200_OK
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['get'])
#     def today(self, request):
#         """
#         Get today's attendance status for the current user
#         """
#         today = timezone.now().date()
#         attendance = Attendance.objects.filter(
#             employee_id__employee_user_id=request.user.id,
#             attendance_date=today
#         ).first()
        
#         serializer = self.get_serializer(attendance)
#         return Response(serializer.data)

#     @action(detail=True, methods=['post'])
#     def validate_attendance(self, request, pk=None):
#         """
#         Validate an attendance record (for HR/Managers)
#         """
#         if not request.user.has_perm('attendance.validate_attendance'):
#             return Response(
#                 {'status': 'error', 'message': 'Permission denied'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
            
#         attendance = self.get_object()
#         attendance.attendance_validated = True
#         attendance.save()
        
#         return Response({'status': 'success', 'message': 'Attendance validated'})


# class OvertimeViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     API endpoint for viewing and managing overtime records
#     """
#     serializer_class = OvertimeSerializer
#     permission_classes = [IsAuthenticatedEmployee]
#     filterset_fields = ['employee_id', 'month', 'year', 'status']
    
#     def get_queryset(self):
#         # HR/Admin can see all overtime records
#         if self.request.user.has_perm('attendance.view_attendanceovertime'):
#             return AttendanceOverTime.objects.all()
#         # Managers can see their team's overtime
#         elif hasattr(self.request.user, 'employee') and self.request.user.employee.employee_work_info.reporting_manager:
#             return AttendanceOverTime.objects.filter(
#                 employee_id__employee_work_info__reporting_manager=self.request.user.employee
#             )
#         # Employees can only see their own overtime
#         return AttendanceOverTime.objects.filter(employee_id__employee_user_id=self.request.user.id)
    
#     @action(detail=True, methods=['post'])
#     def approve(self, request, pk=None):
#         """
#         Approve overtime (for HR/Managers)
#         """
#         if not request.user.has_perm('attendance.approve_attendanceovertime'):
#             return Response(
#                 {'status': 'error', 'message': 'Permission denied'},
#                 status=status.HTTP_403_FORBIDDEN
#             )
            
#         overtime = self.get_object()
#         overtime.status = 'approved'
#         overtime.save()
        
#         return Response({'status': 'success', 'message': 'Overtime approved'})


# class AttendanceReportView(APIView):
#     """
#     API endpoint for generating attendance reports
#     """
#     permission_classes = [IsAuthenticatedEmployee, IsManagerOrHR]
    
#     def get(self, request):
#         start_date = request.query_params.get('start_date')
#         end_date = request.query_params.get('end_date')
#         employee_id = request.query_params.get('employee_id')
        
#         # Validate dates
#         try:
#             start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else timezone.now().date()
#             end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else timezone.now().date()
#         except ValueError:
#             return Response(
#                 {'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
            
#         # Get attendance data
#         queryset = Attendance.objects.filter(
#             attendance_date__range=[start_date, end_date]
#         )
        
#         # Filter by employee if specified
#         if employee_id:
#             queryset = queryset.filter(employee_id=employee_id)
        
#         # For managers, only show their team's data
#         if hasattr(request.user, 'employee') and not request.user.has_perm('attendance.view_attendance'):
#             queryset = queryset.filter(
#                 employee_id__employee_work_info__reporting_manager=request.user.employee
#             )
        
#         # Process data for the report
#         report_data = []
#         for attendance in queryset:
#             report_data.append({
#                 'employee_id': attendance.employee_id.id,
#                 'employee_name': f"{attendance.employee_id.employee_first_name} {attendance.employee_id.employee_last_name}",
#                 'date': attendance.attendance_date,
#                 'check_in': attendance.attendance_clock_in,
#                 'check_out': attendance.attendance_clock_out,
#                 'status': attendance.status,
#                 'total_hours': attendance.attendance_worked_hour,
#                 'overtime': attendance.attendance_overtime if attendance.attendance_overtime_approve else None
#             })
        
#         serializer = AttendanceReportSerializer(report_data, many=True)
#         return Response(serializer.data)
