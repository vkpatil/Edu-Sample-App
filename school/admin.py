from django.contrib import admin

from .models import Course, Enrollment, Quiz, QuizAnswer, QuizAttempt, QuizChoice, QuizQuestion


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "teacher", "created_at")
    search_fields = ("code", "title")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "enrolled_at")
    list_filter = ("status",)


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 2


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "text", "marks")
    list_filter = ("quiz__course",)
    inlines = [QuizChoiceInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "duration_minutes", "is_published", "created_by", "created_at")
    list_filter = ("is_published", "course")
    search_fields = ("title", "course__code", "course__title")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("quiz", "student", "status", "score", "max_score", "submitted_at")
    list_filter = ("status", "quiz__course")


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_choice", "is_correct", "marks_obtained")
