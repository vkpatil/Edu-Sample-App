# Infra (Bicep)

This folder contains a single-resource-group Bicep deployment for:

- VNet + subnets + NSGs
- App Service Plan + Linux Web App (Django)
- PostgreSQL Flexible Server (private access in delegated subnet + private DNS)
- Key Vault (private endpoint + private DNS)
- Application Gateway (WAF v2) routing to the Web App over the Web App private endpoint + private DNS

## Files

- `infra/main.bicep` main template
- `infra/dev.bicepparam` sample parameters (no secrets)
- `infra/TODO.md` deployment checklist

## Deploy

Requires Azure CLI with Bicep support.

```bash
az deployment group create -g <resource-group> -f infra/main.bicep -p infra/dev.bicepparam \
  -p postgresAdminPassword='<secure>' \
  -p appGatewaySslPfxBase64='<base64-pfx>' \
  -p appGatewaySslPfxPassword='<secure>'
```

Notes:

- `webAppName`, `keyVaultName`, and `postgresServerName` must be globally unique.
- PostgreSQL Flexible Server defaults to Burstable in `dev` (`Standard_B2s`, `Burstable`).
- `privateEndpointsSubnetPrefix` and `appGatewaySubnetPrefix` defaults are placeholders; adjust to match your IP plan.
- App Service deploy operations typically use the SCM (Kudu) endpoint; this template provisions a separate private endpoint + DNS zone for SCM.
- PostgreSQL Flexible “private access” uses a delegated subnet + `private.postgres.database.azure.com` (it’s private, but not a Private Endpoint resource).
