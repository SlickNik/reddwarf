from reddwarf.guestagent.models import RemoteSwift
from reddwarf.common import cfg
from reddwarf.openstack.common import log as logging
from reddwarf.common import utils
LOG = logging.getLogger(__name__)

CONF = cfg.CONF


class Storage(object):
    """where and how to store the backups"""

    def get_storage_client(self):
        pass

    @classmethod
    def saveBackUp(cls):
        pass

    @classmethod
    def getBackUp(cls):
        pass


class StoreBySwift(Storage):

    @classmethod
    def saveBackUp(cls, context, container, snapshot_name, snapshot_content):
        """
        :param cls:
        :param context: auth_url and auth_token to access swift
        :param container:
        :param snapshot_name:
        :param snapshot_content:
        :return:
        """
        return RemoteSwift.put(context=context,
                               container=container,
                               name=snapshot_name,
                               file_to_upload=snapshot_content)

    @classmethod
    def getBackUp(cls, context, container, name, out_file):
        """
        :param cls:
        :param context:
        :param container:
        :param name:
        :param out_file:
        :return:
        """
        file = RemoteSwift.get(context=context, container=container, name=name,
                               out_file=out_file)
        return file
        #uncompress
#        utils.execute("tar -zxvf %s" % file)
#        clean up .gz
#        utils.execute('sudo rm -rf %s' % snapshot)
