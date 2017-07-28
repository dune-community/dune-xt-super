#!/usr/bin/env python3

from os import path
import importlib
import os
import stat
import contextlib
from string import Template
import subprocess
import sys
import logging
import tempfile
import time


@contextlib.contextmanager
def remember_cwd(dirname):
    curdir = os.getcwd()
    try:
        os.chdir(dirname)
        yield curdir
    finally:
        os.chdir(curdir)


@contextlib.contextmanager
def autoclear_dir(dirname):
    import shutil
    try:
        if path.isdir(dirname):
            shutil.rmtree(dirname)
        os.makedirs(dirname)
        yield
    except Exception as e:
        raise e
    else:
        shutil.rmtree(dirname)


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
    if not message:
        raise RuntimeError('empty commit message')
    with remember_cwd(dirname):
        try:
            _ = subprocess.check_call(['git', 'commit', '.travis.yml', '-m', '[travis] {}'.format(message)])
        except subprocess.CalledProcessError as er:
            print(dirname)
            print(er)


def _update_plain(scriptdir, tpl_file, module, outname):
    module_dir = os.path.join(superdir, module)
    vars = importlib.import_module(module)
    tpl = Template(open(path.join(scriptdir, tpl_file), 'rt').read())
    txt = tpl.safe_substitute(project_name=module, slug='dune-community/{}'.format(module),
                    authors=vars.authors, modules_to_delete=vars.modules_to_delete,
                    extra_deletes=[])
    outfile = outname(module)
    open(outfile, 'wt').write(txt)
    if outfile.endswith('.bash'):
        os.chmod(outfile, stat.S_IXUSR | stat.S_IWUSR | stat.S_IREAD )


def _update_docker(scriptdir, tpl_file, module, outname, branch='master'):
    tag_matrix = {'gcc_full': {'cc': 'gcc', 'cxx': 'g++', 'deletes':""},
        'gcc_no_istl_no_disc': {'cc': 'gcc', 'cxx': 'g++', 'deletes':"dune-fem dune-pdelab dune-functions dune-typetree dune-istl"},
        'gcc_no_disc': {'cc': 'gcc', 'cxx': 'g++', 'deletes':"dune-fem dune-pdelab"},
        'clang_full': {'cc': 'clang', 'cxx': 'clang++', 'deletes':""}}
    vars = importlib.import_module(module)
    tpl = Template(open(path.join(scriptdir, tpl_file), 'rt').read())
    for tag, settings in tag_matrix.items():
        cc = settings['cc']
        cxx = settings['cxx']
        modules = settings['deletes']
        logger = logging.getLogger('{} - {}'.format(module, tag))
        modules_to_delete = '{} {}'.format(modules, vars.modules_to_delete)
        logger.debug('delete: ' + modules_to_delete)
        tmp_dir = path.join(path.dirname(path.abspath(__file__)), module, tag)
        with autoclear_dir(tmp_dir):
            with remember_cwd(tmp_dir) as oldpwd:
                txt = tpl.safe_substitute(project_name=module, slug='dune-community/{}'.format(module),
                                authors=vars.authors, modules_to_delete=modules_to_delete,
                                branch=branch, cc=cc, cxx=cxx)
                outfile = outname(tmp_dir)
                open(outfile, 'wt').write(txt)
                branch = branch.replace('/', '_')
                docker_target = 'dunecommunity/{}-testing_{}:{}'.format(module, tag, branch)
                with Timer('docker build ' + docker_target, logger.info):
                    _cmd(['docker', 'build', '--rm=False', '-f', os.path.join(oldpwd, outfile),
                                    '-t', docker_target, tmp_dir], logger)
        with Timer('docker push ' + docker_target, logger.info):
            _cmd(['docker', 'push', docker_target], logger)


if __name__ == '__main__':
    level = logging.DEBUG if '-v' in sys.argv else logging.INFO
    logging.basicConfig(level=level)
    scriptdir = path.dirname(path.abspath(__file__))
    superdir = path.join(scriptdir, '..', '..')
    message = ' '.join(sys.argv[1:])
    names = ['common', 'functions', 'la', 'grid'] if 'TRAVIS_MODULE_NAME' not in os.environ else [os.environ['TRAVIS_MODULE_NAME']]

    for i in names:
        module = 'dune-xt-{}'.format(i)
        module_dir = os.path.join(superdir, module)
        branch = os.environ.get('TRAVIS_BRANCH', 'master')
        _update_docker(scriptdir, 'dune-xt-docker/Dockerfile.in', module,
                       lambda k: '{}/Dockerfile'.format(k),
                       branch=branch)
        if _is_dirty(module_dir):
            print('Skipping {} because it is dirty or on a detached HEAD'.format(module))
            continue
        if 'TRAVIS' in os.environ.keys() or 'GITLAB' in os.environ.keys():
            logging.info('Skipping templates because we are on travis')
            continue
        for tpl, outname in (('travis.yml.in', lambda m: path.join(superdir, m, '.travis.yml')),
                            ('dune-xt-docker/after_script.bash.in', lambda m: path.join(superdir, m, '.travis.after_script.bash')),
                            ('dune-xt-docker/script.bash.in', lambda m: path.join(superdir, m, '.travis.script.bash'))):
            _update_plain(scriptdir, tpl, module, outname)
        _commit(module_dir, message)



