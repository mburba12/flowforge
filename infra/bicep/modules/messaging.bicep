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
