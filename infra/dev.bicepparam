using './main.bicep'

param environmentName = 'dev'
param namePrefix = 'edusys'

param location = 'eastus'

param vnetName = 'vnet-dev-core'
param vnetAddressSpaces = [
  '10.50.0.0/16'
]

param appsSubnetName = 'sn-dev-apps'
param appsSubnetPrefix = '10.50.1.0/24'

param dbSubnetName = 'sn-dev-db'
param dbSubnetPrefix = '10.50.2.0/24'

// Use a cost-effective Burstable tier for dev by default.
param postgresSkuName = 'Standard_B2s'
param postgresSkuTier = 'Burstable'

// Adjust these two if they overlap an existing allocation in your VNet.
param privateEndpointsSubnetPrefix = '10.50.3.0/24'
param appGatewaySubnetPrefix = '10.50.4.0/24'

// Provide these securely at deploy-time (do not commit secrets).
param postgresAdminPassword = ''
param appGatewaySslPfxBase64 = ''
param appGatewaySslPfxPassword = ''

