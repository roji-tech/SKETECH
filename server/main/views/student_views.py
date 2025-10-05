from ..models.models import ClassNote, GmeetClass, Student
from main.models import Student, ClassNote, GmeetClass
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView
from main import mydecorators
from pprint import pprint

# class StudentsLogin(View):
#     def get(self, request, *args, **kwargs):
#         return render(request, "staff/students-login.html")

#     def post(self, request, *args, **kwargs):
#         print(request.POST)
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = authenticate(request, username=username, password=password)
#         print(user, username, password)

#         if user is not None:
#             print(user)
#             login(request, user)
#             return redirect('myadmin')
#         else:
#             messages.error(request, 'Invalid username or password')

#         return render(request, "myadmin/login.html")


@mydecorators.student_is_authenticated
class StudentsHome(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        student_info = Student.objects.get(user=request.user)
        user.student = student_info
        pprint(user)
        # Custom logic here
        return render(request, "students/index.html", {"user": user})


class StudentGoogleMeetListView(ListView):
    model = GmeetClass
    template_name = "students/inner/students-gmeet-list.html"
    context_object_name = "gmeets"


class StudentClassNoteListView(ListView):
    model = ClassNote
    template_name = "students/inner/students-class-note.html"
    context_object_name = "notes"


@mydecorators.student_is_authenticated
def class_list_view(request):
    if request.user.is_student:
        student = request.user.student_profile
        student_class = student.student_class

    all_classmates = Student.objects.filter(
        student_class=student_class
    ).order_by("reg_no")
    return render(
        request,
        "students/inner/view_class.html",
        {"all_classmates": all_classmates, "class_name": student_class.name,
            "division": student_class.division},
    )


def e_exam(request):
    return render(request, "students/inner/e-exam.html")


def exam_quiz(request):
    return render(request, "students/inner/exam.html")
