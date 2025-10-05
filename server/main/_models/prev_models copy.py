from __future__ import annotations
import logging
import string
import json
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from datetime import date, timedelta
from django.db import models, transaction
from django.db.models import Q, UniqueConstraint, Count, Avg
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator, validate_comma_separated_integer_list
from django.conf import settings
from django.urls import reverse
from typing import Optional
from model_utils.managers import InheritanceManager

from main.tenancy.models import AuditableModel, SoftDeleteModel, SchoolAwareModel, SchoolOwnedModel


# ----------------------------- User Roles Constants ----------------
SUPERADMIN = "superadmin"
OWNER = "owner"
ADMIN = "admin"
TEACHER = "teacher"
STUDENT = "student"


# ----------------------------- User Manager ----------------
class UserManager(BaseUserManager):
    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            username = email
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', SUPERADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


# ----------------------------- Custom User Model ----------------
class User(AbstractUser):
    """
    Custom user model with multi-tenancy support.
    Username is globally unique, email can be duplicated across schools.
    """
    ES_Sep = "_:_"  # email - school separator for login_email
    
    ROLE_CHOICES = (
        (SUPERADMIN, "Super Admin"),
        (OWNER, "School Owner"),
        (ADMIN, "Admin"),
        (TEACHER, "Teacher"),
        (STUDENT, "Student"),
    )

    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    )

    # Make username globally unique and required
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,  # Globally unique
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    
    # Email doesn't need to be unique globally (can be same across schools)
    email = models.EmailField(
        _('email address'),
        unique=False,  # Not globally unique
        help_text=_('Email address - can be duplicated across different schools')
    )

    role = models.CharField(
        max_length=10, 
        default=STUDENT, 
        choices=ROLE_CHOICES,
        db_index=True
    )
    
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES,
        blank=True
    )
    
    image = models.ImageField(
        upload_to='users/avatars/%Y/%m/%d/',
        blank=True, 
        null=True
    )
    
    phone = models.CharField(
        max_length=20, 
        default="+234----",
        blank=True
    )
    
    # This field ensures unique login per school
    login_email = models.CharField(
        max_length=255, 
        unique=True, 
        editable=False,
        help_text=_('Auto-generated unique login identifier')
    )
    
    school = models.ForeignKey(
        'School',
        on_delete=models.CASCADE, 
        related_name='users', 
        null=True, 
        blank=True,
        help_text=_('School this user belongs to')
    )

    # Fields for better user management
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'  # Use username for authentication
    REQUIRED_FIELDS = ['email', 'role']

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['login_email']),
            models.Index(fields=['school', 'role']),
            models.Index(fields=['email', 'school']),
        ]
        constraints = [
            # Ensure email is unique within each school
            UniqueConstraint(
                fields=['email', 'school'], 
                name='unique_email_per_school',
                condition=Q(school__isnull=False)
            ),
        ]

    @property
    def is_superadmin(self):
        return self.role == SUPERADMIN

    @property
    def is_owner(self):
        return self.role == OWNER

    @property
    def is_admin(self):
        return self.role in [ADMIN, OWNER]

    @property
    def is_teacher(self):
        return self.role == TEACHER

    @property
    def is_student(self):
        return self.role == STUDENT

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def get_user_role(self):
        roles = {
            SUPERADMIN: "Super Admin",
            ADMIN: "School Admin",
            OWNER: "School Owner",
            TEACHER: "Teacher",
            STUDENT: "Student"
        }
        return roles.get(self.role, "Unknown Role")

    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Validate role-school relationship
        if self.role in [TEACHER, STUDENT] and not self.school:
            raise ValidationError({'school': 'Staff and students must belong to a school'})
        
        if self.role == SUPERADMIN and self.school:
            raise ValidationError({'school': 'Superadmin should not belong to any specific school'})

    def save(self, *args, **kwargs):
        school = self.school or get_current_school()

        # Set default password for staff and students
        if (self.is_teacher or self.is_student) and not self.password:
            self.set_password(str(self.last_name).lower() or 'default123')

        # Generate the unique login_email
        if self.school:
            self.login_email = f"{self.username}{self.ES_Sep}{self.school.id}"
        else:
            self.login_email = self.username
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.school.name if self.school else 'No School'})"

    def get_profile(self):
        """Get the user's role-specific profile"""
        if self.is_student and hasattr(self, 'student_profile'):
            return self.student_profile
        elif self.is_teacher and hasattr(self, 'staff_profile'):
            return self.staff_profile
        return None


def get_year_from_date(date_string):
    try:
        year = int(str(date_string).split('-')[0])
        return year
    except (ValueError, IndexError, AttributeError):
        raise ValueError(f"Invalid date format: '{date_string}'. Expected format 'YYYY-MM-DD'.")


