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
