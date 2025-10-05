from __future__ import annotations
# adjust import path if different
from .tenancy.tenancy_models import SchoolAwareModel, AuditableModel, SoftDeleteModel
from main.tenancy.managers import TenantManager, get_current_school
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal

from django.contrib.auth import get_user_model

from main.tenancy.threadlocals import get_current_request
import string
from datetime import date
import time
import sys
from django.db import models, transaction, IntegrityError
from django.db.models import Q
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from typing import Optional
from django.db.models import Q, UniqueConstraint, Count
from django.utils import timezone

from django.contrib.auth.models import AbstractUser, UserManager, make_password
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils.translation import gettext_lazy as _
from main.tenancy.managers import get_current_school
from django.db.models import Q, UniqueConstraint


from .tenancy.tenancy_models import *

SUPERADMIN = "superadmin"
OWNER = "owner"
ADMIN = "admin"
STAFF = "staff"
STUDENT = "student"
PARENT = "parent"

make_password


class UserManager(TenantManager, UserManager):
    """
    Custom user model manager that supports tenant-aware user management.
    Auto-filters users by school, with exceptions for superusers/superadmins.
    """

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        User = get_user_model()
        verify_username = User.get_username(email)
        if User.objects.filter(username=verify_username).exists():
            raise ValidationError("User already exists.")
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", SUPERADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser, SchoolOwnedModel):
    """
    Multi-tenant friendly auth model:
      - **username**: globally unique and used for login (USERNAME_FIELD)
      - **email**: duplicates allowed (globally); optional per-school uniqueness constraint
    #   - **login_email**: unique composite used by some UIs (`username_:_<school_id>`), optional for auth
    """
    ES_Sep = "_:_"  # email - school separator
    ROLE_CHOICES = (
        (SUPERADMIN, "Super Admin"),
        (OWNER, "School Owner"),
        (ADMIN, "Admin"),
        (STAFF, "Staff"),
        (STUDENT, "Student"),
        (PARENT, "Parent"),
    )

    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
    )

    USERNAME_FIELD = 'username'  # Use username for authentication
    REQUIRED_FIELDS = ['role', "email"]

    # Make username globally unique and required
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,  # Globally unique
        help_text=_(
            'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    email = models.EmailField(
        _('email address'), unique=False)  # Non-unique email
    role = models.CharField(
        max_length=10, default=STUDENT, choices=ROLE_CHOICES
    )  # Default role is student
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    image = models.ImageField(blank=True, null=True, default=None)
    phone = models.CharField(max_length=20, default="+234----")
    # login_email = models.CharField(
    #     max_length=255, unique=True, editable=False
    # )  # Proxy field
    # Fields for better user management
    is_email_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    school = models.ForeignKey(
        'School',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        help_text=_('School this user belongs to')
    )

    objects = UserManager()

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["school"]),
            # models.Index(fields=["login_email"]),
        ]
        constraints = [
            # enable if you want email uniqueness *per school* (still not global)
            UniqueConstraint(
                fields=["email", "school"],
                condition=Q(email__isnull=False) & ~Q(
                    email="") & Q(school__isnull=False),
                name="uniq_email_per_school",
            ),
            UniqueConstraint(
                fields=["username"],
                name="uniq_username",
            ),
        ]

    @property
    def is_superadmin(self):
        return self.role == "superadmin"

    @property
    def is_owner(self):
        return self.role == "owner"

    @property
    def is_admin(self):
        return self.role in ["admin", "owner"]

    @property
    def is_school_staff(self):
        return self.role == "staff"

    @property
    def is_student(self):
        return self.role == "student"

    @property
    def full_name(self):
        full_name = self.email  # Using email if first_name and last_name are empty
        if self.first_name and self.last_name:
            full_name = self.first_name + " " + self.last_name
        return full_name

    def __str__(self):
        return "{} ({})".format(self.email, self.full_name)

    @property
    def get_user_role(self):
        roles = {
            "superadmin": "Super Admin",
            "admin": "School Admin",
            "owner": "School Owner",
            "staff": "Staff",
            "student": "Student"
        }
        return roles.get(self.role, "Unknown Role")

    @classmethod
    def get_username(cls, email):
        value = email or "No_Email"
        school = get_current_school()
        if not school:
            return f"{value}{cls.ES_Sep}No_School"
        return f"{value}{cls.ES_Sep}{school.id}"

    # def clean(self):
    #     super().clean()
    #     username = self.get_username(self.email)
    #     if User.objects.filter(username=username).exists():
    #         raise ValidationError("User already exists.")

    def save(self, *args, **kwargs):
        school = self.school or get_current_school()
        try:
            # Custom save logic, if needed
            if (self.is_school_staff or self.is_student) and not self.password:
                self.set_password(str(self.last_name).lower() or 'default123')
        except Exception as e:
            print(e)
            pass

        # Generate the unique username
        if not self.username:
            if school:
                self.username = self.get_username(self.email)
            else:
                self.username = f"{self.email}{self.ES_Sep}No_School"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.school.name if self.school else 'No School'})"

    @property
    def full_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username

    def get_profile(self):
        """Get the user's role-specific profile"""
        if self.is_student and hasattr(self, 'student_profile'):
            return self.student_profile
        elif self.is_school_staff and hasattr(self, 'staff_profile'):
            return self.staff_profile
        return None


def get_year_from_date(date_string):
    try:
        year = int(date_string.split('-')[0])
        return year
    except (ValueError, IndexError):
        # Handle cases where the date string is not in the expected format
        raise ValueError(
            "Invalid date format: '" + date_string + "'. Expected format 'YYYY-MM-DD'."
        )


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

    class Meta:
        abstract = True


# ----------------------------- Core: School ----------------
class School(models.Model):
    """
    Represents a school in the multi-tenant system.
    Each school is a separate tenant with its own users, classes, and data.
    """
    name = models.CharField(
        max_length=100,
        help_text="Full name of the school",
        db_index=True  # Add index for faster lookups
    )

    owner = models.OneToOneField(
        "User",
        on_delete=models.PROTECT,  # Prevent accidental deletion of school owner
        related_name='owned_school',
        help_text="User account that owns this school"
    )

    address = models.TextField(
        default="",
        help_text="Full physical address of the school"
    )

    phone = models.CharField(
        max_length=20,  # Increased from 15 to accommodate international numbers
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
        max_length=255,  # Increased from 100
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
        max_length=50,  # Increased from 15
        null=True,
        blank=True,
        help_text="Abbreviated name for the school (e.g., 'Hogwarts' for 'Hogwarts School of Witchcraft and Wizardry')",
        db_index=True
    )

    subdomain = models.CharField(
        max_length=20,  #
        null=True,
        blank=True,
        unique=True,
        help_text="Unique subdomain identifier for the school (auto-generated if not provided)",
        db_index=True
    )

    code = models.CharField(
        max_length=10,  # Increased from 6
        null=True,
        blank=True,
        # unique=True,
        help_text="Unique code identifier for the school (auto-generated if not provided)",
        db_index=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether the school account is active"
    )

    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_%(class)ss',
        help_text="User who deleted this record"
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
        default=dict,  # e.g {'max_exam_score_for_primary': 60}
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
            models.Index(fields=['subdomain'], name='school_subdomain_idx'),
            models.Index(fields=['email'], name='school_email_idx'),
            models.Index(fields=['is_active'], name='school_active_idx'),
            models.Index(
                fields=['subscription_expiry'],
                name='school_sub_expiry_idx',
                condition=models.Q(is_active=True)
            ),
        ]
        ordering = ['name']
        verbose_name = "School"
        verbose_name_plural = "Schools"
        permissions = [
            ("view_school_dashboard", "Can view school dashboard"),
            ("manage_school_settings", "Can manage school settings"),
        ]

    def clean(self):
        if self.short_name and self.short_name.startswith("SC") and (len(self.short_name) == 6 or len(self.short_name) == 5) and self.short_name[2:].isdigit():
            raise ValidationError("Invalid short name format.")

    # def save(self, *args, **kwargs):
    #     if not self.code:
    #         last_school = School.objects.all().order_by('id').last()
    #         if last_school and last_school.code:
    #             last_code = int(last_school.code[2:])
    #             new_code = f"SC{str(last_code + 1).zfill(4)}"
    #         else:
    #             new_code = "SC0001"
    #         self.code = new_code
    #     super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.code:
            max_retries = 10  # Prevent infinite loops
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # Get the highest existing code
                    last_school = School.objects.exclude(
                        code__isnull=True
                    ).exclude(
                        code=''
                    ).order_by('-code').first()

                    if last_school and last_school.code and last_school.code.startswith('SC'):
                        try:
                            # Extract the numeric part and increment
                            last_num = int(last_school.code[2:])
                            new_num = last_num + 1
                            new_code = f"SC{str(new_num).zfill(4)}"
                        except (ValueError, IndexError) as e:
                            print("Error: ", e)
                            # Fallback if code format is invalid
                            new_code = f"SC{str(int(time.time()))[-4:]}"
                    else:
                        # First school or no valid code found
                        new_code = "SC0001"

                    # Set the code
                    self.code = new_code

                    # Try to save with the new code
                    with transaction.atomic():
                        return super().save(*args, **kwargs)

                except IntegrityError as e:
                    # If we get an integrity error, it means the code exists
                    print("Error: ", e)
                    if 'code' in str(e):
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise RuntimeError(
                                "Failed to generate a unique school code after multiple attempts")
                        continue
                    raise  # Re-raise if it's a different error
        else:
            # If code is provided, just save normally
            return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False, deleted_by=None):
        """Soft delete the model instance."""
        from django.utils import timezone
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=['is_active', 'deleted_at', 'deleted_by'])

    def hard_delete(self, *args, **kwargs):
        """Actually delete the model instance."""
        super().delete(*args, **kwargs)

    @staticmethod
    def get_user_school(user):
        try:
            if hasattr(user, 'is_owner') and user.is_owner:
                # For owners or admins, return the school where they are the owner
                return School.objects.filter(owner=user).first()
            if hasattr(user, 'is_admin') and user.is_admin:
                try:
                    return School.objects.filter(owner=user).first()
                except:
                    return user.school
                # For admins, return the school associated with their admin profile
            elif hasattr(user, 'is_school_staff') and user.is_school_staff:
                # For staff, return the school associated with their staff profile
                return user.staff_profile.school
            elif hasattr(user, 'is_student') and user.is_student:
                # For students, return the school associated with their student profile
                return user.student_profile.school
        except Exception as e:
            raise e
        # end try


