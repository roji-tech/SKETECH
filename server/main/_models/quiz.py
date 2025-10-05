

import re
import json

from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import (
    MaxValueValidator,
    validate_comma_separated_integer_list,
)
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.conf import settings
from django.db.models.signals import pre_save

from django.db.models import Q

from main.quiz.utils import unique_slug_generator
from model_utils.managers import InheritanceManager
from course.models import Course
from ..utils import *

CHOICE_ORDER_OPTIONS = (
    ("content", _("Content")),
    ("random", _("Random")),
    ("none", _("None")),
)

CATEGORY_OPTIONS = (
    ("assignment", _("Assignment")),
    ("exam", _("Exam")),
    ("practice", _("Practice Quiz")),
)


class QuizManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(category__icontains=query)
                | Q(slug__icontains=query)
            )
            qs = qs.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return qs


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    title = models.CharField(verbose_name=_(
        "Title"), max_length=60, blank=False)

    slug = models.SlugField(blank=True, unique=True)
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        help_text=_("A detailed description of the quiz"),
    )
    category = models.TextField(choices=CATEGORY_OPTIONS, blank=True)
    random_order = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_("Random Order"),
        help_text=_(
            "Display the questions in a random order or as they are set?"),
    )

    # max_questions = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Max Questions"),
    #     help_text=_("Number of questions to be answered on each attempt."))

    answers_at_end = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_("Answers at end"),
        help_text=_(
            "Correct answer is NOT shown after question. Answers displayed at the end."
        ),
    )

    exam_paper = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_("Exam Paper"),
        help_text=_(
            "If yes, the result of each attempt by a user will be stored. Necessary for marking."
        ),
    )

    single_attempt = models.BooleanField(
        blank=False,
        default=False,
        verbose_name=_("Single Attempt"),
        help_text=_("If yes, only one attempt by a user will be permitted."),
    )

    pass_mark = models.SmallIntegerField(
        blank=True,
        default=50,
        verbose_name=_("Pass Mark"),
        validators=[MaxValueValidator(100)],
        help_text=_("Percentage required to pass exam."),
    )

    draft = models.BooleanField(
        blank=True,
        default=False,
        verbose_name=_("Draft"),
        help_text=_(
            "If yes, the quiz is not displayed in the quiz list and can only be taken by users who can edit quizzes."
        ),
    )

    timestamp = models.DateTimeField(auto_now=True)

    objects = QuizManager()

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.single_attempt is True:
            self.exam_paper = True

        if self.pass_mark > 100:
            raise ValidationError("%s is above 100" % self.pass_mark)
        if self.pass_mark < 0:
            raise ValidationError("%s is below 0" % self.pass_mark)

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()

    def get_absolute_url(self):
        # return reverse('quiz_start_page', kwargs={'pk': self.pk})
        return reverse("quiz_index", kwargs={"slug": self.course.slug})


def quiz_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator()(instance)


pre_save.connect(quiz_pre_save_receiver, sender=Quiz)


class ProgressManager(models.Manager):
    def new_progress(self, user):
        new_progress = self.create(user=user, score="")
        new_progress.save()
        return new_progress


class Progress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )
    score = models.CharField(
        max_length=1024,
        verbose_name=_("Score"),
        validators=[validate_comma_separated_integer_list],
    )

    objects = ProgressManager()

    class Meta:
        verbose_name = _("User Progress")
        verbose_name_plural = _("User progress records")

    # @property
    def list_all_cat_scores(self):
        score_before = self.score
        output = {}

        if len(self.score) > len(score_before):
            # If a new category has been added, save changes.
            self.save()

        return output

    def update_score(self, question, score_to_add=0, possible_to_add=0):
        # category_test = Category.objects.filter(category=question.category).exists()

        if any(
            [
                item is False
                for item in [
                    score_to_add,
                    possible_to_add,
                    isinstance(score_to_add, int),
                    isinstance(possible_to_add, int),
                ]
            ]
        ):
            return _("error"), _("category does not exist or invalid score")

        to_find = re.escape(str(question.quiz)) + \
            r",(?P<score>\d+),(?P<possible>\d+),"

        match = re.search(to_find, self.score, re.IGNORECASE)

        if match:
            updated_score = int(match.group("score")) + abs(score_to_add)
            updated_possible = int(match.group(
                "possible")) + abs(possible_to_add)

            new_score = ",".join(
                [str(question.quiz), str(updated_score),
                 str(updated_possible), ""]
            )

            # swap old score for the new one
            self.score = self.score.replace(match.group(), new_score)
            self.save()

        else:
            #  if not present but existing, add with the points passed in
            self.score += ",".join(
                [str(question.quiz), str(score_to_add), str(possible_to_add), ""]
            )
            self.save()

    def show_exams(self):
        if self.user.is_superuser:
            return Sitting.objects.filter(complete=True).order_by("-end")
        else:
            return Sitting.objects.filter(user=self.user, complete=True).order_by(
                "-end"
            )


