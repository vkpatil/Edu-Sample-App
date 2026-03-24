# Azure Key Vault Integration

This guide explains how to use Azure Key Vault to securely store and retrieve secrets in the Edu App.

## Overview

The app uses a `SecretsManager` helper class (`config/secrets.py`) that:

1. **Retrieves secrets from Azure Key Vault first** (production)
2. **Falls back to environment variables** (development, CI/CD)
3. **Supports default values** (for optional configuration)

This approach ensures the same code works in:
- Local development (using `.env` file)
- CI/CD pipelines (using GitHub Actions secrets)
- Azure production (using Azure Key Vault)

## Installation

A. Install Azure SDK dependencies:

```bash
pip install -r requirements.txt
```

This includes:
- `azure-identity`: For authentication (DefaultAzureCredential)
- `azure-keyvault-secrets`: For Key Vault access

B. Set up local development (no Key Vault needed):

```bash
# Use environment variables locally
DISABLE_KEY_VAULT=1 python manage.py runserver
```

## Configuration

### For Azure Production

1. **Create an Azure Key Vault** (via Bicep in `infra/main.bicep`):

```bicep
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${environmentName}-${uniqueSuffix}'
  location: location
  properties: {
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: webAppIdentity.properties.principalId // App's managed identity
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
  }
}
```

2. **Add secrets to Key Vault**:

```bash
az keyvault secret set --vault-name <vault-name> --name SECRET-KEY --value <value>
az keyvault secret set --vault-name <vault-name> --name POSTGRES-PASSWORD --value <password>
# Note: Key Vault uses hyphens, Django uses underscores (automatically converted)
```

3. **Set the Key Vault URL environment variable on App Service**:

```bash
az webapp config appsettings set \
  --resource-group <group> \
  --name <app-name> \
  --settings AZURE_KEY_VAULT_URL=https://<vault-name>.vault.azure.net/
```

4. **Assign Managed Identity** to the App Service (via Bicep):

```bicep
identity: {
  type: 'UserAssigned'
  userAssignedIdentities: {
    '${managedIdentityId}': {}
  }
}
```

### For Local Development

Use `.env` file with environment variables:

```bash
# .env

# Django
SECRET_KEY=your-insecure-dev-key-only
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
POSTGRES_DB=edusys_dev
POSTGRES_USER=edusys
POSTGRES_PASSWORD=dev-password-only
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Email
EMAIL_HOST=mailhog
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@edusys.local

# Disable Key Vault for local dev
DISABLE_KEY_VAULT=1
```

### For GitHub Actions CI/CD

Set secrets in the GitHub Actions workflow:

```yaml
# .github/workflows/ci-cd.yml

env:
  POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
  POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
  DISABLE_KEY_VAULT: "1"  # Use env vars, not Key Vault in CI
```

## Usage in Code

### Basic Usage

```python
from config.secrets import get_secrets_manager

secrets = get_secrets_manager()

# Get required secret (raises ValueError if not found and no default)
db_password = secrets.get("POSTGRES_PASSWORD")

# Get optional secret with default
api_key = secrets.get("API_KEY", default="local-dev-key")
```

### Type-Safe Helpers

```python
# Boolean
is_debug = secrets.get_bool("DEBUG", default=False)

# Integer
port = secrets.get_int("POSTGRES_PORT", default=5432)

# List (comma or custom delimiter)
allowed_hosts = secrets.get_list("ALLOWED_HOSTS")
cors_origins = secrets.get_list("CORS_ORIGINS", delimiter="|")

# Optional (returns None if not found)
optional_value = secrets.get_optional("OPTIONAL_SETTING")
```

### In Django Settings

Already configured in `config/settings.py`:

