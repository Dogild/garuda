# -*- coding: utf-8 -*-
import logging
import os
import importlib
from uuid import uuid4
from time import sleep
from bambou import BambouConfig
from setproctitle import setproctitle

logger = logging.getLogger('garuda')

from core.lib import GASDKLibrary
from core.controllers import GACoreController, GAChannelsController
from core.channels import GAChannel
from core.plugins import GALogicPlugin, GAAuthenticationPlugin, GAStoragePlugin, GAPermissionsPlugin

__version__ = '1.0'
__all__ = ['Garuda']
__doc__ = """

## Welcome to Garuda!

Garuda is a Python Application Server that allows you to spawn projects in no time, using a tool set that will take care of:

 - Designing your data model using a GUI
 - Providing a full blown client sdk
 - Providing a cli to interact with your data model
 - Providing a back end to store information (this is Garuda)
 - Providing a UI ToolKit to quickly create the user interfaces
 - Providing a test suite that will run advanced tests, using a GUI

Without adding a single line of code, you will have:

 - All hierarchical CRUD operations on your data model
 - Low level validation for the requests (required attribute, or wrong type, etc)
 - Persistence in a MongoDB (but it could be anything)
 - Flask channel for incoming messages (but it could be anything)
 - Comet-style Push Channel
 - Filtering
 - Pagination

A ready to use system, if you like. The only thing you will need to do, is to focuse on your
business logic, by writing very small plugins. That way your logic is all contained. Garuda will
take care of all the `rest` (pun itended) for you.
"""


