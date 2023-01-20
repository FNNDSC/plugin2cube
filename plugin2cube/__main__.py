#!/usr/bin/env python
import pudb

try:
    from    .                   import plugin2cube
except:
    from plugin2cube            import plugin2cube

from    pathlib                 import Path
from    argparse                import ArgumentParser,                  \
                                       Namespace,                       \
                                       ArgumentDefaultsHelpFormatter,   \
                                       RawTextHelpFormatter

from importlib.metadata import Distribution

__pkg       = Distribution.from_name(__package__)
__version__ = __pkg.version

import  os, sys, json
import  pudb
from    pudb.remote             import set_trace
from    state                   import data

Env             = data.env()

DISPLAY_TITLE = r"""
       _             _        _____            _
      | |           (_)      / __  \          | |
 _ __ | |_   _  __ _ _ _ __  `' / /' ___ _   _| |__   ___
| '_ \| | | | |/ _` | | '_ \   / /  / __| | | | '_ \ / _ \
| |_) | | |_| | (_| | | | | |./ /__| (__| |_| | |_) |  __/
| .__/|_|\__,_|\__, |_|_| |_|\_____/\___|\__,_|_.__/ \___|
| |             __/ |
|_|            |___/
"""

str_desc                =  DISPLAY_TITLE + """

                        -- version """ + __version__ + """ --

                Register a plugin to a CUBE instance.

    This app is a straightforward CLI tool that can be used to
    register a plugin directly to a CUBE instance using the the
    CUBE API directly. This approach bypasses the historic need
    to use a ChRIS Store as an intermediary. Besides being a
    logically much simpler mechanism for registering plugins to
    a CUBE, it also allows for considerable portability of control
    in plugin management.

    Note that an FNNDSC-specific (but not-easily-generalizable)
    solution using fnndsc_chrisomatic is also available, and is
    discussed elsewhere.

"""

package_CLIself         = """
        --dock_image <container_name>                                           \\
        [--name <pluginNameInCUBE>]                                             \\
        [--public_repo <repo_name>]                                             \\
        [--public_repobase <basename>]                                          \\
        [--pluginexec <exec>]                                                   \\
        [--computenames <commalist,of,envs>]                                    \\
        [--CUBEurl <CUBEURL>]                                                   \\
        [--CUBEuser <user>]                                                     \\
        [--CUBEpasswd <password>]                                               \\
        [--jsonFile <jsonRepFile>]                                              \\
        [--inputdir <inputdir>]                                                 \\
        [--outputdir <outputdir>]                                               \\
        [--man]                                                                 \\
        [--verbosity <level>]                                                   \\
        [--debug]                                                               \\
        [--debugTermsize <cols,rows>]                                           \\
        [--debugHost <0.0.0.0>]                                                 \\
        [--debugPort <7900>]"""

package_CLIsynpsisArgs = """
    ARGUMENTS

        --dock_image <container_name>
        The name of the plugin container image. This is typically something like

                                fnndsc/pl-someAnalysis
                                       -- or --
                            localhost/fnndsc/pl-someAnalysis

        and is a REQUIRED parameter.

        [--name <pluginNameInCUBE>]
        The name of the plugin within CUBE. Typically something like
        "pl-someAnalysis". If not supplied, name will be inferred from
        the <container_name>, by stripping and leading prefices and trailing
        versioning.

        [--public_repobase <basename>]
        The base URL of the plugin code, typically on github. If not specified,
        is assumed to be

                    https://github.com/FNNDSC

        [--public_repo <repo_name>]
        The URL of the plugin code, typically on github. This is accessed to
        find a README.[rst|md] which is used by the ChRIS UI when providing
        plugin details. If not supplied, the repo will be assumed to be

                    <public_repobase>/<pluginNameInCUBE>

        [--pluginexec <exec>]
        The name of the actual plugin executable within the image if this
        executable does not conform to standard conventions.

        [--computenames <commalist,of,envs>] ("host")
        A comma separted list of compute environments within a CUBE to which
        the plugin can be registered.

        [--CUBEurl <CUBEURL>] ("http://localhost:8000/api/v1/")
        The URL of the CUBE to manage.

        [--CUBEuser <user>] ("chris")
        The name of the administration CUBE user.

        [--CUBEpasswd <password>] ("chris1234")
        The admin password.

        [--jsonFile <jsonRepFile>]
        If provided, read the representation from <jsonRepFile> and do not
        attempt to run the plugin with docker.

        [--inputdir <inputdir>]
        An optional input directory specifier.

        [--outputdir <outputdir>]
        An optional output directory specifier. Some files are typically created
        and executed from the <outputdir>.

        [--man]
        If specified, show this help page and quit.

        [--verbosity <level>]
        Set the verbosity level. The app is currently chatty at level 0 and level 1
        provides even more information.

        [--debug]
        If specified, toggle internal debugging. This will break at any breakpoints
        specified with 'Env.set_trace()'

        [--debugTermsize <253,62>]
        Debugging is via telnet session. This specifies the <cols>,<rows> size of
        the terminal.

        [--debugHost <0.0.0.0>]
        Debugging is via telnet session. This specifies the host to which to connect.

        [--debugPort <7900>]
        Debugging is via telnet session. This specifies the port on which the telnet
        session is listening.
"""

