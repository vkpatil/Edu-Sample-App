# CPCC PostgreSQL Migration – Complete Pilot Plan

## Document Information
- **Customer:** Central Piedmont Community College (CPCC)
- **Workload:** Elections Application (Pilot – Dev)
- **Source:** On‑prem / existing PostgreSQL
- **Target:** Azure Database for PostgreSQL – Flexible Server
- **Migration Type:** Offline (Dump & Restore) for Pilot
- **Author:** Microsoft CSA (Vijay Patil)
- **Last Updated:** March 2026

---

## 1. Purpose and Scope
This document provides a **complete, end‑to‑end migration plan** for executing the PostgreSQL pilot migration for CPCC. The pilot is intentionally designed to be:
- Low risk
- Repeatable
- Observable
- Aligned to CPCC’s hub‑and‑spoke network model

The pilot validates database migration mechanics, networking, SSL behavior, and application connectivity before scaling to production workloads.

---

## 2. Migration Strategy Overview

### Pilot Approach (Dev)
- **Method:** Offline dump & restore
- **Why:**
  - Simplest execution model
  - Controlled downtime window
  - Clear failure modes
  - Ideal for validating connectivity and SSL early

### Production Direction (Future)
- **Method:** Azure PostgreSQL Migration Service (Online)
- **Why:**
  - Minimal downtime
  - Built‑in validation and cutover
  - Better for production workloads

---

## 3. Roles and Responsibilities

### CPCC Infrastructure / Network Team
- Provision Azure PostgreSQL Flexible Server
- Configure VPN / ExpressRoute routing
- Configure firewall rules (TCP 5432)
- Validate DNS and private connectivity

### CPCC Application Team
- Execute database dump and restore
- Update application connection strings
- Perform functional and smoke testing

### Joint Responsibilities
- Connectivity and SSL validation
- Role and permission alignment
- Pilot success sign‑off

---

## 4. Preconditions and Readiness Checklist

✅ Azure PostgreSQL Flexible Server (Dev) provisioned  
✅ Network path available from migration host to source and target  
✅ Firewall rules allow TCP 5432  
✅ Bash environment available (WSL, Linux VM, or Azure Cloud Shell)  
✅ PostgreSQL client tools installed:
- pg_dump
- pg_restore
- psql
- pg_dumpall

> Client tools must be the **same or newer major version** than the PostgreSQL source/target.

---

## 5. Pilot Migration Flow

1. Validate connectivity
2. Export roles (optional but recommended)
3. Dump schema and data
4. Create target database
5. Restore roles
6. Restore data
7. Post‑migration validation
8. Application smoke testing

---

## 6. Step‑by‑Step Execution Runbook

### Step 1 – Validate Connectivity
```bash
psql -h <source_host> -U <source_user> -d postgres
psql -h <target_flexible_server_fqdn> -U <target_admin_user> -d postgres
```
Successful connection confirms routing, firewall, and SSL compatibility.

---

### Step 2 – Export Roles and Users (Recommended)
```bash
pg_dumpall -r   -h <source_host>   -U <source_admin_user>   > roles.sql
```

If the source is Azure Flexible Server:
```bash
pg_dumpall -r --no-role-passwords   -h <source_host>   -U <source_admin_user>   > roles.sql
```

Optional cleanup:
```bash
sed -i '/azure_superuser/d; /azure_pg_admin/d; /azuresu/d; /^CREATE ROLE replication/d; /^ALTER ROLE replication/d; /^ALTER ROLE/ {s/NOSUPERUSER//; s/NOBYPASSRLS//;}' roles.sql
```

---

### Step 3 – Dump Application Database

**Option A – Plain SQL (Small/Medium DB):**
```bash
pg_dump   -h <source_host>   -U <source_user>   -d <source_db_name>   > app_db.sql
```

**Option B – Directory Format (Larger DB, Faster):**
```bash
pg_dump -Fd   -h <source_host>   -U <source_user>   -d <source_db_name>   -f app_db_dump
```

---

### Step 4 – Create Target Database
```bash
createdb <target_db_name>   -h <target_flexible_server_fqdn>   -U <target_admin_user>
```

---

### Step 5 – Restore Roles (If Exported)
```bash
psql   -h <target_flexible_server_fqdn>   -U <target_admin_user>   -f roles.sql
```

---

### Step 6 – Restore Application Data

**Plain SQL Restore:**
```bash
psql   -h <target_flexible_server_fqdn>   -U <target_admin_user>   -d <target_db_name>   -f app_db.sql | tee restore.log
```

**Directory Restore:**
```bash
pg_restore   -h <target_flexible_server_fqdn>   -U <target_admin_user>   -d <target_db_name>   -j 4   app_db_dump | tee restore.log
```

---

## 7. Post‑Migration Validation

### Database Validation
- Review restore.log for errors
- Confirm critical tables exist
- Validate row counts

```sql
SELECT COUNT(*) FROM <critical_table>;
```

### Permission Validation
- Application role can connect
- No superuser dependencies

---

## 8. Application Validation (Pilot)

1. Update application connection string
2. Restart App Service
3. Execute smoke tests:
   - App startup
   - Login
   - Core Elections workflow

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|-----|-----------|
| SSL / cipher mismatch | Validate connectivity with psql first |
| Firewall or routing issue | Test before data movement |
| Role mismatch | Explicit role export and cleanup |
| Insufficient storage | Allocate ~25% buffer for WAL |

---

## 10. Pilot Exit Criteria

✅ Database migrated successfully  
✅ Application connects to Azure PostgreSQL  
✅ Core functionality validated  
✅ Migration steps documented and repeatable

---

## 11. Next Steps After Pilot

- Decide online migration service for production
- Harden networking (private endpoints, DNS)
- Automate migration steps
- Convert this runbook into production checklist

---

## 12. Document Control
- **Owner:** CPCC / Microsoft
- **Change Control:** Update per migration wave