```python
from config.secrets import get_secrets_manager

secrets = get_secrets_manager(use_key_vault=not os.getenv("DISABLE_KEY_VAULT"))

SECRET_KEY = secrets.get("SECRET_KEY", default="django-insecure-local-dev-only")
DEBUG = secrets.get_bool("DEBUG", default=True)
ALLOWED_HOSTS = secrets.get_list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": secrets.get("POSTGRES_DB", default="edusys"),
        "USER": secrets.get("POSTGRES_USER", default="edusys"),
        "PASSWORD": secrets.get("POSTGRES_PASSWORD", default="edusys"),
        "HOST": secrets.get("POSTGRES_HOST", default="db"),
        "PORT": secrets.get_int("POSTGRES_PORT", default=5432),
    }
}
```

## Secret Names

Map Django environment variables to Key Vault secret names (underscores become hyphens):

| Django Env Var | Key Vault Secret Name |
| --- | --- |
| `SECRET_KEY` | `SECRET-KEY` |
| `POSTGRES_PASSWORD` | `POSTGRES-PASSWORD` |
| `POSTGRES_USER` | `POSTGRES-USER` |
| `POSTGRES_DB` | `POSTGRES-DB` |
| `EMAIL_HOST` | `EMAIL-HOST` |
| `EMAIL_PORT` | `EMAIL-PORT` |
| `DEFAULT_FROM_EMAIL` | `DEFAULT-FROM-EMAIL` |

## Health Check

Check the status of the secrets manager:

```python
from config.secrets import get_secrets_manager

secrets = get_secrets_manager()
status = secrets.health_check()
print(status)
# Output:
# {
#   'key_vault_enabled': True,
#   'key_vault_initialized': True,
#   'key_vault_url': 'https://kv-example.vault.azure.net/',
#   'initialization_error': None
# }
```

## Fallback Behavior

If Key Vault is unavailable:

1. ✅ Local dev with `DISABLE_KEY_VAULT=1` → Uses environment variables only
2. ✅ CI/CD with no Azure credentials → Uses environment variables only
3. ✅ Production with managed identity but Key Vault down → Logs warning, returns default or raises error

## Security Best Practices

1. **Never commit secrets** to Git (`.env` is in `.gitignore`)
2. **Use managed identities** for Azure → no credentials to manage
3. **Rotate secrets regularly** in Key Vault
4. **Limit access** via Key Vault access policies (principle of least privilege)
5. **Audit access** via Azure Monitor and Key Vault diagnostics
6. **Use different vaults** for dev/staging/production

## Troubleshooting

### Key Vault Not Found

```
Failed to initialize Key Vault client: AuthenticationError
```

**Fix**: Ensure `AZURE_KEY_VAULT_URL` is set and your Azure identity has access.

### Secret Not Found

```
ValueError: Secret 'POSTGRES-PASSWORD' not found in Key Vault or environment variables
```

**Fix**: 
1. Verify secret exists: `az keyvault secret show --vault-name <vault> --name POSTGRES-PASSWORD`
2. Check permissions: `az keyvault show --name <vault> --query properties.accessPolicies`
3. Use a default value: `secrets.get("MISSING_SECRET", default="default-value")`

### Azure SDK Not Installed

```
Warning: Azure SDK not installed. Install with: pip install azure-identity azure-keyvault-secrets
```

**Fix**: Run `pip install -r requirements.txt`

## Migration Path

### From Environment Variables to Key Vault

No code changes needed! The `SecretsManager` automatically prefers Key Vault:

1. Create Key Vault secrets with same names (with hyphens)
2. Set `AZURE_KEY_VAULT_URL` environment variable
3. Secrets are now retrieved from Key Vault (fallback to env vars if not found)

### Removing Key Vault (Revert to Env Vars)

1. Unset `AZURE_KEY_VAULT_URL`
2. Or set `DISABLE_KEY_VAULT=1`
3. Code continues to work using environment variables

## Reference

- [Azure Key Vault documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Azure Identity SDK](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/identity/azure-identity/README.md)
- [Django settings best practices](https://docs.djangoproject.com/en/stable/topics/settings/)