# ----------------------------- Core: Academic Sessions ----------------
class AcademicSession(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'academic_sessions'

    def __str__(self):
        return f"{self.name} ({self.school.name}) {'-current' if self.is_current else ''}"

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['-is_current']

    name = models.CharField(max_length=100)  # e.g., "2023/2024"
    start_date = models.DateField()
    end_date = models.DateField()
    next_session_begins = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        _name = ""

        try:
            _name = f"{self.start_date.year}-{self.end_date.year}"
        except Exception as e:
            year1 = get_year_from_date(self.start_date)
            year2 = get_year_from_date(self.end_date)
            _name = f"{year1}-{year2}"

        if self.name != _name:
            self.name = _name

        if not self.name:
            self.name = _name

        # Attempt to split and convert the name parts to integers
        try:
            name_parts = self.name.split('-')
            existing_start_year = int(name_parts[0])
            existing_end_year = int(name_parts[1]) if len(
                name_parts) > 1 else existing_start_year

            # If both years are the same, update the name to just the year
            if existing_start_year == existing_end_year:
                self.name = str(existing_start_year)
        except (ValueError, IndexError):
            year1 = get_year_from_date(self.start_date)
            year2 = get_year_from_date(self.end_date)
            self.name = f"{year1}-{year2}"

        # Retrieve all current sessions for the school
        current_sessions = AcademicSession.objects.filter(
            school=self.school, is_current=True
        )
        print(self.is_current, current_sessions)

        # If this session is marked as current, ensure all others are not
        if self.is_current:
            # Deactivate all other sessions for the same school
            current_sessions.update(is_current=False)
        else:
            # If not marked as current, find the latest session
            latest_session = AcademicSession.objects.filter(
                school=self.school
            ).order_by('-end_date').first()

            # If the latest session is this session, set it as current
            if latest_session == self:
                self.is_current = True
                current_sessions.update(is_current=False)

        # Call the parent class's save method
        super().save(*args, **kwargs)
        # Create terms and classes automatically after the session is saved
        self.create_terms()

    def create_terms(self):
        """Creates 1st, 2nd, and 3rd terms for the academic session."""
        term_names = ['1st', '2nd', '3rd']
        total_days = (self.end_date - self.start_date).days
        term_duration = total_days // 3

        # Define the start date for the first term
        current_start_date = self.start_date

        for index, term_name in enumerate(term_names):
            if index == 2:  # Last term, ensure the end date matches the session end date
                current_end_date = self.end_date
            else:
                current_end_date = current_start_date + \
                    timedelta(days=term_duration)

            # Create or get the term
            Term.objects.get_or_create(
                academic_session=self,
                name=term_name,
                school=self.school,
                defaults={
                    'start_date': current_start_date,
                    'end_date': current_end_date,
                }
            )

            # Set the start date for the next term
            current_start_date = current_end_date + timedelta(days=1)

    def create_all_classes(self):
        """Creates different sets of classes and associated subjects."""
        class_sets = {
            'PRIMARY': ['PRY1', 'PRY2', 'PRY3', 'PRY4', 'PRY5', 'PRY6'],
            'JSS': ['JS1', 'JS2', 'JS3'],
            'SSS': ['SS1', 'SS2', 'SS3'],
            'BASIC': ['BASIC1', 'Basic2', 'Basic3', 'Basic4', 'Basic5', 'Basic6'],
            'KG': ['KG1', 'KG2', 'KG3'],
        }
        default_subjects = ['English', 'Mathematics']

        for class_group, classes in class_sets.items():
            for class_name in classes:
                school_class, created = ClassList.objects.get_or_create(
                    academic_session=self, name=class_name)

                # Create default subjects for each class
                if created:
                    for subject_name in default_subjects:
                        Subject.objects.get_or_create(
                            school_class=school_class, name=subject_name, school=self.school
                        )

    def create_primary5_classes(self):
        # Create Primary 1 to 5 classes
        for i in range(1, 6):
            school_class, _ = ClassList.objects.get_or_create(
                name=f'PRY{i}',
                academic_session=self,
            )
            self.create_subjects_for_class(school_class)

    def create_primary_classes(self):
        # Create Primary 1 to 6 classes
        for i in range(1, 7):
            school_class, _ = ClassList.objects.get_or_create(
                name=f'PRY{i}',
                academic_session=self,
            )
            self.create_subjects_for_class(school_class)

    def create_jss_classes(self):
        # Create JSS1 to JSS3 classes
        for i in range(1, 4):
            school_class, _ = ClassList.objects.get_or_create(
                name=f'JS{i}',
                academic_session=self,
            )
            self.create_subjects_for_class(school_class)

    def create_sss_classes(self):
        # Create SSS1 to SSS3 classes
        for i in range(1, 4):
            school_class, _ = ClassList.objects.get_or_create(
                name=f'SS{i}',
                academic_session=self,
            )
            self.create_subjects_for_class(school_class)

    def create_kg_classes(self):
        # Create KG1 to KG3 classes
        for i in range(1, 4):
            school_class, _ = ClassList.objects.get_or_create(
                name=f'KG{i}',
                academic_session=self,
            )
            self.create_subjects_for_class(school_class)

    def create_basic_classes(self):
        # Create Basic 1 to Basic 6 classes
        for i in range(1, 7):
            school_class, _ = ClassList.objects.get_or_create(
                name=f'BASIC{i}',
                academic_session=self,
            )
            self.create_subjects_for_class(school_class)

    def create_subjects_for_class(self, school_class):
        # Create subjects for a given class (English and Mathematics)
        subjects = ['English', 'Mathematics']
        for subject in subjects:
            Subject.objects.get_or_create(
                name=subject,
                school_class=school_class
            )

    @classmethod
    @transaction.atomic
    def create_default_setup(cls, session_name, start_date, end_date, school):
        with transaction.atomic():
            """Method to create a new academic session and all related data."""
            academic_session, _ = cls.objects.get_or_create(
                school=school,
                name=session_name,
                start_date=start_date,
                end_date=end_date,
                is_current=True
            )
            academic_session.create_terms()
            academic_session.create_all_classes()
            return academic_session


# ----------------------------- Core: Terms ----------------
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

    def __str__(self):
        return f"{self.name} ({self.academic_session.name})"


# ----------------------------- Core: Staff ----------------
class Staff(UserInherit):
    related_name = 'staffs'

    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name='staff_profile')
    department = models.CharField(max_length=15, null=True, blank=True)
    is_teaching_staff = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.department} - {self.user.full_name}"

    class Meta:
        ordering = ['school', 'department']


