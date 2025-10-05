from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from main.tenancy.models import SchoolOwnedModel
from main.tenancy.managers import get_current_school
from django.db.models import Q, UniqueConstraint

SUPERADMIN = "superadmin"
OWNER = "owner"
ADMIN = "admin"
TEACHER = "teacher"
STUDENT = "student"


class UserManager(BaseUserManager, SchoolOwnedModel):
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

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', SUPERADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
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
        (TEACHER, "Teacher"),
        (STUDENT, "Student"),
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
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
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
    image = models.ImageField(blank=True, null=True)
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
                condition=Q(email__isnull=False) & ~Q(email="") & Q(school__isnull=False),
                name="uniq_email_per_school",
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
    def is_teacher(self):
        return self.role == "teacher"

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
            "teacher": "Teacher",
            "student": "Student"
        }
        return roles.get(self.role, "Unknown Role")

    @property
    def ES_Sep(self):
        return "_:_"
    
    @classmethod
    def get_username(cls, email):
        school = get_current_school()
        return f"{email}{cls.ES_Sep}{school.id}"

    def save(self, *args, **kwargs):
        school = self.school or get_current_school()
        try:
            # Custom save logic, if needed
            if (self.is_teacher or self.is_student) and not self.password:
                self.set_password(str(self.last_name).lower() or 'default123')
        except Exception as e:
            print(e)
            pass

        # Generate the unique 
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
        elif self.is_teacher and hasattr(self, 'staff_profile'):
            return self.staff_profile
        return None
    
