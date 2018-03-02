#!/usr/bin/env python3

"""
Update docker images and templated scripts in dune-xt-*

Usage:
  update.py [options] COMMIT_MSG

Arguments:
  COMMIT_MSG The commit message used for the submodules

Options:
   -h --help       Show this message.
   --nd            No docker image building.
   --nc            No committing changes.
   -v --verbose    Set logging level to debug.
"""

from docopt import docopt
from os import path
import importlib
import os
import stat
import contextlib
import jinja2
from string import Template as stringTemplate
import subprocess
import sys
import logging
import tempfile
import time
import six
import re
try:
    import docker
except ImportError:
    print('missing module: pip install docker')
    sys.exit(1)
from docker.utils.json_stream import json_stream

TAG_MATRIX = {'debian_gcc_full': {'cc': 'gcc', 'cxx': 'g++', 'deletes': "", 'base': 'debian'},
        'debian_clang_full': {'cc': 'clang', 'cxx': 'clang++', 'deletes':"", 'base': 'debian'},
        'arch_gcc_full': {'cc': 'gcc', 'cxx': 'g++', 'deletes': "", 'base': 'arch'},}


@contextlib.contextmanager
def remember_cwd(dirname):
    curdir = os.getcwd()
    try:
        os.chdir(dirname)
        yield curdir
    finally:
        os.chdir(curdir)


class Timer(object):
    def __init__(self, section, log):
        self._section = section
        self._start = 0
        self._log = log
        self.time_func = time.time

    def start(self):
        self.dt = -1
        self._start = self.time_func()

    def stop(self):
        self.dt = self.time_func() - self._start

    def __enter__(self):
        self.start()

    def __exit__(self, type_, value, traceback):
        self.stop()
        self._log('Execution of {} took {} (s)'.format(self._section, self.dt))


class CommitMessageMissing(RuntimeError): pass


def _docker_build(client, **kwargs):
    resp = client.api.build(**kwargs)
    if isinstance(resp, six.string_types):
        return client.images.get(resp)
    last_event = None
    image_id = None
    output = []
    for chunk in json_stream(resp):
        if 'error' in chunk:
            msg = chunk['error'] + '\n' + ''.join(output)
            raise docker.errors.BuildError(msg)
        if 'stream' in chunk:
            output.append(chunk['stream'])
            match = re.search(
                r'(^Successfully built |sha256:)([0-9a-f]+)$',
                chunk['stream']
            )
            if match:
                image_id = match.group(2)
        last_event = chunk
    if image_id:
        return client.images.get(image_id)
    raise docker.errors.BuildError(last_event or 'Unknown')


def _is_dirty(dirname):
    with remember_cwd(dirname):
        try:
            # make sure we're on a branch
            _ = subprocess.check_call(['git', 'symbolic-ref', 'HEAD'])
            # no changes to tracked files
            _ = subprocess.check_call(['git', 'diff-index', '--quiet', '--cached', 'HEAD'])
            # no untracked files
            _ = subprocess.check_call(['git', 'diff-files', '--quiet'])
            return False
        except subprocess.CalledProcessError as er:
            print(er)
            return True


def _cmd(cmd, logger):
    logger.debug(' '.join(cmd))
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        logger.debug(out)
    except subprocess.CalledProcessError as cp:
        logger.error(cp.output)
        logger.error('Failed: {}'.format(' '.join(cmd)))
        logger.error('Make sure the pushers group has write access to this repo on hub.cocker.com!')
        raise cp


def _commit(dirname, message):
    logger = logging.getLogger('{}'.format(os.path.basename(dirname)))
    logger.info('committing...')
    if not _is_dirty(dirname):
        return
    if not message or message == '':
        raise CommitMessageMissing(dirname)
    with remember_cwd(dirname):
        try:
            _ = subprocess.check_call(['git', 'add', '.travis.yml', '.travis.make_env_file.py',
                                       '.travis.after_script.bash', '.travis.script.bash',
                                       '.travis.test_python.bash'])
            _ = subprocess.check_call(['git', 'commit', '.travis.yml', '.travis.make_env_file.py',
                                       '.travis.after_script.bash', '.travis.script.bash',
                                       '.travis.test_python.bash',
                                       '-m', '{}'.format(message)])
        except subprocess.CalledProcessError as er:
            print(dirname)
            print(er)
            logger.error('committing... failed')


def _update_plain(scriptdir, tpl_file, module, outname):
    vars = importlib.import_module(module)
    tpl = jinja2.Template(open(path.join(scriptdir, tpl_file), 'rt').read())
    outfile = outname(module)
    vars.__dict__.update({'docker_tags': list(TAG_MATRIX.keys())})
    txt = tpl.render(project_name=module, slug='dune-community/{}'.format(module),
                    extra_deletes=[],
                    **vars.__dict__)
    open(outfile, 'wt').write(txt)
    if outfile.endswith('.bash'):
        os.chmod(outfile, stat.S_IXUSR | stat.S_IWUSR | stat.S_IREAD )