# ----------------------------- Core: Levels & Departments --------------------
class ClassLevel(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Session-independent grade definition (e.g., PRY1, JS2, SS3) with optional **departments** for SSS.

    Why: Avoid re-creating the same grade each session; departments specialize SSS (SCIENCE/ART/COMMERCIAL/etc.).
    """
    related_name = 'class_levels'

    CLASS_CATEGORIES = (
        ("KG", "Kindergarten"),
        ("PRIMARY", "Primary"),
        ("JSS", "Junior Secondary"),
        ("SSS", "Senior Secondary"),
        ("BASIC", "Basic Education"),
    )

    # Departments/specializations; GENERAL = default (esp. KG/PRIMARY/JSS)
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
        ("KG1", "Kindergarten 1"), ("KG2",
                                    "Kindergarten 2"), ("KG3", "Kindergarten 3"),
        ("PRY1", "Primary 1"), ("PRY2", "Primary 2"), ("PRY3", "Primary 3"),
        ("PRY4", "Primary 4"), ("PRY5", "Primary 5"), ("PRY6", "Primary 6"),
        ("JS1", "Junior Secondary 1"), ("JS2",
                                        "Junior Secondary 2"), ("JS3", "Junior Secondary 3"),
        ("SS1", "Senior Secondary 1"), ("SS2",
                                        "Senior Secondary 2"), ("SS3", "Senior Secondary 3"),
    ]

    name = models.CharField(max_length=10, choices=CLASS_CHOICES)
    category = models.CharField(max_length=12, choices=CLASS_CATEGORIES)
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default="GENERAL",
        help_text="Academic department/specialization (mainly for SSS)",
    )
    level_order = models.PositiveIntegerField(
        help_text="Sequential order for progression (1,2,3,...)")
    default_capacity = models.PositiveIntegerField(default=50)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["school", "name", "department"], name="uniq_level_name_dept_per_school"),
            UniqueConstraint(
                fields=["school", "level_order", "department"], name="uniq_level_order_per_dept"),
            models.CheckConstraint(
                check=Q(default_capacity__gte=0), name="level_capacity_non_negative"),
            models.CheckConstraint(
                check=Q(level_order__gte=1), name="level_order_positive"),
        ]
        ordering = ["category", "level_order", "department"]
        indexes = [
            models.Index(fields=["school", "category"]),
            models.Index(fields=["school", "level_order"]),
            models.Index(fields=["school", "department"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        label = self.get_name_display()
        return (
            f"{label} ({self.school.name})" if self.department == "GENERAL"
            else f"{label} - {self.get_department_display()} ({self.school.name})"
        )

    @property
    def full_name(self) -> str:
        label = self.get_name_display()
        return label if self.department == "GENERAL" else f"{label} ({self.get_department_display()})"

    @classmethod
    def create_default_levels(cls, school):
        """Idempotent seeding: KG/PRIMARY/JSS as GENERAL; SSS across all departments."""
        pk_kg = [("KG1", "KG", "GENERAL", 1), ("KG2", "KG",
                                               "GENERAL", 2), ("KG3", "KG", "GENERAL", 3)]
        prim = [
            ("PRY1", "PRIMARY", "GENERAL", 4), ("PRY2", "PRIMARY",
                                                "GENERAL", 5), ("PRY3", "PRIMARY", "GENERAL", 6),
            ("PRY4", "PRIMARY", "GENERAL", 7), ("PRY5", "PRIMARY",
                                                "GENERAL", 8), ("PRY6", "PRIMARY", "GENERAL", 9),
        ]
        jss = [("JS1", "JSS", "GENERAL", 10), ("JS2", "JSS",
                                               "GENERAL", 11), ("JS3", "JSS", "GENERAL", 12)]
        depts = ["SCIENCE", "ART", "COMMERCIAL", "SCIENCE_TECH"]
        sss = [
            (n, "SSS", d, o)
            for d in depts
            for n, o in (("SS1", 13), ("SS2", 14), ("SS3", 15))
        ]
        for name, category, department, order in pk_kg + prim + jss + sss:
            cls.objects.get_or_create(
                school=school,
                name=name,
                department=department,
                defaults={"category": category, "level_order": order},
            )


# ----------------------------- Subjects -------------------------------------
class Subject(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    School-wide subject catalog with applicability by category and department.

    Why: Reuse a single subject definition; pair with per-class assignments per session.
    """
    related_name = 'subjects'

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    is_core = models.BooleanField(
        default=True, help_text="Core subjects are mandatory")
    applicable_categories = models.JSONField(
        default=list, help_text="Category codes this applies to; [] = all")
    applicable_departments = models.JSONField(
        default=list, help_text="Department codes this applies to; [] = all")

    class Meta:
        constraints = [UniqueConstraint(
            fields=["school", "name"], name="uniq_subject_name_per_school")]
        constraints = [UniqueConstraint(
            fields=["school", "code"], name="uniq_subject_code_per_school")]
        ordering = ["name"]
        indexes = [models.Index(fields=["school", "is_core"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.school.name})"

    def is_applicable_to_class_level(self, level: ClassLevel) -> bool:
        cats_ok = (not self.applicable_categories) or (
            level.category in self.applicable_categories)
        depts_ok = (
            (not self.applicable_departments)
            or (level.department in self.applicable_departments)
            or ("GENERAL" in self.applicable_departments)
        )
        return cats_ok and depts_ok

    @classmethod
    def create_default_subjects(cls, school):
        """Idempotent seed with reasonable category/department coverage."""
        rows = [
            ("English Language", "ENG", True, [], []),
            ("Mathematics", "MATH", True, [], []),
            ("Basic Science", "BSC", True, ["KG", "PRIMARY"], ["GENERAL"]),
            ("Social Studies", "SST", True, ["KG", "PRIMARY"], ["GENERAL"]),
            ("Creative Arts", "CA", False, ["KG", "PRIMARY"], ["GENERAL"]),
            ("Physical and Health Education", "PHE",
             True, ["KG", "PRIMARY"], ["GENERAL"]),
            ("Integrated Science", "INT_SCI", True, ["JSS"], ["GENERAL"]),
            ("Basic Technology", "BT", True, ["JSS"], ["GENERAL"]),
            ("Business Studies", "BS", True, ["JSS"], ["GENERAL"]),
            ("Civic Education", "CE", True, ["JSS"], ["GENERAL"]),
            ("Computer Studies", "CS", False, ["JSS", "SSS"], []),
            ("Physics", "PHY", True, ["SSS"], ["SCIENCE", "SCIENCE_TECH"]),
            ("Chemistry", "CHE", True, ["SSS"], ["SCIENCE", "SCIENCE_TECH"]),
            ("Biology", "BIO", True, ["SSS"], ["SCIENCE"]),
            ("Further Mathematics", "F_MATH", False, ["SSS"], ["SCIENCE"]),
            ("Agricultural Science", "AGR", False, ["SSS"], ["SCIENCE"]),
            ("Literature in English", "LIT", True, ["SSS"], ["ART"]),
            ("Government", "GOV", True, ["SSS"], ["ART", "COMMERCIAL"]),
            ("Economics", "ECO", True, ["SSS"], ["ART", "COMMERCIAL"]),
            ("Geography", "GEO", False, ["SSS"], ["ART"]),
            ("History", "HIS", False, ["SSS"], ["ART"]),
            ("CRS", "CRS", False, ["SSS"], ["ART"]),
            ("IRS", "IRS", False, ["SSS"], ["ART"]),
            ("Accounting", "ACC", True, ["SSS"], ["COMMERCIAL"]),
            ("Commerce", "COM", True, ["SSS"], ["COMMERCIAL"]),
            ("Office Practice", "OP", True, ["SSS"], ["COMMERCIAL"]),
            ("Book Keeping", "BK", False, ["SSS"], ["COMMERCIAL"]),
            ("Data Processing", "DP", False, ["SSS"], ["COMMERCIAL"]),
            ("Technical Drawing", "TD", True, ["SSS"], ["SCIENCE_TECH"]),
            ("Basic Electronics", "BE", True, ["SSS"], ["SCIENCE_TECH"]),
            ("Metal Work", "MW", False, ["SSS"], ["SCIENCE_TECH"]),
            ("Wood Work", "WW", False, ["SSS"], ["SCIENCE_TECH"]),
            ("Auto Mechanics", "AM", False, ["SSS"], ["SCIENCE_TECH"]),
            ("French", "FR", False, ["JSS", "SSS"], ["GENERAL", "ART"]),
            ("Fine Arts", "FA", False, ["JSS", "SSS"], ["GENERAL", "ART"]),
            ("Music", "MUS", False, ["JSS", "SSS"], ["GENERAL", "ART"]),
        ]
        for name, code, is_core, cats, depts in rows:
            cls.objects.get_or_create(
                school=school,
                name=name,
                defaults={
                    "code": code,
                    "is_core": is_core,
                    "applicable_categories": cats,
                    "applicable_departments": depts,
                },
            )


# ----------------------------- Session Classes ------------------------------
class ClassList(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Session-specific class list for a `ClassLevel` (homeroom).

    Why: One row per (session, level, division) prevents duplicates and supports different rosters per session.
    """

    related_name = 'classes'
    DIVISION_CHOICES = [(letter, letter) for letter in string.ascii_uppercase]

    label = models.CharField(max_length=100, null=True, blank=True)
    class_level = models.ForeignKey(
        ClassLevel, on_delete=models.CASCADE, related_name="class_instances")
    academic_session = models.ForeignKey(
        "AcademicSession", on_delete=models.CASCADE, related_name="classes")
    division = models.CharField(
        max_length=1, choices=DIVISION_CHOICES, default="A")
    class_teacher = models.ForeignKey(
        "Staff", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_classes")
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["class_level", "academic_session", "division",
                             "school"], name="uniq_classlist_per_session_level_division"),
            models.CheckConstraint(check=Q(capacity__isnull=True) | Q(
                capacity__gte=0), name="classlist_capacity_non_negative"),
        ]
        ordering = ["academic_session", "class_level__level_order", "division"]
        indexes = [
            models.Index(fields=["school", "academic_session"]),
            models.Index(fields=["school", "class_level"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.full_name

    @property
    def name(self) -> str:
        return f"{self.class_level.get_name_display()} {self.division}"

    @property
    def full_name(self) -> str:
        return f"{self.name} ({self.academic_session.name})"

    @property
    def category(self) -> str:
        return self.class_level.category

    @property
    def level_order(self) -> int:
        return self.class_level.level_order

    def clean(self) -> None:
        if self.capacity is None:
            self.capacity = self.class_level.default_capacity
        if self.class_level.school_id != self.school_id:
            raise ValidationError("Class level must belong to the same school")
        sess_school_id = getattr(
            self.academic_session, "school_id", self.school_id)
        if sess_school_id != self.school_id:
            raise ValidationError(
                "Academic session must belong to the same school")

    @classmethod
    def get_classes_ids(cls):
        return cls.objects.values_list('id', flat=True)

    # enrollment helpers
    def get_current_enrollment(self) -> int:
        return self.enrollments.filter(is_active=True).count()

    def seats_left(self) -> int:
        return max((self.capacity or 0) - self.get_current_enrollment(), 0)

    def has_capacity(self) -> bool:
        return self.get_current_enrollment() < (self.capacity or 0)

    def get_applicable_subjects(self):
        """Get all subjects applicable to this class level and department"""
        return Subject.objects.filter(
            models.Q(school=self.school) &
            (
                # Core subjects with no category restriction
                models.Q(applicable_categories=[]) |
                models.Q(applicable_categories__contains=[self.category])
            ) &
            (
                # Subjects with no department restriction
                models.Q(applicable_departments=[]) |
                models.Q(applicable_departments__contains=[self.class_level.department]) |
                models.Q(applicable_departments__contains=[
                         'GENERAL'])  # General subjects
            )
        ).distinct()

    @classmethod
    def create_for_session(cls, academic_session, class_levels=None, divisions=None):
        """Create class instances for a specific session"""
        if class_levels is None:
            class_levels = ClassLevel.objects.filter(
                school=academic_session.school)

        if divisions is None:
            divisions = ['A']  # Default to single division

        created_classes = []
        for class_level in class_levels:
            for division in divisions:
                class_list, created = cls.objects.get_or_create(
                    class_level=class_level,
                    academic_session=academic_session,
                    division=division,
                    school=academic_session.school,
                    defaults={'capacity': class_level.default_capacity}
                )
                if created:
                    created_classes.append(class_list)

                    # Auto-assign subjects for this department
                    applicable_subjects = class_list.get_applicable_subjects()
                    for subject in applicable_subjects:
                        ClassSubjectAssignment.objects.get_or_create(
                            class_list=class_list,
                            subject=subject,
                            school=self.school
                        )

        return created_classes


# ----------------------------- Subject ↔ Class ------------------------------
class ClassSubjectAssignment(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Links subjects to specific class instances with teacher assignments.
    This allows different staff for the same subject in different classes/sessions.
    For example, Mr. Jones might teach Math to Primary 1A, while Mrs. Smith teaches Math to Primary 1B.
    """
    related_name = 'subject_assignments'

    class_list = models.ForeignKey(
        ClassList, on_delete=models.CASCADE, related_name="subject_assignments")
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="class_assignments")
    teacher = models.ForeignKey("Staff", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="subject_assignments")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [UniqueConstraint(
            fields=["class_list", "subject"], name="uniq_subject_per_classlist")]
        indexes = [
            models.Index(fields=["school", "class_list"]),
            models.Index(fields=["school", "teacher"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        teacher_name = getattr(self.teacher, "full_name", None) or "No Teacher"
        return f"{self.subject.name} - {self.class_list.name} ({teacher_name})"

    def clean(self) -> None:
        if not self.subject.is_applicable_to_class_level(self.class_list.class_level):
            raise ValidationError(
                f"{self.subject.name} is not applicable to {self.class_list.class_level.full_name}")


# ----------------------------- Enrollment -----------------------------------
class StudentEnrollment(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Links a `Student` to a `ClassList` **and** its `AcademicSession`.

    Why: One active enrollment per student per session, enabling history and safe transfers.

    Tracks student enrollment in specific classes for specific sessions.
    This is the core of the system that allows a student to be in a class for a specific academic session.
    It replaces a direct student-to-class relationship and allows for tracking a student's academic history.
    """
    related_name = 'enrollments'

    student = models.ForeignKey(
        "Student", on_delete=models.CASCADE, related_name="enrollments")
    class_list = models.ForeignKey(
        ClassList, on_delete=models.CASCADE, related_name="enrollments")
    academic_session = models.ForeignKey(
        "AcademicSession", on_delete=models.CASCADE, related_name="enrollments")

    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    left_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when this enrollment was deactivated")

    # Academic performance tracking
    promoted = models.BooleanField(default=False)
    promotion_date = models.DateField(null=True, blank=True)
    final_grade = models.CharField(max_length=5, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=[
                             "student", "class_list", "school"], name="uniq_student_in_exact_classlist"),
            UniqueConstraint(
                fields=["school", "student", "academic_session"],
                condition=Q(is_active=True),
                name="uniq_active_enrollment_per_session",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "class_list", "is_active"]),
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["academic_session", "is_active"]),
            models.Index(fields=["enrollment_date"]),
            models.Index(fields=["left_at"]),
            models.Index(fields=["promotion_date"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        student_name = getattr(self.student, "full_name",
                               None) or str(self.student)
        return f"{student_name} → {self.class_list.full_name}"

    def clean(self) -> None:
        if self.class_list.school_id != self.school_id:
            raise ValidationError(
                "Student and class must belong to the same school")
        if self.academic_session_id != self.class_list.academic_session_id:
            raise ValidationError(
                "Academic session must match the class's session")
        if self.is_active:
            # capacity check (ignore self when updating)
            current = self.class_list.get_current_enrollment()
            if self.pk and StudentEnrollment.objects.filter(pk=self.pk, is_active=True).exists():
                current -= 1
            if current >= (self.class_list.capacity or 0):
                raise ValidationError(
                    f"Class {self.class_list.name} is at capacity ({self.class_list.capacity} students)")

    @staticmethod
    @transaction.atomic
    def enroll(student, target_class: ClassList) -> "StudentEnrollment":
        """Idempotent per-session enrollment; transfers within session if already enrolled elsewhere."""
        if not target_class.has_capacity():
            raise ValidationError("Class capacity reached.")
        session = target_class.academic_session
        # deactivate existing active enrollment in this session
        StudentEnrollment.objects.filter(
            student=student, academic_session=session, is_active=True
        ).update(is_active=False, left_at=timezone.now())
        # create or reactivate enrollment in target class
        obj, _ = StudentEnrollment.objects.get_or_create(
            school=target_class.school,
            student=student,
            academic_session=session,
            class_list=target_class,
            defaults={"is_active": True},
        )
        obj.is_active = True
        obj.left_at = None  # now active again
        obj.save(update_fields=["is_active", "left_at", "updated_at"])
        return obj

    @transaction.atomic
    def transfer_within_session(self, to_class: ClassList) -> "StudentEnrollment":
        if to_class.academic_session_id != self.academic_session_id:
            raise ValidationError(
                "Cannot transfer across sessions; enroll into the new session instead.")
        return StudentEnrollment.enroll(self.student, to_class)

    @transaction.atomic
    def withdraw(self) -> None:
        self.is_active = False
        self.left_at = timezone.now()
        self.save(update_fields=["is_active", "left_at", "updated_at"])

    def promote_to_next_level(self, target_department: Optional[str] = None):
        """
        Promote to the next level while respecting departments.
        - From JS3 → SS1 requires `target_department`.
        - Otherwise, keep current department.
        """
        current_level = self.class_list.class_level
        next_order = current_level.level_order + 1
        department = target_department if current_level.name == "JS3" else current_level.department
        if current_level.name == "JS3" and not target_department:
            raise ValidationError(
                "Moving to SS1 requires selecting a department (SCIENCE/ART/COMMERCIAL/SCIENCE_TECH)")
        try:
            next_level = ClassLevel.objects.get(
                school=self.school, level_order=next_order, department=department
            )
        except ClassLevel.DoesNotExist:
            raise ValidationError(
                f"No next level found for promotion from {current_level.full_name}")
        # Find or create a class in the same session (caller may move to next session separately)
        next_class = (
            ClassList.objects.filter(
                school=self.school,
                academic_session=self.academic_session,
                class_level=next_level,
            ).first()
        )
        if not next_class:
            next_class = ClassList.create_for_session(self.academic_session, class_levels=[
                                                      next_level], divisions=["A"])[0]
        # deactivate current record and set timestamps
        self.is_active = False
        self.left_at = timezone.now()
        self.promoted = True
        self.promotion_date = timezone.now().date()
        self.save(update_fields=["is_active", "left_at",
                  "promoted", "promotion_date", "updated_at"])
        return StudentEnrollment.enroll(self.student, next_class)


# ----------------------------- Student --------------------------------------
class Student(UserInherit):
    """Student profile; enroll via `StudentEnrollment` for per-session rosters."""
    related_name = 'students'

    reg_no = models.CharField(max_length=20, null=True, blank=True)
    student_id = models.CharField(max_length=20, null=True, blank=True)
    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name="student_profile")
    date_of_birth = models.DateField()
    session_admitted = models.ForeignKey(
        "AcademicSession", on_delete=models.CASCADE, null=True, blank=True, related_name="admitted_students")

    class Meta:
        constraints = [
            UniqueConstraint(fields=["school", "student_id"], condition=Q(
                student_id__isnull=False), name="uniq_student_id_per_school"),
            UniqueConstraint(fields=["school", "reg_no"], condition=Q(
                reg_no__isnull=False), name="uniq_reg_no_per_school"),
            UniqueConstraint(fields=["school", "user"],
                             name="uniq_user_per_school"),
        ]

    @property
    def age(self):
        # Helper method to calculate the student's age
        if not self.date_of_birth:
            return None

        try:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (
                    self.date_of_birth.month, self.date_of_birth.day)
            )
        except Exception as e:
            logging.error(f"Error calculating age: {e}")
            return None

    def __str__(self) -> str:  # pragma: no cover
        display = getattr(self.user, "full_name", None) or getattr(
            self.user, "get_full_name", lambda: str(self.user))()
        return f"{self.student_id or self.reg_no or self.pk} - {display}"

    @property
    def current_enrollment(self) -> Optional[StudentEnrollment]:
        return self.enrollments.filter(is_active=True).order_by("-enrollment_date").first()

    @property
    def current_class(self) -> Optional[ClassList]:
        ce = self.current_enrollment
        return ce.class_list if ce else None

    @transaction.atomic
    def enroll_in_class(self, class_list: ClassList) -> StudentEnrollment:
        StudentEnrollment.objects.filter(
            student=self, academic_session=class_list.academic_session, is_active=True
        ).update(is_active=False, left_at=timezone.now())
        return StudentEnrollment.objects.create(
            student=self,
            class_list=class_list,
            academic_session=class_list.academic_session,
            school=self.school,
        )

    def get_enrollment_history(self):
        """Get chronological enrollment history"""
        return self.enrollments.select_related(
            'class_list__class_level',
            'class_list__academic_session'
        ).order_by('enrollment_date')

    def prev_generate_student_id(self):
        """Generates a unique student ID based on the school and admission year."""
        # Extract short school name or fallback to school ID
        school_short_name = self.school.short_name[:3].upper(
        ) if self.school.short_name else str(self.school.id)

        # Admission year (last 2 digits of current year)
        admission_year = str(self.session_admitted.start_date.year)[-2:]

        # Find the last student in the same school and admission year
        last_student = Student.objects.filter(
            school=self.school, session_admitted=self.session_admitted
        ).order_by('student_id').last()

        if last_student and last_student.student_id:
            # Extract the last 3 digits and increment
            last_number = int(last_student.student_id.split('-')[-1])
            new_number = str(last_number + 1).zfill(3)
        else:
            new_number = "001"  # Start from 001 if no previous student

        # Combine to form the student ID
        return f"{school_short_name}{admission_year}-{new_number}"

    def generate_student_id(self):
        """Generates a unique student ID based on the school and admission year."""
        # Extract short school name or fallback to school ID
        prefix = "STU"

        # Admission year (last 2 digits of current year)
        if self.session_admitted:
            admission_year = str(self.session_admitted.start_date.year)[-2:]
        else:
            admission_year = "25"

        # Find the last student in the same school and admission year
        last_student = Student.objects.filter(
            school=self.school, session_admitted=self.session_admitted
        ).order_by('student_id').last()

        if last_student and last_student.student_id:
            # Extract the last 3 digits and increment
            last_number = int(last_student.student_id.split('-')[-1])
            new_number = str(last_number + 1).zfill(3)
        else:
            new_number = "001"  # Start from 001 if no previous student

        print(f"{prefix}-{admission_year}-{new_number}")
        # Combine to form the student ID
        return f"{prefix}-{admission_year}-{new_number}"

    def generate_unique_student_id(self):
        max_attempts = 5
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            try:
                self.generate_student_id()
            except ObjectDoesNotExist:
                logging.warning(
                    "No students found for the given school and session.")
                break
            except Exception as e:
                logging.error(f"Error generating student ID: {e}")
                continue  # Continue to the next iteration for recovery

        # If unable to generate a unique ID after several attempts
            # raise Exception(
            #         "Unable to generate a unique student ID after multiple attempts.")

    def generate_unique_email(self):
        """Generates a unique dynamic email for the student."""
        school_short_name = self.school.short_name.lower(
        ) if self.school.short_name else "school"
        admission_year = str(self.session_admitted.start_date.year)[-2:]
        base_email = str(self.user.first_name).lower(
        ) + self.user.last_name.lower() + f"@{school_short_name}{admission_year}.com"
        unique_email = base_email

        # Ensure the email is unique
        counter = 1
        while "User".objects.filter(email=unique_email).exists():
            unique_email = f"{self.user.first_name.lower()}." + str(self.user.last_name).lower(
            ) + f"{counter}@{school_short_name}{admission_year}.com"
            counter += 1

        return unique_email

    def save(self, *args, **kwargs):
        # Generate a unique student ID if it's not already set
        if not self.student_id:
            self.student_id = self.generate_unique_student_id()

        # Generate a unique dynamic email if not set
        if not self.user.email:
            self.user.email = self.generate_unique_email()
            self.user.save()

        super().save(*args, **kwargs)


# ----------------------------- Session helpers ------------------------------
class AcademicSessionMethods:
    """
    These are helper methods that can be added to your existing AcademicSession model.
    They provide convenient ways to create a standard setup for a new academic session.
    """

    def create_standard_setup(self):
        """Create standard class levels, subjects, and class instances"""

        ClassLevel.create_default_levels(self.school)
        Subject.create_default_subjects(self.school)
        class_levels = ClassLevel.objects.filter(school=self.school)
        created_classes = ClassList.create_for_session(
            self,
            class_levels=class_levels,
            divisions=['A']  # Start with single division
        )

        # Automatically assign applicable subjects to all classes
        for class_list in created_classes:
            applicable_subjects = class_list.get_applicable_subjects()
            for subject in applicable_subjects:
                ClassSubjectAssignment.objects.get_or_create(
                    class_list=class_list,
                    subject=subject,
                    school=self.school
                )

        return created_classes

    def create_department_classes(self, base_classes=None, departments=None):
        """Create specialized department classes for SSS levels"""
        if departments is None:
            departments = ['SCIENCE', 'ART', 'COMMERCIAL', 'SCIENCE_TECH']

        if base_classes is None:
            base_classes = ['SS1', 'SS2', 'SS3']

        created_classes = []
        for class_name in base_classes:
            for department in departments:
                class_level = ClassLevel.objects.get(
                    school=self.school,
                    name=class_name,
                    department=department
                )

                class_list, created = ClassList.objects.get_or_create(
                    class_level=class_level,
                    academic_session=self,
                    division='A',
                    school=self.school,
                    defaults={'capacity': class_level.default_capacity}
                )

                if created:
                    created_classes.append(class_list)

                    # Auto-assign subjects for this department
                    applicable_subjects = class_list.get_applicable_subjects()
                    for subject in applicable_subjects:
                        ClassSubjectAssignment.objects.get_or_create(
                            class_list=class_list,
                            subject=subject,
                            school=self.school
                        )

        return created_classes


# ----------------------------- Reporting & Utilities ------------------------
class SchoolUtilities:
    """
    This class provides various utility functions for managing school-related data.
    These can be used to perform common tasks like promoting students, getting statistics, etc.
    """

    # ---- quick lookups ----
    @staticmethod
    def available_departments_for_js3_to_ss1() -> list[tuple[str, str]]:
        """Return the supported departments (code, label) for JS3 → SS1 decisions."""
        return list(ClassLevel.DEPARTMENT_CHOICES)[1:]  # exclude GENERAL

    @staticmethod
    def class_department_statistics(school) -> dict[str, dict[str, int]]:
        """Active student & class counts by department (current snapshot)."""
        data: dict[str, dict[str, int]] = {}
        qs = (
            StudentEnrollment.objects.filter(school=school, is_active=True)
            .values("class_list__class_level__department")
            .annotate(student_count=Count("student"), class_count=Count("class_list", distinct=True))
        )
        label_map = dict(ClassLevel.DEPARTMENT_CHOICES)
        for row in qs:
            code = row["class_list__class_level__department"]
            data[code] = {
                "name": label_map.get(code, code),
                "students": row["student_count"],
                "classes": row["class_count"],
            }
        return data

    # ---- reports ----
    @staticmethod
    def report_session_roll(session) -> list[dict]:
        """Roll per class (active counts & capacity) for a given session."""
        qs = (
            ClassList.objects.filter(academic_session=session)
            .annotate(active_count=Count("enrollments", filter=Q(enrollments__is_active=True)))
            .values(
                "id",
                "class_level__name",
                "class_level__department",
                "division",
                "capacity",
                "active_count",
            )
            .order_by("class_level__level_order", "division")
        )
        return list(qs)

    @staticmethod
    def report_department_mix(session) -> dict[str, int]:
        """Active student counts by department for a given session."""
        qs = (
            StudentEnrollment.objects.filter(
                academic_session=session, is_active=True)
            .values("class_list__class_level__department")
            .annotate(n=Count("student"))
        )
        return {row["class_list__class_level__department"]: row["n"] for row in qs}

    @staticmethod
    def report_promotions_by_department(source_session) -> dict[str, int]:
        """Count promotions (flagged on the source-session enrollments) by department."""
        qs = (
            StudentEnrollment.objects.filter(
                academic_session=source_session, promoted=True)
            .values("class_list__class_level__department")
            .annotate(n=Count("id"))
        )
        return {row["class_list__class_level__department"]: row["n"] for row in qs}

    @staticmethod
    def get_available_departments_for_promotion(student):
        """Get available departments when a student is being promoted from JS3 to SS1"""
        if (student.current_class and
                student.current_class.class_level.name == 'JS3'):

            return ClassLevel.objects.filter(
                school=student.school,
                name='SS1'
            ).values_list('department', 'department__verbose_name')
        return []

    @staticmethod
    def get_class_department_statistics(school):
        """Get statistics about class departments in the school"""
        from django.db.models import Count

        stats = {}

        # Get enrollment statistics by department
        department_stats = StudentEnrollment.objects.filter(
            school=school,
            is_active=True
        ).values(
            'class_list__class_level__department',
            'class_list__class_level__department__verbose_name'
        ).annotate(
            student_count=Count('student'),
            class_count=Count('class_list', distinct=True)
        )

        for stat in department_stats:
            department = stat['class_list__class_level__department']
            stats[department] = {
                'name': stat['class_list__class_level__department__verbose_name'],
                'students': stat['student_count'],
                'classes': stat['class_count']
            }

        return stats

    @staticmethod
    def bulk_promote_students(enrollments, target_session, department_assignments=None):
        """
        Bulk promote students to next session.
        department_assignments: dict mapping student_id to target_department for JS3->SS1 promotions
        """
        from django.db import transaction

        promoted_enrollments = []

        with transaction.atomic():
            for enrollment in enrollments:
                try:
                    # For JS3 students, use provided department assignment
                    target_department = None
                    if (enrollment.class_list.class_level.name == 'JS3' and
                            department_assignments and
                            enrollment.student.id in department_assignments):
                        target_department = department_assignments[enrollment.student.id]

                    new_enrollment = enrollment.promote_to_next_level(
                        target_department)

                    # Update to new session if different
                    if (new_enrollment and
                            new_enrollment.class_list.academic_session != target_session):

                        # Find equivalent class in target session
                        target_class = ClassList.objects.filter(
                            class_level=new_enrollment.class_list.class_level,
                            academic_session=target_session,
                            division=new_enrollment.class_list.division
                        ).first()

                        if target_class:
                            new_enrollment.class_list = target_class
                            new_enrollment.save()

                    promoted_enrollments.append(new_enrollment)

                except ValidationError as e:
                    # Log the error and continue with other students
                    print(f"Failed to promote {enrollment.student}: {e}")
                    continue

        return promoted_enrollments


# ----------------------------- GmeetClass ------------------------------
class GmeetClass(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'gmeet_classes'

    title = models.CharField(max_length=50, null=True, blank=True)
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='gmeet_classes')
    description = models.TextField()
    gmeet_link = models.URLField()
    start_time = models.DateTimeField()
    duration = models.DurationField(null=True, blank=True)
    created_by = models.ForeignKey(
        "User", on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role__in': ["teacher", "admin", "owner"]},
        related_name="gmeets"
    )

    def __str__(self):
        try:
            return f"{self.title} - ({self.start_time})"
        except Exception as e:
            print(e)
            return f"Gmeet"

    @classmethod
    def filter_by_class(cls, school_class):  # Filter based on class
        return cls.objects.filter(subject__school_class=school_class)

    @classmethod
    def filter_by_role(cls, request):
        # Get the user's school using the method from the School model
        school: School = School.get_user_school(request.user)

        # Check if the user is an admin
        if request.user.is_admin:
            # Admin or owner can view all GmeetClass for the school
            return cls.objects.filter(school=school).select_related("created_by")

        # Check if the user is a subject teacher
        elif request.user.is_school_staff:
            # Staff can only view the GmeetClass for the subjects they teach
            return cls.objects.filter(
                Q(created_by=request.user) |
                Q(subject__teacher__user=request.user)
            ).select_related("created_by")

        # Check if the user is a student
        elif request.user.is_student:
            # Students can only view GmeetClass for their school class
            return cls.objects.filter(subject__school_class=request.user.student_profile.school_class).select_related("created_by")

        # In case the user has no matching role, return an empty queryset
        return cls.objects.none()


class LessonPlan(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'lesson_plans'

    title = models.CharField(max_length=50, null=True, blank=True)
    school_class = models.ForeignKey(ClassList, on_delete=models.CASCADE)
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='lesson_plans')
    uploaded_by = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name='lesson_plans')
    uploaded_file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.uploaded_file.name} uploaded by {self.uploaded_by.username}"

    @classmethod
    def filter_by_role(cls, request):
        # Get the user's school using the method from the School model
        school: School = School.get_user_school(request.user)

        # Check if the user is an admin
        if request.user.is_admin:
            # Admin or owner can view all GmeetClass for the school
            return cls.objects.all().select_related("created_by")

        # Check if the user is a subject teacher
        elif request.user.is_school_staff:
            # Staff can only view the GmeetClass for the subjects they teach
            return cls.objects.filter(subject__teacher=request.user.staff_profile)

        # Check if the user is a student
        elif request.user.is_student:
            # Students can only view GmeetClass for their school class
            return cls.objects.filter(subject__school_class=request.user.student_profile.school_class)

        # In case the user has no matching role, return an empty queryset
        return cls.objects.none()

    # Filter based on class

    @classmethod
    def filter_by_class(cls, school_class):
        return cls.objects.filter(school_class=school_class)

    # Filter based on teacher
    @classmethod
    def filter_by_teacher(cls, teacher):
        return cls.objects.filter(subject__teacher=teacher)


class ClassNote(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'class_notes'

    lesson_plan = models.ForeignKey(
        LessonPlan, on_delete=models.CASCADE, related_name='class_notes')
    title = models.CharField(max_length=50)
    school_class = models.ForeignKey(
        ClassList, on_delete=models.CASCADE, related_name='+')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(
        upload_to='class_notes_attachments/', null=True, blank=True)
    uploaded_by = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name='lesson_notes')

    def __str__(self):
        return f"Note for {self.lesson_plan.subject.name} ({self.lesson_plan.subject.school_class.name})"

    # Filter based on class
    @classmethod
    def filter_by_class(cls, school_class):
        return cls.objects.filter(lesson_plan__school_class=school_class)

    # Filter based on teacher
    @classmethod
    def filter_by_teacher(cls, teacher):
        return cls.objects.filter(lesson_plan__subject__teacher=teacher)

    @classmethod
    def filter_by_role(cls, request):
        # Get the user's school using the method from the School model
        school: School = School.get_user_school(request.user)

        # Check if the user is an admin
        if request.user.is_admin:
            # Admin or owner can view all GmeetClass for the school
            return cls.objects.all().select_related("uploaded_by")

        # Check if the user is a subject staff
        elif request.user.is_school_staff:
            # staff can only view the GmeetClass for the subjects they teach
            return cls.objects.filter(
                Q(uploaded_by=request.user) |
                Q(lesson_plan__subject__teacher__user=request.user)
            ).select_related("school_class", "lesson_plan")

        # Check if the user is a student
        elif request.user.is_student:
            # Students can only view GmeetClass for their school class
            return cls.objects.filter(subject__school_class=request.user.student_profile.school_class).select_related("created_by")

        # In case the user has no matching role, return an empty queryset
        return cls.objects.none()


"""
# 1) A student's full class history (ordered)
student.get_enrollment_history()

# 2) Current class
student.current_class  # or student.current_enrollment

# 3) Roster for a past classlist
ClassList.objects.get(id=cl_id).enrollments.filter(is_active=True)

# 4) A student's class in a specific session
StudentEnrollment.objects.get(
    student=student, academic_session=session, is_active=True)

# 5) All classlists for a level across years
ClassList.objects.filter(class_level=level).select_related('academic_session').order_by('academic_session__start_date')

# 6) All classes a teacher taught (history)
ClassSubjectAssignment.objects.filter(teacher=teacher).select_related('class_list','class_list__academic_session')
"""


"""
# ----------------------------- Django Admin (place in admin.py) -------------
# These classes are provided here for convenience; move them to your app's admin.py.
try:
    from django.contrib import admin

    @admin.register(ClassList)
    class ClassListAdmin(admin.ModelAdmin):
        list_display = ("name", "academic_session",
                        "class_level", "division", "capacity")
        list_filter = (
            "academic_session",
            ("class_level__department"),
            ("class_level__name"),
            "division",
        )
        search_fields = ("class_level__name",
                         "academic_session__name", "division")

    @admin.register(StudentEnrollment)
    class StudentEnrollmentAdmin(admin.ModelAdmin):
        list_display = (
            "student",
            "class_list",
            "academic_session",
            "is_active",
            "enrollment_date",
            "left_at",
            "promoted",
            "promotion_date",
        )
        list_filter = (
            "is_active",
            "academic_session",
            "promoted",
            ("class_list__class_level__department"),
            ("class_list__class_level__name"),
            "class_list__division",
        )
        search_fields = (
            "student__student_id",
            "student__reg_no",
            "student__user__first_name",
            "student__user__last_name",
            "class_list__class_level__name",
            "class_list__academic_session__name",
        )
        date_hierarchy = "enrollment_date"
except Exception:
    # Admin not installed or import-time side effects should be avoided in some contexts
    pass
"""


'''
# file: main/admin.py
from django.contrib import admin
from .models_departments import ClassLevel, Subject, ClassList, ClassSubjectAssignment, Student, StudentEnrollment
from main.models import School, AcademicSession, User
from main.models_departments import ClassLevel, ClassList, Student, StudentEnrollment
from main.reporting import get_enrollment_roll_for_session, get_promotions_by_department

class EnrollmentStatusFilter(admin.SimpleListFilter):
    """A custom filter to see active, withdrawn, or all enrollments."""
    title = 'Enrollment Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('withdrawn', 'Withdrawn'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'withdrawn':
            return queryset.filter(is_active=False)
        return queryset

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'academic_session',
                    'is_active', 'enrollment_date', 'left_at')
    list_filter = (EnrollmentStatusFilter, 'academic_session',
                   'school_class__class_level__department')
    search_fields = ('student__user__first_name',
                     'student__user__last_name', 'school_class__class_level__name')
    autocomplete_fields = ('student', 'school_class', 'academic_session')

# Register other models for better admin usability
@admin.register(ClassList)
class ClassListAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_session', 'class_level',
                    'class_teacher', 'capacity')
    list_filter = ('academic_session', 'class_level__department',
                   'class_level__category')
    search_fields = ('class_level__name', 'class_teacher__user__first_name')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'reg_no', 'current_class')
    search_fields = ('user__first_name', 'user__last_name',
                     'student_id', 'reg_no')

admin.site.register(ClassLevel)
admin.site.register(Subject)
admin.site.register(ClassSubjectAssignment)



# file: main/reporting.py
from django.db.models import Count
from .models_departments import StudentEnrollment, AcademicSession

def get_enrollment_roll_for_session(session: AcademicSession):
    """
    Generates a class list for a given academic session, ordered by class and student.
    """
    return (
        StudentEnrollment.objects.filter(
            academic_session=session, is_active=True)
        .select_related('student__user', 'school_class__class_level')
        .order_by('school_class__class_level__level_order', 'student__user__last_name', 'student__user__first_name')
    )

def get_promotions_by_department(session: AcademicSession):
    """
    Returns a report of how many students were promoted from each department in a given session.
    """
    return (
        StudentEnrollment.objects.filter(
            academic_session=session, promoted=True)
        .values(
            'school_class__class_level__department',
        )
        .annotate(promoted_count=Count('student'))
        .order_by('-promoted_count')
    )


# file: main/tests/test_reporting.py

from django.test import TestCase
from main.models import School, AcademicSession, User
from main.models_departments import ClassLevel, ClassList, Student, StudentEnrollment
from main.reporting import get_enrollment_roll_for_session, get_promotions_by_department

class ReportingTests(TestCase):

    def setUp(self):
        """Set up a school, sessions, classes, and students for testing."""
        self.school = School.objects.create(
            name="Test School", address="123 Test Lane")
        self.session_2024 = AcademicSession.objects.create(
            school=self.school, name="2024-2025", start_date="2024-09-01", end_date="2025-07-31")
        self.session_2025 = AcademicSession.objects.create(
            school=self.school, name="2025-2026", start_date="2025-09-01", end_date="2026-07-31")

        # Create class levels
        ClassLevel.create_default_levels(self.school)
        self.js3_level = ClassLevel.objects.get(
            name="JS3", department="GENERAL")
        self.ss1_sci_level = ClassLevel.objects.get(
            name="SS1", department="SCIENCE")
        self.ss1_art_level = ClassLevel.objects.get(
            name="SS1", department="ART")

        # Create school classes for the 2024 session
        self.js3_class = ClassList.objects.create(
            school=self.school, academic_session=self.session_2024, class_level=self.js3_level)
        self.ss1_sci_class = ClassList.objects.create(
            school=self.school, academic_session=self.session_2024, class_level=self.ss1_sci_level)
        self.ss1_art_class = ClassList.objects.create(
            school=self.school, academic_session=self.session_2024, class_level=self.ss1_art_level)

        # Create students
        for i in range(5):
            user = User.objects.create_user(
                username=f'student{i}', password='password', first_name=f'Student', last_name=f'{i}')
            student = Student.objects.create(
                school=self.school, user=user, date_of_birth='2010-01-01')
            # Enroll 3 in JS3, 2 in SS1 Science
            if i < 3:
                StudentEnrollment.enroll(student, self.js3_class)
            else:
                StudentEnrollment.enroll(student, self.ss1_sci_class)


    def test_enrollment_roll_for_session(self):
        """Test the per-session roll report."""
        roll = get_enrollment_roll_for_session(self.session_2024)
        self.assertEqual(roll.count(), 5)

        # Check ordering
        self.assertEqual(roll.first().school_class, self.js3_class)
        self.assertEqual(roll.last().school_class, self.ss1_sci_class)

    def test_promotions_by_department(self):
        """Test the promotions by department report."""
        # Promote two JS3 students to SS1 Science and SS1 Art in the same session
        enrollments_to_promote = StudentEnrollment.objects.filter(
            school_class=self.js3_class)[:2]

        enrollments_to_promote[0].promote_to_next_level(target_department="SCIENCE")
        enrollments_to_promote[1].promote_to_next_level(target_department="ART")

        report = get_promotions_by_department(self.session_2024)

        self.assertEqual(len(report), 1)
        general_dept_report = report[0]

        # All promotions are from the GENERAL department (JS3)
        self.assertEqual(
            general_dept_report['school_class__class_level__department'], 'GENERAL')
        self.assertEqual(general_dept_report['promoted_count'], 2)

'''


class Attachment(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Model for storing file attachments that can be linked to various models.
    """
    related_name = 'attachments'

    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        help_text="The actual file that was uploaded"
    )

    display_name = models.CharField(
        max_length=255,
        help_text="Original name of the uploaded file",
        null=True,
        blank=True,
        default=""
    )

    file_size = models.PositiveIntegerField(
        help_text="Size of the file in bytes",
        null=True,
        blank=True,
        default=0
    )

    file_type = models.CharField(
        max_length=100,
        help_text="MIME type of the file",
        null=True,
        blank=True,
        default=""
    )

    uploaded_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        help_text="User who uploaded the file",
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Attachment'
        verbose_name_plural = 'Attachments'

    def __str__(self):
        return f"{self.original_filename} ({self.file_type}, {self.get_file_size_display()})"

    def save(self, *args, **kwargs):
        if not self.original_filename and hasattr(self.file, 'name'):
            self.original_filename = self.file.name

        if self.file and not self.file_size:
            self.file_size = self.file.size

        if self.file and not self.file_type:
            import mimetypes
            self.file_type = mimetypes.guess_type(
                self.file.name)[0] or 'application/octet-stream'

        super().save(*args, **kwargs)

    def get_file_size_display(self):
        """
        Returns the file size in a human-readable format.
        """
        if not self.file_size:
            return "0 bytes"

        for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} PB"


class AnnouncementExpire(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Model for setting default expiration days for announcements when no specific
    expiration date is provided.
    """
    related_name = 'announcement_expiry_settings'

    days = models.PositiveIntegerField(
        default=30,
        help_text="Default number of days before an announcement expires if no expiration date is set"
    )

    class Meta:
        verbose_name = "Announcement Expiration Setting"
        verbose_name_plural = "Announcement Expiration Settings"

    def __str__(self):
        return f"Expires after {self.days} days (School: {self.school.name if self.school else 'Global'})"


class Announcement(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Model for school announcements that can be targeted to specific groups.
    """
    related_name = 'announcements'

    title = models.CharField(
        max_length=200, help_text="Title of the announcement")
    content = models.TextField(help_text="Full content of the announcement")

    # Relationships
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_announcements',
        help_text="User who created this announcement"
    )

    # Target audience
    target_roles = models.JSONField(
        default=list,
        help_text="List of user roles this announcement is for (e.g., ['student', 'staff']). Empty means all roles."
    )

    # Optional targeting
    classes = models.ManyToManyField(
        'ClassList',
        related_name='announcements',
        blank=True,
        help_text="Specific classes this announcement targets (leave empty for all classes)"
    )

    # Status and dates
    is_published = models.BooleanField(
        default=True,
        help_text="Whether this announcement is visible to its target audience"
    )
    publish_date = models.DateTimeField(
        default=timezone.now,
        help_text="When this announcement should become visible"
    )
    expire_date = models.DateField(
        null=True,
        blank=True,
        help_text="When this announcement should expire (optional)"
    )

    # Attachments
    attachments = models.ManyToManyField(
        'Attachment',
        related_name='announcement_attachments',
        blank=True,
        help_text="Files attached to this announcement"
    )

    class Meta:
        ordering = ['-publish_date']
        indexes = [
            models.Index(fields=['school', 'is_published', 'publish_date']),
            models.Index(fields=['expire_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.school.name if self.school else 'No School'}"

    def save(self, *args, **kwargs):
        # Set default expiration if not provided
        if not self.expire_date and hasattr(self, 'school'):
            try:
                expiry_setting = AnnouncementExpire.objects.filter(
                    school=self.school).first()
                if expiry_setting:
                    self.expire_date = timezone.now().date(
                    ) + timezone.timedelta(days=expiry_setting.days)
            except Exception:
                pass

        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if the announcement is currently active."""
        now = timezone.now()
        is_published = self.is_published and self.publish_date <= now
        is_not_expired = self.expire_date is None or self.expire_date >= now.date()
        return is_published and is_not_expired


class AnnouncementComment(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Model for comments on announcements.
    """
    related_name = 'announcement_comments'

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The announcement this comment belongs to"
    )

    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='announcement_comments',
        help_text="User who wrote this comment"
    )

    content = models.TextField(help_text="The comment text")

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.announcement.title}"


class AnnouncementView(SchoolAwareModel, AuditableModel):
    """
    Tracks which users have viewed which announcements.
    """
    related_name = 'announcement_views'

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name='views',
        help_text="The announcement that was viewed"
    )

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='announcement_views',
        help_text="User who viewed the announcement"
    )

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['announcement', 'user'],
                name='unique_announcement_view'
            )
        ]
        indexes = [
            models.Index(fields=['announcement', 'user']),
            models.Index(fields=['viewed_at']),
        ]

    def __str__(self):
        return f"{self.user} viewed {self.announcement.title} on {self.viewed_at}"


