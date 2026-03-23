from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from school.models import Course, Enrollment, Quiz, QuizAttempt
from users.models import User


class RoleAccessTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student_one",
            password="Pass1234!",
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username="student_two",
            password="Pass1234!",
            role=User.Role.STUDENT,
        )
        self.teacher = User.objects.create_user(
            username="teacher_one",
            password="Pass1234!",
            role=User.Role.TEACHER,
        )
        self.other_teacher = User.objects.create_user(
            username="teacher_two",
            password="Pass1234!",
            role=User.Role.TEACHER,
        )
        self.admin = User.objects.create_user(
            username="admin_one",
            password="Pass1234!",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.super_admin = User.objects.create_user(
            username="super_one",
            password="Pass1234!",
            role=User.Role.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )

        self.course_owned = Course.objects.create(code="C101", title="Owned Course", teacher=self.teacher)
        self.course_other = Course.objects.create(code="C202", title="Other Course", teacher=self.other_teacher)

        Enrollment.objects.create(student=self.student, course=self.course_owned, status=Enrollment.Status.ENROLLED)
        Enrollment.objects.create(student=self.other_student, course=self.course_other, status=Enrollment.Status.ENROLLED)

        self.quiz_owned = Quiz.objects.create(
            course=self.course_owned,
            title="Owned Quiz",
            is_published=True,
            created_by=self.teacher,
        )
        self.quiz_other = Quiz.objects.create(
            course=self.course_other,
            title="Other Quiz",
            is_published=True,
            created_by=self.other_teacher,
        )
        self.quiz_unpublished = Quiz.objects.create(
            course=self.course_owned,
            title="Draft Quiz",
            is_published=False,
            created_by=self.teacher,
        )

        self.other_attempt = QuizAttempt.objects.create(
            quiz=self.quiz_owned,
            student=self.other_student,
            status=QuizAttempt.Status.SUBMITTED,
            score=6,
            max_score=10,
            submitted_at=timezone.now(),
        )

    def _login(self, user):
        self.client.force_login(user)

    def test_public_access_guide_is_available_without_login(self):
        response = self.client.get(reverse("access_guide"))
        self.assertEqual(response.status_code, 200)

    def test_public_access_guide_is_available_when_authenticated(self):
        self._login(self.student)
        response = self.client.get(reverse("access_guide"))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_users_are_redirected_from_protected_pages(self):
        protected_urls = [
            reverse("dashboard"),
            reverse("profile"),
            reverse("help_page"),
            reverse("course_list"),
            reverse("enrollment_list"),
            reverse("quiz_list"),
            reverse("course_create"),
            reverse("enrollment_create"),
            reverse("quiz_create"),
            reverse("staff_create"),
            reverse("student_create"),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response.headers.get("Location", ""))

    def test_student_is_blocked_from_staff_management_pages(self):
        self._login(self.student)
        restricted_urls = [
            reverse("course_create"),
            reverse("enrollment_create"),
            reverse("quiz_create"),
            reverse("staff_create"),
            reverse("student_create"),
        ]

        for url in restricted_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_teacher_is_blocked_from_user_management_pages(self):
        self._login(self.teacher)

        self.assertEqual(self.client.get(reverse("staff_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("student_create")).status_code, 403)

    def test_help_page_is_available_to_all_authenticated_roles(self):
        for user in [self.student, self.teacher, self.admin, self.super_admin]:
            self._login(user)
            response = self.client.get(reverse("help_page"))
            self.assertEqual(response.status_code, 200)
            self.client.logout()

    def test_teacher_sees_only_their_courses(self):
        self._login(self.teacher)

        response = self.client.get(reverse("course_list"))
        courses = list(response.context["courses"])

        self.assertEqual({course.pk for course in courses}, {self.course_owned.pk})

    def test_teacher_sees_only_their_quizzes(self):
        self._login(self.teacher)

        response = self.client.get(reverse("quiz_list"))
        quiz_ids = {row["quiz"].id for row in response.context["quiz_rows"]}

        self.assertEqual(quiz_ids, {self.quiz_owned.pk, self.quiz_unpublished.pk})

    def test_student_sees_only_published_quizzes_for_enrolled_courses(self):
        self._login(self.student)

        response = self.client.get(reverse("quiz_list"))
        quiz_ids = {row["quiz"].id for row in response.context["quiz_rows"]}

        self.assertEqual(quiz_ids, {self.quiz_owned.pk})

    def test_student_cannot_view_another_students_result(self):
        self._login(self.student)

        response = self.client.get(reverse("quiz_result", args=[self.other_attempt.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get("Location", ""), reverse("quiz_list"))

    def test_admin_can_open_management_screens(self):
        self._login(self.admin)

        allowed_urls = [
            reverse("course_create"),
            reverse("enrollment_create"),
            reverse("quiz_create"),
            reverse("staff_create"),
            reverse("student_create"),
        ]

        for url in allowed_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_super_admin_sees_all_courses(self):
        self._login(self.super_admin)

        response = self.client.get(reverse("course_list"))
        courses = list(response.context["courses"])

        self.assertEqual({course.pk for course in courses}, {self.course_owned.pk, self.course_other.pk})
