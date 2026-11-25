param location string
param environmentName string
param dataSubnetId string
param postgresAdminLogin string

@allowed([
  'student'
  'production'
])
param deploymentProfile string = 'production'

var isProduction = deploymentProfile == 'production'
var databaseSku = isProduction
  ? 'Standard_D4ds_v5'
  : 'Standard_B2ats_v2'
var databaseTier = isProduction
  ? 'GeneralPurpose'
  : 'Burstable'
var backupRetentionDays = isProduction ? 35 : 7
var geoRedundantBackup = isProduction
  ? 'Enabled'
  : 'Disabled'
var databaseHighAvailability = isProduction
  ? 'ZoneRedundant'
  : 'Disabled'
var databaseStorageSizeGb = isProduction ? 256 : 32
var storageSkuName = isProduction
  ? 'Standard_ZRS'
  : 'Standard_LRS'

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
    name: storageSkuName
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
    name: databaseSku
    tier: databaseTier
  }
  properties: {
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    version: '16'
    backup: {
      backupRetentionDays: backupRetentionDays
      geoRedundantBackup: geoRedundantBackup
    }
    highAvailability: {
      mode: databaseHighAvailability
    }
    network: {
      delegatedSubnetResourceId: dataSubnetId
      publicNetworkAccess: 'Disabled'
    }
    storage: {
      storageSizeGB: databaseStorageSizeGb
      autoGrow: 'Enabled'
    }
  }
}

output keyVaultName string = vault.name
output storageName string = storage.name
output postgresName string = postgres.name
