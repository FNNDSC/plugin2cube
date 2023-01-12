str_about = '''
    The action module provides functionality to run individual
    plugins as well as "pipelines" of plugins.

    This module is the contact "surface" between dypi and a CUBE
    instance. Control/manipulation of the ChRIS instance is effected
    by a set of CLI scripts that this module creates and then executes.

    NOTE: This module is "fragily" dependent on python-chrisclient and
    caw! Changes in those modules could break things here rather
    completely.
'''

from    .                       import  jobber
from    state                   import  data
import  os
import  re
import  pudb
import  json
from    argparse                import ArgumentParser, Namespace
from    chrisclient             import client
import  time

class PluginRun:
    '''
    A simple class wrapper that runs a container image to determine its
    json description
    '''
    def __init__(self, *args, **kwargs):
        self.env                                    = None
        self.plugin                                 = ''
        self.options            : Namespace         = None
        for k, v in kwargs.items():
            if k == 'env'               : self.env                  = v
            if k == 'options'           : self.options              = v
        self.shell              : jobber.Jobber     = jobber.Jobber({
                                                        'verbosity' :   self.options.verbosity,
                                                        'noJobLogging': True
                                                        })

        self.l_runCMDresp       : list  = []

    def chrispl_onCUBEargs(self):
        '''
        Return a string specifying the CUBE instance
        '''
        return {
            'onCUBE':  json.dumps(self.env.CUBE.onCUBE())
        }

    def string_clean(self, str_string : str) -> str:
        """
        Clean/strip/whitespace in a string

        Args:
            str_string (str): string to clean

        Returns:
            str: cleaned up string
        """
        str_clean   = re.sub(r';\n.*--', ';--', str_string)
        str_clean   = str_clean.strip()
        return str_clean

    def chris_plugin_info_args(self, str_containerspec : str) -> dict:
        """
        Args needed to determine json rep for chris template style plugins.

        Args:
            str_containerspec (str): the name of the container

        Returns:
            dict: args to execute
        """
        self.env.INFO('Attempting chris_plugin_info call to find JSON representation...')
        str_args        : str = """
        run --rm %s chris_plugin_info
        """ % (str_containerspec)
        return {
            'args':     self.string_clean(str_args)
        }

    def chris_cookiecutter_info_args(self, str_containerspec : str) -> dict:
        """
        Args needed to determine json rep for cookiecutter style plugins.

        If the CLI options --pluginexec is empty, then this method will attempt
        to infer the exec name for the plugin based on its <str_containerspec>

        Args:
            str_containerspec (str): the name of the container

        Returns:
            dict: args to execute
        """
        self.env.INFO('Attempting cookiecutter call to find JSON representation...')
        str_pluginexec  : str   = self.env.options.pluginexec
        if not len(self.env.options.pluginexec):
            str_pluginexec = (str_containerspec.split('/')[-1]).split('-')[-1]
        str_args        : str   = """
        run --rm %s %s --json
        """ % (str_containerspec, str_pluginexec)
        return {
            'args'  : self.string_clean(str_args)
        }

    def plugin_execForJSON(self, func = None) -> dict:
        '''
        Return the CLI for determining the plugin JSON representation
        '''
        try:
            str_cmd = """docker %s""" % (
                func(self.options.dock_image)['args']
                )
        except:
            str_cmd = ""
        str_cmd = str_cmd.strip().replace('\n', '')
        return {
            'cmd' : str_cmd
        }

    def jsonScript_buildAndExec(self, argfunc) -> dict:
        """
        Build and execute a script to determine the JSON representation
        of a plugin. Various methods can be supported by appropriate
        calling of the argfunc.

        Args:
            argfunc (function): the name of the function that constructs
                                specific CLI to determine json representation

        Returns:
            dict: the result of executing the script
        """
        d_PLCmd             : dict  = self.plugin_execForJSON(argfunc)
        str_PLCmd           : str   = d_PLCmd['cmd']
        str_PLCmdfile       : str   = '%s/cmd.sh' % self.env.outputdir
        b_status            : bool  = False
        d_json              : dict  = {}

        with open(str_PLCmdfile, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(str_PLCmd)
        os.chmod(str_PLCmdfile, 0o755)
        d_runCMDresp        : dict  = self.shell.job_run(str_PLCmdfile)
        return d_runCMDresp

    def json_readFromFile(self) -> dict:
        """
        Read from a CLI specified JSON file and return contents, conforming
        to jsonScript_buildAndExec return

        Returns:
            dict: structure similar to jsonScript_buildAndExec
        """
        d_ret = {
            'stderr'        : 'no error',
            'stdout'        : '',
            'returncode'    : 0
        }
        self.env.INFO("Reading JSON representation from file %s..." % self.options.json)
        try:
            with open(self.env.options.json, 'r') as f:
                d_json  = json.load(f)
            d_ret['stdout']     = json.dumps(d_json, indent = 4)
        except:
            d_ret['stderr']     = 'An error in reading the file was raised'
            d_ret['returncode'] = 1
        return d_ret

    def __call__(self) ->dict:
        '''
        Entry point for determining plugin representation.

        If a json file to read has been specified in the CLI, then this file
        will be read and assumed to contain the JSON representation. If some
        execption occurs when reading this file, then the plugin image itself
        is used to determine (best case/guess) the plugin representation.

        The method attempts to construct two CLI strings to execute:
        * first, using the chris_plugin_info for template plugins
        * failing that, using the cookiecutter calling spec

        '''
        b_status        : bool  = False
        d_runCMDresp    : dict  = {'returncode' : 1}
        if len(self.env.options.json):
            d_runCMDresp        = self.json_readFromFile()
        if d_runCMDresp['returncode']:
            for argfunc in [self.chris_plugin_info_args, self.chris_cookiecutter_info_args]:
                d_runCMDresp    = self.jsonScript_buildAndExec(argfunc)
                if d_runCMDresp['returncode']:
                    self.env.ERROR('\n%s' % json.dumps(d_runCMDresp, indent = 4))
                else: break
        if not d_runCMDresp['returncode']:
            b_status            = True
            self.l_runCMDresp.append(d_runCMDresp)
            try:
                d_json          = json.loads(d_runCMDresp['stdout'])
            except:
                d_json          = {'error' : 'could not parse resultant stdout'}
        return {
            'status'            : b_status,
            'run'               : d_runCMDresp,
            'rep'               : d_json
        }

class Register:
    '''
    A class to connect to a CUBE and facilitate plugin registration
    '''

    def __init__(self, *args, **kwargs):
        self.env                : data.env          =  None
        self.options            : Namespace         = None

        for k, v in kwargs.items():
            if k == 'env'               : self.env                  = v
            if k == 'options'           : self.options              = v

        self.env.INFO("Connecting to CUBE and creating client object...")
        self.cl         : client.Client = client.Client(
                                            self.env.CUBE.url,
                                            self.env.CUBE.user,
                                            self.env.CUBE.password
                                        )
        # self.d_pipelines        : dict  = self.cl.get_pipelines()
        # self.pltopo             : int   = self.cl.get_plugins({'name': 'pl-topologicalcopy'})
        self.ld_workflowhist    : list  = []
        self.ld_topologicalNode : dict  = {'data': []}

    def register_do(self, d_jsonRep : dict) -> dict:
        """
        The actual registration logic

        Returns:
            dict: results from registration call.
        """
        self.env.INFO("Communicating with CUBE to register plugin...")
        try:
            d_response = self.cl.admin_upload_plugin(self.options.computenames, d_jsonRep)
            d_response['status']    = True
        except Exception as e:
            d_response = {
                'status'    : False,
                'message'   : 'an exception occurred',
                'exception' : str(e)
            }
        return d_response

    def __call__(self, d_jsonRep : dict) -> dict:
        """
        The main entry point to register a plugin. The JSON representation
        can be a "old" style description, i.e. that does not contain the
        'name', 'dock_image', and/or 'public_repo' or a new style that does.

        Regardless, in either case, if appropriate CLI flags have been called
        specifying these, then these are added to the representation.

        Args:
            d_jsonRep (dict): the meta plugin json description object

        Returns:
            dict: the registration return
        """

        def assign_if_defined(str_key : str, d_cli : dict, d_jrep : dict) -> dict:
            """
            If a <str_key> exists in the <d_cli> and has non-zero value length
            add to the <d_jrep> dictionary.

            Args:
                str_key (str): the key to examine existence/value length in <d_cli>
                d_cli (dict): a dictionary representation of the CLI options namespace
                d_jrep (dict): a json (plugin) representation to edit

            Returns:
                dict: a possibly updated d_jrep dictionary
            """
            if str_key in d_cli:
                if len(d_cli[str_key]):
                    d_jrep[str_key] = d_cli[str_key]
            return d_jrep

        if d_jsonRep['status']:
            d_cli   = vars(self.options)
            d_json  = d_jsonRep['rep']
            for f in ['name', 'public_repo', 'dock_image']:
                d_json = assign_if_defined(f, d_cli, d_json)

            d_register   : dict         = self.register_do(d_json)
        else:
            self.env.ERROR("Some error was returned when determining the plugin json representation!")
            self.env.ERROR('stdout: %s' % d_jsonRep['run']['stdout'])
            self.env.ERROR('stderr: %s' % d_jsonRep['run']['stderr'])
            self.env.ERROR('return: %s' % d_jsonRep['run']['returncode'])
            d_register = {
                'status'    : False,
                'message'   : 'a failure occured',
                'obj'       : d_jsonRep
            }

        return d_register

