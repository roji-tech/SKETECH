from rest_framework import serializers
from main.models import School, Student, Staff, ClassList, AcademicSession, Term
from django.db.models import Count, Sum, F
from datetime import date, timedelta

class DashboardStatsSerializer(serializers.Serializer):
    """Base serializer for dashboard statistics"""
    total_students = serializers.IntegerField(read_only=True)
    total_staff = serializers.IntegerField(read_only=True)
    total_classes = serializers.IntegerField(read_only=True)
    attendance_rate = serializers.FloatField(read_only=True)
    upcoming_events = serializers.ListField(child=serializers.DictField(), read_only=True)
    announcements = serializers.ListField(child=serializers.DictField(), read_only=True)


class AdminDashboardSerializer(DashboardStatsSerializer):
    """Serializer for admin/owner dashboard data"""
    total_fees_collected = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_fees_pending = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    recent_activities = serializers.ListField(child=serializers.DictField(), read_only=True)


class StaffDashboardSerializer(DashboardStatsSerializer):
    """Serializer for staff/teacher dashboard data"""
    my_classes = serializers.ListField(child=serializers.DictField(), read_only=True)
    todays_schedule = serializers.ListField(child=serializers.DictField(), read_only=True)
    assignments_to_grade = serializers.IntegerField(read_only=True)


class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student dashboard data"""
    todays_schedule = serializers.ListField(child=serializers.DictField(), read_only=True)
    upcoming_assignments = serializers.ListField(child=serializers.DictField(), read_only=True)
    recent_grades = serializers.ListField(child=serializers.DictField(), read_only=True)
    attendance_summary = serializers.DictField(read_only=True)
    announcements = serializers.ListField(child=serializers.DictField(), read_only=True)


class ParentDashboardSerializer(serializers.Serializer):
    """Serializer for parent dashboard data"""
    children = serializers.ListField(child=serializers.DictField(), read_only=True)
    upcoming_events = serializers.ListField(child=serializers.DictField(), read_only=True)
    announcements = serializers.ListField(child=serializers.DictField(), read_only=True)
