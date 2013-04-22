from reddwarf.common import cfg
from reddwarf.guestagent import dbaas, backup
from reddwarf.guestagent import volume
from reddwarf.openstack.common import log as logging
from reddwarf.openstack.common import periodic_task
from reddwarf.openstack.common.gettextutils import _

import os

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

MYSQL_BASE_DIR = "/var/lib/mysql"


class Manager(periodic_task.PeriodicTasks):

    @periodic_task.periodic_task(ticks_between_runs=10)
    def update_status(self, context):
        """Update the status of the MySQL service"""
        dbaas.MySqlAppStatus.get().update()

    def change_passwords(self, context, users):
        return dbaas.MySqlAdmin().change_passwords(users)

    def create_database(self, databases):
        if not databases or len(databases) == 0:
            return
        dbaas.MySqlAdmin().create_database(databases)

    def create_user(self, users):
        if not users or len(users) == 0:
            return
        dbaas.MySqlAdmin().create_user(users)

    def delete_database(self, context, database):
        return dbaas.MySqlAdmin().delete_database(database)

    def delete_user(self, context, user):
        dbaas.MySqlAdmin().delete_user(user)

    def get_user(self, context, username, hostname):
        return dbaas.MySqlAdmin().get_user(username, hostname)

    def grant_access(self, context, username, hostname, databases):
        return dbaas.MySqlAdmin().grant_access(username, hostname, databases)

    def revoke_access(self, context, username, hostname, database):
        return dbaas.MySqlAdmin().revoke_access(username, hostname, database)

    def list_access(self, context, username, hostname):
        return dbaas.MySqlAdmin().list_access(username, hostname)

    def list_databases(self, context, limit=None, marker=None,
                       include_marker=False):
        return dbaas.MySqlAdmin().list_databases(limit, marker,
                                                 include_marker)

    def list_users(self, context, limit=None, marker=None,
                   include_marker=False):
        return dbaas.MySqlAdmin().list_users(limit, marker,
                                             include_marker)

    def enable_root(self, context):
        return dbaas.MySqlAdmin().enable_root()

    def is_root_enabled(self, context):
        return dbaas.MySqlAdmin().is_root_enabled()

    def _perform_restore(self, backup_id, context, restore_location):
        if backup_id:
            LOG.info(_("Restoring database from backup %s" % backup_id))
            backup.restore(context, backup_id, restore_location)
            LOG.info(_("Restored database"))
            if self.is_root_enabled(context):
                dbaas.MySqlAdmin().report_root_enabled(context)
                return True
        return False

    def prepare(self, context, databases, memory_mb, users, device_path=None,
                mount_point=None, backup_id=None):
        """Makes ready DBAAS on a Guest container."""
        dbaas.MySqlAppStatus.get().begin_mysql_install()
        # status end_mysql_install set with secure()
        app = dbaas.MySqlApp(dbaas.MySqlAppStatus.get())
        restart_mysql = False
        if device_path:
            device = volume.VolumeDevice(device_path)
            device.format()
            #if a /var/lib/mysql folder exists, back it up.
            if os.path.exists(CONF.mount_point):
                #stop and do not update database
                app.stop_mysql()
                restart_mysql = True
                #rsync exiting data
                if not backup_id:
                    device.migrate_data(CONF.mount_point)
            #mount the volume
            device.mount(mount_point)
            LOG.debug(_("Mounted the volume."))
            #check mysql was installed and stopped
            if restart_mysql:
                app.start_mysql()
        app.install_if_needed()
        keep_root = self._perform_restore(backup_id, context, CONF.mount_point)
        LOG.info(_("Securing mysql now."))
        app.secure(memory_mb, keep_root=keep_root)

        self.create_database(databases)
        self.create_user(users)
        LOG.info('"prepare" call has finished.')

    def restart(self, context):
        app = dbaas.MySqlApp(dbaas.MySqlAppStatus.get())
        app.restart()

    def start_mysql_with_conf_changes(self, context, updated_memory_size):
        app = dbaas.MySqlApp(dbaas.MySqlAppStatus.get())
        app.start_mysql_with_conf_changes(updated_memory_size)

    def stop_mysql(self, context, do_not_start_on_reboot=False):
        app = dbaas.MySqlApp(dbaas.MySqlAppStatus.get())
        app.stop_mysql(do_not_start_on_reboot=do_not_start_on_reboot)

    def get_filesystem_stats(self, context, fs_path):
        """ Gets the filesystem stats for the path given """
        return dbaas.Interrogator().get_filesystem_volume_stats(fs_path)

    def create_backup(self, context, backup_id):
        """
        Entry point for initiating a backup for this guest agents db instance.
        The call currently blocks until the backup is complete or errors. If
        device_path is specified, it will be mounted based to a point specified
        in configuration.

        :param backup_id: the db instance id of the backup task
        """
        backup.backup(context, backup_id)
