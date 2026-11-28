param location string
param environmentName string

@allowed([
  'student'
  'production'
])
param deploymentProfile string = 'production'

var isProduction = deploymentProfile == 'production'
var serviceBusSkuName = isProduction
  ? 'Premium'
  : 'Standard'
var serviceBusSkuTier = isProduction
  ? 'Premium'
  : 'Standard'

resource serviceBus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: 'sb-flowforge-${environmentName}'
  location: location
  sku: {
    name: serviceBusSkuName
    tier: serviceBusSkuTier
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
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
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'P1D'
  }
}]

output serviceBusName string = serviceBus.name
output queueNames array = queueNames
