targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Environment name used for resource naming.')
param environmentName string = 'dev'

@description('Short prefix used for resource naming (letters/numbers only).')
param namePrefix string = 'edusys'

@description('VNet name.')
param vnetName string = 'vnet-${environmentName}-core'

@description('VNet address spaces.')
param vnetAddressSpaces array = [
  '10.50.0.0/16'
]

@description('Subnet used for App Service outbound VNet integration.')
param appsSubnetName string = 'sn-${environmentName}-apps'

@description('CIDR for the apps subnet (must be within VNet address spaces).')
param appsSubnetPrefix string = '10.50.1.0/24'

@description('Subnet used for Postgres Flexible Server private access (delegated).')
param dbSubnetName string = 'sn-${environmentName}-db'

@description('CIDR for the db subnet (must be within VNet address spaces).')
param dbSubnetPrefix string = '10.50.2.0/24'

@description('Subnet dedicated to private endpoints (recommended).')
param privateEndpointsSubnetName string = 'sn-${environmentName}-private-endpoints'

@description('CIDR for the private endpoints subnet (must be within VNet address spaces).')
param privateEndpointsSubnetPrefix string = '10.50.3.0/24'

@description('Subnet dedicated to Application Gateway.')
param appGatewaySubnetName string = 'sn-${environmentName}-appgw'

@description('CIDR for the Application Gateway subnet (must be within VNet address spaces).')
param appGatewaySubnetPrefix string = '10.50.4.0/24'

@description('App Service Plan SKU (e.g., PV3, P1v3, S1).')
param appServicePlanSkuName string = 'PV3'

@description('Name for the App Service Plan.')
param appServicePlanName string = '${namePrefix}-${environmentName}-asp'

@description('Name for the Django web app.')
param webAppName string = '${namePrefix}-${environmentName}-web'

@description('Python runtime version for the Linux Web App.')
param webAppPythonVersion string = '3.12'

@description('Name for the Key Vault.')
param keyVaultName string = '${namePrefix}-${environmentName}-kv'

@description('Name for the PostgreSQL Flexible Server.')
param postgresServerName string = '${namePrefix}-${environmentName}-pg'

@description('PostgreSQL admin username.')
param postgresAdminLogin string = 'edusysadmin'

@description('PostgreSQL admin password.')
@secure()
param postgresAdminPassword string

@description('PostgreSQL version.')
param postgresVersion string = '16'

@description('PostgreSQL SKU name (example: Standard_B2s for Burstable).')
param postgresSkuName string = 'Standard_B2s'

@description('PostgreSQL SKU tier (example: Burstable).')
param postgresSkuTier string = 'Burstable'

@description('PostgreSQL storage size in GB.')
param postgresStorageSizeGb int = 128

@description('Application Gateway name.')
param appGatewayName string = '${namePrefix}-${environmentName}-agw'

@description('Public IP name for Application Gateway.')
param appGatewayPublicIpName string = '${namePrefix}-${environmentName}-agw-pip'

@description('Base64-encoded PFX data for the Application Gateway TLS certificate.')
@secure()
param appGatewaySslPfxBase64 string

@description('Password for the Application Gateway TLS certificate PFX.')
@secure()
param appGatewaySslPfxPassword string

@description('Private DNS zone name for Azure Web Apps private endpoints.')
param privateDnsZoneWebAppsName string = 'privatelink.azurewebsites.net'

@description('Private DNS zone name for Azure Web Apps SCM (Kudu) private endpoints.')
param privateDnsZoneWebAppsScmName string = 'privatelink.scm.azurewebsites.net'

@description('Private DNS zone name for Key Vault private endpoints.')
param privateDnsZoneKeyVaultName string = 'privatelink.vaultcore.azure.net'

@description('Private DNS zone name for PostgreSQL Flexible Server private access (VNet-injected).')
param privateDnsZonePostgresName string = 'private.postgres.database.azure.com'

var nsgAppsName = '${namePrefix}-${environmentName}-nsg-apps'
var nsgDbName = '${namePrefix}-${environmentName}-nsg-db'
var nsgPeName = '${namePrefix}-${environmentName}-nsg-pe'
var nsgAppGwName = '${namePrefix}-${environmentName}-nsg-agw'

resource nsgApps 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgAppsName
  location: location
  properties: {
    securityRules: [
      {
        name: 'Allow-AppSvc-To-Postgres-5432'
        properties: {
          priority: 200
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '5432'
          sourceAddressPrefix: appsSubnetPrefix
          destinationAddressPrefix: dbSubnetPrefix
        }
      }
      {
        name: 'Allow-AppSvc-To-PrivateEndpoints-443'
        properties: {
          priority: 210
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: appsSubnetPrefix
          destinationAddressPrefix: privateEndpointsSubnetPrefix
        }
      }
    ]
  }
}

