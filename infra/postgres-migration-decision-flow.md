# Azure PostgreSQL Migration Decision Flow

```mermaid
flowchart TD
    A([START]) --> B{Q1: Is downtime tolerance LOW\n(need minimal downtime)?}

    B -->|YES| C[Use Azure PostgreSQL Migration Service (ONLINE)]
    C --> C1[Run premigration validation\n(Validate / Validate and migrate)]
    C --> C2[Requires CDC/logical decoding\nprerequisites + cutover step]

    B -->|NO| D[Use Dump & Restore (OFFLINE)]
    D --> D1[Downtime = dump + restore\n+ validation window]

    C2 --> E
    D1 --> E

    E{Q2: Is your source reachable only\nvia private network (no public IP)?}

    E -->|YES| F[Ensure VPN/ExpressRoute +\nVNet-integrated target; follow migration\nservice networking scenario OR run\ndump/restore from a connected host]

    E -->|NO| G[Public access scenario supported\n(ensure 5432 reachability)]

    F --> H
    G --> H

    H{Q3: Database size / time\nwindow concerns?}

    H -->|Large DB / tight window| I[Prefer directory format + parallelism\n(-Fd / pg_restore)]
    H -->|Small/medium DB| J[Plain format is simplest\n(pg_dump + psql)]

    I --> K
    J --> K

    K{Q4: Need roles/users preserved?}

    K -->|YES| L[Include pg_dumpall -r\n(and handle Flexible Server\npassword restrictions)]
    K -->|NO| M[Migrate schema/data only]

    L --> N([END])
    M --> N
```
