from .models import Term
from django import forms
from library.models import LibraryBook
from main.models import (
    AcademicSession, ClassList,
    GmeetClass, LessonPlan, Subject,
    User, Staff, Student, ClassLevel
)


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['department']

        widgets = {
            'department': forms.TextInput(attrs={
                'placeholder': 'Enter Department',
                'class': 'input',
                'required': 'required'
            }),
        }


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter Password',
            'class': 'input',
        }),
        min_length=8,
        help_text='At least 8 characters. Leave blank to keep current password.'
    )
    
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'input',
        }),
        min_length=8,
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'email', 'phone', 'image']

        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Enter First Name',
                'class': 'input',
                'required': 'required'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Enter Last Name',
                'class': 'input',
                'required': 'required'
            }),
            'gender': forms.Select(attrs={
                'class': 'input-1',
                'required': 'required'
            }, choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female')]),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter Email',
                'class': 'input',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter Phone Number',
                'class': 'input',
            }),
            'image': forms.ClearableFileInput(attrs={
                'onchange': 'previewImage(this);',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['gender'].required = True
        
        # Make image field not required for updates
        if self.instance and self.instance.pk:
            self.fields['password'].help_text = 'Leave blank to keep current password.'
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['image'].required = False

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Only validate passwords if they are being changed
        if password or confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match')
            
            if len(password) < 8:
                self.add_error('password', 'Password must be at least 8 characters long')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Only set password if it's provided
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
            self.save_m2m()
            
        return user


class StudentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # Extract the request object from the keyword arguments
        self.request = kwargs.pop('request', None)
        super(StudentForm, self).__init__(*args, **kwargs)

        print(self.fields)
        if self.request:
            self.fields['session_admitted'].queryset = AcademicSession.get_school_sessions(
                self.request)

            # self.fields['student_class'].queryset = ClassList.get_school_classes(
            #     self.request)

    class Meta:
        model = Student
        fields = [
            'date_of_birth',
            'session_admitted',
            # 'student_class',
            'reg_no'
        ]
        widgets = {
            # 'student_id': forms.TextInput(attrs={
            #     'placeholder': 'Enter Student ID',
            #     'class': 'input',
            #     'required': 'required'
            # }),
            'date_of_birth': forms.DateInput(attrs={
                'placeholder': 'YYYY-MM-DD',
                'class': 'input',
                'required': 'required',
                'type': 'date'
            }),
            # 'admission_date': forms.DateInput(attrs={
            #     'placeholder': 'YYYY-MM-DD',
            #     'class': 'input',
            #     'required': 'required',
            #     'type': 'date'
            # }),
            # 'student_class': forms.Select(attrs={
            #     'class': 'input-1',
            #     'required': 'required'
            # }),
            'session_admitted': forms.Select(attrs={
                'class': 'input-1',
                'required': 'required'
            }),
            'reg_no': forms.TextInput(attrs={
                'placeholder': 'Enter Registration Number',
                'class': 'input',
                'required': 'required'
            }),
        }


class StudentUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'email', "image"]

        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Enter Name',
                'class': 'input',
                'required': 'required'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Enter Name',
                'class': 'input',
                'required': 'required'
            }),
            'gender': forms.Select(attrs={
                'class': 'input-1',
                'required': 'required'
            }, choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female')]),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter Email',
                'class': 'input',
            }),
            'image': forms.ClearableFileInput(attrs={
                'onchange': 'previewImage(this);',
                'class': 'input',
            })
        }

    password = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter Password',
            'class': 'input',
            'disabled': 'disabled',
            'value': "Disabled: Student's Surname in lowercase is default"
        }),
        required=False
    )


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = [
            'start_date',
            'end_date',
            "name", 'is_current',
            #  'next_session_begins', 'max_exam_score'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', "id": "start_date"}),
            'end_date': forms.DateInput(attrs={'type': 'date', "id": "end_date"}),
            'name': forms.TextInput(attrs={'type': 'text', "id": "name", "placeholder": "2024-2025 ( optional )"}),
            # 'next_session_begins': forms.DateInput(attrs={'type': 'date'}),
        }


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['name', 'start_date', 'end_date',
                  'next_term_begins', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'next_term_begins': forms.DateInput(attrs={'type': 'date'}),
        }


