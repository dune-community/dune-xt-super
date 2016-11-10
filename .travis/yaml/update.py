#!/usr/bin/python3

from os import path
import importlib
import os
import contextlib
from string import Template
import subprocess
import sys

@contextlib.contextmanager
def remember_cwd(dirname):
    curdir = os.getcwd()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)


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

def _commit(dirname, message):
    with remember_cwd(dirname):
        try:
            _ = subprocess.check_call(['git', 'commit', '.travis.yml', '-m', '[travis] {}'.format(message)])
            _ = subprocess.check_call(['git', 'push'])
        except subprocess.CalledProcessError as er:
            print(dirname)
            print(er)

scriptdir = path.dirname(path.abspath(__file__))
superdir = path.join(scriptdir, '..', '..')
tpl = Template(open(path.join(scriptdir, 'template.yml'), 'rt').read())
message = ' '.join(sys.argv[1:])

for i in ['common', 'functions', 'la', 'grid']:
    module = 'dune-xt-{}'.format(i)
    module_dir = os.path.join(superdir, module)
    if _is_dirty(module_dir):
        print('Skipping {} because it is dirty'.format(module))
        continue
    vars = importlib.import_module(module)
    outname = path.join(module_dir, '.travis.yml')
    extra_deletes = '' if i == 'grid' or i == 'functions' else 'dune-grid'
    txt = tpl.safe_substitute(project_name=module, slug='dune-community/{}'.format(module),
                     authors=vars.authors, modules_to_delete=vars.modules_to_delete,
                     extra_deletes=extra_deletes, xt_suffix=i)
    open(outname, 'wt').write(txt)
    _commit(module_dir, message)
