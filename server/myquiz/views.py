from django.forms import modelformset_factory
from .forms import QuestionFormSet
from .models import Question
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from main import mydecorators
from main.models import Student

from .forms import QuizForm, QuestionForm
from .models import Quiz, Question, QuestionBank, StudentAnswer, Result
from django.db import models

from django.http import JsonResponse, HttpResponse


from django.views.generic import DetailView


class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quiz/quiz_detail.html'
    context_object_name = 'quiz'


@mydecorators.teacher_is_authenticated
def create_quiz(request):
    if request.method == "POST":
        quiz_form = QuizForm(request.POST, request=request)
        if quiz_form.is_valid():
            quiz = quiz_form.save(commit=False)
            # Assuming Teacher has a relation to User
            quiz.created_by = request.user
            quiz.save()
            return redirect('add-question', quiz_id=quiz.id)
    else:
        quiz_form = QuizForm(request=request)

    return render(request, 'quiz/quiz_form.html', {'form': quiz_form})


@mydecorators.teacher_is_authenticated
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Initialize the formset, allowing up to 5 questions to be added at once
    QuestionFormSet = modelformset_factory(
        Question, form=QuestionForm, extra=5, can_delete=True)

    if request.method == 'POST':
        formset = QuestionFormSet(
            request.POST, request.FILES, queryset=Question.objects.none())
        if formset.is_valid():
            # Save each form in the formset, linking it to the specific quiz
            instances = formset.save(commit=False)
            for instance in instances:
                instance.quiz = quiz
                instance.save()
            messages.success(request, 'Questions added successfully!')
            # Redirect to quiz detail view or any desired page
            return redirect('quiz_detail', pk=quiz.id)
        else:
            print(formset.errors)
            messages.error(
                request, 'There was an error adding the questions. Please try again.')
    else:
        formset = QuestionFormSet(queryset=Question.objects.none())

    return render(request,  'quiz/add_questions.html',  {
        'quiz': quiz,
        'formset': formset,
    })


# @mydecorators.teacher_is_authenticated
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
        correct_answers = 0
        total_questions = questions.count()

        for question in questions:
            selected_option = request.POST.get(str(question.id))
            if selected_option == question.correct_option:
                correct_answers += 1

        # Calculate the score
        score = (correct_answers / total_questions) * 100

        # Save the result for the student
        Result.objects.create(
            student=request.user.student,  # Assuming the student is related to the user
            quiz=quiz,
            score=score,
            term=quiz.term,
            session = quiz.term.session if quiz.term else "2023-2024"  # Replace with actual logic

        )

        return redirect('quiz_result', score=score)

    return render(request, 'quiz/take_quiz.html', {'quiz': quiz, 'questions': questions})


# @mydecorators.teacher_is_authenticated
def quiz_result(request, score):
    """
    View to display the quiz result after a student completes a quiz.
    """
    return render(request, 'quiz/quiz_result.html', {'score': score})


@mydecorators.student_is_authenticated
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    # Assuming a reverse relationship exists for the Student model
    student = Student.objects.get(user=request.user)

    # Check quiz start and end time
    now = timezone.now()
    if quiz.start_date and now < quiz.start_date:
        return render(request, 'quiz/not_started.html', {'quiz': quiz})
    if quiz.end_date and now > quiz.end_date:
        return render(request, 'quiz/expired.html', {'quiz': quiz})

    # Get questions
    questions = quiz.questions.all()

    if request.method == 'POST':
        selected_option = request.POST.get('selected_option')
        question_id = request.POST.get('question_id')
        question = get_object_or_404(Question, id=question_id)

        # Save student's answer
        student_answer, created = StudentAnswer.objects.get_or_create(
            student=student,
            question=question
        )
        student_answer.selected_option = selected_option
        student_answer.save()

        # Calculate and update result for the student
        total_questions = quiz.questions.count()
        correct_answers = StudentAnswer.objects.filter(
            student=student, question__quiz=quiz, selected_option=models.F(
                'question__correct_answer')
        ).count()
        score = (correct_answers / total_questions) * 100

        result, created = Result.objects.get_or_create(
            student=student,
            quiz=quiz
        )
        result.score = score
        result.save()

        # Redirect to next question or result page
        next_question = questions.exclude(id=question.id).first()
        if next_question:
            return redirect('take_quiz', quiz_id=quiz_id)
        else:
            return redirect('quiz_result', quiz_id=quiz_id)

    return render(request, 'quiz/take_quiz.html', {
        'quiz': quiz,
        'questions': questions
    })


@mydecorators.teacher_is_authenticated
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    results = Result.objects.filter(quiz=quiz)

    return render(request, 'quiz/quiz_result.html', {
        'quiz': quiz,
        'results': results
    })
