#!/usr/bin/env python
# --------------------------------------------------------
#       Collection that holds several ErrorAnalyser instances
# created on March 1st 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ErrorAnalyser import ErrorAnalyser
from RunSelection import RunSelection
from RootDraw import *
from Utils import print_banner, log_critical, make_runplan_string
from collections import OrderedDict
from argparse import ArgumentParser


class AnalysisCollection:

    def __init__(self, selection):
        self.Runs = selection.get_selected_runs()
        self.RunPlan = selection.SelectedRunPlan
        self.Trim = selection.RunPlan[self.RunPlan]['trim']
        self.CTRLREG = selection.RunPlan[self.RunPlan]['ctrlreg']

        self.Collection = self.load_collection()
        self.FirstAnalysis = self.Collection.values()[0]

        self.SaveDir = make_runplan_string(self.RunPlan)
        self.Draw = RootDraw(self)

    def load_collection(self):
        dic = OrderedDict()
        for run in self.Runs:
            try:
                dic[run] = ErrorAnalyser(run)
            except IOError as err:
                log_warning(err)
        if not dic:
            log_critical('Empty collection')
        return dic

    def get_hit_rates(self):
        return [col.get_hit_rate(False) for col in self.Collection.itervalues()]

    def get_buffer_errors(self):
        return [col.calc_buffer_proportion(False) for col in self.Collection.itervalues()]

    def draw_buffer_errors(self, show=True):
        gr = make_tgrapherrors('g_bc', 'Buffer Corruptions', x=[r / 1e6 for r in self.get_hit_rates()], y=[e * 1e3 for e in self.get_buffer_errors()])
        format_histo(gr, x_tit='Hit Rate [MHz]', y_tit='Buffer Corruptions [per million]', y_off=1.5)
        self.Draw.draw_histo(gr, show=show, draw_opt='alp', lm=.13)
        return gr


    def draw_run_info(self, canvas, show=True, x=1, y=1):
        return self.FirstAnalysis.draw_run_info(canvas=canvas, show=show, x=x, y=y, runs=self.Runs)

if __name__ == '__main__':

    parser = ArgumentParser(prog='ErrorAnalysisCollection')
    parser.add_argument('plan', nargs='?', help='run plan', default=2)
    args = parser.parse_args()

    print_banner('STARTING ERROR ANALYSER COLLECTION')

    # start command line
    sel = RunSelection()
    sel.select_runs_from_runplan(args.plan)
    z = AnalysisCollection(sel)
