Already Exists
vnet-dev-core
10.50.0.0/16
 
Manual Deployment Required
Subnet
sn-dev-apps - 10.50.1.0/24
sn-dev-db - 10.50.2.0/24
App Services - P2V3
10.50.1.10?
Database
Postgres Flexible
10.50.2.10
Key Vault
Standard
10.50.3.10?
App Insights
 
Firewall Rules
App Services -> Database
TCP 5432 (postgres app?)
App Services -> Hasura
TCP443 (ssl app)
App Services -> Entra
Azure-to-MS-SSO Rule
Add to MS-SSO-Servers object group
Bastions -> Database
TCP5432 (postgres?)
TCP9999 (Unknown App)
TCP1433 (sql?)
Users -> App Gateway
TCP443 (ssl app)
App Gateway -> App Services
TCP443 (ssl app)