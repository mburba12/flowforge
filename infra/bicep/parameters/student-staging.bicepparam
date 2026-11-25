using '../main.bicep'

param environmentName = 'student-staging'
param deploymentProfile = 'student'
param imageTag = 'staging'

param apiImage = 'REPLACE.azurecr.io/flowforge-api'
param workerImage = 'REPLACE.azurecr.io/flowforge-worker'
param webImage = 'REPLACE.azurecr.io/flowforge-web'

param postgresAdminLogin = 'flowforge_admin'

param postgresAdminPassword = readEnvironmentVariable(
  'FLOWFORGE_POSTGRES_ADMIN_PASSWORD'
)
