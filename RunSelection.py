#!/usr/bin/env python
# --------------------------------------------------------
#       Class to select several runs with the same settings
# created on March 14th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Base import Base
from os.path import join, isfile
from json import load, dump
from glob import glob
from Utils import log_message, print_banner, log_warning, make_runplan_string
from collections import OrderedDict
from copy import deepcopy


class RunSelection(Base):
    def __init__(self):

        Base.__init__(self)
        self.RunPlanPath = join(self.Dir, 'runPlans.json')

        self.RunPlan = self.load_runplan()
        self.RunInfo = self.load_run_info()
        self.Selection = OrderedDict()

        self.SelectedRunPlan = None

        self.init_selection()

    def load_runplan(self):
        runplan = {}
        try:
            f = open(self.RunPlanPath, 'r')
            runplan = load(f)
            f.close()
        except IOError:
            log_message('There is no runPlans file yet!')
        return runplan

    def load_run_info(self):
        dic = {}
        for file_name in glob(join(self.DataDir, '*')):
            data = file_name.split('/')[-1].split('-')
            try:
                run = data[0].strip('run')
                hv, cur = data[1], data[2].strip('.root')
                if run.isdigit():
                    dic[run] = {'HV': int(hv), 'Current': int(cur)}
            except IndexError:
                pass
        return OrderedDict((int(run), d) for run, d in sorted(dic.iteritems()))

    def init_selection(self):
        self.reset_selection()

    def reset_selection(self):
        """ Creates a dict of bools to store the selection, which is filled with False (no run selected). """
        for run in self.RunInfo:
            self.Selection[run] = False

    def show_run_info(self):
        print 'Run Current [mA] Voltage [kV]\n'
        for run, dic in self.RunInfo.iteritems():
            print '{r} {c} {v}'.format(r=str(run).rjust(3), c=str(dic['Current']).rjust(12), v=str(dic['HV']).rjust(12))

    def show_selected_runs(self):
        """ Prints and overview of all selected runs. """
        selected_runs = self.get_selected_runs()
        print 'The selections contains {n} runs\n'.format(n=len(selected_runs))
        print 'Run Current [mA] Voltage [kV]\n'
        for run in selected_runs:
            dic = self.RunInfo[run]
            print '{r} {c} {v}'.format(r=str(run).rjust(3), c=str(dic['Current']).rjust(12), v=str(dic['HV']).rjust(12))

    def show_run_plans(self):
        """ Print a list of all run plans from the current test campaign to the console. """
        old = deepcopy(self.Selection)
        print 'RUN PLAN:'
        print '  Nr.    {r}  {t}  {ct}  {v}  {cu}'.format(r='Range'.ljust(16), t='Trim', ct='ctrlreg', v='Voltage [kV]'.ljust(14), cu='Current [mA]'.ljust(14))
        for plan, info in sorted(self.RunPlan.iteritems()):
            self.reset_selection()
            self.select_runs_from_runplan(plan)
            runs = info['runs']
            run_string = '[{min}, ... , {max}]'.format(min=str(runs[0]).zfill(3), max=str(runs[-1]).zfill(3))
            voltages, currents = [dic['HV'] for run, dic in self.RunInfo.iteritems() if run in runs], [dic['Current'] for run, dic in self.RunInfo.iteritems() if run in runs]
            volt_str = '[{min}, ... , {max}]'.format(min=str(min(voltages)).zfill(2), max=str(max(voltages)).zfill(2))
            cur_str = '[{min}, ... , {max}]'.format(min=str(min(currents)).zfill(2), max=str(max(currents)).zfill(2))
            print '  {nr}:  {r}  {t}  {ct}  {v}  {cu}'.format(nr=plan.ljust(4), r=run_string, t=str(info['trim']).ljust(4), ct=str(info['ctrlreg']).ljust(7), v=volt_str, cu=cur_str)
        self.Selection = old

    def select_run(self, run_number, deselect=False):
        if run_number not in self.RunInfo:
            log_warning('Run {run} not found in list of run numbers'.format(run=run_number))
        self.Selection[run_number] = True if not deselect else False

    def deselect_run(self, run_number):
        self.select_run(run_number, deselect=True)

    def select_runs_in_range(self, min_run, max_run, deselect=False):
        for run in self.Selection:
            if max_run >= run >= min_run:
                self.select_run(run, deselect)

    def deselect_runs_in_range(self, min_run, max_run):
        self.select_runs_in_range(min_run, max_run, deselect=True)

    def select_runs_from_runplan(self, plan_nr):
        self.reset_selection()
        plan = make_runplan_string(plan_nr)
        try:
            runs = self.RunPlan[plan]['runs']
            self.SelectedRunPlan = plan
            self.select_runs_in_range(runs[0], runs[-1])
        except KeyError:
            log_warning('Run plan {r} does not exist!'.format(r=plan))

    def save_runplan(self, runplan=None):
        f = open(self.RunPlanPath, 'r+' if isfile(self.RunPlanPath) else 'w')
        runplan = self.RunPlan if runplan is None else runplan
        dump(runplan, f, indent=2, sort_keys=True)
        f.truncate()
        f.close()

    def add_selection_to_runplan(self, plan_nr, trim, ctrlreg):
        """ Saves all selected runs as a run plan with name 'plan_nr'. """
        plan_nr = make_runplan_string(plan_nr)
        assert self.Selection, 'The run selection is completely empty!'

        self.RunPlan[plan_nr] = {'runs': self.get_selected_runs(), 'trim': trim, 'ctrlreg': ctrlreg}
        self.save_runplan()

    def get_selected_runs(self):
        """ :return: list of selected run numbers. """
        runs = [run for run, selected in self.Selection.iteritems() if selected]
        if not runs:
            log_warning('No runs selected!')
        return runs


if __name__ == '__main__':
    print_banner('STARTING RUN SELECTION')
    z = RunSelection()