# ----------------------------- Transaction Type -----------------------------
class TransactionType(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Per-school catalog of transaction types (e.g., TUITION, PTA_DUE, SALARY, REFUND).
    """
    related_name = "transaction_types"

    code = models.SlugField(
        max_length=40, help_text=_("Short code, e.g. TUITION"))
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_income = models.BooleanField(
        default=True, help_text=_("Income=True, Expense=False"))
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["school", "code"],
                             name="uniq_trxtype_code_per_school"),
        ]
        indexes = [
            models.Index(fields=["school", "is_income", "active"]),
            models.Index(fields=["school", "code"]),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({'IN' if self.is_income else 'OUT'})"


# ----------------------------- Transaction QS/Manager ------------------------
class TransactionQuerySet(models.QuerySet):
    def income(self): return self.filter(transaction_type__is_income=True)
    def expense(self): return self.filter(transaction_type__is_income=False)

    def successful(self): return self.filter(status=Transaction.Status.SUCCESS)
    def pending(self): return self.filter(status=Transaction.Status.PENDING)
    def failed(self): return self.filter(status=Transaction.Status.FAILED)
    def refunded(self): return self.filter(status=Transaction.Status.REFUNDED)
    def cancelled(self): return self.filter(
        status=Transaction.Status.CANCELLED)

    def for_student(self, student): return self.filter(payer_student=student)
    def for_staff(self, staff): return self.filter(payer_staff=staff)
    def for_user(self, user): return self.filter(payer_user=user)


class TransactionManager(TenantManager):
    """Tenant-aware manager returning our custom queryset."""
    _queryset_class = TransactionQuerySet

    def get_queryset(self) -> TransactionQuerySet:
        return super().get_queryset()


# ----------------------------- Transaction Model ----------------------------
class Transaction(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    A money movement linked to a payer (Parent/Student/Teacher) and a TransactionType.
    Payer is primarily the `User`; optional profile FKs add denormalized convenience.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        SUCCESS = "SUCCESS", _("Successful")
        FAILED = "FAILED", _("Failed")
        REFUNDED = "REFUNDED", _("Refunded")
        CANCELLED = "CANCELLED", _("Cancelled")

    class Method(models.TextChoices):
        CASH = "CASH", _("Cash")
        BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
        POS = "POS", _("POS")
        ONLINE = "ONLINE", _("Online")
        CHEQUE = "CHEQUE", _("Cheque")
        ADJUSTMENT = "ADJUSTMENT", _("Manual Adjustment")

    class PayerKind(models.TextChoices):
        STUDENT = STUDENT, _("Student")
        PARENT = PARENT, _("Parent")
        # normalized to STAFF role in validation
        TEACHER = "teacher", _("Teacher")

    related_name = "transactions"

    # Core links
    transaction_type = models.ForeignKey(
        TransactionType, on_delete=models.PROTECT, related_name="transactions"
    )
    payer_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="payments_made",
        limit_choices_to=Q(role__in=[PARENT, STUDENT, STAFF]),
        help_text=_("Principal payer user (role must be Parent/Student/Staff)"),
    )
    # Optional denormalized profile FKs for fast filters/reports
    payer_student = models.ForeignKey(
        "Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )
    payer_staff = models.ForeignKey(
        "Staff", on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions"
    )

    payer_kind = models.CharField(
        max_length=12, choices=PayerKind.choices, help_text=_("Declared payer kind")
    )

    # Money
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING)
    method = models.CharField(
        max_length=16, choices=Method.choices, default=Method.ONLINE)

    # Processing / audit
    reference = models.CharField(
        max_length=64,
        help_text=_("Gateway reference / receipt no. Unique within a school"),
    )
    gateway = models.CharField(max_length=32, blank=True, default="", help_text=_(
        "e.g., paystack, flutterwave"))
    narration = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    # Who recorded it
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions_created"
    )

    # Tenant-aware manager
    objects: TransactionManager = TransactionManager()

    class Meta:
        constraints = [
            UniqueConstraint(fields=["school", "reference"],
                             name="uniq_txn_ref_per_school"),
            models.CheckConstraint(check=Q(amount__gt=0),
                                   name="txn_amount_positive"),
        ]
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["school", "transaction_type"]),
            models.Index(fields=["school", "payer_user"]),
            models.Index(fields=["school", "paid_at"]),
            models.Index(fields=["reference"]),
        ]
        ordering = ["-created_at"]

    # ---- convenience properties ----
    @property
    def is_income(self) -> bool:
        return bool(getattr(self.transaction_type, "is_income", True))

    def __str__(self) -> str:  # pragma: no cover
        who = getattr(self.payer_user, "username", str(self.payer_user))
        return f"{self.reference} • {self.transaction_type.name} • {self.amount} {self.currency} • {who}"

    # ---- validation ----
    def clean(self):
        errors = {}

        # Ensure same tenant
        if self.transaction_type and self.transaction_type.school_id != self.school_id:
            errors["transaction_type"] = _(
                "Transaction type must belong to the same school.")

        # Infer / validate payer_kind vs user.role
        role = getattr(self.payer_user, "role", None)
        expected = {
            self.PayerKind.PARENT: PARENT,
            self.PayerKind.STUDENT: STUDENT,
            self.PayerKind.TEACHER: STAFF,  # teacher == staff
        }.get(self.payer_kind)

        if not role:
            errors["payer_user"] = _("Payer user must have a role.")
        elif expected and role != expected:
            # why: prevent mismatched declarations like payer_kind=STUDENT but user is PARENT
            errors["payer_kind"] = _(
                f"Payer kind '{self.payer_kind}' does not match user.role '{role}'.")

        # Profile FKs (if provided) must match user + tenant
        if self.payer_student:
            if self.payer_student.school_id != self.school_id:
                errors["payer_student"] = _(
                    "Student must belong to the same school.")
            if role and role != STUDENT:
                errors["payer_student"] = _(
                    "Payer user must have STUDENT role to attach a student profile.")
            if getattr(self.payer_student, "user_id", None) and self.payer_student.user_id != self.payer_user_id:
                # why: avoid cross-user corruption
                errors["payer_student"] = _(
                    "Student profile does not belong to the payer user.")

        if self.payer_staff:
            if self.payer_staff.school_id != self.school_id:
                errors["payer_staff"] = _(
                    "Staff must belong to the same school.")
            if role and role != STAFF:
                errors["payer_staff"] = _(
                    "Payer user must have STAFF role to attach a staff profile.")
            if getattr(self.payer_staff, "user_id", None) and self.payer_staff.user_id != self.payer_user_id:
                errors["payer_staff"] = _(
                    "Staff profile does not belong to the payer user.")

        if errors:
            raise ValidationError(errors)

    # ---- lifecycle helpers ----
    def _mark(self, status: str, when: Optional[timezone.datetime] = None):
        self.status = status
        if status == self.Status.SUCCESS and not self.paid_at:
            self.paid_at = when or timezone.now()
        self.full_clean()
        self.save(update_fields=["status", "paid_at", "updated_at"])

    @transaction.atomic
    def mark_success(self, when: Optional[timezone.datetime] = None):
        """Mark as successful; sets paid_at if missing."""
        self._mark(self.Status.SUCCESS, when)

    @transaction.atomic
    def mark_failed(self):
        self._mark(self.Status.FAILED)

    @transaction.atomic
    def refund(self, reason: str = ""):
        """Mark as refunded; keep narration trail."""
        self.narration = (self.narration + "\nREFUND: " +
                          reason).strip() if reason else self.narration
        self._mark(self.Status.REFUNDED)

    # ---- save hook ----
    def save(self, *args, **kwargs):
        # why: default school & created_by from thread-locals to reduce caller burden
        if not self.school_id:
            self.school = self.school or get_current_school()
        if not self.created_by_id:
            # best-effort; replace with your request accessor if needed
            req = getattr(get_current_school, "__wrapped__", None)
            try:
                from main.tenancy.threadlocals import get_current_request
                req = get_current_request()
                user = getattr(req, "user", None) if req else None
                if user and getattr(user, "is_authenticated", False):
                    self.created_by = user
            except Exception:
                pass

        # Auto infer payer_kind if not provided
        if not self.payer_kind and self.payer_user_id:
            role = getattr(self.payer_user, "role", None)
            if role == STUDENT:
                self.payer_kind = self.PayerKind.STUDENT
            elif role == STAFF:
                self.payer_kind = self.PayerKind.TEACHER
            else:
                self.payer_kind = self.PayerKind.PARENT  # default fallback

        # Normalize reference spacing
        if self.reference:
            self.reference = self.reference.strip()

        self.full_clean()
        return super().save(*args, **kwargs)


class AuditLog(SchoolOwnedModel):
    """
    Comprehensive audit trail for both requests and model changes.
    Tracks who did what, when, and from where.
    """
    class Action(models.TextChoices):
        REQUEST = "request", _("Request")
        RETRIEVE = "retrieve", _("Retrieve")
        LIST = "list", _("List")
        CREATE = "create", _("Create")
        UPDATE = "update", _("Update")
        DELETE = "delete", _("Delete")
        LOGIN = "login", _("Login")
        LOGOUT = "logout", _("Logout")

    # Actor information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name=_("user")
    )

    # Request context
    ip_address = models.GenericIPAddressField(
        _("IP address"), null=True, blank=True)
    user_agent = models.TextField(_("user agent"), blank=True)
    request_path = models.CharField(
        _("request path"), max_length=512, blank=True)
    request_method = models.CharField(
        _("request method"), max_length=8, blank=True)
    status_code = models.PositiveIntegerField(_("status code"), default=0)
    success = models.BooleanField(_("success"), default=True)

    # Timestamp and context
    timestamp = models.DateTimeField(
        _("timestamp"), default=timezone.now, db_index=True)

    # Change tracking
    action = models.CharField(
        _("action"), max_length=10, choices=Action.choices, db_index=True)
    model = models.CharField(_("model"), max_length=128,
                             blank=True, db_index=True)
    object_id = models.CharField(
        _("object ID"), max_length=64, blank=True, db_index=True)
    changes = models.JSONField(_("changes"), default=dict, blank=True)
    extra = models.JSONField(_("extra data"), default=dict, blank=True)

    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    # School context (for multi-tenancy)
    school = models.ForeignKey(
        "main.School",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name=_("school")
    )

    class Meta:
        verbose_name = _("audit log")
        verbose_name_plural = _("audit logs")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp", "action"]),
            models.Index(fields=["model", "object_id"]),
            models.Index(fields=["school", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} on {self.model or 'system'} by {self.user} at {self.timestamp}"
