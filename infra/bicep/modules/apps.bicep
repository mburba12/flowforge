param location string
param environmentName string
param imageTag string
param apiImage string
param workerImage string
param webImage string
param identityId string

@allowed([
  'student'
  'production'
])
param deploymentProfile string = 'production'

var isProduction = deploymentProfile == 'production'
var containerCpu = isProduction
  ? json('1.0')
  : json('0.5')
var containerMemory = isProduction
  ? '2Gi'
  : '1Gi'
var apiWebMinimumReplicas = isProduction ? 2 : 0
var workerMinimumReplicas = isProduction ? 1 : 0
var maximumReplicas = isProduction ? 20 : 1
var maximumWorkerReplicas = isProduction ? 50 : 1
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
            cpu: containerCpu
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: apiWebMinimumReplicas
        maxReplicas: maximumReplicas
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
            cpu: containerCpu
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: apiWebMinimumReplicas
        maxReplicas: maximumReplicas
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
            cpu: containerCpu
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: workerMinimumReplicas
        maxReplicas: maximumWorkerReplicas
      }
    }
  }
}

output apiFqdn string = api.properties.configuration.ingress.fqdn
output webFqdn string = web.properties.configuration.ingress.fqdn
output workerName string = worker.name
