import logging
from django.contrib.auth import get_user_model
from datetime import date

from django.utils.crypto import get_random_string
from django.db.models import UniqueConstraint
from .users import ADMIN, OWNER, STUDENT, TEACHER
from django.db import models, transaction
import string
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist, ValidationError

User = get_user_model()


def get_year_from_date(date_string):
    try:
        year = int(date_string.split('-')[0])
        return year
    except (ValueError, IndexError):
        # Handle cases where the date string is not in the expected format
        raise ValueError(
            "Invalid date format: '" + date_string + "'. Expected format 'YYYY-MM-DD'."
        )


from main.tenancy.models import AuditableModel, SoftDeleteModel, SchoolAwareModel, SchoolOwnedModel


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


class School(AuditableModel, SoftDeleteModel):
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
        User,
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
    
    code = models.CharField(
        max_length=10,  # Increased from 6
        null=True,
        blank=True,
        unique=True,
        help_text="Unique code identifier for the school (auto-generated if not provided)",
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
        default=dict, # e.g {'max_exam_score_for_primary': 60}
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
        permissions = [
            ("view_school_dashboard", "Can view school dashboard"),
            ("manage_school_settings", "Can manage school settings"),
        ]

    def clean(self):
        if self.short_name and self.short_name.startswith("SC") and (len(self.short_name) == 6 or len(self.short_name) == 5) and self.short_name[2:].isdigit():
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
                # For owners or admins, return the school where they are the owner
                return School.objects.filter(owner=user).first()
            if hasattr(user, 'is_admin') and user.is_admin:
                try:
                    return School.objects.filter(owner=user).first()
                except:
                    return user.school
                # For admins, return the school associated with their admin profile
            elif hasattr(user, 'is_teacher') and user.is_teacher:
                # For staff, return the school associated with their teacher profile
                return user.staff_profile.school
            elif hasattr(user, 'is_student') and user.is_student:
                # For students, return the school associated with their student profile
                return user.student_profile.school
        except Exception as e:
            raise e
        # end try


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


class Staff(UserInherit):
    related_name = 'staff'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    department = models.CharField(max_length=15, null=True, blank=True)
    is_teaching_staff = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.department} - {self.user.full_name}"

    class Meta:
        ordering = ['school', 'department']


class ClassList(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    related_name = 'classes'

    CLASS_CHOICES = [
        ('Basic1', 'Basic 1'),
        ('Basic2', 'Basic 2'),
        ('Basic3', 'Basic 3'),
        ('Basic4', 'Basic 4'),
        ('Basic5', 'Basic 5'),
        ('Basic6', 'Basic 6'),
        ('KG1', 'Kindergarten 1'),
        ('KG2', 'Kindergarten 2'),
        ('KG3', 'Kindergarten 3'),
        ('PRY1', 'Primary 1'),
        ('PRY2', 'Primary 2'),
        ('PRY3', 'Primary 3'),
        ('PRY4', 'Primary 4'),
        ('PRY5', 'Primary 5'),
        ('PRY6', 'Primary 6'),
        ('JS1', 'Junior Secondary 1'),
        ('JS2', 'Junior Secondary 2'),
        ('JS3', 'Junior Secondary 3'),
        ('SS1', 'Senior Secondary 1'),
        ('SS2', 'Senior Secondary 2'),
        ('SS3', 'Senior Secondary 3'),
    ]

    CLASS_CATEGORIES = (
        ("ART", "Art Class"),
        ("SCIENCE", "Science Class"),
        ("PRIMARY", "Primary Classes"),
        ("JUNIOR SEC", "Junior Secondary Classes"),
        ("SCIENCE_TECH", "Science and Technology Class"),
        ("COMMERCIAL", "Commercial Class"),
    )

    DIVISION_CHOICES = [(letter, letter) for letter in string.ascii_uppercase]

    # school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=6, choices=CLASS_CHOICES)
    academic_session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, related_name='classes')
    class_teacher = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'user__role': "teacher"}, related_name="school_class")
    division = models.CharField(
        max_length=10,  blank=True, null=True,
        choices=DIVISION_CHOICES, default=""
    )  # e.g., "A", "B", "C"
    category = models.CharField(
        max_length=12, choices=CLASS_CATEGORIES,
        blank=True, null=True, default=""
    )
    class_capacity = models.IntegerField(default=50)

    def __str__(self):
        return f"{self.get_name_display()} ({self.academic_session.name})"

    class Meta:
        unique_together = ('academic_session', 'name', 'division')

    def __str__(self):
        try:
            return f"{self.get_name_display()} {self.division.name if self.division else ''} ({self.academic_session.name})"
        except:
            return f"{self.get_name_display()} ({self.academic_session.name})"
            # return f"{self.name}({self.academic_session.name})"

    def validate_class_capacity(self):
        if self.students.count() > self.class_capacity:
            message = f"{self.name} already filled!"
            return message

    @classmethod
    def get_school_classes(cls, request):
        school = request.school
        print(ClassList.objects.filter(academic_session__school=school))
        return ClassList.objects.filter(academic_session__school=school)

    @classmethod
    def get_school_class_ids(cls, request):
        school = request.school
        print("Current School ", school)
        print(ClassList.objects.filter(academic_session__school=school))
        # # Use a subquery to explicitly define the filtering
        return cls.objects.filter(
            academic_session__school=school
        ).values_list('id', flat=True)


