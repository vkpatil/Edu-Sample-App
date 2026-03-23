"""
Management command: python manage.py seed_data

Creates a realistic dataset:
  - 1 super admin  (admin / Admin1234!)
  - 2 admins
  - 4 teachers
  - 10 students
  - 8 courses assigned to teachers
  - ~20 enrollments spread across students
"""

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from school.models import Course, Enrollment, Quiz, QuizChoice, QuizQuestion
from users.models import User


SUPER_ADMIN = User.Role.SUPER_ADMIN
ADMIN = User.Role.ADMIN
TEACHER = User.Role.TEACHER
STUDENT = User.Role.STUDENT

DEFAULT_PASSWORD = make_password("Pass1234!")

QUIZ_DURATION_BASE_MINUTES = 8
QUIZ_DURATION_PER_MARK = 2
QUIZ_DURATION_PER_QUESTION = 1
QUIZ_DURATION_MIN = 10
QUIZ_DURATION_MAX = 45


def _user(username, first, last, email, role, is_staff=False, is_superuser=False, password=None):
    return User(
        username=username,
        first_name=first,
        last_name=last,
        email=email,
        role=role,
        is_staff=is_staff or is_superuser,
        is_superuser=is_superuser,
        password=password or DEFAULT_PASSWORD,
    )


USERS = [
    # super admin — fix existing or create fresh
    _user("admin", "System", "Admin", "admin@edusys.local", SUPER_ADMIN, is_superuser=True, password=make_password("Admin1234!")),
    # admins
    _user("admin_sarah", "Sarah", "Bennett", "sarah.bennett@edusys.local", ADMIN, is_staff=True),
    _user("admin_james", "James", "Okafor", "james.okafor@edusys.local", ADMIN, is_staff=True),
    # teachers
    _user("teach_maya", "Maya", "Sharma", "maya.sharma@edusys.local", TEACHER),
    _user("teach_carlos", "Carlos", "Mendez", "carlos.mendez@edusys.local", TEACHER),
    _user("teach_priya", "Priya", "Nair", "priya.nair@edusys.local", TEACHER),
    _user("teach_tom", "Thomas", "Eriksson", "tom.eriksson@edusys.local", TEACHER),
    # students
    _user("stu_alice", "Alice", "Chen", "alice.chen@edusys.local", STUDENT),
    _user("stu_bob", "Bob", "Martins", "bob.martins@edusys.local", STUDENT),
    _user("stu_cleo", "Cleo", "Adeyemi", "cleo.adeyemi@edusys.local", STUDENT),
    _user("stu_dan", "Daniel", "Kowalski", "dan.kowalski@edusys.local", STUDENT),
    _user("stu_eva", "Eva", "Johansson", "eva.johansson@edusys.local", STUDENT),
    _user("stu_frank", "Frank", "Oluwole", "frank.oluwole@edusys.local", STUDENT),
    _user("stu_grace", "Grace", "Kim", "grace.kim@edusys.local", STUDENT),
    _user("stu_han", "Han", "Nguyen", "han.nguyen@edusys.local", STUDENT),
    _user("stu_iris", "Iris", "Popescu", "iris.popescu@edusys.local", STUDENT),
    _user("stu_jack", "Jack", "Fernandez", "jack.fernandez@edusys.local", STUDENT),
]

COURSES_SPEC = [
    ("CS101", "Introduction to Computer Science", "teach_maya"),
    ("MATH201", "Linear Algebra", "teach_carlos"),
    ("ENG301", "Academic Writing", "teach_priya"),
    ("PHY101", "Physics I: Mechanics", "teach_tom"),
    ("CS201", "Data Structures & Algorithms", "teach_maya"),
    ("MATH301", "Probability & Statistics", "teach_carlos"),
    ("ENG401", "Research Methods", "teach_priya"),
    ("PHY201", "Physics II: Electromagnetism", "teach_tom"),
]