class SittingManager(models.Manager):
    def new_sitting(self, user, quiz, course):
        if quiz.random_order is True:
            question_set = quiz.question_set.all().select_subclasses().order_by("?")
        else:
            question_set = quiz.question_set.all().select_subclasses()

        question_set = [item.id for item in question_set]

        if len(question_set) == 0:
            raise ImproperlyConfigured(
                "Question set of the quiz is empty. Please configure questions properly"
            )

        # if quiz.max_questions and quiz.max_questions < len(question_set):
        #     question_set = question_set[:quiz.max_questions]

        questions = ",".join(map(str, question_set)) + ","

        new_sitting = self.create(
            user=user,
            quiz=quiz,
            course=course,
            question_order=questions,
            question_list=questions,
            incorrect_questions="",
            current_score=0,
            complete=False,
            user_answers="{}",
        )
        return new_sitting

    def user_sitting(self, user, quiz, course):
        if (
            quiz.single_attempt is True
            and self.filter(user=user, quiz=quiz, course=course, complete=True).exists()
        ):
            return False
        try:
            sitting = self.get(user=user, quiz=quiz,
                               course=course, complete=False)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz, course)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, course=course, complete=False)[
                0
            ]
        return sitting


class Sitting(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(Quiz, verbose_name=_(
        "Quiz"), on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course, null=True, verbose_name=_("Course"), on_delete=models.CASCADE
    )

    question_order = models.CharField(
        max_length=1024,
        verbose_name=_("Question Order"),
        validators=[validate_comma_separated_integer_list],
    )

    question_list = models.CharField(
        max_length=1024,
        verbose_name=_("Question List"),
        validators=[validate_comma_separated_integer_list],
    )

    incorrect_questions = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name=_("Incorrect questions"),
        validators=[validate_comma_separated_integer_list],
    )

    current_score = models.IntegerField(verbose_name=_("Current Score"))
    complete = models.BooleanField(
        default=False, blank=False, verbose_name=_("Complete")
    )
    user_answers = models.TextField(
        blank=True, default="{}", verbose_name=_("User Answers")
    )
    start = models.DateTimeField(auto_now_add=True, verbose_name=_("Start"))
    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    objects = SittingManager()

    class Meta:
        permissions = (("view_sittings", _("Can see completed exams.")),)

    def get_first_question(self):
        if not self.question_list:
            return False

        first, _ = self.question_list.split(",", 1)
        question_id = int(first)
        return Question.objects.get_subclass(id=question_id)

    def remove_first_question(self):
        if not self.question_list:
            return

        _, others = self.question_list.split(",", 1)
        self.question_list = others
        self.save()

    def add_to_score(self, points):
        self.current_score += int(points)
        self.save()

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(",") if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0  # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()
        self.save()

    def add_incorrect_question(self, question):
        if len(self.incorrect_questions) > 0:
            self.incorrect_questions += ","
        self.incorrect_questions += str(question.id) + ","
        if self.complete:
            self.add_to_score(-1)
        self.save()

    @property
    def get_incorrect_questions(self):
        return [int(q) for q in self.incorrect_questions.split(",") if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ",".join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return f"You have passed this quiz, congratulation"
        else:
            return f"You failed this quiz, give it one chance again."

    def add_user_answer(self, question, guess):
        current = json.loads(self.user_answers)
        current[question.id] = guess
        self.user_answers = json.dumps(current)
        self.save()

    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()
        questions = sorted(
            self.quiz.question_set.filter(
                id__in=question_ids).select_subclasses(),
            key=lambda q: question_ids.index(q.id),
        )

        if with_answers:
            user_answers = json.loads(self.user_answers)
            for question in questions:
                question.user_answer = user_answers[str(question.id)]

        return questions

    @property
    def questions_with_user_answers(self):
        return {q: q.user_answer for q in self.get_questions(with_answers=True)}

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        answered = len(json.loads(self.user_answers))
        total = self.get_max_score
        return answered, total


class Question(models.Model):
    quiz = models.ManyToManyField(Quiz, verbose_name=_("Quiz"), blank=True)
    figure = models.ImageField(
        upload_to="questions/uploads/%Y/%m/%d",
        blank=True,
        null=True,
        verbose_name=_("Figure"),
        help_text=_("Add an image for the question if it's necessary."),
    )
    content = models.CharField(
        max_length=1000,
        blank=False,
        help_text=_("Enter the question text that you want displayed"),
        verbose_name=_("Question"),
    )
    explanation = models.TextField(
        max_length=2000,
        blank=True,
        help_text=_(
            "Explanation to be shown after the question has been answered."),
        verbose_name=_("Explanation"),
    )

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return self.content


class MCQuestion(Question):
    choice_order = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        choices=CHOICE_ORDER_OPTIONS,
        help_text=_(
            "The order in which multichoice choice options are displayed to the user"
        ),
        verbose_name=_("Choice Order"),
    )

    def check_if_correct(self, guess):
        answer = Choice.objects.get(id=guess)

        if answer.correct is True:
            return True
        else:
            return False

    def order_choices(self, queryset):
        if self.choice_order == "content":
            return queryset.order_by("choice")
        if self.choice_order == "random":
            return queryset.order_by("?")
        if self.choice_order == "none":
            return queryset.order_by()
        return queryset

    def get_choices(self):
        return self.order_choices(Choice.objects.filter(question=self))

    def get_choices_list(self):
        return [
            (choice.id, choice.choice)
            for choice in self.order_choices(Choice.objects.filter(question=self))
        ]

    def answer_choice_to_string(self, guess):
        return Choice.objects.get(id=guess).choice

    class Meta:
        verbose_name = _("Multiple Choice Question")
        verbose_name_plural = _("Multiple Choice Questions")


