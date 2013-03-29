from reddwarf.guestagent.backup.backupagent import BackupAgent


def execute(backup_id):
    return BackupAgent().execute_backup(backup_id)
