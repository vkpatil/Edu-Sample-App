# Edu App Azure Architecture

This diagram reflects the infrastructure defined in the Bicep templates for the edu-app deployment. It shows the network boundaries, ingress path, application hosting, data tier, and private connectivity model.

## Summary

The design uses Azure Application Gateway as the public HTTPS entry point. Traffic is routed privately to an Azure App Service Linux Web App hosting the Django application. The web app is integrated with a dedicated application subnet for outbound traffic and accesses supporting services over private networking.

Azure Database for PostgreSQL Flexible Server is deployed with private access in a delegated subnet and is configured for a Burstable SKU by default for the dev environment. Azure Key Vault is exposed only through a private endpoint. Private DNS zones provide name resolution for the web app, SCM endpoint, Key Vault, and PostgreSQL.

## Architecture Diagram

```mermaid
graph TB
    Internet[(Users / Internet)]

    subgraph Edge[Ingress Layer]
        PIP["Public IP<br/>Standard Static"]
        AGW["Application Gateway<br/>WAF v2<br/>HTTPS Listener :443"]
    end

    subgraph Network[Virtual Network: vnet-dev-core]
        subgraph AGWSubnet[App Gateway Subnet<br/>10.50.4.0/24]
            AGWSN["Subnet + NSG<br/>Inbound 443<br/>GatewayManager ports"]
        end

        subgraph AppSubnet[App Service Integration Subnet<br/>10.50.1.0/24]
            APPSN["Subnet + NSG<br/>Outbound to Postgres 5432<br/>Outbound to Private Endpoints 443"]
        end

        subgraph DbSubnet[PostgreSQL Delegated Subnet<br/>10.50.2.0/24]
            DBSN["Delegated Subnet + NSG<br/>Microsoft.DBforPostgreSQL/flexibleServers"]
            PG["Azure Database for PostgreSQL<br/>Flexible Server<br/>PostgreSQL 16<br/>Burstable / Standard_B2s"]
        end

        subgraph PeSubnet[Private Endpoints Subnet<br/>10.50.3.0/24]
            PESN["Subnet + NSG<br/>Private Endpoint policies disabled"]
            PEWEB["Private Endpoint<br/>Web App sites"]
            PESCM["Private Endpoint<br/>Web App scm"]
            PEKV["Private Endpoint<br/>Key Vault vault"]
        end
    end

    subgraph AppLayer[Application Layer]
        ASP["App Service Plan<br/>Linux"]
        WEB["Django Web App<br/>Python 3.12<br/>Public access disabled<br/>System-assigned managed identity"]
    end

    subgraph Security[Security Layer]
        KV["Azure Key Vault<br/>RBAC enabled<br/>Public access disabled"]
    end

    subgraph DNS[Private DNS]
        DNSWEB["privatelink.azurewebsites.net"]
        DNSSCM["privatelink.scm.azurewebsites.net"]
        DNSKV["privatelink.vaultcore.azure.net"]
        DNSPG["private.postgres.database.azure.com"]
    end

    Internet ==> |HTTPS 443| PIP
    PIP --> AGW
    AGW --> |Private backend HTTPS| PEWEB
    AGW -.-> |Health probe / backend hostname| DNSWEB
    AGW --> AGWSN

    ASP --> WEB
    WEB --> |VNet integration| APPSN
    WEB --> |App settings / secret usage| KV
    WEB --> |PostgreSQL 5432| PG
    WEB -.-> |Deployment via Kudu SCM| PESCM

    PEWEB --> WEB
    PESCM --> WEB
    PEKV --> KV

    DNSWEB --> PEWEB
    DNSSCM --> PESCM
    DNSKV --> PEKV
    DNSPG --> PG

    APPSN --> |Private endpoint access 443| PESN
    APPSN --> |DB access 5432| DBSN
    PESN --> PEWEB
    PESN --> PESCM
    PESN --> PEKV
    DBSN --> PG
```

## Presentation Diagram

```mermaid
graph LR
    U["Users"] -->|HTTPS| AGW["Application Gateway\nWAF v2"]
    AGW -->|Private backend HTTPS| WEBPE["Web App Private Endpoint"]
    WEBPE --> WEB["Django Web App\nAzure App Service"]
    WEB -->|Runs on| ASP["Linux App Service Plan"]
    WEB -->|Reads secrets| KVPE["Key Vault Private Endpoint"]
    KVPE --> KV["Azure Key Vault"]
    WEB -->|PostgreSQL 5432| PG["PostgreSQL Flexible Server\nBurstable B2s"]

    subgraph VNet["Virtual Network"]
        AGW
        WEBPE
        KVPE
        WEB
        PG
    end
```

