import datetime
from urllib import request
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny

import pandas as pd
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction

from api.serializers.core_serializers import StudentCreateSerializer
from main.forms import StaffForm, StaffUserForm
from main.models import STAFF, User
from main.tenancy.notification_handler import NotificationManager
from main.models import School, Staff, AcademicSession, Term, ClassList, Student, Subject
from main.tenancy.threadlocals import get_current_school

from ..serializers import (
    SchoolSerializer,
    StaffSerializer,
    ClassListSerializer,
    AcademicSessionSerializer,
    StudentSerializer,
    TermSerializer,
    SubjectSerializer,
)
from ..permissions import IsAdminOrIsStaffOrReadOnly, IsAdminOrReadOnly
from ..serializers.dashboard_serializers import (
    AdminDashboardSerializer,
    StaffDashboardSerializer,
    StudentDashboardSerializer,
    ParentDashboardSerializer,
)

from main.models import SUPERADMIN, OWNER, ADMIN, STAFF, STUDENT, PARENT


class StandardResultSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class SchoolViewSet(ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ClassListViewSet(ModelViewSet):
    serializer_class = ClassListSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # user = self.request.user
        school = self.request.school
        return ClassList.objects.filter(academic_session__school=school)

    @action(detail=False, methods=['GET',], url_path="all")
    def all(self, request, *args, **kwargs):
        print("All Classes", args, kwargs)
        classes = ClassList.objects.all()
        # AcademicSession.create_default_setup(
        #     "2023/2024",
        #     datetime.date(2023, 2, 9),  # Use datetime.date for date values
        #     datetime.date(2024, 12, 4),
        #     request.school
        # )
        # print(classes)

        serializer = ClassListSerializer(classes, many=True)
        return Response(serializer.data)


class AcademicSessionViewSet(ModelViewSet):
    queryset = AcademicSession.objects.all()
    serializer_class = AcademicSessionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_school_sessions(self, request):
        user = self.request.user
        school = School.objects.filter(owner=user).first()
        return AcademicSession.objects.filter(school=school)

    @action(detail=True, methods=['post'])
    def current(self, request):
        user = request.user
        school = user.academic_sessions.first()
        current_session = self.queryset.filter(
            school=school, is_current=True).first()
        if current_session:
            serializer = self.get_serializer(current_session)
            print(serializer.data)
            return Response(serializer.data)
        return Response({'detail': 'No current session found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def make_session_current(self, request, pk=None):
        academic_session = self.get_object()
        AcademicSession.objects.filter(
            school=academic_session.school).update(is_current=False)
        academic_session.is_current = True
        academic_session.save()
        return Response({'detail': 'Academic Session updated as current'})

    @action(detail=True, methods=['post'])
    def create_terms_and_classes_manually(self, request, pk=None):
        academic_session = self.get_object()
        academic_session.create_terms()
        academic_session.create_all_classes()
        return Response({'detail': 'Terms and classes are created successfully'})


class TermViewSet(ReadOnlyModelViewSet):
    serializer_class = TermSerializer
    queryset = Term.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        academic_session_id = self.kwargs.get('academic_session_pk')
        if academic_session_id:
            return self.queryset.filter(academic_session_id=academic_session_id)
        return self.queryset

    # def get_queryset(self, request):
    #   return Term.objects.filter(academic_session_pk=self.kwargs['academic_session_pk'])

    # def get_serializer_context(self):
    #   return {'academic_session_id' : self.kwargs['academic_session_pk']}


class StaffViewSet(ModelViewSet):
    queryset = Staff.objects.all().select_related('user', 'school')
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # for obj in Staff.objects.my_school():
        #     print(obj)
        #     obj.user.set_password("password123")
        #     obj.user.save()

        queryset = Staff.objects.all()
        print("All Staffs:", queryset)
        print("\n\n\n\nrequest in StaffViewSet.get_queryset:", self.request.user.role)

        if self.request.user.role == STUDENT:
            return queryset.filter(user=self.request.user)

        query = self.request.query_params.get('q', None)

        print(query, queryset)

        if query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=query) |  # Search by first name
                Q(user__last_name__icontains=query) |   # Search by last name
                Q(department__icontains=query) |         # Search by department
                Q(user__email__icontains=query)           # Search by email
            )
        return queryset

    @action(detail=False, methods=['GET'])
    def list_staffs(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        print(serializer.data)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['GET'])
    def detail_staff(self, request, pk=None):
        staff = get_object_or_404(Staff, pk=pk)
        serializer = self.get_serializer(staff)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        # Handle both form data and JSON data
        if request.content_type == 'application/json':
            data = request.data
        else:
            data = request.data.dict()
            if 'user.image' in request.FILES:
                data['user.image'] = request.FILES['user.image']

        # Convert flat data to nested format expected by the serializer
        nested_data = {}
        for key, value in data.items():
            if '.' in key:
                # Handle nested fields (e.g., 'user.first_name')
                prefix, field = key.split('.', 1)
                if prefix not in nested_data:
                    nested_data[prefix] = {}
                nested_data[prefix][field] = value
            else:
                nested_data[key] = value

        # Set default password if not provided
        if 'user' in nested_data and 'password' not in nested_data['user']:
            last_name = nested_data['user'].get('last_name', '').lower()
            nested_data['user']['password'] = f"{last_name}@123"

        serializer = self.get_serializer(data=nested_data)
        if serializer.is_valid():
            try:
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    {
                        'success': True,
                        'data': serializer.data,
                        'message': 'Staff created successfully!'
                    },
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
            except Exception as e:
                return Response(
                    {
                        'success': False,
                        'error': str(e),
                        'message': 'Failed to create staff member.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {
                'success': False,
                'errors': serializer.errors,
                'message': 'Validation failed. Please check the provided data.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_create(self, serializer):
        # Add school from the current user's school
        if hasattr(self.request.user, 'school'):
            serializer.save(school=self.request.user.school)
        else:
            serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Handle both form data and JSON data
        if request.content_type == 'application/json':
            data = request.data
        else:
            data = request.data.dict()
            if 'user.image' in request.FILES:
                data['user.image'] = request.FILES['user.image']

        # Convert flat data to nested format
        nested_data = {}
        for key, value in data.items():
            if '.' in key:
                prefix, field = key.split('.', 1)
                if prefix not in nested_data:
                    nested_data[prefix] = {}
                nested_data[prefix][field] = value
            else:
                nested_data[key] = value

        # Don't update password if not provided
        if 'user' in nested_data and 'password' in nested_data['user'] and not nested_data['user']['password']:
            nested_data['user'].pop('password')

        serializer = self.get_serializer(instance, data=nested_data, partial=partial)
        if serializer.is_valid():
            try:
                self.perform_update(serializer)
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'Staff updated successfully!'
                })
            except Exception as e:
                return Response({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to update staff member.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': serializer.errors,
            'message': 'Validation failed. Please check the provided data.'
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({
                'success': True,
                'message': 'Staff member deleted successfully!'
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to delete staff member.'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], parser_classes=[MultiPartParser])
    def import_staff(self, request):
        if 'file' not in request.FILES:
            return Response(
                {
                    'success': False,
                    'error': 'No file provided',
                    'message': 'Please upload a file to import staff data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        try:
            if file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)

            required_columns = ['first_name', 'last_name', 'email', 'department']
            if not all(col in df.columns for col in required_columns):
                return Response(
                    {
                        'success': False,
                        'error': f"Missing required columns. Required: {', '.join(required_columns)}",
                        'message': 'The uploaded file is missing required columns.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            success_count = 0
            error_messages = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Prepare user data
                        user_data = {
                            'first_name': str(row['first_name']).strip(),
                            'last_name': str(row['last_name']).strip(),
                            'email': str(row['email']).strip().lower(),
                            'gender': str(row.get('gender', 'M')).strip().upper()[:1],
                            'phone': str(row.get('phone', '')).strip(),
                            'password': str(row.get('password', '') or f"{row['last_name'].lower()}@123"),
                            'is_active': True
                        }

                        # Prepare staff data
                        staff_data = {
                            'department': str(row['department']).strip(),
                            'is_teaching_staff': bool(row.get('is_teaching_staff', True))
                        }

                        # Check if user already exists
                        user = User.objects.filter(email=user_data['email']).first()
                        
                        if user:
                            # Update existing user and staff
                            for key, value in user_data.items():
                                if key != 'password' and hasattr(user, key):
                                    setattr(user, key, value)
                            
                            if 'password' in user_data and user_data['password']:
                                user.set_password(user_data['password'])
                            
                            user.save()
                            
                            # Update staff
                            staff, created = Staff.objects.get_or_create(user=user)
                            for key, value in staff_data.items():
                                setattr(staff, key, value)
                            staff.save()
                            
                            if created:
                                success_count += 1
                        else:
                            # Create new user and staff
                            user = User.objects.create_user(
                                username=user_data['email'],
                                **{k: v for k, v in user_data.items() if k != 'password'}
                            )
                            if 'password' in user_data and user_data['password']:
                                user.set_password(user_data['password'])
                                user.save()
                            
                            staff = Staff.objects.create(
                                user=user,
                                **staff_data
                            )
                            success_count += 1

                    except Exception as e:
                        error_messages.append(f"Row {index + 2}: {str(e)}")
                        continue

            response_data = {
                'success': True,
                'imported_count': success_count,
                'total_count': len(df),
                'message': f'Successfully imported {success_count} of {len(df)} staff members.'
            }
            
            if error_messages:
                response_data['errors'] = error_messages
                response_data['message'] += f' {len(error_messages)} records failed.'
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': 'An error occurred while processing the file.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class StudentViewSet(ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    # pagination_class = [StandardResultSetPagination]
    filter_backends = [SearchFilter, OrderingFilter]
    ordering_fields = ['user__first_name', 'grade']
    search_fields = ['user__first_name', 'user__last_name', 'department',
                     'student_class__name']  # unique search fields for students
    
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print("\n\n\n\nException in StudentViewSet.create:", e)
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': 'An error occurred while processing the file.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_queryset(self):
        qs = Student.objects.all()
        class_filter = self.request.query_params.get('class', None)
        if class_filter:
            qs = qs.filter(school_class__name__icontains=class_filter)
        return qs.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST' or self.action == 'create':
            return StudentCreateSerializer

        return StudentSerializer

    @action(detail=False, methods=['POST'], parser_classes=[MultiPartParser, FormParser])
    def import_students(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        try:
            if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)

            required_columns = ['first_name', 'last_name', 'email', 'admission_number', 'class_name']
            if not all(col in df.columns for col in required_columns):
                return Response(
                    {"error": f"Missing required columns. Required: {', '.join(required_columns)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        school_class = SchoolClass.objects.get(
                            name=row['class_name'],
                            school=request.user.school
                        )
                    except SchoolClass.DoesNotExist:
                        return Response(
                            {"error": f"Class {row['class_name']} not found"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    user_data = {
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'email': row['email'],
                        'role': 'student',
                        'password': 'defaultpassword'  # Should be changed on first login
                    }
                    
                    student_data = {
                        'admission_number': row['admission_number'],
                        'school_class': school_class.id,
                        'date_of_birth': row.get('date_of_birth'),
                        'gender': row.get('gender', ''),
                        'address': row.get('address', ''),
                        'parent_name': row.get('parent_name', ''),
                        'parent_phone': row.get('parent_phone', ''),
                        'school': request.user.school.id
                    }
                    
                    user_serializer = UserSerializer(data=user_data)
                    student_serializer = StudentCreateSerializer(data=student_data)
                    
                    if user_serializer.is_valid() and student_serializer.is_valid():
                        user = user_serializer.save()
                        student_serializer.save(user=user, school=request.user.school)
                    else:
                        return Response(
                            {"error": f"Invalid data in row {_ + 1}", "details": {**user_serializer.errors, **student_serializer.errors}},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            return Response({"message": "Students imported successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SubjectViewSet(ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrIsStaffOrReadOnly]

    @action(detail=False, methods=['POST'], parser_classes=[MultiPartParser, FormParser])
    def import_subjects(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES['file']
        try:
            if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
                df = pd.read_excel(file)
            else:
                df = pd.read_csv(file)

            required_columns = ['name', 'code', 'type']
            if not all(col in df.columns for col in required_columns):
                return Response(
                    {"error": f"Missing required columns. Required: {', '.join(required_columns)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                subjects = []
                for _, row in df.iterrows():
                    subject_data = {
                        'name': row['name'],
                        'code': row['code'],
                        'type': row['type'],
                        'description': row.get('description', ''),
                        'school': request.user.school.id
                    }
                    
                    if 'staff_id' in df.columns:
                        subject_data['staff'] = row['staff_id']
                    if 'class_id' in df.columns:
                        subject_data['classes'] = [int(x) for x in row['class_id'].split(',') if x.isdigit()]
                    
                    serializer = self.get_serializer(data=subject_data)
                    if serializer.is_valid():
                        subject = serializer.save()
                        if 'classes' in subject_data:
                            subject.classes.set(subject_data['classes'])
                        subjects.append(subject)
                    else:
                        return Response(
                            {"error": f"Invalid data in row {_ + 1}", "details": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            return Response(
                self.get_serializer(subjects, many=True).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        school = get_current_school()

        if not school:
            return Response(
                {"detail": "User is not associated with any school"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Base data common to all roles
        base_data = {
            'upcoming_events': self._get_upcoming_events(school),
            'announcements': self._get_announcements(school),
        }

        # Role-specific data
        if user.role in [SUPERADMIN, OWNER, ADMIN]:
            return self._get_admin_dashboard_data(user, school, base_data)
        elif user.role == STAFF:
            return self._get_staff_dashboard_data(user, school, base_data)
        elif user.role == STUDENT:
            return self._get_student_dashboard_data(user, school, base_data)
        elif user.role == PARENT:
            return self._get_parent_dashboard_data(user, school, base_data)

        return Response(
            {"detail": "Invalid user role"}, 
            status=status.HTTP_403_FORBIDDEN
        )

    def _get_admin_dashboard_data(self, user, school, base_data):
        from main.models import Student, Staff, ClassList, AcademicSession, Subject
        
        try:
            # Get current academic session
            current_session = AcademicSession.objects.filter(
                school=school,
                is_current=True
            ).first()
            
            # Get basic stats
            stats = {
                'total_students': Student.objects.filter(school=school).count(),
                'total_staff': Staff.objects.filter(school=school).count(),
                'total_classes': ClassList.objects.filter(
                    academic_session=current_session,
                ).count() if current_session else 0,
                'total_subjects': Subject.objects.filter(school=school).count(),
                'current_session': current_session.name if current_session else 'Not Set',
            }

            # Merge with base data and return
            data = {**base_data, **stats}
            serializer = AdminDashboardSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response({**serializer.data, **data})

        except Exception as e:
            return Response(
                {"detail": f"Error fetching admin dashboard data: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_staff_dashboard_data(self, user, school, base_data):
        from main.models import ClassList
        
        try:
            staff = user.staff_profile
            current_session = AcademicSession.objects.filter(
                school=school,
                is_current=True
            ).first()
            
            if not current_session:
                return Response(
                    {"detail": "No active academic session"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get staff's classes for current session
            staff_classes = ClassList.objects.filter(
                class_teacher=staff,
                academic_session=current_session,
                school=school
            )

            # Get today's schedule
            today = datetime.datetime.now().date()
            day_of_week = today.weekday()  # 0=Monday, 6=Sunday
            
            todays_schedule = []
            # Timetable.objects.filter(
            #     teacher=staff,
            #     day_of_week=day_of_week,
            #     school=school
            # ).select_related('subject', 'class_group')

            # Get assignments to grade
            assignments_to_grade = []
            # Assignment.objects.filter(
            #     class_group__in=staff_classes,
            #     due_date__gte=today,
            #     school=school
            # ).count()

            data = {
                **base_data,
                'my_classes': [{
                    'id': sc.id,
                    'name': sc.name,
                    'section': sc.division,
                    'student_count': sc.enrollments.filter(is_active=True).count()
                } for sc in staff_classes],
                'todays_schedule': [{
                    'id': s.id,
                    'subject': s.subject.name if s.subject else 'N/A',
                    'class_group': s.class_group.name,
                    'start_time': s.start_time,
                    'end_time': s.end_time
                } for s in todays_schedule],
                'assignments_to_grade': assignments_to_grade,
                'total_students': sum(sc.enrollments.filter(is_active=True).count() for sc in staff_classes)
            }

            serializer = StaffDashboardSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"detail": f"Error fetching staff dashboard data: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_student_dashboard_data(self, user, school, base_data):
        from main.models import StudentEnrollment
        
        try:
            student = user.student_profile
            today = datetime.datetime.now().date()
            day_of_week = today.weekday()
            
            # Get current enrollment
            current_enrollment = StudentEnrollment.objects.filter(
                student=student,
                is_active=True
            ).select_related('class_list').first()
            
            if not current_enrollment:
                return Response(
                    {"detail": "Student is not enrolled in any class"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get today's schedule
            todays_schedule = []
            # Timetable.objects.filter(
            #     class_group=current_enrollment.class_list,
            #     day_of_week=day_of_week,
            #     school=school
            # ).select_related('subject', 'teacher__user')

            # Get upcoming assignments
            upcoming_assignments = []
            # Assignment.objects.filter(
            #     class_group=current_enrollment.class_list,
            #     due_date__gte=today,
            #     school=school
            # ).order_by('due_date')[:5]

            data = {
                **base_data,
                'class_name': current_enrollment.class_list.name,
                'class_teacher': current_enrollment.class_list.class_teacher.user.get_full_name() if current_enrollment.class_list.class_teacher else 'Not Assigned',
                'todays_schedule': [{
                    'subject': s.subject.name if s.subject else 'N/A',
                    'teacher': s.teacher.user.get_full_name() if s.teacher else 'N/A',
                    'start_time': s.start_time,
                    'end_time': s.end_time
                } for s in todays_schedule],
                'upcoming_assignments': [{
                    'id': a.id,
                    'title': a.title,
                    'subject': a.subject.name if a.subject else 'N/A',
                    'due_date': a.due_date,
                    'status': 'Pending'  # Assuming a status field exists
                } for a in upcoming_assignments]
            }

            serializer = StudentDashboardSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"detail": f"Error fetching student dashboard data: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_parent_dashboard_data(self, user, school, base_data):
        from main.models import Student, StudentEnrollment
        
        try:
            parent = user.parent_profile
            children = Student.objects.filter(parent=parent, school=school)
            
            children_data = []
            for child in children:
                current_enrollment = StudentEnrollment.objects.filter(
                    student=child,
                    is_active=True
                ).select_related('class_list').first()
                
                if current_enrollment:
                    children_data.append({
                        'id': child.id,
                        'name': child.user.get_full_name(),
                        'class_name': current_enrollment.class_list.name if current_enrollment.class_list else 'N/A',
                        'class_teacher': current_enrollment.class_list.class_teacher.user.get_full_name() if current_enrollment.class_list and current_enrollment.class_list.class_teacher else 'Not Assigned',
                    })

            data = {
                **base_data,
                'children': children_data
            }

            serializer = ParentDashboardSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"detail": f"Error fetching parent dashboard data: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_upcoming_events(self, school):
        """Helper to get upcoming events for the school"""
        from event.models import Event
        from django.utils import timezone

        try:
            today = timezone.now().date()
            events = Event.objects.filter(
                school=school,
                end_date__gte=today
            ).order_by('start_date')[:5]  # Get next 5 events

            return [{
                'id': e.id,
                'title': e.title,
                'start_date': e.start_date,
                'end_date': e.end_date,
                'description': e.description
            } for e in events]
            
        except Exception:
            return []

    def _get_announcements(self, school):
        """Helper to get recent announcements"""
        from main.models import Announcement
        from django.utils import timezone
        
        try:
            now = timezone.now()
            
            announcements = Announcement.objects.filter(
                is_published=True,
                publish_date__lte=now,
                school=school
            ).filter(
                # Either no expire date or expire_date is in the future
                models.Q(expire_date__isnull=True) | models.Q(expire_date__gte=now.date())
            ).order_by('-publish_date')[:5]  # Get 5 most recent announcements

            return [{
                'id': a.id,
                'title': a.title,
                'content': a.content,
                'publish_date': a.publish_date,
                'expire_date': a.expire_date,
                'created_by': a.created_by.get_full_name() if a.created_by else None
            } for a in announcements]
            
        except Exception:
            return []
