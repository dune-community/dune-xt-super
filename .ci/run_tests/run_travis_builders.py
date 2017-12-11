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
MY_MODULE=dune-gdt
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


def _build_local(base, image, logger):
    dockerdir = path.join(SCRIPTDIR, 'docker')
    with remember_cwd(dockerdir):
        cmd = ['docker', 'build', '--build-arg', 'BASE={}'.format(base), '-t', image, '.']
        _cmd(cmd, logger)


def _run_config(tag, superdir, module, clone_dir, commit, level=logging.DEBUG):
    logger = logging.getLogger(tag)
    myFormatter = logging.Formatter('{}: %(asctime)s - %(message)s'.format(tag))
    handler = logging.StreamHandler()
    handler.setFormatter(myFormatter)
    # logger.addHandler(handler)
    logger.setLevel(level)
    logdir = path.join(superdir, 'log', module)
    makedirs(logdir, exist_ok=True )
    logfile = path.join(logdir, '{}.log'.format(tag))

    with TemporaryDirectory(prefix='testing_{}'.format(module)) as tmp_dir:
        chdir(tmp_dir)
        _cmd(['git', 'clone', clone_dir, 'code'], logger)
        chdir(path.join(tmp_dir,'code'))
        _cmd(['git', 'checkout', commit], logger)
        _cmd(['git', 'submodule', 'update', '--init', '--recursive'], logger)
        baseimage = 'dunecommunity/{}-testing_{}:master'.format(module, tag)
        image = 'local/run_{}-testing_{}:master'.format(module, tag)
        _build_local(baseimage, image, logger)
        _cmd(['docker', 'pull', baseimage], logger)
        with NamedTemporaryFile('wt') as envfile:
            envfile.write(env_tpl.format(slug, commit))
            cmd = ['docker', 'run', '--env-file', envfile.name, '-v', '{}:/root/src/{}'.format(path.join(tmp_dir,'code'), module),
                   image, '/root/src/{}/.travis.script.bash'.format(module)]
            try:
                with open(logfile, 'wt') as log:
                    log.write(' '.join(cmd))
                    log.write('\n'+'-'*79)
                    log.flush()
                    out = subprocess.check_output(cmd, stderr=log, universal_newlines=True)
                    log.write(out)
            except subprocess.CalledProcessError as err:
                logging.error('Failed config: {}'.format(tag))
                logging.error(err)
                logging.error(err.output)
        logger.info('Log at: xdg-open {}'.format(logfile))


arguments = docopt(__doc__)
module = 'dune-xt-{}'.format(arguments['MODULE'])
slug = 'dune-community/{}'.format(module)
level = logging.DEBUG if arguments['--verbose'] else logging.INFO
logging.basicConfig(level=level)

superdir = path.join(SCRIPTDIR, '..', '..')
moduledir = path.join(superdir, module)
chdir(moduledir)
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
with TemporaryDirectory() as clone_tmp:
    clone_dir = path.join(clone_tmp, module)
    _cmd(['git', 'clone', 'https://github.com/{}.git'.format(slug), clone_dir], logging)
    for tag, settings in update.TAG_MATRIX.items():
        tmp_dir = path.join(path.dirname(path.abspath(__file__)), module, tag)
        modules = settings['deletes']
        logger = logging.getLogger('{} - {}'.format(module, tag))
        with update.Timer('testing {} {}'.format(module, tag), logger.info):
            _run_config(tag=tag, superdir=superdir, module=module, clone_dir=clone_dir, commit=commit, level=level)
