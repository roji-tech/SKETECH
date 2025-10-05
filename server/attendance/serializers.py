from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Attendance, AttendanceSettings


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for AttendanceRecord model
    """
    user_name = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    working_hours = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_name', 'attendance_type', 'user_type',
            'date', 'check_in', 'check_out', 'status', 'working_hours',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'working_hours']
        extra_kwargs = {
            'user': {'required': True},
            'date': {'required': True},
            'attendance_type': {'required': True}
        }

    def get_user_name(self, obj):
        """Get the full name of the user"""
        return obj.user.get_full_name() if obj.user else None

    def get_user_type(self, obj):
        """Get the human-readable attendance type"""
        return obj.get_attendance_type_display()

    def validate(self, data):
        """
        Validate the attendance data
        - Ensure check_out is after check_in if both are provided
        - Ensure user can't have multiple records on the same date
        """
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        user = data.get('user')
        date = data.get('date')
        instance = self.instance

        # Validate check-in and check-out times
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({
                'check_out': _('Check-out time must be after check-in time.')
            })

        # Check for duplicate attendance on the same date
        if user and date:
            qs = Attendance.objects.filter(user=user, date=date)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'date': _('An attendance record already exists for this user on this date.')
                })

        return data

    def create(self, validated_data):
        """
        Create a new attendance record with automatic status determination
        """
        return Attendance.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing attendance record with automatic status updates
        """
        instance.check_in = validated_data.get('check_in', instance.check_in)
        instance.check_out = validated_data.get('check_out', instance.check_out)
        instance.status = validated_data.get('status', instance.status)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()
        return instance


class AttendanceSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for AttendanceSettings model
    """
    class Meta:
        model = AttendanceSettings
        fields = [
            'id', 'school_name',
            'staff_start_time', 'staff_end_time', 'staff_late_mark_after',
            'student_start_time', 'student_end_time', 'student_late_mark_after',
            'work_days', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_work_days(self, value):
        """Validate work days are between 0 (Monday) and 6 (Sunday)"""
        if not isinstance(value, list):
            raise serializers.ValidationError(_("Work days must be a list of integers."))
        
        if not all(isinstance(day, int) and 0 <= day <= 6 for day in value):
            raise serializers.ValidationError(
                _("Work days must be integers between 0 (Monday) and 6 (Sunday).")
            )
        
        # Remove duplicates and sort
        return sorted(list(set(value)))


class AttendanceBulkCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk creating attendance records
    """
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text=_("List of user IDs to create attendance records for")
    )
    date = serializers.DateField(required=True)
    status = serializers.ChoiceField(
        choices=Attendance.Status.choices,
        default=Attendance.Status.PRESENT
    )
    attendance_type = serializers.ChoiceField(
        choices=Attendance.AttendanceType.choices,
        required=True
    )