package_CLIexample = """
    BRIEF EXAMPLE

        plugin2cube                                                             \\
            --computenames host,galena                                          \\
            --name pl-volseg                                                    \\
            --dock_image fnndc/pl-volseg                                        \\
            --public_repo https://github.com/FNNDSC/pl-volseg                   \\
            --CUBEurl http:localhost:8000/api/v1/                               \\
            --CUBEuser chrisadmin                                               \\
            --CUBEpasswd something1234

"""

def synopsis(ab_shortOnly = False):
    scriptName = os.path.basename(sys.argv[0])
    shortSynopsis =  '''
    NAME

        plugin2cube

    SYNOPSIS

        plugin2cube                                                             \ '''\
        + package_CLIself + '''

    '''

    description = '''
    DESCRIPTION

        `plugin2cube` is a simple app that allows for the registration of a
        plugin image directly to a CUBE instance without the need of a ChRIS
        Store as intermediary. This allows for simpler, more portable manage-
        ment of plugins in a given CUBE.

        The script does need to determine the plugin JSON representation.
        There are two broad mechanisms for resolving this. The first is to
        simply read this representation from a file. The second is to actually
        _run_ the plugin image to determine the representation.

        Running the image does require `docker` to be present on the host
        executing this script. Two assumptions are made in this case:

            1. The plugin has been created using the `chris_plugin_template`
               in which case the `chris_plugin_info` mechanism is used to
               determine the JSON representation. This is attempted, and if
               successful, the representation is used.
            2. Failing that, the plugin is assumed to be created using the
               cookiecutter mechanism (or similar) and that the plugin code
               supports the `--json` flag to describe its representation. In
               this case, the script, if not explicitly told what the actual
               plugin executable within the image (from --pluginexec) is, will
               assume that the executable can be found from the docker image
               name as

                            <prefix>/<prefix>/.../pl-<pluginexec>

    ''' + package_CLIsynpsisArgs + package_CLIexample
    if ab_shortOnly:
        return shortSynopsis
    else:
        return shortSynopsis + description

parser                  = ArgumentParser(
    description         = '''
A CLI app to upload a plugin to a CUBE instance.
''',
    formatter_class     = RawTextHelpFormatter
)


