targetScope = 'resourceGroup'
param location string = resourceGroup().location
param environmentName string
param postgresAdmin string
@secure() param postgresPassword string
var prefix='ff-${environmentName}'
resource log 'Microsoft.OperationalInsights/workspaces@2023-09-01'={name:'${prefix}-log';location:location;properties:{retentionInDays:30}}
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01'={name:replace('${prefix}acr','-','');location:location;sku:{name:'Basic'};properties:{adminUserEnabled:false}}
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01'={name:take(replace('${prefix}storage','-',''),24);location:location;sku:{name:'Standard_LRS'};kind:'StorageV2';properties:{allowBlobPublicAccess:false;minimumTlsVersion:'TLS1_2'}}
resource bus 'Microsoft.ServiceBus/namespaces@2024-01-01'={name:'${prefix}-sb';location:location;sku:{name:'Basic';tier:'Basic'}}
resource pg 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview'={name:'${prefix}-pg';location:location;sku:{name:'Standard_B1ms';tier:'Burstable'};properties:{administratorLogin:postgresAdmin;administratorLoginPassword:postgresPassword;version:'16';storage:{storageSizeGB:32};backup:{backupRetentionDays:7;geoRedundantBackup:'Disabled'}}}
output registry string=acr.properties.loginServer
output postgres string=pg.properties.fullyQualifiedDomainName
