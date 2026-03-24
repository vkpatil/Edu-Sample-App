# Key Vault Integration Guide

This document explains how to set up and use Azure Key Vault for secure secret management.

## Quick Start

### Local Development (No Key Vault Needed)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your local values (all defaults are provided)

3. Run the app:
   ```bash
   python manage.py runserver
   ```

The `SecretsManager` will automatically use environment variables when `DISABLE_KEY_VAULT=1` is set.

### Production with Azure Key Vault

Follow these steps when deploying to Azure:

## Step 1: Create Azure Key Vault (via Bicep)

The `infra/main.bicep` template automatically creates:
- Azure Key Vault (standard tier, private access only)
- Private endpoint for secure access
- Private DNS zone for resolution
- RBAC role assignment for the web app's managed identity

Deploy the infrastructure:
```bash
az deployment group create \
  --resource-group <your-rg> \
  --template-file infra/main.bicep \
  --parameters infra/dev.bicepparam \
  --parameters postgresAdminPassword=<secure-password>
```

## Step 2: Add Secrets to Key Vault

After deployment, add your application secrets:

```bash
# Get the vault name from deployment output
VAULT_NAME=$(az deployment group show \
  --resource-group <your-rg> \
  --name <deployment-name> \
  --query 'properties.outputs.keyVaultName.value' -o tsv)

# Add secrets (use hyphens, not underscores)
az keyvault secret set --vault-name $VAULT_NAME --name SECRET-KEY --value "your-django-secret-key"
az keyvault secret set --vault-name $VAULT_NAME --name POSTGRES-PASSWORD --value "your-postgres-password"
az keyvault secret set --vault-name $VAULT_NAME --name POSTGRES-USER --value "edusys"
az keyvault secret set --vault-name $VAULT_NAME --name POSTGRES-DB --value "edusys_prod"
```

## Step 3: Configure App Service

The Bicep template automatically sets the `AZURE_KEY_VAULT_URL` app setting, and the web app's managed identity has `Key Vault Secrets User` RBAC role.

You can verify:
```bash
# Check app settings
az webapp config appsettings list \
  --resource-group <your-rg> \
  --name <app-name> \
  --query "[?name=='AZURE_KEY_VAULT_URL']"
```

## Step 4: Test Key Vault Access

Connect to the deployed app and verify secrets are loaded:

```bash
# SSH into the app or use Azure Shell to test
curl https://<app-name>.azurewebsites.net/

# Check logs for any Key Vault errors
az webapp log tail \
  --resource-group <your-rg> \
  --name <app-name>
```

## Secret Names

The application uses Python environment variable names (with underscores). Key Vault automatically converts them to using hyphens:

| Python Variable | Key Vault Secret Name |
| --- | --- |
| SECRET_KEY | SECRET-KEY |
| POSTGRES_PASSWORD | POSTGRES-PASSWORD |
| POSTGRES_USER | POSTGRES-USER |
| POSTGRES_DB | POSTGRES-DB |
| EMAIL_HOST | EMAIL-HOST |
| EMAIL_PORT | EMAIL-PORT |
| GET_SECRET_FROM_EMAIL | DEFAULT-FROM-EMAIL |

## Troubleshooting

### Secret Not Found in Key Vault

```
ValueError: Secret 'POSTGRES-PASSWORD' not found in Key Vault or environment variables
```

**Solution**: Verify the secret exists and the app's managed identity has access:

```bash
# List secrets
az keyvault secret list --vault-name $VAULT_NAME

# Check RBAC role
az role assignment list \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/$VAULT_NAME \
  --query "[?principalName=='<web-app-name>']"
```

### Authentication Errors

```
AuthenticationError: Failed to authenticate
```

**Possible causes**:
1. App's managed identity doesn't have the role
2. Key Vault network access is restricted (check firewall rules)
3. Managed identity is not enabled on the app

**Solution**:
```bash
# Enable managed identity
az webapp identity assign \
  --resource-group <your-rg> \
  --name <app-name> \
  --query principalId -o tsv

# Grant role (replace <principal-id> from above)
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee <principal-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/$VAULT_NAME
```

### Key Vault URL Not Set

```
WARNING: AZURE_KEY_VAULT_URL not set. Will use environment variables only.
```

**Solution**: Verify the app setting is configured:

```bash
az webapp config appsettings set \
  --resource-group <your-rg> \
  --name <app-name> \
  --settings AZURE_KEY_VAULT_URL=https://<vault-name>.vault.azure.net/
```

## Security Best Practices

1. **Rotate secrets regularly**
   ```bash
   # Update a secret
   az keyvault secret set --vault-name $VAULT_NAME --name SECRET-KEY --value "new-value"
   ```

2. **Monitor access**
   - Enable Key Vault diagnostic logging
   - Review access logs in Azure Monitor

3. **Limit blast radius**
   - Use separate vaults for dev/staging/production
   - Use managed identities (not connection strings)

4. **Backup and recovery**
   - Enable soft delete and purge protection
   - Regularly backup secrets

## Code Examples

### Using Secrets in Django Apps

```python
# In config/settings.py (already configured)
from config.secrets import get_secrets_manager

secrets = get_secrets_manager()

# Get a required secret
db_password = secrets.get("POSTGRES_PASSWORD")

# Get optional secret with default
debug = secrets.get_bool("DEBUG", default=False)

# Get list of values
allowed_hosts = secrets.get_list("ALLOWED_HOSTS", default=["localhost"])
```

### Custom Application Code

```python
# In any Django view or task
from config.secrets import get_secrets_manager

secrets = get_secrets_manager()

# Get a secret
api_key = secrets.get("MY_API_KEY")

# Get with default for optional settings
timeout = secrets.get_int("REQUEST_TIMEOUT", default=30)
```

## Migration from Environment Variables

No code changes needed! The migration is transparent:

1. **Before**: Secrets in `.env` file (local dev) or app settings (Azure)
2. **Add**: Create a Key Vault and add secrets
3. **Set**: Configure `AZURE_KEY_VAULT_URL` environment variable
4. **Done**: Secrets are now retrieved from Key Vault (with fallback to env vars)

The `SecretsManager` checks Key Vault first, then falls back to environment variables.

## References

- [Azure Key Vault Python SDK](https://docs.microsoft.com/en-us/python/api/azure-keyvault-secrets)
- [Azure SDK DefaultAzureCredential](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)
- [Django Settings Management](https://docs.djangoproject.com/en/stable/topics/settings/)
- [Bicep Key Vault Template Reference](https://docs.microsoft.com/en-us/azure/templates/microsoft.keyvault/vaults)