parser.add_argument(
            '--version',
            default = False,
            dest    = 'b_version',
            action  = 'store_true',
            help    = 'print version info'
)
parser.add_argument(
            '--man',
            default = False,
            action  = 'store_true',
            help    = 'show a man page'
)
parser.add_argument(
            '--osenv',
            default = False,
            action  = 'store_true',
            help    = 'show the base os environment'
)
parser.add_argument(
            '--synopsis',
            default = False,
            action  = 'store_true',
            help    = 'show a synopsis'
)
parser.add_argument(
            '--inputdir',
            default = './',
            help    = 'optional directory specifying extra input-relative data'
)
parser.add_argument(
            '--outputdir',
            default = './',
            help    = 'optional directory specifying location of any output data'
)
parser.add_argument(
            '--computenames',
            default = 'host',
            help    = 'comma separated list of compute environments against which to register the plugin'
)
parser.add_argument(
            '--dock_image',
            default = '',
            help    = 'name of the docker container'
)
parser.add_argument(
            '--name',
            default = '',
            help    = 'plugin name within CUBE'
)
parser.add_argument(
            '--public_repo',
            default = '',
            help    = 'repo hosting the container image'
)
parser.add_argument(
            '--public_repobase',
            default = 'https://github.com/FNNDSC',
            help    = 'a default base public repo'
)
parser.add_argument(
            '--pluginexec',
            default = '',
            help    = 'plugin executable name for cookiecutter style pluginsp'
)
parser.add_argument(
            '--jsonFile',
            default = '',
            help    = 'plugin JSON representation file'
)
parser.add_argument(
            '--CUBEurl',
            default = 'http://localhost:8000/api/v1/',
            help    = 'CUBE URL'
)
parser.add_argument(
            '--CUBEuser',
            default = 'chirs',
            help    = 'CUBE username'
)
parser.add_argument(
            '--CUBEpasswd',
            default = 'chris1234',
            help    = 'CUBE password'
)
parser.add_argument(
            '--verbosity',
            default = '0',
            help    = 'verbosity level of app'
)
parser.add_argument(
            "--debug",
            help    = "if true, toggle telnet pudb debugging",
            dest    = 'debug',
            action  = 'store_true',
            default = False
)
parser.add_argument(
            "--debugTermSize",
            help    = "the terminal 'cols,rows' size for debugging",
            default = '253,62'
)
parser.add_argument(
            "--debugPort",
            help    = "the debugging telnet port",
            default = '7900'
)
parser.add_argument(
            "--debugHost",
            help    = "the debugging telnet host",
            default = '0.0.0.0'
)

def Env_setup(options: Namespace):
    """
    Setup the environment

    Args:
        options (Namespace):    options passed from the CLI caller
    """
    global Env
    status  : bool          = True
    options.inputdir        = Path(options.inputdir)
    options.outputdir       = Path(options.outputdir)
    Env.inputdir            = options.inputdir
    Env.outputdir           = options.outputdir
    Env.CUBE.url            = str(options.CUBEurl)
    Env.CUBE.user           = str(options.CUBEuser)
    Env.CUBE.password       = str(options.CUBEpasswd)
    Env.debug_setup(
                debug       = options.debug,
                termsize    = options.debugTermSize,
                port        = options.debugPort,
                host        = options.debugHost
    )
    if not len(options.dock_image):
        Env.ERROR("The '--dock_image <value>' CLI MUST be specified!")
        status              = False
    return status

def earlyExit_check(args) -> int:
    """
    Perform some preliminary checks

    If version or synospis are requested, print these and return
    code for early exit.
    """
    if args.man or args.synopsis:
        print(str_desc)
        if args.man:
            str_help     = synopsis(False)
        else:
            str_help     = synopsis(True)
        print(str_help)
        return 1
    if args.b_version:
        print("Name:    %s\nVersion: %s" % (__pkg.name, __version__))
        return 1
    return 0

def main(args=None):
    """
    Main method for the programmatical calling of the plugin2cube
    module
    """
    global Env
    Env.version         = plugin2cube.__version__

    options             = parser.parse_args()
    retcode     : int   = 1
    if earlyExit_check(options): return 1

    # set_trace(term_size=(253, 62), host = '0.0.0.0', port = 7900)

    Env.options     = options
    if Env_setup(options):
        Env.set_telnet_trace_if_specified()
        if int(options.verbosity) > 1: print(DISPLAY_TITLE)
        d_register  = plugin2cube.plugin2cube(options = options, env = Env).run()
        if d_register['status']:    retcode = 0

    Env.INFO("terminating with code %d..." % retcode, level = 2)
    return retcode

if __name__ == '__main__':
    sys.exit(main(args))