resource nsgDb 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgDbName
  location: location
  properties: {
    securityRules: [
      {
        name: 'Allow-AppSvc-To-Postgres-5432'
        properties: {
          priority: 200
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '5432'
          sourceAddressPrefix: appsSubnetPrefix
          destinationAddressPrefix: dbSubnetPrefix
        }
      }
    ]
  }
}

resource nsgPe 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgPeName
  location: location
  properties: {
    securityRules: [
      {
        name: 'Allow-AppGw-To-PrivateEndpoints-443'
        properties: {
          priority: 200
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: appGatewaySubnetPrefix
          destinationAddressPrefix: privateEndpointsSubnetPrefix
        }
      }
      {
        name: 'Allow-AppSvc-To-PrivateEndpoints-443'
        properties: {
          priority: 210
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: appsSubnetPrefix
          destinationAddressPrefix: privateEndpointsSubnetPrefix
        }
      }
    ]
  }
}

resource nsgAppGw 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgAppGwName
  location: location
  properties: {
    securityRules: [
      {
        name: 'Allow-GatewayManager-65200-65535'
        properties: {
          priority: 190
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRanges: [
            '65200-65535'
          ]
          sourceAddressPrefix: 'GatewayManager'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-Internet-To-AppGw-443'
        properties: {
          priority: 200
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'Internet'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'Allow-AppGw-To-PrivateEndpoints-443'
        properties: {
          priority: 210
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: appGatewaySubnetPrefix
          destinationAddressPrefix: privateEndpointsSubnetPrefix
        }
      }
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: vnetAddressSpaces
    }
  }
}

resource appsSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = {
  name: '${vnet.name}/${appsSubnetName}'
  properties: {
    addressPrefix: appsSubnetPrefix
    networkSecurityGroup: {
      id: nsgApps.id
    }
    delegations: [
      {
        name: 'delegation-appservice'
        properties: {
          serviceName: 'Microsoft.Web/serverFarms'
        }
      }
    ]
  }
  dependsOn: [
    vnet
  ]
}

resource dbSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = {
  name: '${vnet.name}/${dbSubnetName}'
  properties: {
    addressPrefix: dbSubnetPrefix
    networkSecurityGroup: {
      id: nsgDb.id
    }
    delegations: [
      {
        name: 'delegation-postgres'
        properties: {
          serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
        }
      }
    ]
  }
  dependsOn: [
    vnet
  ]
}

resource privateEndpointsSubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = {
  name: '${vnet.name}/${privateEndpointsSubnetName}'
  properties: {
    addressPrefix: privateEndpointsSubnetPrefix
    networkSecurityGroup: {
      id: nsgPe.id
    }
    privateEndpointNetworkPolicies: 'Disabled'
  }
  dependsOn: [
    vnet
  ]
}

resource appGatewaySubnet 'Microsoft.Network/virtualNetworks/subnets@2023-11-01' = {
  name: '${vnet.name}/${appGatewaySubnetName}'
  properties: {
    addressPrefix: appGatewaySubnetPrefix
    networkSecurityGroup: {
      id: nsgAppGw.id
    }
  }
  dependsOn: [
    vnet
  ]
}

resource privateDnsZoneWebApps 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneWebAppsName
  location: 'global'
}

resource privateDnsZoneWebAppsScm 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneWebAppsScmName
  location: 'global'
}

resource privateDnsZoneKeyVault 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneKeyVaultName
  location: 'global'
}

resource privateDnsZonePostgres 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZonePostgresName
  location: 'global'
}

resource privateDnsZoneWebAppsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${privateDnsZoneWebApps.name}/${namePrefix}-${environmentName}-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource privateDnsZoneWebAppsScmLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${privateDnsZoneWebAppsScm.name}/${namePrefix}-${environmentName}-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource privateDnsZoneKeyVaultLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${privateDnsZoneKeyVault.name}/${namePrefix}-${environmentName}-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource privateDnsZonePostgresLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${privateDnsZonePostgres.name}/${namePrefix}-${environmentName}-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  sku: {
    name: appServicePlanSkuName
  }
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    publicNetworkAccess: 'Disabled'
    virtualNetworkSubnetId: appsSubnet.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|${webAppPythonVersion}'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      alwaysOn: true
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'AZURE_KEY_VAULT_URL'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'DATABASE_HOST'
          value: '${postgresServerName}.postgres.database.azure.com'
        }
        {
          name: 'DATABASE_NAME'
          value: 'postgres'
        }
        {
          name: 'DATABASE_USER'
          value: postgresAdminLogin
        }
        {
          name: 'DATABASE_PASSWORD'
          value: postgresAdminPassword
        }
      ]
    }
  }
  dependsOn: [
    appsSubnet
  ]
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Deny'
    }
  }
}

