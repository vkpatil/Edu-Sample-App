from django.urls import path

from .views import StyledLoginView, help_view, profile_view, register_view, staff_user_create_view, student_create_view

urlpatterns = [
    path("login/", StyledLoginView.as_view(), name="login"),
    path("register/", register_view, name="register"),
    path("help/", help_view, name="help_page"),
    path("profile/", profile_view, name="profile"),
    path("staff/create/", staff_user_create_view, name="staff_create"),
    path("students/create/", student_create_view, name="student_create"),
]
