# -*- coding: utf-8 -*-
from uuid import uuid4
from bambou import NURESTRootObject

from .serializable import GASerializable


class GASession(GASerializable):
    """

    """
    def __init__(self, garuda_uuid=None, root_object=None):
        """
        """
        super(GASession, self).__init__()

        self._uuid = str(uuid4())
        self._garuda_uuid = garuda_uuid
        self.root_object = root_object
        self.ttl = None

        self.register_attribute(type=str, internal_name='_uuid')
        self.register_attribute(type=str, internal_name='_garuda_uuid')
        self.register_attribute(type=NURESTRootObject, internal_name='root_object')

    @property
    def uuid(self):
        """
        """
        return self._uuid

    @property
    def redis_key(self):
        """
        """
        return 'sessions:%s' % self.uuid

    @property
    def garuda_uuid(self):
        """
        """
        return self._garuda_uuid
