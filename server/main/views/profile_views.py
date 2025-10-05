
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django import forms
from main.models import School, User, Staff, Student


# class EditProfileForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['phone', 'gender', 'image']
#         widgets = {
#             'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
#             'gender': forms.Select(attrs={'class': 'form-control'}),
#             'image': forms.ClearableFileInput(),
#         }


# class TeacherProfileForm(EditProfileForm):
#     class Meta(EditProfileForm.Meta):
#         model = User
#         fields = EditProfileForm.Meta.fields + ['teacher_profile__department']


# class StudentProfileForm(EditProfileForm):
#     class Meta(EditProfileForm.Meta):
#         model = User
#         fields = EditProfileForm.Meta.fields + \
#             ['student_profile__reg_no', 'student_profile__date_of_birth']


@login_required
def edit_profile(request):
    user = request.user

    # if user.is_teacher:
    #     form_class = TeacherProfileForm
    # elif user.is_student:
    #     form_class = StudentProfileForm
    # else:
    #     form_class = EditProfileForm

    # if request.method == 'POST':
    #     form = form_class(request.POST, request.FILES, instance=user)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(
    #             request, 'Your profile has been updated successfully!')
    #         return redirect('profile_settings')
    #     else:
    #         messages.error(request, 'Please correct the errors below.')
    # else:
    #     form = form_class(instance=user)

    return render(request, 'edit_profile.html', {'form': "form"})


def profile_settings(request):
    user = request.user
    user.school = School.get_user_school(request.user)
    print(user.school)
    return render(request, 'profile.html', {'user': user})
