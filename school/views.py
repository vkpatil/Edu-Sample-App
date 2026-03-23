from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from users.models import User
from users.permissions import role_required

from .forms import CourseForm, EnrollmentForm, QuizForm, QuizQuestionCreateForm, StaffEnrollmentCreateForm
from .models import Course, Enrollment, Quiz, QuizAnswer, QuizAttempt, QuizChoice, QuizQuestion


@login_required
def course_list_view(request):
    if request.user.role == User.Role.TEACHER:
        courses = Course.objects.select_related("teacher").filter(teacher=request.user)
    elif request.user.role in {User.Role.STUDENT, User.Role.ADMIN, User.Role.SUPER_ADMIN}:
        courses = Course.objects.select_related("teacher").all()
    else:
        courses = Course.objects.none()
    return render(request, "school/course_list.html", {"courses": courses})


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPER_ADMIN)
def course_create_view(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            if request.user.role == User.Role.TEACHER and not course.teacher_id:
                course.teacher = request.user
            course.save()
            messages.success(request, "Course created successfully.")
            return redirect("course_list")
    else:
        form = CourseForm()
        if request.user.role == User.Role.TEACHER:
            form.fields["teacher"].initial = request.user

    return render(request, "school/course_form.html", {"form": form})


@login_required
@role_required(User.Role.STUDENT)
def enroll_view(request):
    if request.method == "POST":
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = request.user
            try:
                enrollment.save()
                messages.success(request, "Enrollment successful.")
                return redirect("enrollment_list")
            except Exception:
                form.add_error("course", "You are already enrolled in this course.")
    else:
        form = EnrollmentForm()

    return render(request, "school/enroll_form.html", {"form": form})


@login_required
def enrollment_list_view(request):
    if request.user.role == User.Role.STUDENT:
        enrollments = Enrollment.objects.select_related("course").filter(student=request.user)
    elif request.user.role == User.Role.TEACHER:
        enrollments = Enrollment.objects.select_related("course", "student").filter(course__teacher=request.user)
    elif request.user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
        enrollments = Enrollment.objects.select_related("course", "student").all()
    else:
        enrollments = Enrollment.objects.none()

    return render(request, "school/enrollment_list.html", {"enrollments": enrollments})


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPER_ADMIN)
def enrollment_status_update_view(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.user.role == User.Role.TEACHER and enrollment.course.teacher_id != request.user.id:
        messages.error(request, "You can only update students enrolled in your courses.")
        return redirect("enrollment_list")

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in Enrollment.Status.values:
            enrollment.status = new_status
            enrollment.save(update_fields=["status"])
            messages.success(request, "Enrollment status updated.")
    return redirect("enrollment_list")


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPER_ADMIN)
def enrollment_create_view(request):
    if request.method == "POST":
        form = StaffEnrollmentCreateForm(request.POST)
        if request.user.role == User.Role.TEACHER:
            form.fields["course"].queryset = Course.objects.filter(teacher=request.user)

        if form.is_valid():
            enrollment = form.save(commit=False)
            if request.user.role == User.Role.TEACHER and enrollment.course.teacher_id != request.user.id:
                form.add_error("course", "You can only enroll students into your own courses.")
            else:
                try:
                    enrollment.save()
                    messages.success(request, "Enrollment created successfully.")
                    return redirect("enrollment_list")
                except IntegrityError:
                    form.add_error(None, "This student is already enrolled in that course.")
    else:
        form = StaffEnrollmentCreateForm()
        if request.user.role == User.Role.TEACHER:
            form.fields["course"].queryset = Course.objects.filter(teacher=request.user)

    return render(request, "school/enrollment_create.html", {"form": form})


