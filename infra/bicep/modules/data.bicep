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
