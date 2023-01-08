# plugin2cube

[![Version](https://img.shields.io/docker/v/fnndsc/pl-plugin2cube?sort=semver)](https://hub.docker.com/r/fnndsc/pl-plugin2cube)
[![MIT License](https://img.shields.io/github/license/fnndsc/pl-plugin2cube)](https://github.com/FNNDSC/pl-plugin2cube/blob/main/LICENSE)
[![ci](https://github.com/FNNDSC/pl-plugin2cube/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/pl-plugin2cube/actions/workflows/ci.yml)

## Abstract

Small utility app that "registers" a ChRIS plugin to a CUBE instance from the CLI.

## Installation

Easiest vector for installation is

```bash
pypi install plugin2cube
```

## Examples

`plugin2cube` accepts several CLI flags/arguments that together specify the CUBE instance, the plugin JSON description, as well as additional parameters needed for registration.

```shell
plugin2cube --CUBEurl http://localhost:8000/api/v1/ --CUBEuser chris --CUBEpassword chris1234 \
            --dock_name pl-plugin \
            --name pl-imageProc   \
            --json $(docker run --rm
            fnndsc/pl-imageProx chris_plugin_info)
```

## Development

Instructions for developers.

### Building

Build a local container image:

```shell
docker build -t local/plugin2cube .
```

### Running

Mount the source code `plugin2cube.py` into a container to try out changes without rebuild.

```shell
docker run --rm -it --userns=host  \
    -v $PWD/plugin2ccube.py:/usr/local/lib/python3.11/site-packages/plugin2cube.py:ro \
    -v $PWD/control:/usr/local/lib/python3.11/site-packages/control:ro \
    -v $PWD/logic:/usr/local/lib/python3.11/site-packages/logic:ro \
    -v $PWD/state:/usr/local/lib/python3.11/site-packages/state:ro \
    -v $PWD/in:/incoming:ro -v $PWD/out:/outgoing:rw -w /outgoing \
    local/plugin2cube plugin2cube --man
```

### Testing

Run unit tests using `pytest`.
It's recommended to rebuild the image to ensure that sources are up-to-date.
Use the option `--build-arg extras_require=dev` to install extra dependencies for testing.

```shell
docker build -t localhost/fnndsc/pl-plugin2cube:dev --build-arg extras_require=dev .
docker run --rm -it localhost/fnndsc/pl-plugin2cube:dev pytest
```

## Release

Steps for release can be automated by [Github Actions](.github/workflows/ci.yml).
This section is about how to do those steps manually.

### Increase Version Number

Increase the version number in `setup.py` and commit this file.

### Push Container Image

Build and push an image tagged by the version. For example, for version `1.2.3`:

```
docker build -t docker.io/fnndsc/pl-plugin2cube:1.2.3 .
docker push docker.io/fnndsc/pl-plugin2cube:1.2.3
```

