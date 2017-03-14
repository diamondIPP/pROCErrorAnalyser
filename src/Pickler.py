#!/usr/bin/env python
# --------------------------------------------------------
#       Module to save and read files in pickle format
# created on March 7th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from os.path import join
from Utils import ensure_dir, log_warning
from pickle import dump, load


class Pickler(object):

    def __init__(self, analysis):

        self.Dir = join(analysis.ProgramDir, 'pickles')
        self.RunNumber = analysis.RunNumber if hasattr(analysis, 'RunNumber') else None
        ensure_dir(self.Dir)

        self.TestCampaign = ''
        self.Path = None

    def set_path(self, sub_dir, name=None, run='', ch=None, suf=None, camp=None):
        ensure_dir(join(self.Dir, sub_dir))
        name = name if name is not None else ''
        campaign = self.TestCampaign if camp is None else camp
        run = str(self.RunNumber).zfill(3) if self.RunNumber is not None else run
        ch = str(ch) if ch is not None else ''
        suf = str(suf) if suf is not None else ''
        tot_name = '_'.join([item for item in [name, campaign, run, ch, suf] if item])
        self.Path = join(self.Dir, sub_dir, '{n}.pickle'.format(n=tot_name))

    def get_path(self):
        if self.Path is None:
            log_warning('Set the path first!')
        return self.Path

    def run(self, function, value=None, params=None):
        if value is not None:
            f = open(self.get_path(), 'w')
            dump(value, f)
            f.close()
            return value
        try:
            f = open(self.get_path(), 'r')
            ret_val = load(f)
            f.close()
        except IOError:
            f = open(self.get_path(), 'w')
            ret_val = function() if params is None else function(params)
            dump(ret_val, f)
            f.close()
        return ret_val