class UserInherit(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    @property
    def full_name(self):
        return f"{self.user.full_name}"

    @property
    def phone(self):
        return f"{self.user.phone}"

    @property
    def email(self):
        return f"{self.user.email}"


# ----------------------------- Core: School ----------------
class School(AuditableModel, SoftDeleteModel):
    """
    Represents a school in the multi-tenant system.
    Each school is a separate tenant with its own users, classes, and data.
    """
    name = models.CharField(
        max_length=100,
        help_text="Full name of the school",
        db_index=True
    )
    
    owner = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='owned_school',
        help_text="User account that owns this school"
    )
    
    address = models.TextField(
        default="",
        help_text="Full physical address of the school"
    )
    
    phone = models.CharField(
        max_length=20,
        help_text="Primary contact number for the school",
        db_index=True
    )
    
    email = models.EmailField(
        help_text="Primary contact email for the school",
        db_index=True
    )
    
    website = models.URLField(
        null=True,
        blank=True,
        help_text="School's website URL"
    )
    
    motto = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text="School's motto or tagline"
    )
    
    about = models.TextField(
        default="",
        blank=True,
        help_text="Detailed description of the school"
    )
    
    logo = models.ImageField(
        upload_to='schools/logos/%Y/%m/%d/',
        default="schools/logos/default.png",
        null=True,
        blank=True,
        help_text="School's logo image"
    )
    
    short_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Abbreviated name for the school",
        db_index=True
    )
    
    code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        unique=True,
        help_text="Unique code identifier for the school",
        db_index=True
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the school account is active"
    )
    
    subscription_plan = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Current subscription plan"
    )
    
    subscription_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the current subscription expires"
    )
    
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON field for storing school-specific settings"
    )

    schema_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Schema name for the school"
    )

    class Meta:
        indexes = [
            models.Index(fields=['name'], name='school_name_idx'),
            models.Index(fields=['code'], name='school_code_idx'),
            models.Index(fields=['email'], name='school_email_idx'),
            models.Index(fields=['is_active'], name='school_active_idx'),
            models.Index(fields=['created_at'], name='school_created_at_idx'),
            models.Index(
                fields=['subscription_expiry'], 
                name='school_sub_expiry_idx',
                condition=models.Q(is_active=True)
            ),
        ]
        ordering = ['name']
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def clean(self):
        if self.short_name and self.short_name.startswith("SC") and (len(self.short_name) in [5, 6]) and self.short_name[2:].isdigit():
            raise ValidationError("Invalid short name format.")

    def save(self, *args, **kwargs):
        if not self.code:
            last_school = School.objects.all().order_by('id').last()
            if last_school and last_school.code:
                last_code = int(last_school.code[2:])
                new_code = f"SC{str(last_code + 1).zfill(4)}"
            else:
                new_code = "SC0001"
            self.code = new_code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @staticmethod
    def get_user_school(user):
        try:
            if hasattr(user, 'is_owner') and user.is_owner:
                return School.objects.filter(owner=user).first()
            if hasattr(user, 'is_admin') and user.is_admin:
                try:
                    return School.objects.filter(owner=user).first()
                except:
                    return user.school
            elif hasattr(user, 'is_teacher') and user.is_teacher:
                return user.staff_profile.school
            elif hasattr(user, 'is_student') and user.is_student:
                return user.student_profile.school
        except Exception as e:
            logging.error(f"Error getting user school: {e}")
            return None