@login_required
def quiz_list_view(request):
    user = request.user
    if user.role == User.Role.STUDENT:
        quizzes = Quiz.objects.filter(
            is_published=True,
            course__enrollments__student=user,
            course__enrollments__status=Enrollment.Status.ENROLLED,
        ).distinct()
    elif user.role == User.Role.TEACHER:
        quizzes = Quiz.objects.filter(course__teacher=user)
    elif user.role in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
        quizzes = Quiz.objects.all()
    else:
        quizzes = Quiz.objects.none()

    quizzes = quizzes.select_related("course", "created_by")
    attempts = {
        a.quiz_id: a
        for a in QuizAttempt.objects.filter(student=user, quiz_id__in=[q.id for q in quizzes]).select_related("quiz")
    }
    quiz_rows = [{"quiz": quiz, "attempt": attempts.get(quiz.id)} for quiz in quizzes]
    return render(request, "school/quiz_list.html", {"quiz_rows": quiz_rows})


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPER_ADMIN)
def quiz_create_view(request):
    if request.method == "POST":
        form = QuizForm(request.POST)
        if request.user.role == User.Role.TEACHER:
            form.fields["course"].queryset = Course.objects.filter(teacher=request.user)

        if form.is_valid():
            quiz = form.save(commit=False)
            if request.user.role == User.Role.TEACHER and quiz.course.teacher_id != request.user.id:
                form.add_error("course", "You can only create quizzes for your own courses.")
            else:
                quiz.created_by = request.user
                quiz.save()
                messages.success(request, "Quiz created. Add at least one question.")
                return redirect("quiz_question_create", quiz_id=quiz.id)
    else:
        form = QuizForm()
        if request.user.role == User.Role.TEACHER:
            form.fields["course"].queryset = Course.objects.filter(teacher=request.user)

    return render(request, "school/quiz_form.html", {"form": form})


@login_required
@role_required(User.Role.TEACHER, User.Role.ADMIN, User.Role.SUPER_ADMIN)
def quiz_question_create_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related("course"), pk=quiz_id)
    if request.user.role == User.Role.TEACHER and quiz.course.teacher_id != request.user.id:
        messages.error(request, "You can only edit quizzes for your own courses.")
        return redirect("quiz_list")

    if request.method == "POST":
        form = QuizQuestionCreateForm(request.POST)
        if form.is_valid():
            question = QuizQuestion.objects.create(
                quiz=quiz,
                text=form.cleaned_data["text"],
                marks=form.cleaned_data["marks"],
                order=form.cleaned_data["order"],
            )
            correct_choice = int(form.cleaned_data["correct_choice"])
            for idx in range(1, 5):
                QuizChoice.objects.create(
                    question=question,
                    text=form.cleaned_data[f"choice_{idx}"],
                    is_correct=(idx == correct_choice),
                )
            messages.success(request, "Question added to quiz.")
            if "save_and_finish" in request.POST:
                return redirect("quiz_list")
            return redirect("quiz_question_create", quiz_id=quiz.id)
    else:
        next_order = quiz.questions.aggregate(max_order=Max("order")).get("max_order") or 0
        form = QuizQuestionCreateForm(initial={"order": next_order + 1})

    return render(
        request,
        "school/question_form.html",
        {"form": form, "quiz": quiz, "question_count": quiz.questions.count()},
    )


