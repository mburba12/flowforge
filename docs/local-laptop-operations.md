# Local laptop operations

## Start
`& .\scripts\local\Start-FlowForge.ps1 -ProjectRoot $PWD.Path`

## Status
`& .\scripts\local\Get-FlowForgeStatus.ps1 -ProjectRoot $PWD.Path`

## Restart API
`& .\scripts\local\Restart-FlowForge.ps1 -ProjectRoot $PWD.Path`

## Stop application only
`& .\scripts\local\Stop-FlowForge.ps1 -ProjectRoot $PWD.Path`

Use `-All` to stop all Compose services. Volumes are never removed.

## Backup
`& .\scripts\local\Backup-FlowForge.ps1 -ProjectRoot $PWD.Path`

## Restore to a new database
`& .\scripts\local\Restore-FlowForge.ps1 -BackupPath .\var\backups\<file>.dump -DestinationDatabase flowforge_restore_manual`

Never restore over `flowforge` without the explicit `-AllowLiveOverwrite` switch.
