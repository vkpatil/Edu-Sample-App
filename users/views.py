from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from school.models import Course, Enrollment, Quiz

from .forms import RegistrationForm, StaffUserCreateForm, StudentCreateForm, StyledAuthenticationForm, UserProfileForm
from .models import User
from .permissions import role_required


class StyledLoginView(LoginView):
    authentication_form = StyledAuthenticationForm
    template_name = "auth/login.html"


def home_view(request):
    return render(request, "home.html")


def access_guide_view(request):
    return render(request, "access_guide.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student account created successfully. Please sign in.")
            return redirect("login")
    else:
        form = RegistrationForm()
    return render(request, "auth/register.html", {"form": form})


@login_required
def dashboard_view(request):
    user = request.user
    if user.role == User.Role.STUDENT:
        context = {
            "my_enrollments": Enrollment.objects.filter(student=user).count(),
            "active_courses": Enrollment.objects.filter(
                student=user,
                status=Enrollment.Status.ENROLLED,
            ).count(),
            "completed_courses": Enrollment.objects.filter(
                student=user,
                status=Enrollment.Status.COMPLETED,
            ).count(),
            "available_quizzes": Quiz.objects.filter(
                is_published=True,
                course__enrollments__student=user,
                course__enrollments__status=Enrollment.Status.ENROLLED,
            ).distinct().count(),
        }
        return render(request, "users/dashboard_student.html", context)

    if user.role == User.Role.TEACHER:
        teacher_courses = Course.objects.filter(teacher=user)
        context = {
            "my_courses": teacher_courses.count(),
            "active_students": Enrollment.objects.filter(
                course__teacher=user,
                status=Enrollment.Status.ENROLLED,
            ).values("student").distinct().count(),
            "my_quizzes": Quiz.objects.filter(course__teacher=user).count(),
            "draft_quizzes": Quiz.objects.filter(course__teacher=user, is_published=False).count(),
            "top_courses": teacher_courses.annotate(enrolled=Count("enrollments")).order_by("-enrolled", "title")[:5],
        }
        return render(request, "users/dashboard_teacher.html", context)

    if user.role == User.Role.ADMIN:
        context = {
            "total_students": User.objects.filter(role=User.Role.STUDENT).count(),
            "total_teachers": User.objects.filter(role=User.Role.TEACHER).count(),
            "total_courses": Course.objects.count(),
            "total_quizzes": Quiz.objects.count(),
            "top_courses": Course.objects.annotate(enrolled=Count("enrollments")).order_by("-enrolled", "title")[:5],
        }
        return render(request, "users/dashboard_admin.html", context)

    if user.role == User.Role.SUPER_ADMIN:
        context = {
            "total_students": User.objects.filter(role=User.Role.STUDENT).count(),
            "total_teachers": User.objects.filter(role=User.Role.TEACHER).count(),
            "total_admins": User.objects.filter(role=User.Role.ADMIN).count(),
            "total_courses": Course.objects.count(),
            "published_quizzes": Quiz.objects.filter(is_published=True).count(),
            "top_courses": Course.objects.annotate(enrolled=Count("enrollments")).order_by("-enrolled", "title")[:5],
        }
        return render(request, "users/dashboard_super_admin.html", context)

    return HttpResponseForbidden("You do not have permission to access this page.")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "users/profile.html", {"form": form})


@login_required
def help_view(request):
    role = request.user.role
    role_actions = {
        User.Role.STUDENT: [
            "Browse courses and self-enroll",
            "Track your own enrollments and progress",
            "Take published quizzes for enrolled courses",
            "View your own quiz results",
            "Update your profile",
        ],
        User.Role.TEACHER: [
            "View and manage only your assigned courses",
            "Create quizzes and questions for your courses",
            "View enrollments and update status in your courses",
            "Review quiz results for your course quizzes",
            "Update your profile",
        ],
        User.Role.ADMIN: [
            "View and manage all courses, enrollments, and quizzes",
            "Create staff and student accounts",
            "Use administrative management screens",
            "Access full quiz result visibility",
            "Update your profile",
        ],
        User.Role.SUPER_ADMIN: [
            "All admin capabilities across the platform",
            "Global user and platform oversight",
            "Access full course, enrollment, quiz, and result visibility",
            "Use Django admin panel and platform controls",
            "Update your profile",
        ],
    }

    context = {
        "role_actions": role_actions.get(role, []),
    }
    return render(request, "users/help.html", context)


@login_required
@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def staff_user_create_view(request):
    if request.method == "POST":
        form = StaffUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff user created successfully.")
            return redirect("staff_create")
    else:
        form = StaffUserCreateForm()
    return render(request, "users/staff_create.html", {"form": form})


@login_required
@role_required(User.Role.ADMIN, User.Role.SUPER_ADMIN)
def student_create_view(request):
    if request.method == "POST":
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student created successfully.")
            return redirect("student_create")
    else:
        form = StudentCreateForm()

    return render(request, "users/student_create.html", {"form": form})
