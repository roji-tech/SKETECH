import django.db
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, SlidingToken, Token, UntypedToken

from main.models import STAFF, STUDENT
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.settings import api_settings

from main.models import User, School, Staff, ClassList, AcademicSession, Term, LessonPlan, Subject, Student
from main.models import School
from main.tenancy.threadlocals import get_current_school
import logging
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name',
                  'gender', 'email', 'phone', 'image']


class ClassListSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(
        source='get_name_display', read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True)
    # class_capacity = serializers.SerializerMethodField(method_name='get_class_capacity')

    class Meta:
        model = ClassList
        fields = [
            'id',
            'name',
            'name_display',
            'division',
            'category',
            'class_capacity',
            'category_display',
            'academic_session',
            'class_teacher',
        ]


class SchoolSerializer(serializers.ModelSerializer):
    #   classes = ClassListSerializer(read_only=True, many=True)
    # owner = UserSerializer()

    class Meta:
        model = School
        fields = ['id', 'name', 'address', 'phone', 'email',
                  'logo', "short_name", "code", "website", "motto", "about",]


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ['academic_session', 'name', 'start_date', 'end_date']

        def create(self, validated_data):
            academic_session_id = self.context['academic_session_id']
            return Term.objects.create(academic_session_id=academic_session_id, **validated_data)


class AcademicSessionSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    terms = TermSerializer(read_only=True, many=True)

    class Meta:
        model = AcademicSession
        fields = ['id', 'name', 'school', 'start_date', 'terms',
                  'end_date', 'is_current', 'next_session_begins']
        read_only_fields = ['name', 'is_current', 'school_name']

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

        # def get_school(self, obj):
        #   return str(obj.school.name)


# class CreateStaffSerializer(serializers.Serializer):
#     user_id = serializers.IntegerField()
#     school_id = serializers.IntegerField()
#     department = serializers.CharField(
#         max_length=24, required=False, allow_blank=True)

#     def validate_user_id(self, value):
#         try:
#             user = User.objects.get(id=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError(
#                 'User with this id does not exit')
#         return value

#     def validate_school_id(self, value):
#         try:
#             school = School.objects.get(id=value)
#         except School.DoesNotExist:
#             raise serializers.ValidationError(
#                 'School with this id does not exit')
#         return value

#     def create(self, validated_data):
#         user = User.objects.get(id=validated_data['user_id'])
#         school = School.objects.get(id=validated_data['school_id'])
#         department = validated_data.get('department', '')

#         teacher = Teacher.objects.create(
#             user=user,
#             school=school,
#             department=department
#         )
#         return teacher

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['name', 'teacher']


class LessonPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonPlan
        fields = ['title', 'school_class', 'subject',
                  'uploaded_file', 'uploaded_by']


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    # full_name = serializers.SerializerMethodField(
    #     method_name='get_student_full_name')

    class Meta:
        model = Student
        fields = ['user', 'reg_no', 'school', 'session_admitted', "date_of_birth"]


class StudentCreateSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    session_admitted = serializers.SerializerMethodField(
        method_name='get_formatted_admission_date')

    class Meta:
        model = Student
        fields = ['user', 'reg_no', 'session_admitted', "date_of_birth"]

    def create(self, validated_data):
        school = get_current_school()
        try:
            with transaction.atomic():
                print(school)

                user_data = validated_data.pop('user')
                user_data['role'] = STUDENT
                user_data['school'] = school
                user = User(**user_data)
                user.username = User.get_username(user_data.get('email'))
                user.set_password(str(user.last_name).lower())
                user.save()

                validated_data['school'] = school
                validated_data['user'] = user
                student = Student(**validated_data)
                student.save()
            return student
        except Exception as e:
            print("\n\n\n\nException in StudentCreateSerializer.create:", e)
            raise serializers.ValidationError(str(e))

    def validate(self, attrs):
        try:
            print("\n\n\n\n attrs in StudentCreateSerializer.validate:", attrs)
            return super().validate(attrs)
        except Exception as e:
            print("\n\n\n\nException in StudentCreateSerializer.validate:", e)
            raise serializers.ValidationError(str(e))

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save()
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    def get_student_full_name(self, obj):
        return obj.get_full_name()

    def get_formatted_admission_date(self, obj):
        try:
            return obj.session_admitted.strftime('%d-%b-%Y')
        except:
          return None

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    is_teaching_staff = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = Staff
        fields = ['id', 'user', 'department', 'is_teaching_staff']

    def create(self, validated_data):
        try:
            print(Staff.objects.values("user", "user__email"))
            with transaction.atomic():
                school = get_current_school()
                user_data = validated_data.pop('user', {})

                # Validate required fields
                required_fields = ['email', 'first_name', 'last_name']
                for field in required_fields:
                    if field not in user_data or not user_data[field]:
                        raise serializers.ValidationError({field: f"This field is required."})

                # Create user
                user_data['role'] = STAFF
                if school:
                    user_data['school'] = school

                user = User(
                    username=User.get_username(user_data.get('email')),
                    email=user_data.get('email'),
                    role=STAFF,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    gender=user_data.get('gender', 'M'),
                    phone=user_data.get('phone', ''),
                    image=user_data.get('image'),
                    school=school
                )
                user.set_password(user_data.get('password', 'password123'))
                user.save()

                # Create staff
                staff = Staff(
                    user=user,
                    school_id=school.id,
                    department=validated_data.get('department', ''),
                    is_teaching_staff=validated_data.get('is_teaching_staff', False),
                    school=school
                )
                try:
                    staff.save()
                    return staff
                except Exception as e:
                    print(f"Error creating staff: {str(e)}")
                    logger.error(f"Error creating staff: {str(e)}")
                    raise serializers.ValidationError({"error": str(e)})
                
        except django.db.IntegrityError as e:
            if 'duplicate key' in str(e).lower():
                raise serializers.ValidationError({"email": "A user with this email already exists."})
            raise serializers.ValidationError({"error": "Database error occurred. Please try again."})
            
        except Exception as e:
            print(f"Error creating staff: {str(e)}")
            logger.error(f"Error creating staff: {str(e)}")
            raise serializers.ValidationError({"error": str(e)})

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Update user fields
        for field, value in user_data.items():
            if field == 'password' and value:
                user.set_password(value)
            elif field != 'password':
                setattr(user, field, value)
        user.save()

        # Update staff fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        return instance