# ----------------------------- Academic Sessions ----------------
class AcademicSession(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'academic_sessions'

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    next_session_begins = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['-is_current', '-start_date']
        indexes = [
            models.Index(fields=['school', 'is_current']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.school.name}) {'-current' if self.is_current else ''}"

    def save(self, *args, **kwargs):
        # Auto-generate name from dates
        try:
            start_year = self.start_date.year
            end_year = self.end_date.year
            if start_year == end_year:
                self.name = str(start_year)
            else:
                self.name = f"{start_year}-{end_year}"
        except AttributeError:
            pass

        # Handle current session logic
        if self.is_current:
            AcademicSession.objects.filter(
                school=self.school, is_current=True
            ).exclude(pk=self.pk).update(is_current=False)

        super().save(*args, **kwargs)
        self.create_terms()

    def create_terms(self):
        """Creates 1st, 2nd, and 3rd terms for the academic session."""
        term_names = ['1st', '2nd', '3rd']
        total_days = (self.end_date - self.start_date).days
        term_duration = total_days // 3

        current_start_date = self.start_date

        for index, term_name in enumerate(term_names):
            if index == 2:
                current_end_date = self.end_date
            else:
                current_end_date = current_start_date + timedelta(days=term_duration)

            Term.objects.get_or_create(
                academic_session=self,
                name=term_name,
                school=self.school,
                defaults={
                    'start_date': current_start_date,
                    'end_date': current_end_date,
                }
            )

            current_start_date = current_end_date + timedelta(days=1)


# ----------------------------- Terms ----------------
class Term(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'terms'

    TERM_CHOICES = [
        ('1st', '1st Term'),
        ('2nd', '2nd Term'),
        ('3rd', '3rd Term'),
    ]
    
    academic_session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, related_name='terms'
    )
    name = models.CharField(max_length=4, choices=TERM_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    next_term_begins = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('academic_session', 'name')
        indexes = [
            models.Index(fields=['academic_session', 'is_current']),
        ]

    def __str__(self):
        return f"{self.name} ({self.academic_session.name})"


# ----------------------------- Staff ----------------
class Staff(UserInherit):
    related_name = 'staff'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, null=True, blank=True)
    department = models.CharField(max_length=50, null=True, blank=True)
    is_teaching_staff = models.BooleanField(default=True)
    date_of_employment = models.DateField(null=True, blank=True)
    qualification = models.TextField(blank=True)
    specialization = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['school', 'department', 'user__first_name']
        indexes = [
            models.Index(fields=['school', 'employee_id']),
            models.Index(fields=['school', 'is_teaching_staff']),
        ]

    def __str__(self):
        return f"{self.department} - {self.user.full_name}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)

    def generate_employee_id(self):
        """Generate unique employee ID"""
        year = timezone.now().year % 100  # Get last 2 digits of year
        last_staff = Staff.objects.filter(school=self.school).order_by('id').last()
        
        if last_staff and last_staff.employee_id:
            try:
                last_number = int(last_staff.employee_id.split('-')[-1])
                new_number = str(last_number + 1).zfill(3)
            except (ValueError, IndexError):
                new_number = "001"
        else:
            new_number = "001"
        
        return f"EMP-{year}-{new_number}"


# ----------------------------- Class Level & Departments ----------------
class ClassLevel(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'class_levels'

    CLASS_CATEGORIES = (
        ("KG", "Kindergarten"),
        ("PRIMARY", "Primary"),
        ("JSS", "Junior Secondary"),
        ("SSS", "Senior Secondary"),
        ("BASIC", "Basic Education"),
    )

    DEPARTMENT_CHOICES = (
        ("GENERAL", "General"),
        ("ART", "Art Class"),
        ("SCIENCE", "Science Class"),
        ("COMMERCIAL", "Commercial Class"),
        ("SCIENCE_TECH", "Science & Technology Class"),
        ("TECHNICAL", "Technical Class"),
    )

    CLASS_CHOICES = [
        ("Basic1", "Basic 1"), ("Basic2", "Basic 2"), ("Basic3", "Basic 3"),
        ("Basic4", "Basic 4"), ("Basic5", "Basic 5"), ("Basic6", "Basic 6"),
        ("KG1", "Kindergarten 1"), ("KG2", "Kindergarten 2"), ("KG3", "Kindergarten 3"),
        ("PRY1", "Primary 1"), ("PRY2", "Primary 2"), ("PRY3", "Primary 3"),
        ("PRY4", "Primary 4"), ("PRY5", "Primary 5"), ("PRY6", "Primary 6"),
        ("JS1", "Junior Secondary 1"), ("JS2", "Junior Secondary 2"), ("JS3", "Junior Secondary 3"),
        ("SS1", "Senior Secondary 1"), ("SS2", "Senior Secondary 2"), ("SS3", "Senior Secondary 3"),
    ]

    name = models.CharField(max_length=10, choices=CLASS_CHOICES)
    category = models.CharField(max_length=12, choices=CLASS_CATEGORIES)
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default="GENERAL",
    )
    level_order = models.PositiveIntegerField()
    default_capacity = models.PositiveIntegerField(default=50)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["school", "name", "department"], name="uniq_level_name_dept_per_school"),
            UniqueConstraint(fields=["school", "level_order", "department"], name="uniq_level_order_per_dept"),
        ]
        ordering = ["category", "level_order", "department"]
        indexes = [
            models.Index(fields=["school", "category"]),
            models.Index(fields=["school", "level_order"]),
        ]

    def __str__(self):
        label = self.get_name_display()
        return (
            f"{label} ({self.school.name})" if self.department == "GENERAL"
            else f"{label} - {self.get_department_display()} ({self.school.name})"
        )


