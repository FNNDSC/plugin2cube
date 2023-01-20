#!/usr/bin/env python
__version__ = '2.2.4'

from    pathlib                 import Path

import  os, sys, json
import  pudb
from    pudb.remote             import set_trace

from    concurrent.futures      import ThreadPoolExecutor
from    threading               import current_thread

from    datetime                import datetime, timezone

from    state                   import data
from    logic                   import behavior
from    control                 import action

class plugin2cube:

    def __init__(self, *args, **kwargs):
        """
        constructor
        """
        self.env                                    = None
        self.options            : Namespace         = None
        for k, v in kwargs.items():
            if k == 'env'               : self.env                  = v
            if k == 'options'           : self.options              = v

    def prep_do(self) -> action.PluginRep:
        """
        Perform some setup and initial LOG output

        Args:
            options (Namespace): input CLI options

        Returns:
            action.PluginRep: a runnable object that is used to determine the
                              plugin JSON representation
        """

        PLjson                  = action.PluginRep(
                                        env     = self.env,
                                        options = self.options
                                )

        self.env.INFO("Doing some quick prep...", level = 2)

        self.env.DEBUG("plugin arguments...", level = 3)
        for k,v in self.options.__dict__.items():
             self.env.DEBUG("%25s:  [%s]" % (k, v), level = 3)
        self.env.DEBUG("", level = 3)

        if self.options.osenv:
            self.env.DEBUG("base environment...")
            for k,v in os.environ.items():
                self.env.DEBUG("%25s:  [%s]" % (k, v), level = 3)
            self.env.DEBUG("")

        return PLjson

    def plugin_add(self, PLjson : action.PluginRep) -> dict:
        """
        Add the described plugin to the specified CUBE.

        Args:
            options (Namespace): CLI option space
            PLjson (action.PluginRep): a runnable object used to determine the
                                       base JSON representation

        Returns:
            dict: the JSON return from the CUBE API for registration
        """

        def file_timestamp(str_stamp : str = ""):
            """
            Simple timestamp to file

            Args:
                str_prefix (str): an optional prefix string before the timestamp
            """
            timenow                 = lambda: datetime.now(timezone.utc).astimezone().isoformat()
            str_heartbeat   : str   = str(self.env.outputdir.joinpath('run-%s.log' % str_threadName))
            fl                      = open(str_heartbeat, 'a')
            fl.write('{}\t%s\n'.format(timenow()) % str_stamp)
            fl.close()

        def jsonRep_get() -> dict:
            """
            Determine the plugin JSON representation

            Returns:
                dict: JSON representation
            """
            d_jsonRep   = PLjson()
            return d_jsonRep

        register                = action.Register(env = self.env, options = self.options)
        d_register      : dict  = None
        str_threadName  : str   = current_thread().getName()
        file_timestamp('START')

        self.env.INFO("Registering plugin <magenta>%s</magenta>..." % self.options.dock_image)
        d_register          = register(jsonRep_get())
        if d_register['status']:
            self.env.INFO('Registration of plugin <magenta>%s</magenta>: <green>OK!</green>' % self.options.dock_image)
            self.env.INFO('\n%s' % json.dumps(d_register, indent = 4), level = 3)
        else:
            self.env.INFO('Registration <magenta>%s</magenta>: <red>Failed!</red>' % self.options.dock_image)
            self.env.ERROR(d_register['obj']['run']['stderr'])
            self.env.ERROR('\n%s' % json.dumps(d_register, indent= 4), level = 2)
        file_timestamp('\n%s' % json.dumps(d_register, indent = 4))
        file_timestamp('END')
        return d_register

    def run(self) -> dict:
        """
        Main entry point into the module

        Returns:
            dict: results from the registration
        """
        return self.plugin_add(self.prep_do())

