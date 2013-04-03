from reddwarf.guestagent.backup.backupagent import BackupAgent


def execute(context, backup_id):
    """
    Main entry point for starting a backup based on the given backup id.  This
    will create a backup for this DB instance and will then store the backup
    in a configured repository (e.g. Swift)

    :param context:     the context token which contains the users details
    :param backup_id:   the id of the persisted backup object
    """
    return BackupAgent().execute_backup(context, backup_id)
