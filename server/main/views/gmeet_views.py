from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from main.models import GmeetClass, Subject

from django import forms
from main import mydecorators


class GmeetClassForm(forms.ModelForm):  # GmeetClass Form
    class Meta:
        model = GmeetClass
        fields = ["title", 'subject', 'description',
                  'gmeet_link', 'start_time', 'duration']
        widgets = {
            'title': forms.TextInput(attrs={'type': 'text', 'class': 'input', 'required': 'false', 'id': "meeting-title", 'placeholder': "Meeting Title"}),
            'subject': forms.Select(attrs={'class': 'input'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'input', 'required': 'true'}),
            'duration': forms.NumberInput(attrs={'type': 'text', 'class': 'input', 'placeholder': 'Duration in minutes 00:00:00', 'required': 'true', 'min': 0}),            'gmeet_link': forms.URLInput(attrs={'class': 'input', 'placeholder': 'Link'}),
            'description': forms.Textarea(attrs={'class': 'input', 'placeholder': 'Description', 'required': 'false', 'rows': 5}),

            #     <div class="inline-f">
            #     <label for="duration" class="label">Duration</label>
            #     <input type="text" name="duration" value="00:00:07" id="id_duration">
            #   </div>
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pop user from kwargs
        self.user = user
        super(GmeetClassForm, self).__init__(*args, **kwargs)

        # self.fields["created_by"].value = user
        if user and user.is_teacher:
            # Filter subjects based on the logged-in teacher
            self.fields['subject'].queryset = Subject.objects.filter(
                teacher=user.teacher_profile)
        else:
            # Show all subjects for admins or other users
            self.fields['subject'].queryset = Subject.objects.all()

# Gmeet Classes
# Gmeet Classes
# Gmeet Classes
# Gmeet Classes
# Gmeet Classes
# Gmeet Classes


class ClassFormView:
    def form_valid(self, form):
        # Set the created_by field to the logged-in user
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass the user to the form
        return kwargs


@mydecorators.is_authenticated
class GmeetClassListView(ListView):  # GmeetClass ListView
    model = GmeetClass
    template_name = 'gmeet/gmeet_list.html'
    context_object_name = 'gmeet_classes'

    def get_queryset(self):  # Filter the Gmeet classes based on the school or user criteria
        qs = GmeetClass.filter_by_role(self.request)
        print(qs)
        return qs


@mydecorators.is_authenticated
class GmeetClassDetailView(DetailView):  # GmeetClass DetailView
    model = GmeetClass
    template_name = 'gmeetclass_detail.html'
    context_object_name = 'gmeet_class'


@mydecorators.is_authenticated
class GmeetClassCreateView(ClassFormView, CreateView):  # GmeetClass Create View
    model = GmeetClass
    form_class = GmeetClassForm
    template_name = 'gmeet/gmeet_create.html'
    success_url = reverse_lazy('gmeetclass-list')


@mydecorators.is_authenticated
class GmeetClassUpdateView(ClassFormView, UpdateView):  # GmeetClass Update View
    model = GmeetClass
    form_class = GmeetClassForm
    template_name = 'gmeet/gmeet_create.html'
    success_url = reverse_lazy('gmeetclass-list')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        print(kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form(self, form_class=None):
        print(self.__class__, self.form_class(**self.get_form_kwargs()))

        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())


@mydecorators.is_authenticated
class GmeetClassDeleteView(DeleteView):  # GmeetClass Delete View
    model = GmeetClass
    template_name = 'gmeet/gmeetclass_confirm_delete.html'
    success_url = reverse_lazy('gmeetclass-list')


# """Google Meet Views"""


# def add_gmeet(request):
#     if request.method == "POST":
#         form = GoogleMeetForm(request.POST)
#         if form.is_valid():
#             form.save(commit=False)
#             form.created_by = request.user
#             messages.success(request, "Google Meet Session added successfully")
#             return redirect("staff")

#     form = GoogleMeetForm()
#     return render(request, "staff/gmeet/upload-gmeet.html", {"form": form})


# def staff_edit_gmeet(request, pk):
#     gmeets = get_object_or_404(GmeetClass, pk=pk)
#     if request.method == "POST":
#         form = GoogleMeetForm(request.POST, instance=gmeets)
#         if form.is_valid():
#             form.save()
#             messages.success(
#                 request, "Google Meet Session updated successfully")
#             return redirect("staff")

#     form = GoogleMeetForm(instance=gmeets)
#     return render(
#         request, "staff/gmeet/gmeets.html", {"form": form, "gmeets": gmeets}
#     )