class CustomSelect(forms.widgets.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option_dict = super().create_option(name, value, label, selected,
                                            index, subindex=subindex, attrs=attrs)
        # Customize the `option` elements
        option_dict['attrs']['class'] = 'custom-option-class'
        # Example of inline styles for options
        option_dict['attrs']['style'] = 'color: blue;'
        return option_dict


class ClassForm(forms.ModelForm):
    class Meta:
        model = ClassList
        fields = ['label', 'academic_session', 'class_teacher',
                  'division', 'class_level', 'is_active']
        widgets = {
            'label': forms.TextInput(attrs={
                'class': 'form-control',
                'required': 'required',
                'placeholder': 'e.g., SS1 Science A'
            }),
            'academic_session': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'class_teacher': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'division': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A, B, C or 1, 2, 3'
            }),
            'class_level': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'name': 'A descriptive name for the class (e.g., SS1 Science A)',
            'division': 'Optional division/section identifier (e.g., A, B, 1, 2, etc.)',
            'class_level': 'Select the academic level this class belongs to',
            'is_active': 'Uncheck to archive this class'
        }

    def __init__(self, *args, **kwargs):
        # Extract the request object from the keyword arguments
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        if self.request:
            # Filter academic sessions to only show those from the current school
            self.fields['academic_session'].queryset = AcademicSession.get_school_sessions(
                self.request)

            # Filter staff to only show those from the current school
            self.fields['class_teacher'].queryset = Staff.objects.all()

            # Filter class levels to only show those from the current school
            self.fields['class_level'].queryset = ClassLevel.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        academic_session = cleaned_data.get('academic_session')

        # Check for duplicate class names within the same academic session
        if name and academic_session:
            qs = ClassList.objects.filter(
                name__iexact=name,
                academic_session=academic_session
            )

            if self.instance.pk:  # For updates
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    'name', 'A class with this name already exists in the selected academic session.')

        return cleaned_data


class SubjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extract the request object from the keyword arguments
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ["name", "code", "description", "is_core", "applicable_categories", "applicable_departments"]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Subject Name',
            }),
            # 'school_class': forms.Select(attrs={
            #     'class': 'form-control',
            # }),
            # 'teacher': forms.Select(attrs={
            #     'class': 'form-control',
            # }),
        }


class GoogleMeetForm(forms.ModelForm):
    class Meta:
        model = GmeetClass
        fields = ['title', 'subject', 'description',
                  'start_time', 'gmeet_link']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            # 'subject': 'Meeting Title',
            'start_time': 'Date and Time',
        }


class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = ['id', 'school_class', 'subject',
                  'uploaded_by', 'uploaded_file']
        widgets = {
            'uploaded_file': forms.ClearableFileInput(attrs={'class': 'input'}),
            'school_clas': forms.Select(attrs={'class': 'input'}),
        }


class LibraryBookForm(forms.ModelForm):
    class Meta:
        model = LibraryBook
        fields = ['book_image', 'title_with_author', 'book']
        labels = {
            'book_image_url': 'Book Image',
            'title': 'Book Title',
            'author': 'Author Name',
        }
        widgets = {
            'book_image_url': forms.URLInput(attrs={'placeholder': 'Enter Image URL'}),
            'title': forms.TextInput(attrs={'placeholder': 'Enter Book Title'}),
            'author': forms.TextInput(attrs={'placeholder': 'Enter Author Name'}),
        }
        help_texts = {
            'book_image_url': 'Provide a valid URL for the book cover image.',
        }
