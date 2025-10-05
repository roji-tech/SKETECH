from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView


from django import forms
from main.models import LessonPlan, ClassNote


class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = ['title', 'school_class', 'subject', 'uploaded_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Lesson Plan Title'
            }),
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'uploaded_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }),
        }


class ClassNoteForm(forms.ModelForm):
    class Meta:
        model = ClassNote
        fields = ['lesson_plan', 'title',
                  'school_class', 'content', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Class Note Title'
            }),
            'lesson_plan': forms.Select(attrs={'class': 'form-control'}),
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Class Note Content'
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }),
        }


# Lesson Plan Views


class LessonPlanListView(ListView):
    model = LessonPlan
    template_name = 'lesson_plan/lesson_plan_list.html'
    context_object_name = 'lesson_plans'


class LessonPlanDetailView(DetailView):
    model = LessonPlan
    template_name = 'lesson_plan/lesson_plan_detail.html'
    context_object_name = 'lesson_plan'


# class LessonPlanCreateView(CreateView):
#     model = LessonPlan
#     form_class = LessonPlanForm
#     template_name = 'lesson_plan/lesson_plan_form.html'
#     success_url = reverse_lazy('lesson_plan_list')


# class LessonPlanUpdateView(UpdateView):
#     model = LessonPlan
#     form_class = LessonPlanForm
#     template_name = 'lesson_plan/lesson_plan_form.html'
#     success_url = reverse_lazy('lesson_plan_list')


# class LessonPlanDeleteView(DeleteView):
#     model = LessonPlan
#     template_name = 'lesson_plan/lesson_plan_confirm_delete.html'
#     success_url = reverse_lazy('lesson_plan_list')

# ClassNote Views


# class ClassNoteListView(ListView):
#     model = ClassNote
#     template_name = 'class_note/class_note_list.html'
#     context_object_name = 'class_notes'


# class ClassNoteDetailView(DetailView):
#     model = ClassNote
#     template_name = 'class_note/class_note_detail.html'
#     context_object_name = 'class_note'


# class ClassNoteCreateView(CreateView):
#     model = ClassNote
#     form_class = ClassNoteForm
#     success_url = reverse_lazy('class_note_list')


# class ClassNoteUpdateView(UpdateView):
#     model = ClassNote
#     form_class = ClassNoteForm
#     template_name = 'class_note/class_note_form.html'
#     success_url = reverse_lazy('class_note_list')


# class ClassNoteDeleteView(DeleteView):
#     model = ClassNote
#     template_name = 'class_note/class_note_confirm_delete.html'
#     success_url = reverse_lazy('class_note_list')


class StaffHome(View):
    def get(self, request, *args, **kwargs):
        # Custom logic here
        return render(request, "staff/index.html")


"""LessonPlan Views"""


"""Notes Views"""


def add_notes(request):
    return render(request, "staff/notes/TeachersNote.html")


def upload_notes(request):
    return render(request, "staff/notes/uploadNote.html")


"""Examination Views"""


def view_examination(request):
    return render(request, "staff/exam/examinations.html")


# """Assignments Views"""

# def continous_assessment_view(request):
#     if request.method == 'POST':
#         form = ContinuousAssessmentForm(request.POST, request.FILES)
#         if form.is_valid():
#             assessment = form.save(commit=False)
#             assessment.uploaded_by = request.user.teacher
#             assessment.save()
#             return redirect('assessment-list')
#     else:
#         form = ContinuousAssessmentForm()

#     assessments = ContinuousAssessment.objects.filter(uploaded_by=request.user.teacher)

#     return render(request, 'staff/homework/homework.html', {'form' : form, 'assessments': assessments})

# def edit_continous_assessnent(request, pk):
#     assessment = ContinuousAssessment.objects.get(uploaded_by=request.user.teacher, pk=pk)
#     if request.method == 'POST':
#         form = ContinuousAssessmentForm(request.POST, request.FILES, instance=assessment)
#         if form.is_valid():
#             form.save()
#             return redirect('assessment-list')
#     else:
#         form = ContinuousAssessmentForm()
#     return render(request, 'staff/homework/homework.html', {'form' : form, 'assessment' : assessment})


def add_assignments(request):
    return render(request, "staff/homework/homework.html")


"""results Views"""


def results_list(request):
    return render(request, "staff/results/results.html")
