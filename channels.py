# -*- coding: utf-8 -*-

from flask import Flask, request, make_response
from copy import deepcopy

from gaexceptions import NotImplementedException
from utils import GARequest, GASession, Resource


class CommunicationChannel(object):
    """

    """
    def start(self):
        """
        """
        raise NotImplementedException('CommunicationChannel should implement start method')

    def stop(self):
        """
        """
        raise NotImplementedException('CommunicationChannel should implement stop method')

    def is_running(self):
        """

        """
        raise NotImplementedException('CommunicationChannel should implement is running method')

    def receive(self):
        """

        """
        raise NotImplementedException('CommunicationChannel should implement receive method')

    def send(self):
        """

        """
        raise NotImplementedException('CommunicationChannel should implement send method')

    def push(self):
        """

        """
        raise NotImplementedException('CommunicationChannel should implement push method')


class RESTCommunicationChannel(CommunicationChannel):
    """

    """
    def __init__(self, controller, **kwargs):
        """
        """
        self._is_running = False
        self.controller = controller
        self.app = Flask(self.__class__.__name__)

        self.app.add_url_rule('/', 'vsd', self.index, defaults={'path': ''})
        self.app.add_url_rule('/<path:path>', 'vsd', self.index, methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD'])
        self.start_parameters = kwargs

    def start(self):
        """
        """
        if self.is_running:
            return

        self._is_running = True
        self.app.run(**self.start_parameters)

    def stop(self):
        """
        """
        if not self.is_running:
            return

        self._is_running = False

    @property
    def is_running(self):
        """
        """
        return self._is_running

    def _extract_data(self, data):
        """

        """
        return deepcopy(data)

    def _extract_headers(self, headers):
        """

        """
        headers = {}

        for header in request.headers:
            headers[header[0]] = header[1]

        return headers

    def index(self, path):
        """
        """

        data = self._extract_data(request.json)
        headers = self._extract_headers(request.headers)

        print '--- Request from %s ---' % headers['Host']

        ga_request = GARequest(method=request.method, url=request.url, data=data, headers=headers)
        ga_session = GASession(resource=Resource(), user='me', data={}, action='create')

        response = self.controller.launch_operation(session=ga_session, request=ga_request)

        print '--- Response to %s ---' % headers['Host']

        if response['status'] >= 300:
            http_response = make_response(response['reason'])
        else:
            http_response = make_response(response['data'])

        http_response.status_code = response['status']
        http_response.mimetype = 'application/json'

        return http_response
