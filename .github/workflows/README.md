# GitHub Actions CI/CD Runbook

This project uses the workflow at `.github/workflows/ci-cd.yml` to run tests and deploy the Django app to Azure Web App.

## Pipeline Overview

- Trigger on pull requests to `main`: runs CI only
- Trigger on push to `main`: runs CI, then deploys to Azure Web App
- Trigger on manual run (`workflow_dispatch`): runs the same workflow from GitHub Actions UI

Job flow:

1. `ci`
2. `deploy` (only after `ci` succeeds, and not on pull requests)

## Workflow File

- `.github/workflows/ci-cd.yml`
- `.github/workflows/db-migration-deploy.yml`

## Database Migration Pipeline

The database pipeline is separated from app deployment so schema updates are controlled and auditable.

### Triggers

- Pull requests to `main` when migration-related files change
- Pushes to `main` when migration-related files change
- Manual execution (`workflow_dispatch`) for actual migration deployment

### Jobs

- `migration_validation`
- Runs `makemigrations --check --dry-run`
- Runs `migrate --plan`
- Uses an ephemeral PostgreSQL service container

- `deploy_migrations`
- Runs only when manually triggered and `apply=true`
- Applies migrations with `python manage.py migrate --noinput`
- Uses target GitHub Environment (`dev` or `prod`)

### Required Secrets For Migration Deployment

Set these as Environment Secrets in GitHub (`dev` and/or `prod`):

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

### How To Run A Database Deployment

1. Open GitHub Actions and select `Django DB Migration Pipeline`.
2. Click `Run workflow`.
3. Select environment (`dev` or `prod`).
4. Set `apply` to `true`.
5. Run and monitor the `deploy_migrations` job logs.

### Important Notes

- If your target PostgreSQL server is on a private network (for example, VNet only), GitHub-hosted runners may not reach it.
- In that case, run this workflow on a self-hosted runner with network access to the database.

## What CI Does

The `ci` job runs on Ubuntu and provisions PostgreSQL as a service container.

It then:

1. Checks out source code
2. Sets up Python 3.13
3. Installs dependencies from `requirements.txt`
4. Runs migrations: `python manage.py migrate --noinput`
5. Runs tests: `python manage.py test`

CI environment variables are injected in the workflow for test execution (database host is `127.0.0.1`).

## What CD Does

The `deploy` job:

1. Depends on `ci` success (`needs: ci`)
2. Runs only for `main` pushes (not pull requests)
3. Deploys app package to Azure Web App using `azure/webapps-deploy@v3`
4. Publishes deployment URL in the `dev` GitHub Environment

## One-Time Setup (How To Create This In A New Repo)

- Create `.github/workflows/ci-cd.yml`.
- In GitHub repo, go to Settings > Secrets and variables > Actions, then add `AZURE_WEBAPP_NAME` and `AZURE_WEBAPP_PUBLISH_PROFILE`.
- In GitHub repo, go to Settings > Environments, create `dev` environment.
- In Azure Web App Configuration, set app settings listed below.
- Push code to `main` (or open PR) and verify workflow execution in Actions tab.

## Required GitHub Secrets

- `AZURE_WEBAPP_NAME`: Azure Web App name
- `AZURE_WEBAPP_PUBLISH_PROFILE`: publish profile XML from Azure Web App

How to get publish profile:

1. Azure Portal > App Service > your app
2. Select `Get publish profile`
3. Copy file contents and save as GitHub secret value

## Required Azure Web App App Settings

Set these values in Azure Portal > App Service > Configuration:

- `SECRET_KEY`
- `DEBUG` (recommended `0` for cloud)
- `ALLOWED_HOSTS` (include your Azure hostname)
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Example `ALLOWED_HOSTS` value:

- `your-app-name.azurewebsites.net,localhost,127.0.0.1`

## Branch And Environment Strategy

- `main` branch is deployment branch in this workflow
- Pull requests validate quality but do not deploy
- `dev` GitHub Environment is currently used for deployment target metadata

## Troubleshooting

### CI fails to connect to database

- Confirm PostgreSQL service block exists in workflow
- Confirm `POSTGRES_HOST` is `127.0.0.1`
- Check logs for `pg_isready` health status

### Tests fail after migrations

- Run locally with same commands:
  - `python manage.py migrate --noinput`
  - `python manage.py test`
- Verify migrations are committed

### Deploy step fails with publish profile error

- Re-download publish profile from Azure Portal
- Replace `AZURE_WEBAPP_PUBLISH_PROFILE` secret
- Confirm `AZURE_WEBAPP_NAME` exactly matches the App Service name

### App deploys but returns runtime errors

- Verify Azure App Settings values
- Verify database host is reachable from the app environment
- Check App Service Log Stream and application logs

## Suggested Next Improvements

- Add lint/security checks (for example, Ruff and Bandit) before tests
- Split deployments into `dev` and `prod` workflows with branch/tag promotion
- Add database migration safety checks for production
- Use OpenID Connect (`azure/login`) instead of publish profile for stronger security
