# EduSys Django Web App

Professional educational management system built with Django, PostgreSQL, Docker, MailHog, and Bootstrap.

## Stack

- Django 5.1
- PostgreSQL (db/user/password: `edusys`)
- Docker Compose for local development
- MailHog for development email capture
- Bootstrap 5 with custom branding
- Azure Key Vault for production secrets management

## User Roles

- Super Admin
- Admin
- Teacher
- Student

## Quick Start

1. Copy env template:

```bash
cp .env.example .env
```

2. Build and run:

```bash
docker compose up --build
```

3. Open app:

- App: <http://localhost:8000>
- MailHog: <http://localhost:8025>

## Documentation

### Infrastructure & Deployment
- **GitHub Actions**: `.github/workflows/README.md` - CI/CD pipeline setup and troubleshooting
- **Database Migrations**: `.github/workflows/db-migration-deploy.yml` - Schema migration workflow
- **Architecture**: `infra/architecture.md` - System design and resource diagrams
- **Infrastructure as Code**: `infra/main.bicep` - Azure resource provisioning template

### Secrets Management
- **Key Vault Setup**: `KEYVAULT_SETUP.md` - Step-by-step guide for Azure Key Vault integration
- **Key Vault Implementation**: `KEYVAULT_IMPLEMENTATION.md` - Technical overview and architecture
- **Key Vault Details**: `config/KEY_VAULT_SETUP.md` - API reference and best practices

## Local Development (without Docker)

1. Create and activate virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure PostgreSQL is running with db/user/password as `edusys`.
4. Copy `.env.example` to `.env`
5. Run migrations: `python manage.py migrate`
6. Create admin user: `python manage.py createsuperuser`
6. Start app: `python manage.py runserver`

## Core Routes

- `/` home page
- `/accounts/login/` login
- `/accounts/register/` student signup
- `/dashboard/` role-aware dashboard
- `/school/courses/` course catalog
- `/school/enroll/` student enrollment form
- `/school/enrollments/` enrollment listing and status updates

## Access Matrix

### Route Access (by Role)

| Route | Student | Teacher | Admin | Super Admin | Notes |
|---|---|---|---|---|---|
| `/dashboard/` | Yes | Yes | Yes | Yes | Role-specific dashboard template |
| `/accounts/profile/` | Yes | Yes | Yes | Yes | Own profile only |
| `/accounts/staff/create/` | No | No | Yes | Yes | Staff management only |
| `/accounts/students/create/` | No | No | Yes | Yes | Student management only |
| `/school/courses/` | Yes | Yes | Yes | Yes | Teacher sees only own courses |
| `/school/courses/create/` | No | Yes | Yes | Yes | Teacher restricted to own assignment |
| `/school/enroll/` | Yes | No | No | No | Student self-enrollment |
| `/school/enrollments/` | Yes | Yes | Yes | Yes | Role-scoped data visibility |
| `/school/enrollments/create/` | No | Yes | Yes | Yes | Teacher can enroll only in own courses |
| `/school/enrollments/<id>/status/` | No | Yes | Yes | Yes | Teacher can update own courses only |
| `/school/quizzes/` | Yes | Yes | Yes | Yes | Role-scoped quiz listing |
| `/school/quizzes/create/` | No | Yes | Yes | Yes | Teacher can create for own courses |
| `/school/quizzes/<quiz_id>/questions/create/` | No | Yes | Yes | Yes | Teacher can edit own-course quizzes |
| `/school/quizzes/<quiz_id>/take/` | Yes | No | No | No | Student only, published + enrolled |
| `/school/quiz-attempts/<attempt_id>/result/` | Yes | Yes | Yes | Yes | Role-scoped result visibility |

### Data Visibility Rules

Student

- Courses: can browse course catalog.
- Enrollments: only own records.
- Quizzes: only published quizzes for currently enrolled courses.
- Results: only own attempts.

Teacher

- Courses: only courses where `course.teacher == request.user`.
- Enrollments: only enrollments for their courses.
- Quizzes: only quizzes for their courses (including drafts).
- Results: only attempts for quizzes in their courses.

Admin / Super Admin

- Courses, enrollments, quizzes, and results: full visibility.
- User management screens: accessible.

### Validation Notes

- Route and role checks are covered in `school/tests/test_role_access.py`.
- If test execution fails locally with `permission denied to create database`, grant the DB user permission to create test databases or run tests against a user with `CREATEDB` privilege.
