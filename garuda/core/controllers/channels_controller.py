# -*- coding: utf-8 -*-
import os
import sys
import signal
import logging

from garuda.core.controllers import GACoreController

logger = logging.getLogger('garuda.controller.channels')


class GAChannelsController(object):
    """

    """
    def __init__(self, garuda_uuid, channels, redis_info, additional_controller_classes, logic_plugins, authentication_plugins, storage_plugins, permission_plugins):
        """
        """
        self._garuda_uuid = garuda_uuid
        self._channels = channels
        self._redis_info = redis_info
        self._logic_plugins = logic_plugins
        self._authentication_plugins = authentication_plugins
        self._storage_plugins = storage_plugins
        self._permission_plugins = permission_plugins
        self._additional_controller_classes = additional_controller_classes
        self._channel_pids = []

    # Implementation

    @property
    def garuda_uuid(self):
        """
        """
        return self._garuda_uuid

    @property
    def channels(self):
        """
        """
        return self._channels

    @property
    def redis_info(self):
        """
        """
        return self._redis_info

    @property
    def logic_plugins(self):
        """
        """
        return self._logic_plugins

    @property
    def authentication_plugins(self):
        """
        """
        return self._authentication_plugins

    @property
    def storage_plugins(self):
        """
        """
        return self._storage_plugins

    @property
    def permission_plugins(self):
        """
        """
        return self._permission_plugins

    @property
    def additional_controller_classes(self):
        """
        """
        return self._additional_controller_classes

    @property
    def channel_pids(self):
        """
        """
        return self._channel_pids

    def start(self):
        """
        """
        logger.info("Forking communication channels...")

        for channel in self._channels:

            pid = os.fork()
            if not pid:  # pragma: no cover
                break
            else:
                self._channel_pids.append(pid)
                logger.info('Channel %s forked with pid: %s' % (channel.manifest().identifier, pid))

        if not pid:  # pragma: no cover
            core = GACoreController(garuda_uuid=self._garuda_uuid,
                                    redis_info=self._redis_info,
                                    logic_plugins=self._logic_plugins,
                                    additional_controller_classes=self._additional_controller_classes,
                                    authentication_plugins=self._authentication_plugins,
                                    storage_plugins=self._storage_plugins,
                                    permission_plugins=self._permission_plugins)

            channel.core_controller = core
            channel.did_fork()
            channel.run()
            logger.info("Channels subprocess %s exited gracefuly." % os.getpid())
            channel.did_exit()
            sys.exit(0)
        else:
            logger.info("All channels successfully forked")

    def stop(self):
        """
        """
        for pid in self._channel_pids:
            logger.info("Killing channel with pid %s" % pid)
            os.kill(pid, signal.SIGTERM)

        self._channel_pids = []