@login_required
@role_required(User.Role.STUDENT)
def quiz_take_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related("questions__choices"), pk=quiz_id, is_published=True)

    is_enrolled = Enrollment.objects.filter(
        student=request.user,
        course=quiz.course,
        status=Enrollment.Status.ENROLLED,
    ).exists()
    if not is_enrolled:
        messages.error(request, "You can only take quizzes for courses where you are enrolled.")
        return redirect("quiz_list")

    attempt, _ = QuizAttempt.objects.get_or_create(quiz=quiz, student=request.user)
    if attempt.status == QuizAttempt.Status.SUBMITTED:
        messages.info(request, "You already submitted this quiz.")
        return redirect("quiz_result", attempt_id=attempt.id)

    questions = list(quiz.questions.all())
    total_questions = len(questions)
    if total_questions == 0:
        messages.error(request, "This quiz has no questions yet.")
        return redirect("quiz_list")

    max_score = sum(q.marks for q in questions)

    def _clamp_index(value):
        return max(1, min(total_questions, value))

    def _attempt_url(q_index, saved=False):
        url = f"{reverse('quiz_take', args=[quiz.id])}?q={_clamp_index(q_index)}"
        if saved:
            url = f"{url}&saved=1"
        return url

    def _save_attempt_scores():
        total = attempt.answers.aggregate(total=Sum("marks_obtained")).get("total") or 0
        attempt.score = total
        attempt.max_score = max_score
        attempt.save(update_fields=["score", "max_score"])

    current_index = _clamp_index(int(request.GET.get("q", 1)))

    quiz_duration_seconds = quiz.duration_minutes * 60
    elapsed_seconds = max(0, int((timezone.now() - attempt.started_at).total_seconds()))
    remaining_seconds = max(0, quiz_duration_seconds - elapsed_seconds)

    if remaining_seconds <= 0 and attempt.status == QuizAttempt.Status.IN_PROGRESS:
        _save_attempt_scores()
        attempt.status = QuizAttempt.Status.SUBMITTED
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["status", "submitted_at"])
        messages.info(request, "Quiz timer ended. Your attempt was auto-submitted.")
        return redirect("quiz_result", attempt_id=attempt.id)

    if request.method == "POST":
        current_index = _clamp_index(int(request.POST.get("current_index", current_index)))
        question = questions[current_index - 1]
        selected_choice_id = request.POST.get(f"question_{question.id}")

        if selected_choice_id:
            selected_choice = question.choices.filter(id=selected_choice_id).first()
            if selected_choice:
                marks_obtained = question.marks if selected_choice.is_correct else 0
                QuizAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        "selected_choice": selected_choice,
                        "is_correct": selected_choice.is_correct,
                        "marks_obtained": marks_obtained,
                    },
                )

        _save_attempt_scores()

        action = request.POST.get("action")
        if action == "submit":
            attempt.status = QuizAttempt.Status.SUBMITTED
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["status", "submitted_at"])
            messages.success(request, f"Quiz submitted. Your score is {attempt.score}/{attempt.max_score}.")
            return redirect("quiz_result", attempt_id=attempt.id)

        if action == "prev":
            return redirect(_attempt_url(current_index - 1, saved=True))
        if action == "next":
            return redirect(_attempt_url(current_index + 1, saved=True))
        return redirect(_attempt_url(current_index, saved=True))

    answer_map = {
        ans.question_id: ans
        for ans in QuizAnswer.objects.filter(attempt=attempt).select_related("selected_choice")
    }
    current_question = questions[current_index - 1]
    selected_answer = answer_map.get(current_question.id)

    question_states = [
        {
            "index": idx,
            "answered": question.id in answer_map,
            "current": idx == current_index,
        }
        for idx, question in enumerate(questions, start=1)
    ]

    live_score = sum(float(ans.marks_obtained) for ans in answer_map.values())
    answered_count = len(answer_map)
    live_percent = round((live_score / max_score) * 100, 2) if max_score else 0
    show_saved = request.GET.get("saved") == "1"

    return render(
        request,
        "school/quiz_take.html",
        {
            "quiz": quiz,
            "attempt": attempt,
            "current_question": current_question,
            "current_index": current_index,
            "total_questions": total_questions,
            "selected_choice_id": selected_answer.selected_choice_id if selected_answer else None,
            "answered_count": answered_count,
            "live_score": live_score,
            "max_score": max_score,
            "live_percent": live_percent,
            "is_first": current_index == 1,
            "is_last": current_index == total_questions,
            "question_states": question_states,
            "show_saved": show_saved,
            "remaining_seconds": remaining_seconds,
        },
    )


@login_required
def quiz_result_view(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "student", "quiz__course").prefetch_related(
            "answers__question", "answers__selected_choice"
        ),
        pk=attempt_id,
    )

    if request.user.role == User.Role.STUDENT:
        if attempt.student_id != request.user.id:
            messages.error(request, "You can only view your own quiz results.")
            return redirect("quiz_list")
    elif request.user.role == User.Role.TEACHER:
        if attempt.quiz.course.teacher_id != request.user.id:
            messages.error(request, "You can only view results for your course quizzes.")
            return redirect("quiz_list")
    elif request.user.role not in {User.Role.ADMIN, User.Role.SUPER_ADMIN}:
        messages.error(request, "You do not have permission to access quiz results.")
        return redirect("quiz_list")

    ordered_answers = attempt.answers.select_related("question", "selected_choice").order_by("question__order")

    percent = 0
    if attempt.max_score:
        percent = round((float(attempt.score) / float(attempt.max_score)) * 100, 2)

    return render(request, "school/quiz_result.html", {"attempt": attempt, "percent": percent, "ordered_answers": ordered_answers})
