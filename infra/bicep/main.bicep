targetScope = 'resourceGroup'

param location string = resourceGroup().location
param environmentName string

@allowed([
  'student'
  'production'
])
param deploymentProfile string = 'production'
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
    deploymentProfile: deploymentProfile
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
    deploymentProfile: deploymentProfile
  }
}

module messaging 'modules/messaging.bicep' = {
  name: 'messaging'
  params: {
    location: location
    environmentName: environmentName
    deploymentProfile: deploymentProfile
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
    deploymentProfile: deploymentProfile
  }
}

output apiFqdn string = apps.outputs.apiFqdn
output webFqdn string = apps.outputs.webFqdn
output keyVaultName string = data.outputs.keyVaultName
output serviceBusName string = messaging.outputs.serviceBusName
