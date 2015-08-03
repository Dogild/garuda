# -*- coding: utf-8 -*-

import gevent

from time import sleep
from utils import GAContext, URLParser
from channels import RESTCommunicationChannel
from gaexceptions import ContextException

from collections import namedtuple
PluginContext = namedtuple('PluginContext', ['plugin', 'context'])
from multiprocessing import Process


class ProcessManager(object):
    """ Multi process manager

    """
    def __init__(self):
        """ Initializes a ProcessManager

        """
        self._processes = list()

    def wait_until_exit(self):
        """ Wait until all process are finished.

        """
        [t.join() for t in self._processes]

        self._processes = list()

    def start(self, method, *args, **kwargs):
        """ Start a method in a separate process

            Args:
                method: the method to start in a separate process
                args: Accept args/kwargs arguments
        """
        process = Process(target=method, args=args, kwargs=kwargs)
        process.is_daemon = True
        process.start()
        self._processes.append(process)

    def is_running(self):
        """ Returns true if one process is running
        """

        for process in self._processes:
            if process.is_alive():
                return True

        return False

    def stop_all(self):
        """ Stop all current processes
        """
        for process in self._processes:
            process.terminate()

        self.wait_until_exit()


class CoreController(object):
    """

    """
    def __init__(self):
        """
        """
        self._channels = []
        self._process_manager = ProcessManager()

        flask2000 = RESTCommunicationChannel(controller=self, port=2000, debug=True, use_reloader=False)
        flask3000 = RESTCommunicationChannel(controller=self, port=3000, debug=True, use_reloader=False)

        self.register_channel(flask2000)
        self.register_channel(flask3000)

    def register_channel(self, channel):
        """
        """
        if channel not in self._channels:
            self._channels.append(channel)

    def unregister_channel(self, channel):
        """
        """
        if channel in self._channels:
            self._channels.remove(channel)

    def start(self):
        """
        """
        for channel in self._channels:
            self._process_manager.start(channel.start)

    def is_running(self):
        """
        """
        return self._process_manager.is_running()

    def stop(self, signal=None, frame=None):
        """
        """
        self._process_manager.stop_all()

        for channel in self._channels:
            channel.stop()

    def launch_operation(self, session, request):
        """
        """
        # TODO: Indicate what to do in the operation

        context = GAContext(session=session, request=request)
        try:
            manager = OperationsManager(context=context)
            manager.run()
        except ContextException:
            print context.errors
            last_error = context.errors[-1]
            return last_error

        # TODO: Create response from context

        return {'status': 200, 'data': 'ok'}


READ_OPERATIONS_METHODS = ['GET', 'HEAD', 'OPTIONS']
WRITE_OPERATIONS_METHODS = ['POST', 'PUT', 'DELETE']