@description('Allow web app to read secrets from Key Vault via managed identity.')
resource keyVaultSecretReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, webApp.identity.principalId, 'Key Vault Secrets User')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: webApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource keyVaultPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${namePrefix}-${environmentName}-pe-kv'
  location: location
  properties: {
    subnet: {
      id: privateEndpointsSubnet.id
    }
    privateLinkServiceConnections: [
      {
        name: 'keyvault'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: [
            'vault'
          ]
          privateLinkServiceConnectionState: {
            status: 'Approved'
            description: 'Auto-approved by IaC'
            actionsRequired: 'None'
          }
        }
      }
    ]
  }
  dependsOn: [
    privateEndpointsSubnet
    keyVault
  ]
}

resource keyVaultPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  name: '${keyVaultPrivateEndpoint.name}/default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'keyvault'
        properties: {
          privateDnsZoneId: privateDnsZoneKeyVault.id
        }
      }
    ]
  }
  dependsOn: [
    keyVaultPrivateEndpoint
    privateDnsZoneKeyVaultLink
  ]
}

resource privateDnsZoneKeyVault 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: privateDnsZoneKeyVaultName
  location: 'global'
}

resource privateDnsZoneKeyVaultLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: '${privateDnsZoneKeyVault.name}/${namePrefix}-${environmentName}-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnet.id
    }
  }
  dependsOn: [
    privateDnsZoneKeyVault
    vnet
  ]
}

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01' = {
  name: postgresServerName
  location: location
  sku: {
    name: postgresSkuName
    tier: postgresSkuTier
  }
  properties: {
    version: postgresVersion
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: postgresStorageSizeGb
    }
    backup: {
      backupRetentionDays: 7
    }
    network: {
      publicNetworkAccess: 'Disabled'
      delegatedSubnetResourceId: dbSubnet.id
      privateDnsZoneArmResourceId: privateDnsZonePostgres.id
    }
    highAvailability: {
      mode: 'Disabled'
    }
    createMode: 'Create'
  }
  dependsOn: [
    dbSubnet
    privateDnsZonePostgresLink
  ]
}


resource kvPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${namePrefix}-${environmentName}-pe-kv'
  location: location
  properties: {
    subnet: {
      id: privateEndpointsSubnet.id
    }
    privateLinkServiceConnections: [
      {
        name: 'kv'
        properties: {
          privateLinkServiceId: keyVault.id
          groupIds: [
            'vault'
          ]
          privateLinkServiceConnectionState: {
            status: 'Approved'
            description: 'Auto-approved by IaC'
            actionsRequired: 'None'
          }
        }
      }
    ]
  }
  dependsOn: [
    privateEndpointsSubnet
    keyVault
  ]
}

resource kvPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  name: '${kvPrivateEndpoint.name}/default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'kv'
        properties: {
          privateDnsZoneId: privateDnsZoneKeyVault.id
        }
      }
    ]
  }
  dependsOn: [
    kvPrivateEndpoint
    privateDnsZoneKeyVaultLink
  ]
}

resource webAppPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${namePrefix}-${environmentName}-pe-web'
  location: location
  properties: {
    subnet: {
      id: privateEndpointsSubnet.id
    }
    privateLinkServiceConnections: [
      {
        name: 'webapp'
        properties: {
          privateLinkServiceId: webApp.id
          groupIds: [
            'sites'
          ]
          privateLinkServiceConnectionState: {
            status: 'Approved'
            description: 'Auto-approved by IaC'
            actionsRequired: 'None'
          }
        }
      }
    ]
  }
  dependsOn: [
    privateEndpointsSubnet
    webApp
  ]
}

resource webAppPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  name: '${webAppPrivateEndpoint.name}/default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'webapps'
        properties: {
          privateDnsZoneId: privateDnsZoneWebApps.id
        }
      }
    ]
  }
  dependsOn: [
    webAppPrivateEndpoint
    privateDnsZoneWebAppsLink
  ]
}

resource webAppScmPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: '${namePrefix}-${environmentName}-pe-web-scm'
  location: location
  properties: {
    subnet: {
      id: privateEndpointsSubnet.id
    }
    privateLinkServiceConnections: [
      {
        name: 'webapp-scm'
        properties: {
          privateLinkServiceId: webApp.id
          groupIds: [
            'scm'
          ]
          privateLinkServiceConnectionState: {
            status: 'Approved'
            description: 'Auto-approved by IaC'
            actionsRequired: 'None'
          }
        }
      }
    ]
  }
  dependsOn: [
    privateEndpointsSubnet
    webApp
  ]
}