# (student_username, course_code, status)
ENROLLMENTS_SPEC = [
    ("stu_alice",  "CS101",   "ENROLLED"),
    ("stu_alice",  "MATH201", "ENROLLED"),
    ("stu_alice",  "ENG301",  "COMPLETED"),
    ("stu_bob",    "CS101",   "ENROLLED"),
    ("stu_bob",    "PHY101",  "DROPPED"),
    ("stu_cleo",   "MATH201", "ENROLLED"),
    ("stu_cleo",   "CS201",   "ENROLLED"),
    ("stu_dan",    "ENG301",  "ENROLLED"),
    ("stu_dan",    "ENG401",  "ENROLLED"),
    ("stu_eva",    "CS101",   "COMPLETED"),
    ("stu_eva",    "CS201",   "ENROLLED"),
    ("stu_frank",  "PHY101",  "ENROLLED"),
    ("stu_frank",  "PHY201",  "ENROLLED"),
    ("stu_grace",  "MATH301", "ENROLLED"),
    ("stu_grace",  "CS101",   "ENROLLED"),
    ("stu_han",    "CS201",   "ENROLLED"),
    ("stu_han",    "MATH201", "COMPLETED"),
    ("stu_iris",   "ENG301",  "ENROLLED"),
    ("stu_iris",   "ENG401",  "ENROLLED"),
    ("stu_jack",   "PHY101",  "ENROLLED"),
    ("stu_jack",   "CS101",   "ENROLLED"),
]

