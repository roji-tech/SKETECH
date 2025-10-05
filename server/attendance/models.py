# from django.db import models
# from django.conf import settings
# from django.utils import timezone
# from django.utils.translation import gettext_lazy as _


# class Attendance(models.Model):
#     """
#     Base model for tracking attendance records for both staff and students.
#     """
#     class AttendanceType(models.TextChoices):
#         STAFF = 'staff', _('Staff')
#         STUDENT = 'student', _('Student')

#     class Status(models.TextChoices):
#         PRESENT = 'present', _('Present')
#         ABSENT = 'absent', _('Absent')
#         LATE = 'late', _('Late')
#         HALF_DAY = 'half_day', _('Half Day')
#         HOLIDAY = 'holiday', _('Holiday')
#         LEAVE = 'leave', _('On Leave')
#         EXCUSED = 'excused', _('Excused Absence')

#     # User can be either staff or student
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='attendance_records',
#         verbose_name=_('user')
#     )
#     attendance_type = models.CharField(
#         max_length=10,
#         choices=AttendanceType.choices,
#         verbose_name=_('attendance type')
#     )
#     date = models.DateField(verbose_name=_('date'))
#     check_in = models.DateTimeField(
#         null=True, 
#         blank=True,
#         verbose_name=_('check in time')
#     )
#     check_out = models.DateTimeField(
#         null=True, 
#         blank=True,
#         verbose_name=_('check out time')
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=Status.choices,
#         default=Status.PRESENT,
#         verbose_name=_('status')
#     )
#     notes = models.TextField(
#         blank=True, 
#         null=True,
#         verbose_name=_('notes')
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name=_('created at')
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name=_('updated at')
#     )

#     class Meta:
#         ordering = ['-date', 'user']
#         unique_together = ['user', 'date']
#         verbose_name = _('attendance record')
#         verbose_name_plural = _('attendance records')
#         indexes = [
#             models.Index(fields=['user', 'date']),
#             models.Index(fields=['attendance_type', 'date']),
#             models.Index(fields=['status', 'date']),
#         ]

#     def __str__(self):
#         return f"{self.user.get_full_name()} - {self.date} ({self.get_status_display()})"

#     @property
#     def working_hours(self):
#         """Calculate working/attended hours if both check-in and check-out are present"""
#         if self.check_in and self.check_out:
#             duration = self.check_out - self.check_in
#             return round(duration.total_seconds() / 3600, 2)  # Convert to hours
#         return 0


# class AttendanceSettings(models.Model):
#     """
#     Model to store attendance-related settings for the school.
#     """
#     school_name = models.CharField(
#         max_length=255,
#         default='School',
#         verbose_name=_('school name')
#     )
    
#     # Staff settings
#     staff_start_time = models.TimeField(
#         default='08:00:00',
#         verbose_name=_('staff start time')
#     )
#     staff_end_time = models.TimeField(
#         default='16:00:00',
#         verbose_name=_('staff end time')
#     )
#     staff_late_mark_after = models.IntegerField(
#         default=15,
#         verbose_name=_('staff late mark after (minutes)'),
#         help_text=_("Mark staff as late after X minutes from start time")
#     )
    
#     # Student settings
#     student_start_time = models.TimeField(
#         default='08:30:00',
#         verbose_name=_('student start time')
#     )
#     student_end_time = models.TimeField(
#         default='14:30:00',
#         verbose_name=_('student end time')
#     )
#     student_late_mark_after = models.IntegerField(
#         default=10,
#         verbose_name=_('student late mark after (minutes)'),
#         help_text=_("Mark student as late after X minutes from start time")
#     )
    
#     # Common settings
#     work_days = models.JSONField(
#         default=list,
#         help_text=_("List of work days (0=Monday, 6=Sunday)")
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = _('attendance settings')
#         verbose_name_plural = _('attendance settings')

#     def __str__(self):
#         return f"{self.school_name} - Attendance Settings"

#     @classmethod
#     def load(cls):
#         """Load or create a single settings instance"""
#         obj, created = cls.objects.get_or_create(pk=1)
#         return obj