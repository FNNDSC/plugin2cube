str_about = '''
    Module that provides the several "action" abstracted classes --

    Essentially this provides a base class for CLI operations that
    sets up a jobber object, as well some derived classes that are
    used to run specific CLI apps as well as some API calling in
    the larger context of CUBE/ChRIS
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


pluginexec          = lambda s: ((s.split('/')[-1]).split('-')[-1]).split(':')[0]
pluginname          = lambda s: ((s.split('/')[-1])).split(':')[0]
public_repo         = lambda u, s: '%s/%s' % (u, pluginname(s))

class Shexec:
    '''
    A thin base class providing the chassis for executing sh-based apps.
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
                                                        'verbosity' :   0,
                                                        'noJobLogging': True
                                                        })

        self.l_runCMDresp       : list  = []

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

    def cmd_checkResponse(self, d_resp : dict) -> bool:
        """
        Check the d_resp from a jobber call,
        log a response, and return True/False

        Args:
            d_resp (dict): a response object from a jobber call

        Returns:
            bool: True/False pending d_resp
        """
        b_OK    : bool  = False
        if not d_resp.get('returncode'):
            self.env.INFO("\t<green>OK!</green>")
            self.env.INFO("\n%s" % json.dumps(d_resp, indent = 4), level = 2)
            b_OK        = True
        else:
            self.env.ERROR("\tFailed!", level = 1)
            self.env.ERROR("\n%s" % json.dumps(d_resp, indent = 4), level = 2)
            b_OK        = False
        return b_OK

    def __call__(self) ->dict:
        '''
        Base entry point
        '''
        b_status        : bool  = False
        d_runCMDresp    : dict  = {'returncode' : 1}
        d_json          : dict  = {'nop' : 'dummy return'}
        return {
            'status'            : b_status,
            'run'               : d_runCMDresp,
            'detail'            : d_json
        }

class PluginRep(Shexec):
    '''
    A specialization of Shexec that runs a container image to determine its
    json description
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def chrispl_onCUBEargs(self):
        '''
        Return a string specifying the CUBE instance
        '''
        return {
            'onCUBE':  json.dumps(self.env.CUBE.onCUBE())
        }

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

    def containerspec_parse(self, str_containerspec : str, **kwargs) -> str:
        """
        Given a containerspec of pattern

            <prefix>/<prefix>/.../[intro]-<name>[:version]

        return various parsed elements, based on `kwargs` "return = <choice>"
        where <choice> is:

                pluginexec
                pluginname
                public_repo

        Args:
            str_containerspec (str): the container string name

        Returns:
            str: a parsed string such as the pluginexec name or the pluginfullname
        """
        str_result  : str   = ""
        str_parse   : str   = 'pluginexec'
        for k,v in kwargs.items():
            if k == 'find'      : str_parse     = v
        if 'exec' in str_parse.lower():
            str_result  = pluginexec(str_containerspec)
        if 'name' in str_parse.lower():
            str_result  = pluginname(str_containerspec)
        if 'repo' in str_parse.lower():
            str_result  = public_repo(self.env.options.public_repobase, str_containerspec)
        return str_result

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
            str_pluginexec = self.containerspec_parse(str_containerspec, find = 'pluginexec')
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

    def docker_pull(self) -> dict:
        """
        Pull the container image.

        Returns:
            dict: results from jobber call
        """
        str_cmd         : str   = "docker pull %s" % self.options.dock_image
        d_dockerpull    : dict  = self.shell.job_run(str_cmd)
        self.env.INFO("\t$> %s" % str_cmd)
        return d_dockerpull

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

        self.env.INFO("\t$> %s" % str_PLCmd)
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
        self.env.INFO("Reading JSON representation from file '%s'..." % self.options.jsonFile)
        try:
            with open(self.env.options.json, 'r') as f:
                d_json  = json.load(f)
            d_ret['stdout']     = json.dumps(d_json, indent = 4)
        except:
            d_ret['stderr']     = "An error in reading the file '%s' was raised" % self.options.jsonFile
            d_ret['returncode'] = 1
        self.cmd_checkResponse(d_ret)
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

        def docker_pullIfNeeded() -> bool:
            """
            Pull the docker image -- this is needed only if we are not
            reading the representation from file.

            Returns:
                bool: True/False pending pull success/fail
            """
            b_pullOK        : bool  = True
            d_dockerPull    : dict  = {
                "message"   : "no pull needed since user specified readFromJSONFile"
            }
            if not len(self.options.jsonFile):
                d_dockerPull    = self.docker_pull()
                b_pullOK        = self.cmd_checkResponse(d_dockerPull)
            return d_dockerPull, b_pullOK

        def jsonRepFromImage_get() -> dict:
            for argfunc in [self.chris_plugin_info_args, self.chris_cookiecutter_info_args]:
                d_runCMDresp    = self.jsonScript_buildAndExec(argfunc)
                if self.cmd_checkResponse(d_runCMDresp): break

            return d_runCMDresp

        def jsonRep_get() -> dict:
            b_jsonOK         : bool = False
            if len(self.env.options.jsonFile):
                d_runCMDresp        = self.json_readFromFile()
            else:
                d_runCMDresp        = jsonRepFromImage_get()
            if not d_runCMDresp['returncode']:
                b_jsonOK    = True
            else:
                b_jsonOK    = False
            return d_runCMDresp, b_jsonOK

        b_status        : bool  = False
        b_pullOK        : bool  = False
        b_jsonOK        : bool  = False
        d_runCMDresp    : dict  = {'returncode' : 1}
        d_json          : dict  = {'error' : 'could not pull image'}

        d_runCMDresp, b_pullOK  = docker_pullIfNeeded()
        if b_pullOK:
            d_runCMDresp, b_jsonOK  = jsonRep_get()
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

class CHRS(Shexec):
    '''
    A specialization of Shexec that runs CHRS
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def login(self) -> dict:
        """
        Log in to CUBE via `chrs`.

        Returns:
            dict: results from login call.
        """
        str_cmd         : str   = self.string_clean("""
        chrs login --address %s --username %s --password %s
        """ % (
                self.options.CUBEurl,
                self.options.CUBEuser,
                self.options.CUBEpasswd
        ))
        d_login         : dict  = self.shell.job_run(str_cmd)
        self.env.INFO("\t$> %s" % str_cmd)
        return d_login

    def pipeline_add(self, str_filename : str) -> dict:
        """
        Add a pipeline file

        Args:
            str_filename (str): name of the pipeline file

        Returns:
            dict: results from pipeline addition
        """
        str_cmd         : str   = self.string_clean("""
        chrs pipeline-file add %s
        """ % (str_filename))
        d_pipeline_add  : dict  = self.shell.job_run(str_cmd)
        self.env.INFO("\t$> %s" % str_cmd)
        return d_pipeline_add

    def chrispl_onCUBEargs(self):
        '''
        Return a string specifying the CUBE instance
        '''
        return {
            'onCUBE':  json.dumps(self.env.CUBE.onCUBE())
        }

    def __call__(self) ->dict:
        '''
        Entry point for adding pipelines and additionally registering
        any plugin dependencies.

        '''
        b_status        : bool  = False
        d_runCMDresp    : dict  = {'returncode' : 1}
        d_json          : dict  = {'error' : 'all attempts to add pipeline failed'}

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


