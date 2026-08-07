# Backup and restore

`scripts/backup.sh` creates a local evidence backup of configs and non-secret state.
`scripts/restore-test.sh` restores into an isolated temp directory and verifies structure.

Encrypted backups are used when `BACKUP_ENCRYPTION_KEY_FILE` is provided.
