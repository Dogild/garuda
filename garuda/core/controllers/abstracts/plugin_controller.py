# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger('garuda.controller.plugin')

from garuda.core.models import GAPlugin
from garuda.core.channels.abstracts import GAChannel


class GAPluginController(object):
    """
    """
    def __init__(self, plugins, core_controller):
        """
        """

        self._core_controller = core_controller
        self._plugins = []

        for plugin in plugins:
            self.register_plugin(plugin=plugin)

    @property
    def core_controller(self):
        """
        """
        return self._core_controller

    def register_plugin(self, plugin, plugin_type):
        """
        """
        if not isinstance(plugin, plugin_type):
            logger.error("Plugin %s cannot be registered to %s" % (plugin, self))
            return

        if plugin in self._plugins:
            logger.warn("Plugin %s is already registered in controller %s" % (plugin, self))
            return

        logger.debug("Registering plugin '%s (%s)'" % (plugin.manifest().identifier, plugin.manifest().name))

        plugin.core_controller = self.core_controller

        plugin.will_register()
        self._plugins.append(plugin)
        plugin.did_register()

    def unregister_plugin(self, plugin):
        """
        """

        if plugin not in self._plugins:
            logger.warn("No plugin %s registered in controller %s" % (plugin, self))
            return

        logger.info("Unregister plugin %s in controller %s" % (plugin, self))
        plugin.will_unregister()
        self._plugins.remove(plugin)
        plugin.did_unregister()

        plugin.core_controller = None

    def unregister_all_plugins(self):
        """
        """
        for plugin in self._plugins:
            self.unregister_plugin(plugin)
