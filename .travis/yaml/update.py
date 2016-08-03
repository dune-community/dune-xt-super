#!/usr/bin/python3

from os import path
import importlib
from string import Template

scriptdir = path.dirname(path.abspath(__file__))
superdir = path.join(scriptdir, '..', '..')

tpl = Template(open(path.join(scriptdir, 'template.yml'), 'rt').read())

for i in ['common', 'functions', 'la', 'grid']:
    module = 'dune-xt-{}'.format(i)
    vars = importlib.import_module(module)
    outname = path.join(superdir, module, '.travis.yml')
    extra_deletes = '' if i == 'grid' or i == 'functions' else 'dune-grid'
    txt = tpl.safe_substitute(project_name=module, slug='dune-community/{}'.format(module),
                     authors=vars.authors, modules_to_delete=vars.modules_to_delete,
                     extra_deletes=extra_deletes, xt_suffix=i)
    open(outname, 'wt').write(txt)