class Choice(models.Model):
    question = models.ForeignKey(
        MCQuestion, verbose_name=_("Question"), on_delete=models.CASCADE
    )

    choice = models.CharField(
        max_length=1000,
        blank=False,
        help_text=_("Enter the choice text that you want displayed"),
        verbose_name=_("Content"),
    )

    correct = models.BooleanField(
        blank=False,
        default=False,
        help_text=_("Is this a correct answer?"),
        verbose_name=_("Correct"),
    )

    def __str__(self):
        return self.choice

    class Meta:
        verbose_name = _("Choice")
        verbose_name_plural = _("Choices")



# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================



# file: main/assessme# file: main/quiz/models.py
from __future__ import annotations
from typing import Optional
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from main.tenancy.models import SchoolAwareModel, AuditableModel, SoftDeleteModel

SUBJECT_FK = "main.Subject"
CLASSLIST_FK = "main.ClassList"
SESSION_FK = "main.AcademicSession"
TERM_FK = "main.Term"
STUDENT_FK = "main.Student"


class QuizManager(models.Manager):
    def published(self):
        return self.get_queryset().filter(is_published=True)

    def search(self, query: str | None = None):
        qs = self.get_queryset()
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(subject__name__icontains=query)
            ).distinct()
        return qs

    def for_class(self, class_list):
        return self.get_queryset().filter(Q(class_lists=class_list) | Q(class_lists__isnull=True))

    def for_student(self, student, now: Optional[timezone.datetime] = None):
        now = now or timezone.now()
        session_id = getattr(getattr(student, "current_enrollment", None), "academic_session_id", None)
        base = self.get_queryset().filter(school=student.school, is_published=True)
        # Assigned directly OR assigned to the student's active class for the same session OR global (no assignments)
        qs = base.filter(
            Q(assigned_students=student)
            | Q(class_lists__enrollments__student=student, academic_session_id=session_id)
            | (Q(class_lists__isnull=True) & Q(assigned_students__isnull=True))
        ).distinct()
        # availability window
        return qs.filter(Q(start_time__isnull=True) | Q(start_time__lte=now)).filter(
            Q(end_time__isnull=True) | Q(end_time__gte=now)
        )


