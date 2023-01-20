str_about = '''
    This module is responsible for handling some state related information
    which is mostly information about the ChRIS/CUBE instance.

    Core data includes information on the ChRIS/CUBE instances as well as
    information relevant to the pipeline to be scheduled.
'''

from    pudb.remote             import set_trace
from    curses                  import meta
from    pathlib                 import Path
from    argparse                import Namespace
from    loguru                  import logger
import  pudb
import  json
import  os
import  inspect
import  sys

logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> │ "
    "<level>{level: <5}</level> │ "
    "<yellow>{name: >28}</yellow>::"
    "<cyan>{function: <30}</cyan> @"
    "<cyan>{line: <4}</cyan> ║ "
    "<level>{message}</level>"
)
logger.remove()
logger.add(sys.stderr, format=logger_format)

class env:
    '''
    A class that contains environmental data -- mostly information about CUBE
    as well as data pertaining to the orthanc instance
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self._version   : str               = ''
        self._options   : Namespace         = None
        self._inputdir  : Path              = None
        self._outputdir : Path              = None
        self.CUBE       : CUBEinstance      = CUBEinstance()
        self.debug      : dict              = {
            'do'        : False,
            'termsize'  : (80,25),
            'port'      : 7900,
            'host'      : '0.0.0.0'
        }

    def DEBUG(self, *args, **kwargs):
        level   : int   = 1
        for k,v in kwargs.items():
            if k == 'level' : level = v
        if int(self.options.verbosity) >= level:
            logger.opt(depth=1, colors=True).debug(*args)

    def INFO(self, *args, **kwargs):
        level   : int   = 1
        for k,v in kwargs.items():
            if k == 'level' : level = v
        if int(self.options.verbosity) >= level:
            logger.opt(depth=1, colors=True).info(*args)

    def ERROR(self, *args, **kwargs):
        level   : int   = 0
        for k,v in kwargs.items():
            if k == 'level' : level = v
        if int(self.options.verbosity) >= level:
            logger.opt(depth=1).error(*args)

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, a):
        self._version   = a

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, a):
        self._options   = a

    @property
    def inputdir(self):
        return self._inputdir

    @inputdir.setter
    def inputdir(self, a):
        self._inputdir = a

    @property
    def outputdir(self):
        return self._outputdir

    @outputdir.setter
    def outputdir(self, a):
        self._outputdir = a

    def debug_setup(self, **kwargs) -> dict:
        """
        Setup the debugging structure based on <kwargs>

        Returns:
            dict: the debug structure
        """
        str_termsize    : str   = ""
        str_port        : str   = ""
        str_host        : str   = "0.0.0.0"
        b_debug         : bool  = False
        for k,v in kwargs.items():
            if k == 'debug'     :   b_debug         = v
            if k == 'termsize'  :   str_termsize    = v
            if k == 'port'      :   str_port        = v
            if k == 'host'      :   str_host        = v

        cols, rows  = str_termsize.split(',')
        self.debug['do']        = b_debug
        self.debug['termsize']  = (int(cols), int(rows))
        self.debug['port']      = int(str_port)
        self.debug['host']      = str_host
        return self.debug

    def set_telnet_trace_if_specified(self):
        """
        If specified in the env, pause for a telnet debug.

        If you are debugging, just "step" to return to the location
        in your code where you specified to break!
        """
        if self.debug['do']:
            set_trace(
                term_size   = self.debug['termsize'],
                host        = self.debug['host'],
                port        = self.debug['port']
            )

    def set_trace(self):
        """
        Simple "override" for setting a trace. If the Env is configured
        for debugging, then this set_trace will be called. Otherwise it
        will be skipped.

        This is useful for leaving debugging set_traces in the code, and
        being able to at runtime choose to debug or not.

        If you are debugging, just "step" to return to the location
        in your code where you specified to break!

        Returns:
            _type_: _description_
        """
        if self.debug['do']:
            pudb.set_trace()

class CUBEinstance:
    '''
    A class that contains data pertinent to a specific CUBE instance
    '''

    def __init__(self, *args, **kwargs):
        self.d_CUBE = {
            'user'      : '',
            'password'  : '',
            'address'   : '',
            'port'      : '',
            'route'     : '',
            'protocol'  : '',
            'url'       : ''
        }

    @property
    def user(self):
        return self.d_CUBE['user']

    @user.setter
    def user(self, a):
        self.d_CUBE['user'] = a

    @property
    def password(self):
        return self.d_CUBE['password']

    @password.setter
    def password(self, a):
        self.d_CUBE['password'] = a

    @property
    def url(self):
        return self.d_CUBE['url']

    @url.setter
    def url(self, a):
        self.d_CUBE['url'] = a

    @property
    def IP(self):
        return self.d_CUBE['address']

    @IP.setter
    def IP(self, a):
        self.d_CUBE['address'] = a

    @property
    def port(self):
        return self.d_CUBE['port']

    @port.setter
    def port(self, a):
        self.d_CUBE['port'] = a

    def onCUBE(self) -> dict:
        '''
        Return a dictionary that is a subset of self.d_CUBE
        suitable for using in calls to the CLI tool 'chrispl-run'
        '''
        return {
            'protocol': self('protocol'),
            'port':     self('port'),
            'address':  self('address'),
            'user':     self('user'),
            'password': self('password')
        }

    def url_decompose(self, *args) -> dict:
        """
        Decompose a URL into its constituent parts

        Returns:
            dict: self.d_CUBE
        """
        if len(args):
            self.d_CUBE['url']  = args[0]

        self.d_CUBE['protocol'], str_rest = self.d_CUBE['url'].split('://')
        str_IPport              = str_rest.split('/')[0]
        str_route               = '/' + '/'.join(str_rest.split('/')[1:])
        l_IPport                = str_rest.split(':')
        if len(l_IPport) == 2:
            self.d_CUBE['address'], self.d_CUBE['port'] = l_IPport
        else:
            self.d_CUBE['address']  = l_IPport[0]
        return self.d_CUBE

    def furl(self, *args):
        '''
        get/set the URL
        '''
        str_colon : str = ""
        if len(self.d_CUBE['port']):
            str_colon   = ":"
        if len(args):
            self.d_CUBE['url']  = args[0]
        else:
            self.d_CUBE['url']  = '%s://%s%s%s%s' % (
                self.d_CUBE['protocol'],
                self.d_CUBE['address'],
                str_colon,
                self.d_CUBE['port'],
                self.d_CUBE['route']
            )
        return self.d_CUBE['url']

    def user(self, *args) -> str:
        '''
        get/set the CUBE user
        '''
        if len(args): self.d_CUBE['user']  = args[0]
        return self.d_CUBE['user']

    def password(self, *args) -> str:
        '''
        get/set the CUBE user
        '''
        if len(args): self.d_CUBE['password']  = args[0]
        return self.d_CUBE['password']

    def set(self, str_key, str_val):
        '''
        set str_key to str_val
        '''
        if str_key in self.d_CUBE.keys():
            self.d_CUBE[str_key]    = str_val

    def __call__(self, str_key):
        '''
        get a value for a str_key
        '''
        if str_key in self.d_CUBE.keys():
            return self.d_CUBE[str_key]
        else:
            return ''
