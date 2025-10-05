

from django.forms import modelformset_factory
from django import forms
from .models import Quiz, Question, AcademicSession, Term
from main.models import School


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'quiz_type', 'school_class',
                  'subject', 'start_date', 'end_date', 'term']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Get the current user's school
        school = School.get_user_school(request.user)

        if school:
            # Get the current academic session for the school
            current_session = AcademicSession.objects.filter(
                school=school, is_current=True).first()

            if current_session:
                # Get the current term in the current session
                current_term = Term.objects.filter(
                    academic_session=current_session).order_by('-start_date').first()

                # Set the current term as the default value for the 'term' field
                if current_term:
                    self.fields['term'].initial = current_term


# class QuestionForm(forms.ModelForm):
#     class Meta:
#         model = Question
#         fields = ['question_text', 'image', 'option_1',
#                   'option_2', 'option_3', 'option_4', 'correct_answer']

#     option_3 = forms.CharField(required=False)
#     option_4 = forms.CharField(required=False)

#     # def clean_correct_answer(self):
#     #     correct_answer = self.cleaned_data.get('correct_answer')
#     #     options = [
#     #         self.cleaned_data.get('option_1'),
#     #         self.cleaned_data.get('option_2'),
#     #         self.cleaned_data.get('option_3'),
#     #         self.cleaned_data.get('option_4')
#     #     ]
#     #     if correct_answer not in options:
#     #         raise forms.ValidationError(
#     #             "The correct answer must be one of the options provided.")
#     #     return correct_answer


#     class Meta:
#         model = Question
#         fields = ['question_text', 'image', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_answer']

#     def clean(self):
#         cleaned_data = super().clean()
#         correct_answer = cleaned_data.get('correct_answer')
#         options = [
#             cleaned_data.get('option_1'),
#             cleaned_data.get('option_2'),
#         ]

#         # Include optional options if they are provided
#         option_3 = cleaned_data.get('option_3')
#         option_4 = cleaned_data.get('option_4')
#         if option_3:
#             options.append(option_3)
#         if option_4:
#             options.append(option_4)

#         # Ensure that at least two options are provided
#         if not all(options[:2]):
#             raise forms.ValidationError("At least two options are required.")

#         # Ensure the correct answer is one of the provided options
#         if correct_answer not in options:
#             raise forms.ValidationError("The correct answer must be one of the provided options.")

#         return cleaned_data


class QuestionForm(forms.ModelForm):
    option_3 = forms.CharField(required=False, initial="")
    option_4 = forms.CharField(required=False, initial="")
    option_5 = forms.CharField(required=False, initial="")
    option_6 = forms.CharField(required=False, initial="")

    class Meta:
        model = Question
        fields = ['question_text', 'image', 'option_1',
                  'option_2', 'option_3', 'option_4',
                  'option_5', 'option_6', 'correct_answer']
        widgets = {
            'correct_answer': forms.TextInput(attrs={
                'class': 'correct_answer',
                'required': 'required',
                "type": "hidden"
            }),
        }
        labels = {
            'option_1': 'A',
            'option_2': 'B',
            'option_3': 'C',
            'option_4': 'D',
            'option_5': 'E',
            'option_6': 'F',
        }

    def clean(self):
        cleaned_data = super().clean()
        print(cleaned_data)
        correct_answer = cleaned_data.get('correct_answer')
        option_1 = cleaned_data.get('option_1')
        option_2 = cleaned_data.get('option_2')
        option_3 = cleaned_data.get('option_3')
        option_4 = cleaned_data.get('option_4')
        option_5 = cleaned_data.get('option_5')
        option_6 = cleaned_data.get('option_6')

        options = [option_1, option_2]
        if option_3:
            options.append(option_3)
        if option_4:
            options.append(option_4)
        if option_5:
            options.append(option_5)
        if option_6:
            options.append(option_6)
        # Ensure at least two options are provided
        if len([opt for opt in options if opt != None and str(opt).strip()]) < 2:
            raise forms.ValidationError("At least two options are required.")

        # Ensure the correct answer is one of the provided options
        if correct_answer not in options:
            raise forms.ValidationError(
                "The correct answer must be one of the provided options.")

        return cleaned_data


QuestionFormSet = modelformset_factory(Question, fields=(
    'question_text', 'option_1', 'option_2', 'option_3',
    'option_4',  'option_5', 'option_6', 'correct_answer'), extra=5)
