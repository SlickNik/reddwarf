import uuid
from mockito import when, any
import swiftclient.client as swift_client
import swiftclient


class SwiftObjectStore(object):
    def __init__(self):
        pass


class SwiftClientStub(object):
    """
    Component for controlling behavior of Swift Client Stub.  Instantiated
    before tests are invoked in "fake" mode.  Invoke methods to control
    behavior so that systems under test can interact with this as it is a
    real swift client with a real backend

    example:

    if FAKE:
        swift_stub = SwiftClientStub()
        swift_stub.with_account('xyz')

    # returns swift account info and auth token
    component_using_swift.get_swift_account()

    if FAKE:
        swift_stub.with_container('test-container-name')

    # returns swift container information - mostly faked
    component_using.swift.create_container('test-container-name')
    component_using_swift.get_container_info('test-container-name')

    if FAKE:
        swift_stub.with_object('test-container-name', 'test-object-name',
            'test-object-contents')

    # returns swift object info and contents
    component_using_swift.create_object('test-container-name',
        'test-object-name', 'test-contents')
    component_using_swift.get_object('test-container-name', 'test-object-name')

    if FAKE:
        swift_stub.without_object('test-container-name', 'test-object-name')

    # allows object to be removed ONCE
    component_using_swift.remove_object('test-container-name',
        'test-object-name')
    # throws ClientException - 404
    component_using_swift.get_object('test-container-name', 'test-object-name')
    component_using_swift.remove_object('test-container-name',
        'test-object-name')

    if FAKE:
        swift_stub.without_object('test-container-name', 'test-object-name')

    # allows container to be removed ONCE
    component_using_swift.remove_container('test-container-name')
    # throws ClientException - 404
    component_using_swift.get_container('test-container-name')
    component_using_swift.remove_container('test-container-name')
    """

    def __init__(self):
        self._connection = swift_client.Connection()
        # simulate getting an unknown container
        when(swift_client.Connection).get_container(any()).thenRaise(
            swiftclient.ClientException('Resource Not Found', http_status=404))

        self._containers = {}
        self._containers_list = []
        self._objects = {}

    def _remove_object(self, name, some_list):
        idx = [i for i, obj in enumerate(some_list) if obj['name'] == name]
        if len(idx) == 1:
            del some_list[idx[0]]

    def _ensure_object_exists(self, container, name):
        self._connection.get_object(container, name)

    def with_account(self, account_id):
        """
        setups up account headers

        example:

        if FAKE:
            swift_stub = SwiftClientStub()
            swift_stub.with_account('xyz')

        # returns swift account info and auth token
        component_using_swift.get_swift_account()

        :param account_id: account id
        """

        def account_resp():
            return ({'content-length': '2', 'accept-ranges': 'bytes',
                     'x-timestamp': '1363049003.92304',
                     'x-trans-id': 'tx9e5da02c49ed496395008309c8032a53',
                     'date': 'Tue, 10 Mar 2013 00:43:23 GMT',
                     'x-account-bytes-used': '0',
                     'x-account-container-count': '0',
                     'content-type': 'application/json; charset=utf-8',
                     'x-account-object-count': '0'}, self._containers_list)

        when(swift_client.Connection).get_auth().thenReturn((
            u"http://127.0.0.1:8080/v1/AUTH_c7b038976df24d96bf1980f5da17bd89",
            u'MIINrwYJKoZIhvcNAQcCoIINoDCCDZwCAQExCTAHBgUrDgMCGjCCDIgGCSqGSIb3'
            u'DQEHAaCCDHkEggx1eyJhY2Nlc3MiOiB7InRva2VuIjogeyJpc3N1ZWRfYXQiOiAi'
            u'MjAxMy0wMy0xOFQxODoxMzoyMC41OTMyNzYiLCAiZXhwaXJlcyI6ICIyMDEzLTAz'
            u'LTE5VDE4OjEzOjIwWiIsICJpZCI6ICJwbGFjZWhvbGRlciIsICJ0ZW5hbnQiOiB7'
            u'ImVuYWJsZWQiOiB0cnVlLCAiZGVzY3JpcHRpb24iOiBudWxsLCAibmFtZSI6ICJy'
            u'ZWRkd2FyZiIsICJpZCI6ICJjN2IwMzg5NzZkZjI0ZDk2YmYxOTgwZjVkYTE3YmQ4'
            u'OSJ9fSwgInNlcnZpY2VDYXRhbG9nIjogW3siZW5kcG9pbnRzIjogW3siYWRtaW5')
        )
        when(swift_client.Connection).get_account().thenReturn(account_resp())
        return self

    def _create_container(self, container_name):
        container = {'count': 0, 'bytes': 0, 'name': container_name}
        self._containers[container_name] = container
        self._containers_list.append(container)
        self._objects[container_name] = []

    def _ensure_container_exists(self, container):
        self._connection.get_container(container)

    def _delete_container(self, container):
        self._remove_object(container, self._containers_list)
        del self._containers[container]
        del self._objects[container]

    def with_container(self, container_name):
        """
        sets expectations for creating a container and subsequently getting its
        information

        example:

        if FAKE:
            swift_stub.with_container('test-container-name')

        # returns swift container information - mostly faked
        component_using.swift.create_container('test-container-name')
        component_using_swift.get_container_info('test-container-name')

        :param container_name: container name that is expected to be created
        """

        def container_resp(container):
            return ({'content-length': '2', 'x-container-object-count': '0',
                     'accept-ranges': 'bytes', 'x-container-bytes-used': '0',
                     'x-timestamp': '1363370869.72356',
                     'x-trans-id': 'tx7731801ac6ec4e5f8f7da61cde46bed7',
                     'date': 'Fri, 10 Mar 2013 18:07:58 GMT',
                     'content-type': 'application/json; charset=utf-8'},
                    self._objects[container])

        # if this is called multiple times then nothing happens
        when(swift_client.Connection).put_container(container_name).thenReturn(
            None)
        self._create_container(container_name)
        # return container headers
        when(swift_client.Connection).get_container(container_name).thenReturn(
            container_resp(container_name))

        return self

    def without_container(self, container):
        """
        sets expectations for removing a container and subsequently throwing an
        exception for further interactions

        example:

        if FAKE:
            swift_stub.without_container('test-container-name')

        # returns swift container information - mostly faked
        component_using.swift.remove_container('test-container-name')
        # throws exception "Resource Not Found - 404"
        component_using_swift.get_container_info('test-container-name')

        :param container: container name that is expected to be removed
        """
        # first ensure container
        self._ensure_container_exists(container)
        # allow one call to get container and then throw exceptions (may need
        # to be revised
        when(swift_client.Connection).delete_container(container).thenRaise(
            swiftclient.ClientException("Resource Not Found", http_status=404))
        when(swift_client.Connection).get_container(container).thenRaise(
            swiftclient.ClientException("Resource Not Found", http_status=404))
        self._delete_container(container)
        return self

    def with_object(self, container, name, contents):
        """
        sets expectations for creating an object and subsequently getting its
        contents

        example:

        if FAKE:
        swift_stub.with_object('test-container-name', 'test-object-name',
            'test-object-contents')

        # returns swift object info and contents
        component_using_swift.create_object('test-container-name',
            'test-object-name', 'test-contents')
        component_using_swift.get_object('test-container-name',
            'test-object-name')

        :param container: container name that is the object belongs
        :param name: the name of the object expected to be created
        :param contents: the contents of the object
        """

        self._connection.get_container(container)
        when(swift_client.Connection).put_object(container, name,
                                                 contents).thenReturn(
                                                     uuid.uuid1())
        when(swift_client.Connection).get_object(container, name).thenReturn(
            ({'content-length': len(contents), 'accept-ranges': 'bytes',
              'last-modified': 'Mon, 10 Mar 2013 01:06:34 GMT',
              'etag': 'eb15a6874ce265e2c3eb1b4891567bab',
              'x-timestamp': '1363568794.67584',
              'x-trans-id': 'txef3aaf26c897420c8e77c9750ce6a501',
              'date': 'Mon, 10 Mar 2013 05:35:14 GMT',
              'content-type': 'application/octet-stream'}, contents)
        )
        self._remove_object(name, self._objects[container])
        self._objects[container].append(
            {'bytes': 13, 'last_modified': '2013-03-15T22:10:49.361950',
             'hash': 'ccc55aefbf92aa66f42b638802c5e7f6', 'name': name,
             'content_type': 'application/octet-stream'})
        return self

    def without_object(self, container, name):
        """
        sets expectations for deleting an object

        example:

        if FAKE:
        swift_stub.without_object('test-container-name', 'test-object-name')

        # allows container to be removed ONCE
        component_using_swift.remove_container('test-container-name')
        # throws ClientException - 404
        component_using_swift.get_container('test-container-name')
        component_using_swift.remove_container('test-container-name')

        :param container: container name that is the object belongs
        :param name: the name of the object expected to be removed
        """
        self._ensure_container_exists(container)
        self._ensure_object_exists(container, name)
        # throw exception if someone calls get object
        when(swift_client.Connection).get_object(container, name).thenRaise(
            swiftclient.ClientException('Resource Not found', http_status=404))
        when(swift_client.Connection).delete_object(
            container, name).thenReturn(None).thenRaise(
                swiftclient.ClientException('Resource Not Found',
                                            http_status=404))
        self._remove_object(name, self._objects[container])
        return self

def fake_create_swift_client(*args):
    return SwiftClientStub()