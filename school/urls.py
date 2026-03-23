from django.urls import path

from .views import (
    course_create_view,
    course_list_view,
    enrollment_create_view,
    enrollment_list_view,
    enrollment_status_update_view,
    enroll_view,
    quiz_create_view,
    quiz_list_view,
    quiz_question_create_view,
    quiz_result_view,
    quiz_take_view,
)

urlpatterns = [
    path("courses/", course_list_view, name="course_list"),
    path("courses/create/", course_create_view, name="course_create"),
    path("enroll/", enroll_view, name="enroll"),
    path("enrollments/create/", enrollment_create_view, name="enrollment_create"),
    path("enrollments/", enrollment_list_view, name="enrollment_list"),
    path("enrollments/<int:pk>/status/", enrollment_status_update_view, name="enrollment_status_update"),
    path("quizzes/", quiz_list_view, name="quiz_list"),
    path("quizzes/create/", quiz_create_view, name="quiz_create"),
    path("quizzes/<int:quiz_id>/questions/create/", quiz_question_create_view, name="quiz_question_create"),
    path("quizzes/<int:quiz_id>/take/", quiz_take_view, name="quiz_take"),
    path("quiz-attempts/<int:attempt_id>/result/", quiz_result_view, name="quiz_result"),
]
