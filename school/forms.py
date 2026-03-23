from django import forms

from users.models import User
from users.forms import BootstrapFormMixin

from .models import Course, Enrollment, Quiz


class CourseForm(BootstrapFormMixin, forms.ModelForm):
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.TEACHER),
        required=False,
    )

    class Meta:
        model = Course
        fields = ("title", "code", "description", "teacher")


class EnrollmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("course",)


class StaffEnrollmentCreateForm(BootstrapFormMixin, forms.ModelForm):
    student = forms.ModelChoiceField(queryset=User.objects.filter(role=User.Role.STUDENT))
    course = forms.ModelChoiceField(queryset=Course.objects.select_related("teacher").all())

    class Meta:
        model = Enrollment
        fields = ("student", "course")


class QuizForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ("course", "title", "description", "duration_minutes", "is_published")


class QuizQuestionCreateForm(BootstrapFormMixin, forms.Form):
    text = forms.CharField(max_length=500)
    marks = forms.IntegerField(min_value=1, initial=1)
    order = forms.IntegerField(min_value=1, initial=1)

    choice_1 = forms.CharField(max_length=300, label="Choice 1")
    choice_2 = forms.CharField(max_length=300, label="Choice 2")
    choice_3 = forms.CharField(max_length=300, label="Choice 3")
    choice_4 = forms.CharField(max_length=300, label="Choice 4")

    correct_choice = forms.ChoiceField(
        choices=(("1", "Choice 1"), ("2", "Choice 2"), ("3", "Choice 3"), ("4", "Choice 4"))
    )
