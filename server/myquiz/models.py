from django.db import models
from django.conf import settings
from main.models import User, AcademicSession, Term, ClassList, Student, Subject

# Define your existing models like ClassList, AcademicSession, etc.


class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = [
        ('homework', 'Homework'),
        ('ca', 'Continuous Assessment'),
        ('exam', 'Exam'),
    ]
    title = models.CharField(max_length=100)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPE_CHOICES)
    school_class = models.ForeignKey(ClassList, on_delete=models.CASCADE)
    term = models.ForeignKey(Term,  on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject,  on_delete=models.CASCADE)
    created_by: User = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ["teacher"]},
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def academic_session(self) -> AcademicSession:
        return self.term.academic_session

    def __str__(self):
        return f"{self.title} - {self.school_class.name} ({self.quiz_type})"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=200)
    option_1 = models.CharField(max_length=200, default="")
    option_2 = models.CharField(max_length=200, default="")
    option_3 = models.CharField(max_length=200, default="")
    option_4 = models.CharField(max_length=200, default="")
    option_5 = models.CharField(max_length=200, default="")
    option_6 = models.CharField(max_length=200, default="")
    correct_answer = models.CharField(max_length=200)
    exclude = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to='quiz_images/%Y/%m/%d/', null=True, blank=True)

    def __str__(self):
        return self.question_text


class QuestionBank(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='question_bank')
    question_text = models.TextField()
    image = models.ImageField(
        upload_to='question_bank_images/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return f"Question for {self.subject.name}"


class StudentAnswer(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=200, default="")

    def is_correct(self):
        return self.selected_option == self.question.correct_answer


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.DecimalField(decimal_places=1, default=0.0, max_digits=5)

    def __str__(self):
        return f'{self.student} - {self.quiz.title}: {self.score}'

    def calculate_total_score(self):
        total_questions = self.quiz.questions.count()
        correct_answers = sum(
            1 for answer in self.studentanswer_set.all() if answer.is_correct()
        )
        self.score = (correct_answers / total_questions) * 100
        self.save()


class TermResult(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="term_result")
    school_class = models.ForeignKey(ClassList, on_delete=models.CASCADE)
    term = models.ForeignKey(Term,  on_delete=models.CASCADE)
    academic_session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE)
    total_score = models.FloatField()

    def calculate_term_total(self):
        quizzes = Quiz.objects.filter(
            school_class=self.school_class, term=self.term, academic_session=self.academic_session
        )
        total_score = sum(
            Result.objects.filter(quiz=quiz, student=self.student).first().score for quiz in quizzes
        )
        self.total_score = total_score / len(quizzes)  # Average score
        self.save()


class SessionResult(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="session_result")
    school_class = models.ForeignKey(ClassList, on_delete=models.CASCADE)
    academic_session = models.ForeignKey(
        AcademicSession, on_delete=models.CASCADE)
    total_score = models.FloatField()

    def calculate_session_total(self):
        terms = ['1st', '2nd', '3rd']
        term_results = TermResult.objects.filter(
            student=self.student, school_class=self.school_class, academic_session=self.academic_session
        )
        self.total_score = sum(
            term.total_score for term in term_results) / len(terms)
        self.save()


# class CardPin(model)