class OperationsManager(object):
    """

    """
    def __init__(self, context):
        """
        """
        self.context = context

    def run(self):
        """
        """
        method = self.context.request.method.upper()

        if method in READ_OPERATIONS_METHODS:
            self._perform_read_operation()
        else:
            self._perform_write_operation()

    def _prepare_context_for_read_operation(self):
        """
        """
        url = self.context.request.url
        parser = URLParser(url)
        resources = parser.resources

        resource = resources[-1]

        if resource.value is None:
            # Get All resource.name
            self.context.action = GAContext.ACTION_READALL
            if len(resources) == 1:
                parent = ModelController.get_current_user()

            else:  # Having a parent and a child
                parent_resource = resources[0]
                parent = ModelController.get_object(parent_resource.name, parent_resource.value)

                if parent is None:
                    self.context.report_error(status=404, reason='Unable to retrieve object parent %s with identifier %s' % (parent_resource.name, parent_resource.value))
                    raise ContextException()

            self.context.parent = parent
            self.context.objects = ModelController.get_objects(parent, resource.name)

        else:
            # Get a specific resource.name
            self.context.action = GAContext.ACTION_READ
            self.context.object = ModelController.get_object(resource.name, resource.value)

    def _perform_read_operation(self):
        """

        """

        self._prepare_context_for_read_operation()

        plugin_manager = PluginsManager(context=self.context)

        plugin_manager.perform_delegate(delegate='begin_read_operation')

        plugin_manager.perform_delegate(delegate='should_perform_read')

        if len(self.context.errors) > 0:
            raise ContextException()

        plugin_manager.perform_delegate(delegate='preprocess_read')

        ModelController.read()

        plugin_manager.perform_delegate(delegate='end_read_operation')

    def _prepare_context_for_write_operation(self):
        """
        """
        method = self.context.request.method.upper()
        url = self.context.request.url
        parser = URLParser(url)
        resources = parser.resources

        if method is 'POST':
            self.context.action = GAContext.ACTION_CREATE
        elif method is 'PUT':
            self.context.action = GAContext.ACTION_UPDATE
        elif method is 'DELETE':
            self.context.action = GAContext.ACTION_DELETE
        else:
            self.context.report_error(status=409, reason='Unknown ACTION for method %s' % method)
            raise ContextException()

        resource = resources[-1]

        if self.context.action != GAContext.ACTION_CREATE and resource.value is None:
            self.context.report_error(status=405, reason='Unable to %s a resource without its identifier' % self.context.action)
            raise ContextException()

        if len(resources) == 1:
            parent = None

        else:  # Having a parent and a child
            parent_resource = resources[0]
            self.context.parent = ModelController.get_object(parent_resource.name, parent_resource.value)

            if parent is None:
                self.context.report_error(status=404, reason='Unable to retrieve object parent %s with identifier %s' % (parent_resource.name, parent_resource.value))
                raise ContextException()

        if self.context.action == GAContext.CREATE:
            self.context.object = ModelController.create_object(resource.name)
        else:
            self.context.object = ModelController.get_object(resource.name, resource.value)

    def _perform_write_operation(self):
        """
        """
        self._prepare_context_for_write_operation()
        pass


class PluginsManager(object):
    """

    """
    _plugins = []

    def __init__(self, context, timeout=2):
        """

        """
        self.context = context  # Plugin contexts' parent
        self.timeout = timeout  # Gevent spawn timeout
        self.plugins_contexts = []  # Plugins available for the current context

        for plugin in self._plugins:
            if plugin.is_listening(rest_name=context.session.resource.rest_name, action=context.session.action):
                plugin_context = PluginContext(plugin=plugin, context=context.copy())
                self.plugins_contexts.append(plugin_context)

    @classmethod
    def register_plugin(cls, plugin):
        """

        """
        cls._plugins.append(plugin)

    @classmethod
    def unregister_plugin(cls, plugin):
        """

        """
        cls._plugins.remove(plugin)

    def perform_delegate(self, delegate, *args, **kwargs):
        """
        """
        if len(self.plugins_contexts) == 0:
            return

        jobs = []
        for plugin_context in self.plugins_contexts:

            plugin = plugin_context.plugin
            context = plugin_context.context
            method = getattr(plugin, delegate, None)

            if method:
                jobs.append(gevent.spawn(method, context=context, *args, **kwargs))

        gevent.joinall(jobs, timeout=self.timeout)

        contexts = [job.value for job in jobs]
        self.context.merge_contexts(contexts)


class ModelController(object):
    """

    """
    @classmethod
    def read(cls, *args, **kwargs):
        """
        """
        print '** Let the police...Wait for it...'
        sleep(2)
        print '...do the job **'

    @classmethod
    def get_objects(self, parent, resource_name):
        """
        """
        sleep(1)
        return [object()]

    @classmethod
    def get_object(self, resource_name, resource_value):
        """
        """
        sleep(1)
        return object()

    @classmethod
    def create_object(self, resource_name):
        """
        """
        sleep(1)
        return object()

    @classmethod
    def save_object(self, object, parent=None):
        """
        """
        sleep(1)
        return object