class Garuda(object):
    """
        Garuda is the base object of the system. This class allows you to easily start a Garuda project.
    """

    def __init__(self, sdks_info, redis_info, channels=[], plugins=[], additional_controller_classes=[], additional_master_controller_classes=[],
                 log_level=logging.INFO, log_handler=None, runloop=True, banner=True, debug=False):
        """ Initializes Garuda.

        """
        setproctitle('garuda-server')
        BambouConfig.set_should_raise_bambou_http_error(False)

        self._uuid = str(uuid4())
        self._redis_info = redis_info if redis_info else {'host': '127.0.0.1', 'port': '6379', 'db': 0}
        self._runloop = runloop
        self._sdks_info = sdks_info
        self._sdk_library = GASDKLibrary()
        self._channels = channels
        self._debug = debug
        self._additional_controller_classes = additional_controller_classes
        self._additional_master_controller_classes = additional_master_controller_classes

        self._authentication_plugins = []
        self._storage_plugins = []
        self._logic_plugins = []
        self._permission_plugins = []

        for sdk_info in self._sdks_info:
            self._sdk_library.register_sdk(identifier=sdk_info['identifier'], sdk=importlib.import_module(sdk_info['module']))

        for plugin in plugins:

            if isinstance(plugin, GAChannel):
                self._channels.append(plugin)
            elif isinstance(plugin, GAAuthenticationPlugin):
                self._authentication_plugins.append(plugin)
            elif isinstance(plugin, GAStoragePlugin):
                self._storage_plugins.append(plugin)
            elif isinstance(plugin, GAPermissionsPlugin):
                self._permission_plugins.append(plugin)
            elif isinstance(plugin, GALogicPlugin):
                self._logic_plugins.append(plugin)

        if banner:
            self.print_banner()

        if not log_handler:
            log_handler = logging.StreamHandler()
            log_handler.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
            logger.addHandler(log_handler)

        logger.setLevel(log_level)

        self._channels_controller = GAChannelsController(garuda_uuid=self._uuid,
                                                         channels=self._channels,
                                                         redis_info=self._redis_info,
                                                         additional_controller_classes=self._additional_controller_classes,
                                                         logic_plugins=self._logic_plugins,
                                                         authentication_plugins=self._authentication_plugins,
                                                         storage_plugins=self._storage_plugins,
                                                         permission_plugins=self._permission_plugins)

        self._master_core = GACoreController(garuda_uuid=self._uuid,
                                             redis_info=self._redis_info,
                                             logic_plugins=[],
                                             additional_controller_classes=self._additional_master_controller_classes,
                                             authentication_plugins=self._authentication_plugins,
                                             storage_plugins=self._storage_plugins,
                                             permission_plugins=self._permission_plugins)

    def _init_debug_mode(self):
        """
        """
        try:
            import resource
            import guppy
            import signal

            print '# DBG MODE: Debug Mode active'
            print '# DBG MODE: Initial memory usage : %f (MB)' % (float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024 / 1024)
            print '# DBG MODE: Collecting initial heap snaphot...'
            hp = guppy.hpy()
            heap_initial = hp.heap()

            heap_initial  # make pep8 happy

            def handle_signal(signal_number, frame_stack):
                self._launch_debug_mode()

            signal.signal(signal.SIGHUP, handle_signal)

            print '# DBG MODE: Initial heap snaphot collected'
            print '# DBG MODE: Do a `kill -HUP %s` to enter the debug mode at anytime' % os.getpid()
            print '# DBG MODE: Hitting CTRL+C stop Garuda then enter the debugg mode.'
        except:
            print '# DBG MODE: Cannot use Debugging Mode. Modules needed: `ipdb`, `resource`, `objgraph` and `guppy`'
            self._debug = False
        finally:
            print ''

    def _launch_debug_mode(self):
        """
        """
        import ipdb
        import resource
        import guppy

        print ''
        print '# DBG MODE: Entering Debugging Mode...'
        print '# DBG MODE: Final memory usage : %f (MB)' % (float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024 / 1024)
        print '# DBG MODE: Collecting final heap snaphot...'
        hp = guppy.hpy()
        heap_current = hp.heap()
        heap_current  # make pep8 happy
        print '# DBG MODE: Current heap snaphot collected'
        print '# DBG MODE: You can see the heap snaphots in variables `heap_initial` and `heap_current`'
        print '# DBG MODE: Starting ipdb (CTRL+D to exit)'
        print ''
        ipdb.set_trace()

    def print_banner(self):
        """
        """
        all_sdks = ', '.join([item['module'] for item in self._sdks_info])
        all_channels = ', '.join([channel.manifest().name for channel in self._channels])
        all_storages = ', '.join([plugin.manifest().name for plugin in self._storage_plugins])
        all_auth = ', '.join([plugin.manifest().name for plugin in self._authentication_plugins])
        all_perms = ', '.join([plugin.manifest().name for plugin in self._permission_plugins])

        print """
                       1y9~
             .,:---,      "9"R            Garuda %s
         ,N"`    ,jyjjRN,   `n ?          ==========
       #^   y&T        `"hQ   y 'y
     (L  ;R@l                 ^a \w       PID: %d
    (   #^4                    Q  @
    Q  # ,W                    W  ]V      %d channel%s           %s
   |# @L Q                    W   Q|      %s sdk%s               %s
    V @  Vp                  ;   #^[      %d storage plugin%s    %s
    ^.R[ 'Q@               ,4  .& ,T      %d auth plugin%s       %s
     (QQ  'Q4p           (R  ,BL (T       %d permission plugin%s %s
       hQ   H,`"QQQL}Q"`,;&RR   x
         "g   YQ,    ```     :F`          %d logic plugin%s
           "E,  `"B@MD&DR@B`
               '"N***xD"`

               """ % (__version__, os.getpid(),
                      len(self._channels), "s" if len(self._channels) > 1 else "", ": %s" % all_channels if len(all_channels) else "",
                      len(self._sdks_info), "s" if len(self._sdks_info) > 1 else "", ": %s" % all_sdks if len(all_sdks) else "",
                      len(self._storage_plugins), "s" if len(self._storage_plugins) > 1 else "", ": %s" % all_storages if len(all_storages) else "",
                      len(self._authentication_plugins), "s" if len(self._authentication_plugins) > 1 else "", ": %s" % all_auth if len(all_auth) else "",
                      len(self._permission_plugins), "s" if len(self._permission_plugins) > 1 else "", ": %s" % all_perms if len(all_perms) else "",
                      len(self._logic_plugins), "s" if len(self._logic_plugins) > 1 else "")

    def start(self):
        """
        """
        if self._debug:
            self._init_debug_mode()

        self._channels_controller.start()
        self._master_core.start()

        logger.info('Garuda is up and ready to rock! (press CTRL-C to exit)')

        if self._runloop:
            while True:
                try:
                    sleep(300000)
                except KeyboardInterrupt:
                    break

        self.stop()

    def stop(self):
        """
        """
        self._channels_controller.stop()
        self._master_core.stop()

        logger.info('Garuda is stopped')

        if self._debug:
            self._launch_debug_mode()
