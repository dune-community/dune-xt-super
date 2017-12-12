#!/usr/bin/env python3

"""
Update docker images and templated scripts in dune-xt-*

Usage:
  run_travis_builders.py [options] MODULE

Arguments:
  MODULE one of la,functions,grid or common

Options:
   -h --help       Show this message.
   -v --verbose    Set logging level to debug.
   -t TAG --tag=TAG only test selected docker image tag, ex: clang_full
"""
import contextlib
import logging
import pprint
import subprocess
from tempfile import TemporaryDirectory, NamedTemporaryFile
from os import path, chdir, getcwd, makedirs
import update
from docopt import docopt

env_tpl = '''
TRAVIS_REPO_SLUG={}
TRAVIS_PULL_REQUEST="false"
TRAVIS_COMMIT={}
MY_MODULE={}
LOCAL_USER=r_milk01
LOCAL_UID=1000
LOCAL_GID=1000
'''

SCRIPTDIR = path.dirname(path.abspath(__file__))

@contextlib.contextmanager
def remember_cwd(dirname):
    curdir = getcwd()
    try:
        chdir(dirname)
        yield curdir
    finally:
        chdir(curdir)


def _cmd(cmd, logger):
    logger.debug(' '.join(cmd))
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
    logger.debug(out)


def _build_local(base, image, logger, module, commit):
    _cmd(['docker', 'pull', base], logger)
    slug = 'dune-community/{}'.format(module)
    dockerdir = path.join(SCRIPTDIR, 'docker')
    with open(path.join(dockerdir, 'env.sh'), 'wt') as envfile:
        envfile.write(env_tpl.format(slug, commit, module))
    with remember_cwd(dockerdir):
        cmd = ['docker', 'build', '--build-arg', 'BASE={}'.format(base), '-t', image, '.']
        _cmd(cmd, logger)


def _run_config(tag, superdir, module, module_dir, commit, logger):
    logdir = path.join(superdir, 'log', module)
    makedirs(logdir, exist_ok=True )
    logfile = path.join(logdir, '{}.log'.format(tag))

    baseimage = 'dunecommunity/{}-testing_{}:master'.format(module, tag)
    image = 'local/run_{}-testing_{}:master'.format(module, tag)
    _build_local(base=baseimage, image=image, logger=logger, module=module, commit=commit)

    cmd = ['docker', 'run', '-v', '{}:/root/src/{}'.format(module_dir, module),
           image, '/root/src/{}/.travis.script.bash'.format(module)]
    try:
        with open(logfile, 'wt') as log:
            log.write(' '.join(cmd))
            log.write('\n'+'-'*79)
            subprocess.check_call(cmd, stderr=log, stdout=log, universal_newlines=True)
    except subprocess.CalledProcessError as err:
        logging.error('Failed config: {}'.format(tag))
        logging.error(err)
    logger.info('Log at: xdg-open {}'.format(logfile))


def process_module(module, tags):
    level = logging.DEBUG if arguments['--verbose'] else logging.INFO
    logging.basicConfig(level=level)

    superdir = path.join(SCRIPTDIR, '..', '..')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    module_dir = path.join(superdir, module)
    for tag in tags:
        logger = logging.getLogger('{} - {}'.format(module, tag))
        logger.setLevel(level)
        with update.Timer('testing {} {}'.format(module, tag), logger.info):
            logger.info('Starting: {}'.format(module))
            _run_config(tag=tag, superdir=superdir, module=module, module_dir=module_dir,
                        commit=commit, logger=logger)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    module = 'dune-xt-{}'.format(arguments['MODULE'])
    if arguments['--tag']:
        tags = [arguments['--tag']]
    else:
        tags = update.TAG_MATRIX.keys()
    process_module(module, tags)