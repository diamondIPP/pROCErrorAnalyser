#!/usr/bin/env python
# --------------------------------------------------------
#       Collection that holds several ErrorAnalyser instances
# created on March 1st 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ErrorAnalyser import ErrorAnalyser
from RootDraw import *
from Utils import print_banner
from collections import OrderedDict

class AnalysisCollection:

    def __init__(self):
        self.Runs = range(1, 7)
        self.Collection = self.load_collection()
        self.FirstAnalysis = self.Collection.values()[0]

        self.Draw = RootDraw(self)

    def load_collection(self):
        dic = OrderedDict()
        for run in self.Runs:
            dic[run] = ErrorAnalyser(run)
        return dic

    def get_hit_rates(self):
        return [col.get_hit_rate(False) for col in self.Collection.itervalues()]

    def draw_buffer_errors(self):
        errors = [col.calc_buffer_proportion(False) for col in self.Collection.itervalues()]
        gr = make_tgrapherrors('g_bc', 'Buffer Corruptions', x=self.get_hit_rates(), y=errors)
        format_histo(gr)
        self.Draw.draw_histo(gr, draw_opt='alp')

    def draw_run_info(self, canvas, show=True, x=1, y=1):
        return self.FirstAnalysis.draw_run_info(canvas=canvas, show=show, x=x, y=y, runs=self.Runs)

if __name__ == '__main__':
    # command line argument parsing

    # parser = ArgumentParser(prog='ErrorAnalyser')
    # parser.add_argument('run', nargs='?', help='run number', default=1, type=int)
    # args = parser.parse_args()

    print_banner('STARTING ERROR ANALYSER COLLECTION')

    # start command line
    z = AnalysisCollection()