def _build_base(scriptdir, base, cc, cxx, commit, refname):
    client = docker.from_env(version='auto')
    slug_postfix = 'base_{}_{}'.format(base, cc)
    logger = logging.getLogger('{}'.format(slug_postfix))
    dockerdir = path.join(scriptdir, 'dune-xt-docker_base')
    dockerfile = path.join(dockerdir, 'Dockerfile')
    repo = 'dunecommunity/dune-xt-docker_{}'.format(slug_postfix)
    with Timer('docker build ', logger.info):
        buildargs = {'COMMIT': commit, 'CC': cc, 'CXX': cxx, 'BASE': base}
        img = _docker_build(client, rm=False, buildargs=buildargs,
                            tag='{}:{}'.format(repo, commit), path=dockerdir)
        img.tag(repo, refname)
    with Timer('docker push ', logger.info):
        client.images.push(repo)
    return img


def _build_combination(tag_matrix, dockerdir, module, commit, refname):
    client = docker.from_env(version='auto')
    imgs = []
    for tag, settings in tag_matrix.items():
        cc = settings['cc']
        cxx = settings['cxx']
        vars = importlib.import_module(module)
        tmp_dir = path.join(path.dirname(path.abspath(__file__)), module, tag)
        modules = settings['deletes']
        logger = logging.getLogger('{} - {}'.format(module, tag))
        modules_to_delete = '{} {}'.format(modules, vars.modules_to_delete)
        logger.debug('delete: ' + modules_to_delete)
        repo = 'dunecommunity/{}-testing_{}'.format(module, tag)

        with Timer('docker build ', logger.info):
            buildargs = {'COMMIT': commit, 'CC': cc, 'project_name': module,
                         'modules_to_delete': modules_to_delete, 'BASE': settings['base']}
            img = _docker_build(client, rm=False, buildargs=buildargs,
                    tag='{}:{}'.format(repo, commit), path=dockerdir)
            img.tag(repo, refname)
        with Timer('docker push ', logger.info):
            client.images.push(repo)
        imgs.append(img)
    return imgs


if __name__ == '__main__':
    arguments = docopt(__doc__)
    skip_docker = arguments['--nd']
    skip_commit = arguments['--nc']
    level = logging.DEBUG if arguments['--verbose'] else logging.INFO
    logging.basicConfig(level=level)
    scriptdir = path.dirname(path.abspath(__file__))
    superdir = path.join(scriptdir, '..', '..')
    message = arguments['COMMIT_MSG']
    names = ['common', 'functions', 'la', 'grid'] if 'TRAVIS_MODULE_NAME' not in os.environ else [os.environ['TRAVIS_MODULE_NAME']]

    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], universal_newlines=True).strip()
    commit = os.environ.get('CI_COMMIT_SHA', head)
    refname = os.environ.get('CI_COMMIT_REF_NAME', 'master').replace('/', '_')

    all_compilers = {(f['base'], f['cc'], f['cxx']) for f in TAG_MATRIX.values()}
    if not skip_docker:
        base_imgs = [_build_base(scriptdir, base, cc, cxx, commit, refname) for base, cc, cxx in all_compilers]
    else:
        base_imgs = []

    module_imgs = []
    for i in names:
        module = 'dune-xt-{}'.format(i)
        module_dir = os.path.join(superdir, module)

        if not skip_docker:
            module_imgs += _build_combination(tag_matrix=TAG_MATRIX,
                                              dockerdir=os.path.join(scriptdir, 'dune-xt-docker'),
                                              module=module,
                                              commit=commit, refname=refname)
        if _is_dirty(module_dir):
            print('Skipping {} because it is dirty or on a detached HEAD'.format(module))
            continue
        if 'TRAVIS' in os.environ.keys() or 'GITLAB' in os.environ.keys():
            logging.info('Skipping templates because we are on travis')
            continue
        for tpl, outname in (('travis.yml.in', lambda m: path.join(superdir, m, '.travis.yml')),
                            ('dune-xt-docker/after_script.bash.in', lambda m: path.join(superdir, m, '.travis.after_script.bash')),
                            ('dune-xt-docker/script.bash.in', lambda m: path.join(superdir, m, '.travis.script.bash')),
                            ('dune-xt-docker/test_python.bash.in', lambda m: path.join(superdir, m, '.travis.test_python.bash')),
                            ('dune-xt-docker/make_env_file.py', lambda m: path.join(superdir, m, '.travis.make_env_file.py'))):
            _update_plain(scriptdir, tpl, module, outname)

    for i in names:
        module = 'dune-xt-{}'.format(i)
        module_dir = os.path.join(superdir, module)
        if not skip_commit:
            _commit(module_dir, message)
    if skip_docker:
        sys.exit(0)
    client = docker.from_env(version='auto')