# ----------------------------- Subjects ----------------
class Subject(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'subjects'

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    is_core = models.BooleanField(default=True)
    applicable_categories = models.JSONField(default=list)
    applicable_departments = models.JSONField(default=list)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["school", "name"], name="uniq_subject_name_per_school"),
            UniqueConstraint(fields=["school", "code"], name="uniq_subject_code_per_school", 
                           condition=Q(code__isnull=False) & ~Q(code='')),
        ]
        ordering = ["name"]
        indexes = [
            models.Index(fields=["school", "is_core"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.school.name})"


# ----------------------------- Session Classes ----------------
class ClassList(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'classes'
    
    DIVISION_CHOICES = [(letter, letter) for letter in string.ascii_uppercase]

    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name="class_instances")
    academic_session = models.ForeignKey("AcademicSession", on_delete=models.CASCADE, related_name="classes")
    division = models.CharField(max_length=1, choices=DIVISION_CHOICES, default="A")
    class_teacher = models.ForeignKey("Staff", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_classes")
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["class_level", "academic_session", "division", "school"], 
                           name="uniq_classlist_per_session_level_division"),
        ]
        ordering = ["academic_session", "class_level__level_order", "division"]
        indexes = [
            models.Index(fields=["school", "academic_session"]),
            models.Index(fields=["school", "class_level"]),
        ]

    def __str__(self):
        return self.full_name

    @property
    def name(self):
        return f"{self.class_level.get_name_display()} {self.division}"

    @property
    def full_name(self):
        return f"{self.name} ({self.academic_session.name})"


# ----------------------------- Student with Improved ID Generation ----------------
class Student(UserInherit):
    related_name = 'students'
    
    reg_no = models.CharField(max_length=20, null=True, blank=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    date_of_birth = models.DateField()
    session_admitted = models.ForeignKey("AcademicSession", on_delete=models.CASCADE, 
                                       null=True, blank=True, related_name="admitted_students")
    
    # Additional student fields
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["school", "student_id"], 
                           condition=Q(student_id__isnull=False), 
                           name="uniq_student_id_per_school"),
            UniqueConstraint(fields=["school", "reg_no"], 
                           condition=Q(reg_no__isnull=False), 
                           name="uniq_reg_no_per_school"),
            UniqueConstraint(fields=["school", "user"], 
                           name="uniq_user_per_school"),
        ]
        indexes = [
            models.Index(fields=['school', 'student_id']),
            models.Index(fields=['school', 'session_admitted']),
        ]

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        
        try:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        except Exception as e:
            logging.error(f"Error calculating age: {e}")
            return None

    def __str__(self):
        return f"{self.student_id or self.reg_no or self.pk} - {self.user.full_name}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = self.generate_unique_student_id()
        super().save(*args, **kwargs)

    def generate_unique_student_id(self):
        """Generate a truly unique student ID with proper error handling"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                # Use school code or fallback
                if self.school.code:
                    prefix = self.school.code
                else:
                    prefix = f"SC{self.school.id:04d}"
                
                # Get admission year
                if self.session_admitted:
                    year = str(self.session_admitted.start_date.year)[-2:]
                else:
                    year = str(timezone.now().year)[-2:]
                
                # Get next sequential number for this school and year
                with transaction.atomic():
                    # Get the last student with similar pattern
                    pattern = f"{prefix}{year}"
                    last_student = Student.objects.select_for_update().filter(
                        school=self.school,
                        student_id__startswith=pattern
                    ).order_by('student_id').last()
                    
                    if last_student and last_student.student_id:
                        try:
                            # Extract number from the end
                            last_id = last_student.student_id
                            number_part = last_id[len(pattern):]
                            last_number = int(number_part)
                            new_number = last_number + 1
                        except (ValueError, IndexError):
                            new_number = 1
                    else:
                        new_number = 1
                    
                    # Format: SCHOOLCODEYY000001
                    student_id = f"{pattern}{new_number:06d}"
                    
                    # Check if this ID already exists (shouldn't with proper locking)
                    if not Student.objects.filter(student_id=student_id).exists():
                        return student_id
                        
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed to generate student ID: {e}")
                continue
        
        # Fallback: use UUID-like approach
        import uuid
        fallback_id = f"STU{str(uuid.uuid4())[:8].upper()}"
        logging.warning(f"Used fallback student ID: {fallback_id}")
        return fallback_id


# ----------------------------- Student Enrollment ----------------
class StudentEnrollment(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'enrollments'

    student = models.ForeignKey("Student", on_delete=models.CASCADE, related_name="enrollments")
    class_list = models.ForeignKey(ClassList, on_delete=models.CASCADE, related_name="enrollments")
    academic_session = models.ForeignKey("AcademicSession", on_delete=models.CASCADE, related_name="enrollments")

    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    left_at = models.DateTimeField(null=True, blank=True)

    promoted = models.BooleanField(default=False)
    promotion_date = models.DateField(null=True, blank=True)
    final_grade = models.CharField(max_length=5)