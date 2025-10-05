from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404

# Create your views here.


from django import forms
from main import mydecorators
from .models import Complaint


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'Enter complaint subject'}),
            'description': forms.Textarea(attrs={'placeholder': 'Describe the issue'}),
        }


@mydecorators.admin_is_authenticated
def submit_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user  # Associate complaint with the logged-in admin
            complaint.save()
            return redirect('complaints')
    else:
        form = ComplaintForm()

    complaints = Complaint.objects.all()
    return render(request, 'report/submit_complaint.html', {'form': form, "complaints": complaints})


@mydecorators.admin_is_authenticated
def update_complaint(request, pk):
    print(type(pk))
    instance = get_object_or_404(Complaint, pk=pk)

    form = ComplaintForm(instance=instance)
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            print(complaint.user)
            print(complaint.user_id)
            print(dir(complaint))

            if not complaint.instance.user:
                complaint.instance.user = request.user  # Associate complaint with the logged-in admin

            complaint.save()
            return redirect('complaints')
    else:
        form = ComplaintForm(instance=instance)

    complaints = Complaint.objects.all()
    return render(request, 'report/submit_complaint.html', {'form': form, "complaints": complaints})