class Register(Shexec):
    '''
    A class to connect to a CUBE and facilitate plugin registration
    '''

    def __init__(self, *args, **kwargs):
        self.env                : data.env          =  None
        self.options            : Namespace         = None

        for k, v in kwargs.items():
            if k == 'env'               : self.env                  = v
            if k == 'options'           : self.options              = v

        self.env.INFO("Connecting to CUBE and creating client object...", level =2)
        self.cl         : client.Client = client.Client(
                                            self.env.CUBE.url,
                                            self.env.CUBE.user,
                                            self.env.CUBE.password
                                        )
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
            d_apicall   = self.cl.admin_upload_plugin(self.options.computenames, d_jsonRep)
            d_response  = {
                'status'        : True,
                'stdout'        : d_apicall,
                'stderr'        : '',
                'returncode'    : 0
            }
        except Exception as e:
            d_response  = {
                'status'        : False,
                'stdout'        : 'an exception occurred',
                'stderr'        : str(e),
                'returncode'    : 1
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
            b_status    = False
            if not len(d_cli['dock_image']):
                self.env.ERROR('The parameter "--dock_image" must be set and have non-zero length!')
            if str_key in d_cli:
                b_status = True
                if len(d_cli[str_key]):
                    d_jrep[str_key] = d_cli[str_key]
                else:
                    if str_key == 'name': d_jrep[str_key] = pluginname(d_cli['dock_image'])
                    if str_key == 'public_repo' : d_jrep[str_key] = \
                        public_repo(d_cli['public_repobase'],
                                    d_cli['dock_image'])
            return d_jrep, b_status

        d_register  : dict  = {
            'status'    : False,
            'obj'       : {
                'run'   : {
                    'stderr'    : ""
                }
            }
        }
        b_statusAND : bool  = True
        b_status    : bool  = False
        if d_jsonRep['status']:
            d_cli   = vars(self.options)
            d_json  = d_jsonRep['rep']
            for f in ['dock_image', 'name', 'public_repo']:
                d_json, status = assign_if_defined(f, d_cli, d_json)
                b_statusAND &= status
            if not b_statusAND:
                d_register['obj']['run']['stderr']  = 'A required CLI parameter is missing!'
            else:
                d_register['obj']['run']            = self.register_do(d_json)
                self.cmd_checkResponse(d_register['obj']['run'])
        else:
            d_register = {
                'status'    : b_status,
                'message'   : 'a failure occured',
                'obj'       : d_jsonRep
            }
        if d_register['obj']['run'].get('status'):
            d_register['status']    = d_register['obj']['run'].get('status')

        return d_register