## Deployment Flow Diagram

```mermaid
graph TB
    Dev["Engineer / CI Runner"] -->|az deployment group create| Bicep["Bicep Template + Params"]
    Bicep --> RG["Azure Resource Group"]

    RG --> Net["VNet + Subnets + NSGs"]
    RG --> Edge["Public IP + Application Gateway"]
    RG --> App["App Service Plan + Web App"]
    RG --> Data["PostgreSQL Flexible Server"]
    RG --> Sec["Key Vault"]
    RG --> Dns["Private DNS Zones"]
    RG --> Pe["Private Endpoints\nWeb / SCM / Key Vault"]

    Secrets["Deploy-time Secrets\nPostgres Password\nTLS PFX + Password"] -.-> Bicep
    Dns --> Pe
    Net --> App
    Net --> Data
    Net --> Pe
    Edge --> Pe
    App --> Data
    App --> Sec
```

## Executive Overview

```mermaid
graph LR
    Users["Users"] --> Gateway["Secure Entry\nApplication Gateway"]
    Gateway --> App["Web Application\nDjango on App Service"]
    App --> Database["Managed Database\nPostgreSQL Flexible Server"]
    App --> Secrets["Secrets Management\nAzure Key Vault"]

    PrivateNet["Private Network Boundaries"] -.-> Gateway
    PrivateNet -.-> App
    PrivateNet -.-> Database
    PrivateNet -.-> Secrets
```

## VNet, Subnets, And Application Systems

```mermaid
graph TB
    Internet[(Users)] -->|HTTPS 443| AGW["Application Gateway\nWAF v2"]

    subgraph VNet["VNet: vnet-dev-core"]
        subgraph SubnetAgw["Subnet: App Gateway\n10.50.4.0/24"]
            AGW
        end

        subgraph SubnetApps["Subnet: App Service Integration\n10.50.1.0/24"]
            WEB["Django Web App\nAzure App Service"]
        end

        subgraph SubnetDb["Subnet: PostgreSQL Delegated\n10.50.2.0/24"]
            PG["PostgreSQL Flexible Server\nBurstable B2s"]
        end

        subgraph SubnetPe["Subnet: Private Endpoints\n10.50.3.0/24"]
            PEWEB["Private Endpoint\nWeb App"]
            PESCM["Private Endpoint\nSCM / Kudu"]
            PEKV["Private Endpoint\nKey Vault"]
        end
    end

    ASP["App Service Plan\nLinux"] --> WEB
    AGW -->|Private backend HTTPS| PEWEB
    PEWEB --> WEB
    PESCM -.->|Deployment path| WEB
    WEB -->|PostgreSQL 5432| PG
    WEB -->|Secrets / config| PEKV
    PEKV --> KV["Azure Key Vault"]
```

## Resource Inventory

| Layer | Resource | Notes |
| --- | --- | --- |
| Ingress | Application Gateway | WAF v2, public HTTPS entry point |
| Ingress | Public IP | Standard static IP for gateway frontend |
| Compute | App Service Plan | Hosts Linux Web App |
| Compute | Web App | Django app, Python 3.12, public network disabled |
| Data | PostgreSQL Flexible Server | Private access, delegated subnet, Burstable default |
| Security | Key Vault | RBAC enabled, private endpoint only |
| Network | VNet + 4 subnets | App Gateway, App Service, DB, and Private Endpoints |
| DNS | 4 private DNS zones | Web App, SCM, Key Vault, PostgreSQL |

## Key Flows

- Users enter through Application Gateway over HTTPS.
- Application Gateway forwards traffic to the Web App through its private endpoint.
- The Web App reaches PostgreSQL through delegated private networking.
- The Web App reaches Key Vault through a private endpoint.
- Private DNS zones resolve all private endpoints and private PostgreSQL hostnames inside the VNet.

## Notes

- This is an intended-state architecture from IaC, not a discovered live-resource diagram.
- PostgreSQL is set to Burstable for dev defaults, not General Purpose.
- Deployment secrets and certificate material still need to be supplied at deploy time.
- The presentation and executive views are simplified from the engineering view for readability.