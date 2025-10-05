from django.contrib import admin
from myquiz.admin_filters import AcademicSessionFilter, ActiveQuizFilter
from .models import Quiz, Question, QuestionBank, StudentAnswer, Result, TermResult, SessionResult


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # Number of extra blank question fields


@admin.action(description='Activate selected quizzes')
def activate_quizzes(self, request, queryset):
    # Assuming you add an `is_active` field to Quiz
    queryset.update(is_active=True)


@admin.action(description='Deactivate selected quizzes')
def deactivate_quizzes(self, request, queryset):
    queryset.update(is_active=False)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', "id", 'quiz_type', 'school_class', 'subject',
                    'term', 'academic_session', 'created_by', 'start_date', 'end_date')
    list_filter = ('quiz_type', 'school_class', 'subject',
                   'term', AcademicSessionFilter, ActiveQuizFilter)
    search_fields = ('title', 'school_class__name', 'subject__name')
    inlines = [QuestionInline]
    actions = [activate_quizzes, deactivate_quizzes]  # Add your custom actions


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_text', 'correct_answer')
    list_filter = ('quiz', 'quiz__school_class', 'quiz__subject')
    search_fields = ('question_text', 'quiz__title')


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('subject', 'question_text')
    search_fields = ('question_text', 'subject__name')


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'selected_option')
    list_filter = ('question__quiz', 'student')
    search_fields = ('student__name', 'question__question_text')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score')
    list_filter = ('quiz', 'student')
    search_fields = ('student__name__icontains', 'quiz__title__icontains')
    readonly_fields = ('score',)  # Prevent manual editing of the score


@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'term',
                    'academic_session', 'total_score')
    list_filter = ('school_class', 'term', 'academic_session')
    search_fields = ('student__name', 'school_class__name')
    readonly_fields = ('total_score',)  # Prevent manual editing of the score


@admin.register(SessionResult)
class SessionResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class',
                    'academic_session', 'total_score')
    list_filter = ('school_class', 'academic_session')
    search_fields = ('student__name', 'school_class__name')
