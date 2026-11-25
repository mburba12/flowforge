$ErrorActionPreference = "Stop"

$Root = Join-Path (Get-Location) "infra\bicep"
$Modules = Join-Path $Root "modules"
New-Item -ItemType Directory -Path $Modules -Force | Out-Null

@'
targetScope = 'resourceGroup'

param location string = resourceGroup().location
param environmentName string
param imageTag string
param apiImage string
param workerImage string
param webImage string
param postgresAdminLogin string

@secure()
param postgresAdminPassword string

module network 'modules/network.bicep' = {
  name: 'network'
  params: {
    location: location
    environmentName: environmentName
  }
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  params: {
    location: location
    environmentName: environmentName
  }
}

module observability 'modules/observability.bicep' = {
  name: 'observability'
  params: {
    location: location
    environmentName: environmentName
  }
}

module data 'modules/data.bicep' = {
  name: 'data'
  params: {
    location: location
    environmentName: environmentName
    dataSubnetId: network.outputs.dataSubnetId
    postgresAdminLogin: postgresAdminLogin
    postgresAdminPassword: postgresAdminPassword
  }
}

module messaging 'modules/messaging.bicep' = {
  name: 'messaging'
  params: {
    location: location
    environmentName: environmentName
  }
}

module apps 'modules/apps.bicep' = {
  name: 'apps'
  params: {
    location: location
    environmentName: environmentName
    imageTag: imageTag
    apiImage: apiImage
    workerImage: workerImage
    webImage: webImage
    identityId: identity.outputs.identityId
    logAnalyticsCustomerId: observability.outputs.customerId
    logAnalyticsSharedKey: observability.outputs.sharedKey
  }
}

output apiFqdn string = apps.outputs.apiFqdn
output webFqdn string = apps.outputs.webFqdn
output keyVaultName string = data.outputs.keyVaultName
output serviceBusName string = messaging.outputs.serviceBusName
'@ | Set-Content -LiteralPath (Join-Path $Root "main.bicep") -Encoding UTF8

@'
param location string
param environmentName string

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'vnet-flowforge-${environmentName}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.40.0.0/16'
      ]
    }
    subnets: [
      {
        name: 'apps'
        properties: {
          addressPrefix: '10.40.0.0/23'
          delegations: [
            {
              name: 'container-apps'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: 'data'
        properties: {
          addressPrefix: '10.40.4.0/24'
          delegations: [
            {
              name: 'postgres-flexible-server'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
        }
      }
      {
        name: 'private-endpoints'
        properties: {
          addressPrefix: '10.40.5.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

output vnetId string = vnet.id
output appsSubnetId string = vnet.properties.subnets[0].id
output dataSubnetId string = vnet.properties.subnets[1].id
output privateEndpointsSubnetId string = vnet.properties.subnets[2].id
'@ | Set-Content -LiteralPath (Join-Path $Modules "network.bicep") -Encoding UTF8

@'
param location string
param environmentName string

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-flowforge-${environmentName}'
  location: location
}

output identityId string = identity.id
output principalId string = identity.properties.principalId
output clientId string = identity.properties.clientId
'@ | Set-Content -LiteralPath (Join-Path $Modules "identity.bicep") -Encoding UTF8

@'
param location string
param environmentName string

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-flowforge-${environmentName}'
  location: location
  properties: {
    retentionInDays: 90
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-flowforge-${environmentName}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

output customerId string = logs.properties.customerId

@secure()
output sharedKey string = listKeys(logs.id, logs.apiVersion).primarySharedKey

output applicationInsightsConnectionString string = insights.properties.ConnectionString
'@ | Set-Content -LiteralPath (Join-Path $Modules "observability.bicep") -Encoding UTF8

@'
param location string
param environmentName string
param dataSubnetId string
param postgresAdminLogin string

@secure()
param postgresAdminPassword string

resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: take('kv-flowforge-${environmentName}-${uniqueString(resourceGroup().id)}', 24)
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Disabled'
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: take('stflowforge${environmentName}${uniqueString(resourceGroup().id)}', 24)
  location: location
  sku: {
    name: 'Standard_ZRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Disabled'
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: 'psql-flowforge-${environmentName}'
  location: location
  sku: {
    name: 'Standard_D4ds_v5'
    tier: 'GeneralPurpose'
  }
  properties: {
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    version: '16'
    backup: {
      backupRetentionDays: 35
      geoRedundantBackup: 'Enabled'
    }
    highAvailability: {
      mode: 'ZoneRedundant'
    }
    network: {
      delegatedSubnetResourceId: dataSubnetId
      publicNetworkAccess: 'Disabled'
    }
    storage: {
      storageSizeGB: 256
      autoGrow: 'Enabled'
    }
  }
}

output keyVaultName string = vault.name
output storageName string = storage.name
output postgresName string = postgres.name
'@ | Set-Content -LiteralPath (Join-Path $Modules "data.bicep") -Encoding UTF8

@'
param location string
param environmentName string

resource serviceBus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: 'sb-flowforge-${environmentName}'
  location: location
  sku: {
    name: 'Premium'
    tier: 'Premium'
    capacity: 1
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    zoneRedundant: true
  }
}

var queueNames = [
  'documents'
  'webhooks'
  'reconciliation'
  'workflows'
  'notifications'
  'deadletter-replay'
]

resource queues 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = [for queueName in queueNames: {
  parent: serviceBus
  name: queueName
  properties: {
    lockDuration: 'PT5M'
    maxDeliveryCount: 10
    deadLetteringOnMessageExpiration: true
    enablePartitioning: true
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'P1D'
  }
}]

output serviceBusName string = serviceBus.name
output queueNames array = queueNames
'@ | Set-Content -LiteralPath (Join-Path $Modules "messaging.bicep") -Encoding UTF8

@'
param location string
param environmentName string
param imageTag string
param apiImage string
param workerImage string
param webImage string
param identityId string
param logAnalyticsCustomerId string

@secure()
param logAnalyticsSharedKey string

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-flowforge-${environmentName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-flowforge-api-${environmentName}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${apiImage}:${imageTag}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 2
        maxReplicas: 20
      }
    }
  }
}

resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-flowforge-web-${environmentName}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'web'
          image: '${webImage}:${imageTag}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 2
        maxReplicas: 20
      }
    }
  }
}

resource worker 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-flowforge-worker-${environmentName}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Multiple'
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${workerImage}:${imageTag}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 50
      }
    }
  }
}

output apiFqdn string = api.properties.configuration.ingress.fqdn
output webFqdn string = web.properties.configuration.ingress.fqdn
output workerName string = worker.name
'@ | Set-Content -LiteralPath (Join-Path $Modules "apps.bicep") -Encoding UTF8

Write-Host "Rewrote Phase 5B Bicep sources." -ForegroundColor Green

az bicep build --file (Join-Path $Root "main.bicep")
if ($LASTEXITCODE -ne 0) {
    throw "Phase 5B main Bicep compilation still fails."
}

Get-ChildItem $Modules -Filter "*.bicep" -File | ForEach-Object {
    az bicep build --file $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Bicep compilation failed: $($_.Name)"
    }
}

Write-Host "PHASE 5B BICEP COMPILATION PASSED" -ForegroundColor Green
