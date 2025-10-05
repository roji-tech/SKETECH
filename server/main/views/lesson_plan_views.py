# from .views import (
#     GmeetClassListView, GmeetClassDetailView, GmeetClassCreateView, GmeetClassUpdateView, GmeetClassDeleteView,
#     LessonPlanListView, LessonPlanDetailView, LessonPlanCreateView, LessonPlanUpdateView, LessonPlanDeleteView,
#     ClassNoteListView, ClassNoteDetailView, ClassNoteCreateView, ClassNoteUpdateView, ClassNoteDeleteView
# )
from django.views.generic import ListView, DetailView
# from .forms import GmeetClassForm, LessonPlanForm, ClassNoteForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from main.models import GmeetClass, School, LessonPlan, ClassNote


from django import forms


class LessonPlanForm(forms.ModelForm):  # LessonPlan Form
    class Meta:
        model = LessonPlan
        fields = ['school_class', 'subject', 'title', 'uploaded_file']
        widgets = {
            'uploaded_file': forms.ClearableFileInput(attrs={'accept': 'application/pdf,application/msword'})
        }


class LessonPlanCreateView(CreateView):  # LessonPlan Create View
    model = LessonPlan
    form_class = LessonPlanForm
    template_name = 'lessonplan/lessonplan_create.html'
    success_url = reverse_lazy('list-lessonplans')

    def get_queryset(self):
        return LessonPlan.filter_by_role(self.request)

    def form_valid(self, form):
        # Set the uploader as the current user
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)


class LessonPlanUpdateView(UpdateView):  # LessonPlan Update View
    model = LessonPlan
    form_class = LessonPlanForm
    template_name = 'lessonplan/lessonplan_create.html'
    success_url = reverse_lazy('list-lessonplans')

    def get_queryset(self):
        return LessonPlan.filter_by_role(self.request)


class LessonPlanDeleteView(DeleteView):  # LessonPlan Delete View
    model = LessonPlan
    template_name = 'lessonplan/lessonplan_confirm_delete.html'
    success_url = reverse_lazy('list-lessonplans')


class LessonPlanListView(ListView):  # LessonPlan ListView with filters
    model = LessonPlan
    template_name = 'lessonplan/lessonplan_list.html'
    context_object_name = 'lesson_plans'

    def get_queryset(self):
        return LessonPlan.filter_by_role(self.request)


class LessonPlanDetailView(DetailView):  # LessonPlan DetailView
    model = LessonPlan
    template_name = 'lessonplan_detail.html'
    context_object_name = 'lesson_plan'
