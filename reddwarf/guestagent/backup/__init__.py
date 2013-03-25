from reddwarf.guestagent.backup.backupagent import BackupAgent


def execute(backup_id, mount_point=None):
    return BackupAgent().execute_backup(backup_id, mount_point)
