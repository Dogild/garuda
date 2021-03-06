from uuid import uuid4
from bambou import NURESTRootObject

from garuda.core.plugins import GAAuthenticationPlugin
from garuda.core.models import GAPluginManifest


class FakeAuthPlugin(GAAuthenticationPlugin):
    """
    """

    @classmethod
    def manifest(self):
        """
        """
        return GAPluginManifest(name='test.fake.auth', version=1.0, identifier='test.fake.auth')

    def authenticate(self, request=None, session=None):
        """
        """
        root = NURESTRootObject()
        root.id = 'id'
        root.api_key = 'token'
        root.user_name = 'username'
        return root

    def should_manage(self, request):
        """
        """
        return True

    def extract_session_identifier(self, request):
        """
        """
        return request.token
