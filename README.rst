plugin2cube
===========

|Version| |MIT License| |ci|

Abstract
--------

Small utility app that “registers” a ChRIS plugin to a CUBE instance
from the CLI. As of January 2023, CUBE no longer needs a companion store
for plugin registration. It is now possible to register a plugin
directly to CUBE itself using updates to the CUBE API. This utility
script leverages this API to allow for direct registration of plugins.

Overview
--------

``plugin2cube`` is a simple app that allows for the registration of a
plugin image directly to a CUBE instance without the need of a ChRIS
Store as intermediary. This allows for simpler, more portable management
of plugins in a given CUBE.

The script does need to determine the plugin JSON representation. There
are two broad mechanisms for resolving this. The first is to simply read
this representation from a file. The second is to actually *run* the
plugin image to determine the representation.

Running the image does require ``docker`` to be present on the host
executing this script. Two assumptions are made in this case:

-  The plugin has been created using the ``chris_plugin_template`` in
   which case the ``chris_plugin_info`` mechanism is used to determine
   the JSON representation. This is attempted, and if successful, the
   representation is used.
-  Failing that, the plugin is assumed to be created using the
   cookiecutter mechanism (or similar) and that the plugin code supports
   the ``--json`` flag to describe its representation. In this case, the
   script, if not explicitly told what the actual plugin executable
   within the image (from –pluginexec) is, will assume that the
   executable can be found from the docker image name
   ``<prefix>/<prefix>/.../pl-<pluginexec>``

Arguments
---------

.. code:: html

           --dock_image <container_name>
           The name of the plugin container image. This is typically something like

                                   fnndsc/pl-someAnalysis
           or
                               localhost/fnndsc/pl-someAnalysis

           --name <pluginNameInCUBE>
           The name of the plugin within CUBE. Typically something like
           "pl-someAnalysis".

           --public_repo <repo_name>
           The URL of the plugin code, typically on github. This is accessed to
           find a README.[rst|md] which is used by the ChRIS UI when providing
           plugin details.

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

           [--json <jsonRepFile>]
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

Installation
------------

Easiest vector for installation is

.. code:: bash

   pip install plugin2cube

Examples
--------

``plugin2cube`` accepts several CLI flags/arguments that together
specify the CUBE instance, the plugin JSON description, as well as
additional parameters needed for registration. For a full list of
supported arguments, do

.. code:: shell

   plugin2cube --man

To register a plugin, do

.. code:: shell

   # Simplest way -- json representation is determined by running the container
   # This requires of course that the machine running this script has docker installed!
   plugin2cube --CUBEurl http://localhost:8000/api/v1/ --CUBEuser chris --CUBEpassword chris1234 \
               --dock_image local/pl-imageProc                         \
               --name pl-imageProc                                     \
               --public_repo https://github.com/FNNDSC/pl-imageProc

Development
-----------

Instructions for developers.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To debug, the simplest mechanism is to trigger the internal remote
telnet session with the ``--debug`` CLI. Then, in the code, simply add
``Env.set_trace()`` calls where appropriate. These can remain in the
codebase (i.e. you don’t need to delete/comment them out) since they are
only *live* when a ``--debug`` flag is passed.

Testing
~~~~~~~

Run unit tests using ``pytest``. Coming soon!

*-30-*

.. |Version| image:: https://img.shields.io/docker/v/fnndsc/pl-plugin2cube?sort=semver
   :target: https://hub.docker.com/r/fnndsc/pl-plugin2cube
.. |MIT License| image:: https://img.shields.io/github/license/fnndsc/pl-plugin2cube
   :target: https://github.com/FNNDSC/pl-plugin2cube/blob/main/LICENSE
.. |ci| image:: https://github.com/FNNDSC/pl-plugin2cube/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/FNNDSC/pl-plugin2cube/actions/workflows/ci.yml
