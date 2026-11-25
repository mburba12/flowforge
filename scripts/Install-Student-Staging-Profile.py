from pathlib import Path


def replace_required(
    path: Path,
    old: str,
    new: str,
) -> None:
    text = path.read_text(encoding="utf-8")

    if old not in text:
        if new in text:
            print(f"ALREADY UPDATED: {path} -> {new}")
            return

        raise RuntimeError(
            f"Expected setting not found in {path}: {old}"
        )

    path.write_text(
        text.replace(old, new),
        encoding="utf-8",
    )

    print(f"UPDATED: {path}")


root = Path("infra/bicep")

# ---------------------------------------------------------
# data.bicep
# ---------------------------------------------------------

data_path = root / "modules" / "data.bicep"

replace_required(
    data_path,
    "param postgresAdminLogin string",
    """param postgresAdminLogin string

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
  : 'Standard_LRS'""",
)

replace_required(
    data_path,
    "name: 'Standard_ZRS'",
    "name: storageSkuName",
)

replace_required(
    data_path,
    "name: 'Standard_D4ds_v5'",
    "name: databaseSku",
)

replace_required(
    data_path,
    "tier: 'GeneralPurpose'",
    "tier: databaseTier",
)

replace_required(
    data_path,
    "backupRetentionDays: 35",
    "backupRetentionDays: backupRetentionDays",
)

replace_required(
    data_path,
    "geoRedundantBackup: 'Enabled'",
    "geoRedundantBackup: geoRedundantBackup",
)

replace_required(
    data_path,
    "mode: 'ZoneRedundant'",
    "mode: databaseHighAvailability",
)

replace_required(
    data_path,
    "storageSizeGB: 256",
    "storageSizeGB: databaseStorageSizeGb",
)

# ---------------------------------------------------------
# messaging.bicep
# ---------------------------------------------------------

messaging_path = root / "modules" / "messaging.bicep"

replace_required(
    messaging_path,
    "param environmentName string",
    """param environmentName string

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
  : 'Standard'""",
)

replace_required(
    messaging_path,
    "name: 'Premium'",
    "name: serviceBusSkuName",
)

replace_required(
    messaging_path,
    "tier: 'Premium'",
    "tier: serviceBusSkuTier",
)

# Premium-only capacity and zone redundancy cannot be used in Standard.
replace_required(
    messaging_path,
    """    capacity: 1
""",
    "",
)

replace_required(
    messaging_path,
    """    zoneRedundant: true
""",
    "",
)

# Standard Service Bus does not support partitioning together with
# duplicate detection on every queue configuration in the same way
# as the Premium profile. Keep the durable queue semantics and remove
# the unnecessary partitioning flag.
replace_required(
    messaging_path,
    """    enablePartitioning: true
""",
    "",
)

# ---------------------------------------------------------
# apps.bicep
# ---------------------------------------------------------

apps_path = root / "modules" / "apps.bicep"

replace_required(
    apps_path,
    "param identityId string",
    """param identityId string

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
var maximumWorkerReplicas = isProduction ? 50 : 1""",
)

replace_required(
    apps_path,
    "cpu: json('1.0')",
    "cpu: containerCpu",
)

replace_required(
    apps_path,
    "memory: '2Gi'",
    "memory: containerMemory",
)

replace_required(
    apps_path,
    "minReplicas: 2",
    "minReplicas: apiWebMinimumReplicas",
)

replace_required(
    apps_path,
    "minReplicas: 1",
    "minReplicas: workerMinimumReplicas",
)

replace_required(
    apps_path,
    "maxReplicas: 20",
    "maxReplicas: maximumReplicas",
)

replace_required(
    apps_path,
    "maxReplicas: 50",
    "maxReplicas: maximumWorkerReplicas",
)

# ---------------------------------------------------------
# observability.bicep
# ---------------------------------------------------------

observability_path = (
    root / "modules" / "observability.bicep"
)

replace_required(
    observability_path,
    "param environmentName string",
    """param environmentName string

@allowed([
  'student'
  'production'
])
param deploymentProfile string = 'production'

var logRetentionDays = (
  deploymentProfile == 'production'
    ? 90
    : 30
)""",
)

replace_required(
    observability_path,
    "retentionInDays: 90",
    "retentionInDays: logRetentionDays",
)

# ---------------------------------------------------------
# main.bicep
# ---------------------------------------------------------

main_path = root / "main.bicep"

replace_required(
    main_path,
    "param environmentName string",
    """param environmentName string

@allowed([
  'student'
  'production'
])
param deploymentProfile string = 'production'""",
)

replace_required(
    main_path,
    """    environmentName: environmentName
  }
}

module data""",
    """    environmentName: environmentName
    deploymentProfile: deploymentProfile
  }
}

module data""",
)

replace_required(
    main_path,
    """    postgresAdminLogin: postgresAdminLogin
    postgresAdminPassword: postgresAdminPassword
  }
}

module messaging""",
    """    postgresAdminLogin: postgresAdminLogin
    postgresAdminPassword: postgresAdminPassword
    deploymentProfile: deploymentProfile
  }
}

module messaging""",
)

replace_required(
    main_path,
    """module messaging 'modules/messaging.bicep' = {
  name: 'messaging'
  params: {
    location: location
    environmentName: environmentName
  }
}""",
    """module messaging 'modules/messaging.bicep' = {
  name: 'messaging'
  params: {
    location: location
    environmentName: environmentName
    deploymentProfile: deploymentProfile
  }
}""",
)

replace_required(
    main_path,
    """    logAnalyticsSharedKey: observability.outputs.sharedKey
  }
}""",
    """    logAnalyticsSharedKey: observability.outputs.sharedKey
    deploymentProfile: deploymentProfile
  }
}""",
)

print(
    "PASSED: Production architecture preserved "
    "and student staging profile installed."
)