class Subject(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    school_class = models.ForeignKey(
        ClassList, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="subjects")

    class Meta:
        unique_together = ('school_class', 'name')

    def __str__(self):
        return f"{self.name} - {self.school_class.name}"


class Student(UserInherit):
    reg_no = models.CharField(max_length=20, null=True,
                              blank=True)  # e.g., "STU-2023-001"
    student_id = models.CharField(max_length=20, null=True, blank=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='student_profile')
    date_of_birth = models.DateField()
    # admission_date = models.DateField(default=date.today)
    student_class = models.ForeignKey(
        ClassList, on_delete=models.CASCADE, related_name='students', null=True, blank=True)

    session_admitted = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE, null=True, blank=True)  # e.g., 2023/2024

    @property
    def full_name(self):
        return f"{self.user.full_name}"

    @property
    def email(self):
        return f"{self.user.email}"

    @property
    def klass(self):
        return f"{self.student_class.get_name_display()} {self.student_class.division}"

    @property
    def student_age(self):
        # Helper method to calculate the student's age
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (
                self.date_of_birth.month, self.date_of_birth.day)
        )

    class Meta:
        constraints = [
            # Ensure `student_id` is unique within the same school
            UniqueConstraint(fields=['school', 'student_id'],
                             name='unique_student_id_per_school'),
            # Ensure `reg_no` is unique within the same school
            UniqueConstraint(fields=['school', 'reg_no'],
                             name='unique_reg_no_per_school'),
            UniqueConstraint(fields=['school', 'user'],
                             name='unique_user_per_school'),
        ]

    def __str__(self):
        return f"{self.id} - {self.user.full_name}"

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
        while User.objects.filter(email=unique_email).exists():
            unique_email = f"{self.user.first_name.lower()}." + str(self.user.last_name).lower(
            ) + f"{counter}@{school_short_name}{admission_year}.com"
            counter += 1

        return unique_email

    def __str__(self):
        return f"{self.student_id} - {self.user.full_name}"

    def save(self, *args, **kwargs):
        # Generate a unique student ID if it's not already set
        if not self.student_id:
            self.student_id = self.generate_unique_student_id()

        # Generate a unique dynamic email if not set
        if not self.user.email:
            self.user.email = self.generate_unique_email()
            self.user.save()

        super().save(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     # Save the instance first to generate the ID
    #     print(self.id, "Printing ID from Student save method")
    #     if not self.id:
    #         super().save(*args, **kwargs)  # Save first to get the ID
    #     print(self.id, "Printing ID from Student save method")

    #     # Ensure reg_no is available before updating student_id
    #     if self.reg_no:
    #         self.student_id = f"STU-{self.session_admitted}-{self.reg_no}"

    #     super().save(*args, **kwargs)  # Save again with updated student_idI


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
        User, on_delete=models.SET_NULL,
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
        elif request.user.is_teacher:
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
        User, on_delete=models.CASCADE, related_name='lesson_plans')
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
        elif request.user.is_teacher:
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
        User, on_delete=models.CASCADE, related_name='lesson_notes')

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

        # Check if the user is a subject teacher
        elif request.user.is_teacher:
            # Staff can only view the GmeetClass for the subjects they teach
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

