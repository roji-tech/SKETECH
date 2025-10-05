# from rest_framework import serializers
# from django.utils import timezone
# from datetime import datetime, time
# from attendance.models import Attendance, AttendanceActivity, AttendanceOverTime
# from employee.models import Employee


# class AttendanceActivitySerializer(serializers.ModelSerializer):
#     """
#     Serializer for AttendanceActivity model
#     """
#     class Meta:
#         model = AttendanceActivity
#         fields = [
#             'id', 'attendance_date', 'in_datetime', 'out_datetime',
#             'in_time', 'out_time', 'status'
#         ]
#         read_only_fields = ['id', 'attendance_date', 'in_datetime', 'out_datetime']


# class AttendanceSerializer(serializers.ModelSerializer):
#     """
#     Serializer for Attendance model
#     """
#     employee_name = serializers.CharField(source='employee_id.employee_first_name', read_only=True)
#     employee_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
#     activities = AttendanceActivitySerializer(many=True, read_only=True)
    
#     class Meta:
#         model = Attendance
#         fields = [
#             'id', 'employee_id', 'employee_name', 'attendance_date',
#             'attendance_clock_in', 'attendance_clock_out', 'attendance_worked_hour',
#             'attendance_overtime', 'attendance_overtime_approve', 'attendance_validated',
#             'is_holiday', 'activities', 'status'
#         ]
#         read_only_fields = [
#             'id', 'attendance_worked_hour', 'attendance_overtime',
#             'attendance_overtime_approve', 'attendance_validated'
#         ]

#     def validate(self, data):
#         """
#         Validate the attendance data
#         """
#         if 'attendance_clock_in' in data and 'attendance_clock_out' in data:
#             if data['attendance_clock_in'] and data['attendance_clock_out']:
#                 if data['attendance_clock_in'] >= data['attendance_clock_out']:
#                     raise serializers.ValidationError(
#                         "Check-out time must be after check-in time."
#                     )
#         return data


# class CheckInSerializer(serializers.Serializer):
#     """
#     Serializer for check-in operation
#     """
#     employee_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
#     notes = serializers.CharField(required=False, allow_blank=True)
#     location = serializers.CharField(required=False, allow_blank=True)
    
#     def validate(self, data):
#         """
#         Validate check-in data
#         """
#         employee = data['employee_id']
#         today = timezone.now().date()
        
#         # Check if already checked in today
#         existing_attendance = Attendance.objects.filter(
#             employee_id=employee,
#             attendance_date=today
#         ).first()
        
#         if existing_attendance and existing_attendance.attendance_clock_in:
#             raise serializers.ValidationError("Already checked in for today.")
            
#         return data


# class CheckOutSerializer(serializers.Serializer):
#     """
#     Serializer for check-out operation
#     """
#     employee_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
#     notes = serializers.CharField(required=False, allow_blank=True)
#     location = serializers.CharField(required=False, allow_blank=True)
    
#     def validate(self, data):
#         """
#         Validate check-out data
#         """
#         employee = data['employee_id']
#         today = timezone.now().date()
        
#         # Check if checked in today
#         attendance = Attendance.objects.filter(
#             employee_id=employee,
#             attendance_date=today
#         ).first()
        
#         if not attendance or not attendance.attendance_clock_in:
#             raise serializers.ValidationError("No check-in found for today.")
            
#         if attendance.attendance_clock_out:
#             raise serializers.ValidationError("Already checked out for today.")
            
#         return data


# class OvertimeSerializer(serializers.ModelSerializer):
#     """
#     Serializer for AttendanceOverTime model
#     """
#     employee_name = serializers.CharField(source='employee_id.employee_first_name', read_only=True)
    
#     class Meta:
#         model = AttendanceOverTime
#         fields = [
#             'id', 'employee_id', 'employee_name', 'month', 'year',
#             'overtime', 'overtime_second', 'status'
#         ]
#         read_only_fields = ['id', 'overtime', 'overtime_second']


# class AttendanceReportSerializer(serializers.Serializer):
#     """
#     Serializer for attendance reports
#     """
#     employee_id = serializers.IntegerField()
#     employee_name = serializers.CharField()
#     date = serializers.DateField()
#     check_in = serializers.TimeField(allow_null=True)
#     check_out = serializers.TimeField(allow_null=True)
#     status = serializers.CharField()
#     total_hours = serializers.DurationField(allow_null=True)
#     overtime = serializers.DurationField(allow_null=True)
