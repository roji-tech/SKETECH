from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from main.models import ClassNote

from django import forms
from django.shortcuts import render, redirect

# class ClassNoteForm(forms.ModelForm):  # ClassNote Form
#     class Meta:
#         model = ClassNote
#         fields = ['school_class', 'lesson_plan',
#                   'title', 'content', 'attachment']
#         widgets = {
#             'title': forms.TextInput(attrs={"placeholder": "Topic Title"}),
#             'content': forms.Textarea(attrs={'rows': 5}),
#             # 'attachment': forms.URLInput(attrs={'placeholder': 'Attach a link to the file'})
#         }


class ClassNoteForm(forms.ModelForm):
    class Meta:
        model = ClassNote
        fields = ['title', 'school_class',
                  'content', 'attachment', 'lesson_plan']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Enter note title',
            }),
            'school_class': forms.Select(attrs={
                'class': 'input',
            }),
            'content': forms.Textarea(attrs={
                'class': 'input',
                'placeholder': 'Enter note content',
                'rows': 5,
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'input',
            }),
            'lesson_plan': forms.Select(attrs={
                'class': 'input',
            }),
        }


def class_note_create(request):
    template_name = 'notes/uploadNote.html'
    if request.method == 'POST':
        form = ClassNoteForm(request.POST, request.FILES)
        form.instance.uploaded_by = request.user
        if form.is_valid():
            form.save()
            # Update to your class note list URL
            return redirect('classnote-list')
    else:
        form = ClassNoteForm()
    return render(request, template_name, {'form': form})


class ClassNoteCreateView(CreateView):  # ClassNote Create View
    model = ClassNote
    form_class = ClassNoteForm
    template_name = 'notes/uploadNote.html'
    success_url = reverse_lazy('classnote-list')

    def post(self, request, *args: str, **kwargs):
        # print(request)
        # print(self.get_form())
        # return super().post(request, *args, **kwargs)

        form = self.get_form()
        print(form.instance)
        print(form.instance)
        print(form.instance)
        if form.is_valid():
            return self.form_valid(form)
        else:
            print(form.errors)
            # return self.form_invalid(form)

    def form_valid(self, form):
        print(form.instance)
        print(form.instance)
        print(form.instance)
        print(form.instance)
        print("form.instance")
        return super().form_valid(form)


class ClassNoteUpdateView(UpdateView):  # ClassNote Update View
    model = ClassNote
    form_class = ClassNoteForm
    template_name = 'note/classnote_form.html'
    success_url = reverse_lazy('classnote-list')


# ClassNote Delete View
class ClassNoteDeleteView(DeleteView):
    model = ClassNote
    template_name = 'notes/classnote_confirm_delete.html'
    success_url = reverse_lazy('classnote-list')


class ClassNoteDetailView(DetailView):  # ClassNote DetailView
    model = ClassNote
    template_name = 'classnote_detail.html'
    context_object_name = 'class_note'


class ClassNoteListView(ListView):  # ClassNote ListView with filters
    model = ClassNote
    template_name = 'notes/notes.html'
    context_object_name = 'class_notes'

    def get_queryset(self):  # Assuming class is passed as a GET param
        school_class = self.request.GET.get('class')
        return ClassNote.filter_by_role(request=self.request)
    # def get_queryset(self):
    #     # Filter class notes by school
    #     return ClassNote.objects.filter(school_class__school=self.request.user.school)


# def upload_lesson_plan(request, pk):
#     lesson_plan = get_object_or_404(LessonPlan, pk=pk)
#     if request.method == "POST":

#         form = LessonPlanForm(request.POST, request.FILES,
#                               instance=lesson_plan)
#         if form.is_valid():
#             lesson_plan_instance = form.save(commit=False)
#             lesson_plan_instance.uploaded_by = request.user
#             lesson_plan_instance.save()
#             return redirect("lessons_lists")

#     else:

#         form = LessonPlanForm(instance=lesson_plan)
#         return render(
#             request,
#             "staff/lessonplan/edit-lesson-note.html",
#             {"form": form, "lesson_plan": lesson_plan},
#         )


# def lessons_list(request):
#     lesson_plans = LessonPlan.objects.all()
#     return render(
#         request, "staff/notes/lessonNoteList.html", {
#             "lesson_plans": lesson_plans}
#     )