QUIZZES_SPEC = [
    {
        "course_code": "CS101",
        "title": "CS101 Fundamentals Check",
        "description": "Core concepts in introductory computer science.",
        "is_published": True,
        "questions": [
            {
                "text": "Which data structure follows FIFO?",
                "marks": 2,
                "choices": ["Stack", "Queue", "Tree", "Graph"],
                "correct": 2,
            },
            {
                "text": "Binary numbers use which base?",
                "marks": 1,
                "choices": ["2", "8", "10", "16"],
                "correct": 1,
            },
            {
                "text": "Which keyword defines a function in Python?",
                "marks": 1,
                "choices": ["func", "def", "function", "lambda"],
                "correct": 2,
            },
        ],
    },
    {
        "course_code": "CS101",
        "title": "CS101 Logic and Control Flow",
        "description": "Conditionals, loops, and boolean logic.",
        "is_published": True,
        "questions": [
            {
                "text": "Which operator means logical AND in Python?",
                "marks": 1,
                "choices": ["&&", "and", "&", "AND"],
                "correct": 2,
            },
            {
                "text": "A for-loop is best used when:",
                "marks": 2,
                "choices": ["condition unknown", "iterating a known sequence", "storing files", "debugging only"],
                "correct": 2,
            },
            {
                "text": "What does `break` do inside a loop?",
                "marks": 1,
                "choices": ["Skips one iteration", "Ends the loop", "Restarts loop", "Raises error"],
                "correct": 2,
            },
        ],
    },
    {
        "course_code": "MATH201",
        "title": "Linear Algebra Basics",
        "description": "Vectors, matrices, and systems of equations.",
        "is_published": True,
        "questions": [
            {
                "text": "A 2x3 matrix has how many elements?",
                "marks": 1,
                "choices": ["5", "6", "7", "8"],
                "correct": 2,
            },
            {
                "text": "What is the determinant of a 2x2 identity matrix?",
                "marks": 2,
                "choices": ["0", "1", "2", "Undefined"],
                "correct": 2,
            },
            {
                "text": "Which operation is valid for vectors of same dimension?",
                "marks": 1,
                "choices": ["Addition", "Cross DB", "Factorization", "Transpose only"],
                "correct": 1,
            },
        ],
    },
    {
        "course_code": "MATH301",
        "title": "Probability Essentials",
        "description": "Intro to events, distributions, and expectations.",
        "is_published": True,
        "questions": [
            {
                "text": "Probability values are always between:",
                "marks": 1,
                "choices": ["-1 and 1", "0 and 1", "0 and 100", "1 and 10"],
                "correct": 2,
            },
            {
                "text": "If events A and B are independent, P(A and B) equals:",
                "marks": 2,
                "choices": ["P(A)+P(B)", "P(A)-P(B)", "P(A)P(B)", "P(A)/P(B)"],
                "correct": 3,
            },
            {
                "text": "Expected value is often interpreted as:",
                "marks": 1,
                "choices": ["Median only", "Long-run average", "Mode", "Variance"],
                "correct": 2,
            },
        ],
    },
    {
        "course_code": "ENG301",
        "title": "Academic Writing Skills",
        "description": "Structure, argument flow, and citation basics.",
        "is_published": True,
        "questions": [
            {
                "text": "Which section states your main argument clearly?",
                "marks": 1,
                "choices": ["Conclusion", "References", "Thesis statement", "Appendix"],
                "correct": 3,
            },
            {
                "text": "A good paragraph should generally contain:",
                "marks": 2,
                "choices": ["Only quotes", "Topic sentence and supporting details", "Only data tables", "No transitions"],
                "correct": 2,
            },
            {
                "text": "Why cite sources in academic writing?",
                "marks": 1,
                "choices": ["To increase word count", "To avoid plagiarism and support claims", "To shorten essays", "To avoid editing"],
                "correct": 2,
            },
        ],
    },
    {
        "course_code": "ENG401",
        "title": "Research Methods Readiness",
        "description": "Research design and evidence evaluation.",
        "is_published": True,
        "questions": [
            {
                "text": "Which is an example of primary research?",
                "marks": 2,
                "choices": ["Reading a textbook", "Conducting a survey", "Summarizing an article", "Watching a lecture"],
                "correct": 2,
            },
            {
                "text": "A literature review is mainly used to:",
                "marks": 1,
                "choices": ["Ignore prior work", "Map existing knowledge", "Write abstract only", "Avoid citations"],
                "correct": 2,
            },
            {
                "text": "Which research approach often uses interviews?",
                "marks": 1,
                "choices": ["Qualitative", "Only numerical", "Pure algebraic", "None"],
                "correct": 1,
            },
        ],
    },
    {
        "course_code": "PHY101",
        "title": "Mechanics Checkpoint",
        "description": "Kinematics and Newton's laws fundamentals.",
        "is_published": True,
        "questions": [
            {
                "text": "SI unit of force is:",
                "marks": 1,
                "choices": ["Joule", "Pascal", "Newton", "Watt"],
                "correct": 3,
            },
            {
                "text": "Newton's second law is commonly written as:",
                "marks": 2,
                "choices": ["E=mc^2", "F=ma", "pV=nRT", "V=IR"],
                "correct": 2,
            },
            {
                "text": "If velocity is constant, acceleration is:",
                "marks": 1,
                "choices": ["Positive", "Negative", "Zero", "Infinite"],
                "correct": 3,
            },
        ],
    },
    {
        "course_code": "PHY201",
        "title": "Electromagnetism Essentials",
        "description": "Electric field, current, and magnetic effects.",
        "is_published": True,
        "questions": [
            {
                "text": "Unit of electric current is:",
                "marks": 1,
                "choices": ["Volt", "Ampere", "Ohm", "Tesla"],
                "correct": 2,
            },
            {
                "text": "Ohm's law is:",
                "marks": 2,
                "choices": ["P=IV", "V=IR", "F=qE", "B=muH"],
                "correct": 2,
            },
            {
                "text": "A stronger magnetic field around a wire is produced by:",
                "marks": 1,
                "choices": ["Less current", "More current", "No current", "Thicker paper"],
                "correct": 2,
            },
        ],
    },
    {
        "course_code": "CS201",
        "title": "Data Structures Midpoint Quiz",
        "description": "Arrays, linked lists, stacks, queues, and complexity.",
        "is_published": True,
        "questions": [
            {
                "text": "Average-case lookup in a hash table is roughly:",
                "marks": 2,
                "choices": ["O(1)", "O(n)", "O(log n)", "O(n log n)"],
                "correct": 1,
            },
            {
                "text": "Which structure is best for LIFO operations?",
                "marks": 1,
                "choices": ["Queue", "Stack", "Heap", "Tree"],
                "correct": 2,
            },
            {
                "text": "Binary search requires data to be:",
                "marks": 1,
                "choices": ["Random", "Sorted", "Encrypted", "Hashed"],
                "correct": 2,
            },
            {
                "text": "What is time complexity of linear search?",
                "marks": 1,
                "choices": ["O(1)", "O(log n)", "O(n)", "O(n^2)"],
                "correct": 3,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with demo users, courses, and enrollments."

    def handle(self, *args, **options):
        with transaction.atomic():
            self._seed_users()
            self._seed_courses()
            self._seed_enrollments()
            self._seed_quizzes()
        self.stdout.write(self.style.SUCCESS("✓ Seed complete."))

    def _seed_users(self):
        for spec in USERS:
            obj, created = User.objects.update_or_create(
                username=spec.username,
                defaults={
                    "first_name": spec.first_name,
                    "last_name": spec.last_name,
                    "email": spec.email,
                    "role": spec.role,
                    "is_staff": spec.is_staff,
                    "is_superuser": spec.is_superuser,
                    "password": spec.password,
                },
            )
            label = "created" if created else "updated"
            self.stdout.write(f"  {label}: {obj.username} ({obj.role})")

    def _seed_courses(self):
        for code, title, teacher_username in COURSES_SPEC:
            teacher = User.objects.get(username=teacher_username)
            obj, created = Course.objects.update_or_create(
                code=code,
                defaults={"title": title, "teacher": teacher},
            )
            label = "created" if created else "updated"
            self.stdout.write(f"  {label} course: {obj.code} - {obj.title}")

    def _seed_enrollments(self):
        for student_username, course_code, status in ENROLLMENTS_SPEC:
            student = User.objects.get(username=student_username)
            course = Course.objects.get(code=course_code)
            obj, created = Enrollment.objects.update_or_create(
                student=student,
                course=course,
                defaults={"status": status},
            )
            label = "enrolled" if created else "updated"
            self.stdout.write(f"  {label}: {student.username} → {course_code} ({status})")

    def _recommended_duration_minutes(self, quiz_spec):
        total_marks = sum(q_spec["marks"] for q_spec in quiz_spec["questions"])
        question_count = len(quiz_spec["questions"])
        estimated = (
            QUIZ_DURATION_BASE_MINUTES
            + (total_marks * QUIZ_DURATION_PER_MARK)
            + (question_count * QUIZ_DURATION_PER_QUESTION)
        )
        return max(QUIZ_DURATION_MIN, min(QUIZ_DURATION_MAX, estimated))

    def _seed_quizzes(self):
        for quiz_spec in QUIZZES_SPEC:
            course = Course.objects.select_related("teacher").get(code=quiz_spec["course_code"])
            created_by = course.teacher or User.objects.filter(role=TEACHER).first()
            duration_minutes = quiz_spec.get(
                "duration_minutes",
                self._recommended_duration_minutes(quiz_spec),
            )
            quiz, created = Quiz.objects.update_or_create(
                course=course,
                title=quiz_spec["title"],
                defaults={
                    "description": quiz_spec["description"],
                    "is_published": quiz_spec["is_published"],
                    "duration_minutes": duration_minutes,
                    "created_by": created_by,
                },
            )
            label = "created" if created else "updated"
            self.stdout.write(f"  {label} quiz: {quiz.title} ({course.code}, {duration_minutes} min)")

            QuizQuestion.objects.filter(quiz=quiz).delete()
            for idx, q_spec in enumerate(quiz_spec["questions"], start=1):
                question = QuizQuestion.objects.create(
                    quiz=quiz,
                    text=q_spec["text"],
                    marks=q_spec["marks"],
                    order=idx,
                )
                for choice_index, choice_text in enumerate(q_spec["choices"], start=1):
                    QuizChoice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=choice_index == q_spec["correct"],
                    )