class Quiz(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    """
    Quiz linked to **term**, **subject**, **class list(s)** and optionally **specific students**.

    - Use `class_lists` to assign to homerooms; use `assigned_students` for targeted delivery.
    - `academic_session` & `term` keep the quiz anchored in time.
    """

    # Basic
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)

    # Academic context
    subject = models.ForeignKey(SUBJECT_FK, on_delete=models.CASCADE, related_name="quizzes")
    academic_session = models.ForeignKey(SESSION_FK, on_delete=models.CASCADE, related_name="quizzes")
    term = models.ForeignKey(TERM_FK, on_delete=models.SET_NULL, null=True, blank=True, related_name="quizzes")

    # Audience
    class_lists = models.ManyToManyField(CLASSLIST_FK, blank=True, related_name="quizzes")
    assigned_students = models.ManyToManyField(STUDENT_FK, blank=True, related_name="assigned_quizzes")

    # Config
    CATEGORY_CHOICES = [
        ("assignment", "Assignment"),
        ("exam", "Exam"),
        ("practice", "Practice Quiz"),
        ("homework", "Homework"),
        ("test", "Class Test"),
    ]
    DIFFICULTY_CHOICES = [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="practice")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")

    total_marks = models.PositiveIntegerField(default=0)
    pass_mark_percentage = models.PositiveIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Timing & attempts
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    max_attempts = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    # Availability
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Behaviour
    randomize_questions = models.BooleanField(default=False)
    randomize_options = models.BooleanField(default=False)
    show_results_immediately = models.BooleanField(default=True)
    show_correct_answers = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=True)

    # Publish
    is_published = models.BooleanField(default=False)

    objects = QuizManager()

    class Meta:
        constraints = [UniqueConstraint(fields=["school", "slug"], name="unique_quiz_slug_per_school")]
        indexes = [
            models.Index(fields=["school", "subject", "is_published"]),
            models.Index(fields=["school", "category", "is_published"]),
            models.Index(fields=["start_time", "end_time"]),
            models.Index(fields=["academic_session", "term"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base or "quiz"
            i = 1
            while Quiz.objects.filter(school=self.school, slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self) -> None:
        # cross-tenant safety
        if getattr(self.subject, "school_id", self.school_id) != self.school_id:
            raise ValidationError("Subject must belong to the same school as the quiz")
        if self.term and getattr(self.term.academic_session, "school_id", self.school_id) != self.school_id:
            raise ValidationError("Term must belong to the same school")
        # ensure class lists belong to same school and session (when provided)
        for cl in self.class_lists.all():
            if cl.school_id != self.school_id:
                raise ValidationError("All assigned classes must belong to the same school")
            if self.academic_session_id and cl.academic_session_id != self.academic_session_id:
                raise ValidationError("Assigned class session must match quiz academic_session")
        # ensure assigned students belong to the same school
        for st in self.assigned_students.all():
            if st.school_id != self.school_id:
                raise ValidationError("Assigned students must belong to the same school")

    # Frontend helpers
    @property
    def is_available(self) -> bool:
        try:
            if not self.is_published:
                return False
            now = timezone.now()
            if self.start_time and now < self.start_time:
                return False
            if self.end_time and now > self.end_time:
                return False
            return True
        except Exception as e:
            logging.error(f"Error checking quiz availability: {e}")
            return False

    def is_assigned_to_student(self, student) -> bool:
        try:
            if student.school_id != self.school_id:
                return False
            if self.assigned_students.filter(pk=student.pk).exists():
                return True
            # check class assignment within same session
            ce = getattr(student, "current_enrollment", None)
            if ce and ce.academic_session_id == self.academic_session_id:
                return self.class_lists.filter(pk=ce.class_list_id).exists()
            return False
        except Exception as e:
            logging.error(f"Error checking quiz assignment to student: {e}")
            return False

    def to_public_dict(self):
        return {
            "id": self.pk,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "instructions": self.instructions,
            "subjectId": self.subject_id,
            "sessionId": self.academic_session_id,
            "termId": self.term_id,
            "category": self.category,
            "difficulty": self.difficulty,
            "totalMarks": self.total_marks,
            "passMarkPercent": self.pass_mark_percentage,
            "durationMinutes": self.duration_minutes,
            "maxAttempts": self.max_attempts,
            "windowStart": self.start_time.isoformat() if self.start_time else None,
            "windowEnd": self.end_time.isoformat() if self.end_time else None,
            "randomizeQuestions": self.randomize_questions,
            "randomizeOptions": self.randomize_options,
            "showResultsImmediately": self.show_results_immediately,
            "showCorrectAnswers": self.show_correct_answers,
            "allowReview": self.allow_review,
            "isPublished": self.is_published,
            "isAvailable": self.is_available,
            "classListIds": list(self.class_lists.values_list("id", flat=True)),
            "assignedStudentIds": list(self.assigned_students.values_list("id", flat=True)),
        }


class QuizQuestion(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    KIND_CHOICES = (
        ("single", "Single Choice"),
        ("multiple", "Multiple Choice"),
        ("true_false", "True/False"),
        ("short_answer", "Short Answer"),
        ("essay", "Essay"),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default="single")
    text = models.TextField()
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True)
    image = models.ImageField(upload_to="quiz/questions/%Y/%m/%d/", null=True, blank=True)
    is_required = models.BooleanField(default=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["quiz", "order"])]

    def to_public_dict(self):
        return {
            "id": self.pk,
            "kind": self.kind,
            "text": self.text,
            "points": float(self.points),
            "order": self.order,
            "explanation": self.explanation,
            "image": self.image.url if self.image else None,
            "required": self.is_required,
            "options": [o.to_public_dict() for o in self.options.order_by("order", "id")],
        }


class QuizOption(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["question", "order"])]

    def to_public_dict(self):
        return {"id": self.pk, "text": self.text}


class QuizAttempt(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(STUDENT_FK, on_delete=models.CASCADE, related_name="quiz_attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=12, default="in_progress")  # in_progress, submitted, graded
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["quiz", "student"]), models.Index(fields=["status"])]
        constraints = [
            UniqueConstraint(fields=["quiz", "student"], condition=Q(status="in_progress"), name="uniq_active_attempt"),
        ]

    def clean(self) -> None:
        if self.quiz.school_id != getattr(self.student, "school_id", None):
            raise ValidationError("Student and quiz must belong to the same school")
        # enforce assignment and availability
        if not self.quiz.is_assigned_to_student(self.student):
            raise ValidationError("Quiz is not assigned to this student or their class")
        if not self.quiz.is_available:
            raise ValidationError("Quiz is not currently available")
        # attempts
        used = QuizAttempt.objects.filter(quiz=self.quiz, student=self.student).exclude(pk=self.pk).count()
        if used >= (self.quiz.max_attempts or 1):
            raise ValidationError("Maximum number of attempts reached")

    @property
    def passed(self) -> bool:
        if not self.submitted_at:
            return False
        total = float(self.quiz.total_marks or 0)
        threshold = (total * float(self.quiz.pass_mark_percentage or 0)) / 100.0
        return float(self.score or 0) >= threshold


class QuizAnswer(SchoolAwareModel, AuditableModel, SoftDeleteModel):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="answers")
    selected_option_ids = models.JSONField(default=list, blank=True)
    text_answer = models.TextField(blank=True, default="")
    is_correct = models.BooleanField(default=False)
    points_awarded = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        indexes = [models.Index(fields=["attempt", "question"])]
        constraints = [UniqueConstraint(fields=["attempt", "question"], name="uniq_answer_per_question_attempt")]

    def auto_mark(self):
        q = self.question
        if q.kind in ("single", "multiple", "true_false"):
            correct_ids = set(q.options.filter(is_correct=True).values_list("id", flat=True))
            chosen = set(self.selected_option_ids or [])
            self.is_correct = chosen == correct_ids
            self.points_awarded = q.points if self.is_correct else 0
        # short_answer/essay left for manual marking