resource webAppScmPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  name: '${webAppScmPrivateEndpoint.name}/default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'webapps-scm'
        properties: {
          privateDnsZoneId: privateDnsZoneWebAppsScm.id
        }
      }
    ]
  }
  dependsOn: [
    webAppScmPrivateEndpoint
    privateDnsZoneWebAppsScmLink
  ]
}

resource appGatewayPublicIp 'Microsoft.Network/publicIPAddresses@2023-11-01' = {
  name: appGatewayPublicIpName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource appGateway 'Microsoft.Network/applicationGateways@2023-11-01' = {
  name: appGatewayName
  location: location
  properties: {
    sku: {
      name: 'WAF_v2'
      tier: 'WAF_v2'
    }
    autoscaleConfiguration: {
      minCapacity: 1
      maxCapacity: 2
    }
    sslCertificates: [
      {
        name: 'listener-cert'
        properties: {
          data: appGatewaySslPfxBase64
          password: appGatewaySslPfxPassword
        }
      }
    ]
    gatewayIPConfigurations: [
      {
        name: 'appGatewayIpConfig'
        properties: {
          subnet: {
            id: appGatewaySubnet.id
          }
        }
      }
    ]
    frontendIPConfigurations: [
      {
        name: 'publicFrontend'
        properties: {
          publicIPAddress: {
            id: appGatewayPublicIp.id
          }
        }
      }
    ]
    frontendPorts: [
      {
        name: 'port443'
        properties: {
          port: 443
        }
      }
    ]
    backendAddressPools: [
      {
        name: 'webappPool'
        properties: {
          backendAddresses: [
            {
              fqdn: '${webApp.name}.azurewebsites.net'
            }
          ]
        }
      }
    ]
    backendHttpSettingsCollection: [
      {
        name: 'httpsSettings'
        properties: {
          port: 443
          protocol: 'Https'
          cookieBasedAffinity: 'Disabled'
          pickHostNameFromBackendAddress: true
          requestTimeout: 60
          probe: {
            id: resourceId('Microsoft.Network/applicationGateways/probes', appGatewayName, 'httpsProbe')
          }
        }
      }
    ]
    probes: [
      {
        name: 'httpsProbe'
        properties: {
          protocol: 'Https'
          pickHostNameFromBackendHttpSettings: true
          path: '/'
          interval: 30
          timeout: 30
          unhealthyThreshold: 3
          match: {
            statusCodes: [
              '200-399'
            ]
          }
        }
      }
    ]
    httpListeners: [
      {
        name: 'httpsListener'
        properties: {
          frontendIPConfiguration: {
            id: resourceId('Microsoft.Network/applicationGateways/frontendIPConfigurations', appGatewayName, 'publicFrontend')
          }
          frontendPort: {
            id: resourceId('Microsoft.Network/applicationGateways/frontendPorts', appGatewayName, 'port443')
          }
          protocol: 'Https'
          sslCertificate: {
            id: resourceId('Microsoft.Network/applicationGateways/sslCertificates', appGatewayName, 'listener-cert')
          }
        }
      }
    ]
    requestRoutingRules: [
      {
        name: 'rule1'
        properties: {
          ruleType: 'Basic'
          priority: 100
          httpListener: {
            id: resourceId('Microsoft.Network/applicationGateways/httpListeners', appGatewayName, 'httpsListener')
          }
          backendAddressPool: {
            id: resourceId('Microsoft.Network/applicationGateways/backendAddressPools', appGatewayName, 'webappPool')
          }
          backendHttpSettings: {
            id: resourceId('Microsoft.Network/applicationGateways/backendHttpSettingsCollection', appGatewayName, 'httpsSettings')
          }
        }
      }
    ]
    webApplicationFirewallConfiguration: {
      enabled: true
      firewallMode: 'Prevention'
      ruleSetType: 'OWASP'
      ruleSetVersion: '3.2'
    }
  }
  dependsOn: [
    appGatewaySubnet
    appGatewayPublicIp
    webAppPrivateEndpoint
    webAppPrivateDnsZoneGroup
  ]
}

output vnetId string = vnet.id
output appsSubnetId string = appsSubnet.id
output dbSubnetId string = dbSubnet.id
output privateEndpointsSubnetId string = privateEndpointsSubnet.id
output appGatewaySubnetId string = appGatewaySubnet.id
output webAppHostname string = '${webApp.name}.azurewebsites.net'
output keyVaultUrl string = keyVault.properties.vaultUri
