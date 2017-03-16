#!/usr/bin/env python
# --------------------------------------------------------
#       Class to analyse several analysis collections
# created on March 15th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from collections import OrderedDict
from AnalysisCollection import AnalysisCollection
from Utils import log_critical, print_banner
from argparse import ArgumentParser
from json import loads
from RootDraw import *
from RunSelection import RunSelection


class PlanCollection(object):

    def __init__(self, runplans):
        self.RunPlans = runplans
        self.Collection = self.load_collection()
        self.FirstAnalysis = self.Collection.values()[0].FirstAnalysis

        self.Draw = RootDraw(self)

    def load_collection(self):
        dic = OrderedDict()
        for plan in self.RunPlans:
            try:
                sel = RunSelection()
                sel.select_runs_from_runplan(plan)
                dic[plan] = AnalysisCollection(sel)
            except IOError as err:
                log_warning(err)
        if not dic:
            log_critical('Empty collection')
        return dic

    def draw_buffer_corruptions(self, show=True):
        mg = make_tmultigraph('mg_be', 'Buffer Corruptions')
        leg = self.Draw.make_legend(nentries=len(self.Collection), x1=.15, x2=.5)
        for plan, col in self.Collection.iteritems():
            gr = col.draw_buffer_errors(show=False)
            format_histo(gr, color=self.Draw.get_color())
            mg.Add(gr, 'pl')
            leg.AddEntry(gr, 'Trim: {t}, ctrlreg: {c}'.format(t=col.Trim, c=col.CTRLREG), 'pl')
        format_histo(mg, x_tit='Hit Rate [MHz]', y_tit='Buffer Corruptions [per million]', y_off=1.5, draw_first=True)
        self.Draw.draw_histo(mg, show=show, draw_opt='a', lm=.13, bm=.1, l=leg)

if __name__ == '__main__':
    parser = ArgumentParser(prog='ErrorAnalysisCollection')
    parser.add_argument('plans', nargs='?', help='run plan', default='[2, 3, 4, 5]')
    args = parser.parse_args()

    print_banner('STARTING RUNPLAN COLLECTION')

    z = PlanCollection(loads(args.plans))
