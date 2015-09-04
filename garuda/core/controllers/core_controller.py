# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger('Garuda.CoreController')

from .models_controller import ModelsController
from .operations_manager import OperationsManager
from .thread_manager import ThreadManager
from .push_controller import PushController
from .sessions_manager import SessionsManager

from garuda.channels.rest import RESTCommunicationChannel
from garuda.core.models import GAContext, GAResponse, GARequest, GAError

from uuid import uuid4

import ssl

class CoreController(object):
    """

    """
    def __init__(self):
        """
        """
        self._uuid = str(uuid4())
        self._channels = []
        self._thread_manager = ThreadManager()
        self._models_controller = ModelsController()
        self._sessions_manager = SessionsManager()
        self._push_controller = PushController()
        self.push_controller.start()

        context = None
        # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        # context.load_cert_chain("/Users/chserafi/Desktop/keys/vns.pem", "/Users/chserafi/Desktop/keys/vns-Key.pem")

        flask2000 = RESTCommunicationChannel(controller=self, port=2000, threaded=True, debug=True, use_reloader=False, ssl_context=context)
        flask3000 = RESTCommunicationChannel(controller=self, port=3000, threaded=True, debug=True, use_reloader=False, ssl_context=context)

        self.register_channel(flask2000)
        # self.register_channel(flask3000)

    @property
    def uuid(self):
        """
        """
        return self._uuid

    @property
    def models_controller(self):
        """
        """
        return self._models_controller

    @property
    def push_controller(self):
        """
        """
        return self._push_controller

    @property
    def sessions_manager(self):
        """
        """
        return self._sessions_manager

    def register_channel(self, channel):
        """
        """
        logger.debug('Register channel %s' % channel)
        if channel not in self._channels:
            self._channels.append(channel)

    def unregister_channel(self, channel):
        """
        """
        logger.debug('Unregister channel %s' % channel)
        if channel in self._channels:
            self._channels.remove(channel)

    def start(self):
        """
        """
        logger.debug('Starting core controller')
        for channel in self._channels:
            logger.debug('Starting channel %s' % channel)
            self._thread_manager.start(channel.start)

    def is_running(self):
        """
        """
        return self._thread_manager.is_running()

    def stop(self, signal=None, frame=None):
        """
        """
        logger.debug('Stopping core controller')
        self._thread_manager.stop_all()
        self.push_controller.flush(garuda_uuid=self.uuid)
        self.push_controller.stop()

    def execute(self, request):
        """
        """
        session_uuid = request.parameters['password'] if 'password' in request.parameters else None
        session = self.sessions_manager.get(session_uuid=session_uuid)
        context = GAContext(session=session, request=request)

        logger.debug('Execute action %s on session UUID=%s' % (request.action, session_uuid))

        if session is None:
            context.report_error(type=GAError.TYPE_UNAUTHORIZED, property='', title='Unauthorized access', description='Could not grant access. Please log in.')
            return GAResponse(status=context.errors.type, content=context.errors)

        manager = OperationsManager(context=context, models_controller=self.models_controller)
        manager.run()

        if context.has_errors():
            return GAResponse(status=context.errors.type, content=context.errors)



        if request.action is GARequest.ACTION_READALL:
            return GAResponse(status=GAResponse.STATUS_SUCCESS, content=context.objects)

        self.push_controller.add_notification(garuda_uuid=self.uuid, action=request.action, entities=[context.object])
        return GAResponse(status=GAResponse.STATUS_SUCCESS, content=context.object)

    def execute_authenticate(self, request):
        """
        """
        session = self.sessions_manager.create_session(request=request, models_controller=self.models_controller, garuda_uuid=self.uuid)
        context = GAContext(session=session, request=request)

        logger.debug('Execute action %s on session UUID=%s' % (request.action, session.uuid if session else None))

        if session is None:
            description = 'Unable to authenticate'
            context.report_error(type=GAError.TYPE_AUTHENTICATIONFAILURE, property='', title='Authentication failed!', description=description)

        if context.has_errors():
            return GAResponse(status=context.errors.type, content=context.errors)

        return GAResponse(status=GAResponse.STATUS_SUCCESS, content=session.user)

    def get_queue(self, request):
        """
        """

        session_uuid = request.parameters['password'] if 'password' in request.parameters else None
        session = self.sessions_manager.get(session_uuid=session_uuid)
        # context = GAContext(session=session, request=request)

        if session is None:
            # TODO: Create a GAResponse
            # context.report_error(type=GAError.TYPE_UNAUTHORIZED, property='', title='Unauthorized access', description='Could not grant access. Please log in.')
            return None

        logger.debug('Set listening %s session UUID=%s for push notification' % (request.action, session_uuid))

        session.is_listening_push_notifications = True
        self.sessions_manager.save(session)

        queue = self.push_controller.get_queue_for_session(session.uuid)

        return queue