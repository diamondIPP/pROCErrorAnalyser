#!/usr/bin/env python
# --------------------------------------------------------
#       Software  to analyse and categorise read-out errors in the layer 1 CMS pixel modules
# created on February 28th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import TFile, TH2F, TH2I, TCutG, TH1I, TF1, TProfile
from argparse import ArgumentParser
from sys import path
from os.path import join as joinpath
from os.path import dirname, realpath
path.insert(1, joinpath(dirname(realpath(__file__)), 'src'))
from RootDraw import *
from Utils import print_banner, capitalise
from glob import glob
from Pickler import Pickler
from numpy import ceil, zeros


class ErrorAnalyser:

    def __init__(self, run):

        self.RunNumber = run
        self.DataDir = '/data/procErrors'
        self.File = TFile(self.get_file_name(run))
        self.Tree = self.File.Get('tree')
        self.ProgramDir = dirname(realpath(__file__))
        self.SaveDir = run

        self.NCols = 52
        self.NRows = 80
        self.NRocs = 16
        self.Voltage = self.get_file_name(run).split('-')[1]
        self.Current = self.get_file_name(run).split('-')[2].split('.')[0]

        self.NEntries = self.Tree.GetEntries()
        self.Values = {}

        self.Bins2D = [self.NCols, - .5, self.NCols - .5, self.NRows, - .5, self.NRows - .5]
        self.ModBins2D = [self.NCols * 8, - .5, self.NCols * 8 - .5, self.NRows * 2, - .5, self.NRows * 2 - .5]
        self.EventBins = [int(self.NEntries / 5e3), 0, self.NEntries]

        self.Pickler = Pickler(self)
        self.Drawer = RootDraw(self)

    def get_file_name(self, run):
        for file_name in glob(joinpath(self.DataDir, '*')):
            if str(run).zfill(3) in file_name:
                return file_name
        raise IOError('Could not find run {r} in {d}'.format(r=run, d=self.DataDir))

    def get_valid_hits(self):
        self.Pickler.set_path('ValidHits')

        def func():
            log_message('Getting valid hits for run {r} ...'.format(r=self.RunNumber))
            return int(self.Tree.Draw('plane', 'buffer_corruption<1', 'goff'))
        return self.Pickler.run(func)

    def get_valid_events(self):
        self.Pickler.set_path('ValidEvents')

        def func():
            log_message('Getting valid events for run {r} ...'.format(r=self.RunNumber))
            return int(self.Tree.GetEntries('plane&&buffer_corruption<1'))
        return self.Pickler.run(func)

    def get_hit_rate(self, prnt=True, string=False):
        rate = self.get_valid_hits() / (2.5e-8 * self.NEntries)
        r_string = '{0:5.1f} MHz'.format(rate / 1000000)
        if prnt:
            print 'Hit Rate:   {r}'.format(r=r_string)
        return rate if not string else r_string

    def get_event_rate(self,  prnt=True, string=False):
        rate = self.get_valid_events() / (2.5e-8 * self.NEntries)
        r_string = '{0:5.4f} MHz'.format(rate / 1000000)
        print 'Hit Rate:   {r}'.format(r=r_string) if prnt else do_nothing()
        return rate if not string else r_string

    def get_pixel_error(self, name):
        self.Pickler.set_path('PixelErrors', name=capitalise(name))

        def func():
            log_message('Getting {n}s for run {r} ...'.format(r=self.RunNumber, n=' '.join(name.split('_'))))
            n = self.Tree.Draw(name, '{n} > 0'.format(n=name), 'goff')
            return sum(self.Tree.GetV1()[i] for i in xrange(n))
        return self.Pickler.run(func)

    def get_buffer_errors(self):
        return self.get_pixel_error('buffer_corruption')

    def get_invalid_address(self):
        return self.get_pixel_error('invalid_address')

    def get_invalid_pulse_height(self):
        return self.get_pixel_error('invalid_pulse_height')

    def calc_buffer_proportion(self, prnt=True):
        n = self.get_buffer_errors() / float(self.get_valid_hits()) * 100
        print '{0:6.4f}% Buffer Corruptions'.format(n) if prnt else do_nothing()

    def draw_time_bes(self, show=True):
        h = TProfile('h_tbe', 'Time Evolution of the Buffer Corruptions', *self.EventBins)
        self.Tree.Draw('buffer_corruption*1000:Entry$>>h_tbe', '', 'goff')
        format_histo(h, x_tit='Event Number', y_tit='Buffer Corruption [per mill]', y_off=2., stats=0)
        self.Drawer.draw_histo(h, show=show, lm=.15, rm=.1)

    def draw_event_size(self, fit=True, show=True):
        h = TH1I('h_es', 'Event Size', 100, 0, 100)
        self.Tree.Draw('@plane.size()>>h_es', '', 'goff')
        f = None
        if fit:
            set_root_output(False)
            set_statbox(only_fit=True, entries=1.5, w=.2)
            f = TF1('fit', '[0]*TMath::Poisson(x, [1])', 0, 100)
            f.SetParameters(1e7, 5)
            f.SetParNames('Constant', 'Event Rate #lambda')
            h.SetName('Fit Result')
            h.Fit(f, 'q')
        x_range = [h.FindFirstBinAbove(0) - 3, h.FindLastBinAbove(0) + 3]
        format_histo(h, x_tit='Number of Hits per Event', y_tit='Number of Entries', y_off=1.6, x_range=x_range)
        self.Drawer.draw_histo(h, show=show, lm=.14)
        return h if not fit else f.GetParameter(1)

    def draw_occupancy(self, roc=0, show=True):
        h = TH2I('h_oc', 'Occupancy ROC {n}'.format(n=roc), *self.Bins2D)
        self.Tree.Draw('row:col >> h_oc', '', 'goff')
        format_histo(h, x_tit='col', y_tit='row', z_tit='Number of Entries', y_off=1.3, z_off=1.6, stats=0)
        self.Drawer.draw_histo(h, draw_opt='colz', lm=.13, rm=0.17, show=show)

    def draw_module_occupancy(self, show=True):
        self.Pickler.set_path('Histos', name='ModOccupancy')

        def func():
            hits_per_event = self.get_valid_hits() / float(self.get_valid_events())
            data = [zeros((self.NCols, self.NRows)) for _ in xrange(self.NRocs)]
            n_events = int(1e7 / hits_per_event)
            for i in xrange(int(ceil(self.get_valid_hits() / 1e7))):
                # print i
                self.Tree.SetEstimate(self.Tree.Draw('plane', 'row!=80', 'goff', n_events, i * n_events))
                n = self.Tree.Draw('col:row:plane', 'row!=80', 'goff', n_events, i * n_events)
                for j in xrange(n):
                    data[int(self.Tree.GetV3()[j])][int(self.Tree.GetV1()[j])][int(self.Tree.GetV2()[j])] += 1
            return self.draw_map(data, show=False)
        h = self.Pickler.run(func)
        self.Drawer.draw_histo(h, draw_opt='colz', lm=.055, rm=0.105, show=show, x=2, y=.6, f=self.draw_module_grid)
        return h

    def draw_buffer_map(self, rel=False, show=True):
        self.Pickler.set_path('Histos', name='BufErrors{m}'.format(m='Rel' if rel else 'Abs'))

        def func():
            log_message('Drawing buffer map for run {r}'.format(r=self.RunNumber))
            good_data = [zeros(self.NCols) for _ in xrange(self.NRocs)]
            if rel:
                h1 = self.draw_module_occupancy(show=False)
                for col in xrange(h1.GetNbinsX()):
                    for row in xrange(h1.GetNbinsY()):
                        # r = row if row < self.NRows else 2 * self.NRows - row - 1
                        c = col % self.NCols if row < self.NRows else (8 * self.NCols - 1 - col) % self.NCols
                        roc = col / self.NCols if row < self.NRows else 15 - col / self.NCols
                        pl = (roc - 12) % 16
                        good_data[pl][c] += h1.GetBinContent(col + 1, row + 1)
            bad_data = [zeros(self.NCols) for _ in xrange(self.NRocs)]
            self.Tree.SetEstimate(self.Tree.Draw('plane', 'buffer_corruption', 'goff'))
            n = self.Tree.Draw('col:row:plane', 'buffer_corruption', 'goff')
            for i in xrange(n):
                try:
                    bad_data[int(self.Tree.GetV3()[i])][int(self.Tree.GetV1()[i])] += 1
                except IndexError as err:
                    log_warning('Column out of range: {e}'.format(e=err))
            data = [zeros((self.NCols, self.NRows)) for _ in xrange(self.NRocs)]
            for pl in xrange(self.NRocs):
                for col in xrange(self.NCols):
                    for row in xrange(self.NRows):
                        data[pl][col][row] = bad_data[pl][col] / (float(good_data[pl][col]) + bad_data[pl][col]) * 1000 if rel else bad_data[pl][col]
            return self.draw_map(data, False)
        h = self.Pickler.run(func)
        format_histo(h, name='Buffer Corruptions', z_tit='Number of Errors' if not rel else 'Buffer Errors [per mill]', stats=0)
        self.Drawer.draw_histo(h, draw_opt='colz', lm=.055, rm=0.105, show=show, x=2, y=.6, f=self.draw_module_grid)
        return h

    def draw_map(self, data, show=True):
        h = TH2F('h_moc', 'Module Occupancy', *self.ModBins2D)
        for ipl, pl in enumerate(data):
            for ix, col in enumerate(pl):
                for iy, row in enumerate(col):
                    roc = (ipl + 12) % 16
                    x_off = self.NCols * (roc % 8)
                    # Reverse order of the upper ROC row:
                    y = iy if (roc < 8) else (2 * self.NRows - iy - 1)
                    x = (ix + x_off) if (roc < 8) else (8 * self.NCols - 1 - x_off - ix)
                    h.SetBinContent(x + 1, y + 1, row)
        format_histo(h, x_tit='col', y_tit='row', z_tit='Number of Entries', y_off=.45, z_off=.5, stats=0, lab_size=.06, tit_size=.06)
        self.Drawer.draw_histo(h, draw_opt='colz', lm=.055, rm=0.105, show=show, x=2, y=.6, f=self.draw_module_grid)
        return h

    def draw_module_grid(self, show=True):
        for i in xrange(2):
            for j in xrange(8):
                rows, cols = self.NRows, self.NCols
                x = array([cols * j - .5, cols * (j + 1) - .5, cols * (j + 1) - .5, cols * j - .5, cols * j - .5], 'd')
                y = array([rows * i - .5, rows * i - .5, rows * (i + 1) - .5, rows * (i + 1) - .5, rows * i - .5], 'd')
                cut = TCutG('r{n}'.format(n=j + (j * i)), 5, x, y)
                cut.SetLineColor(1)
                cut.SetLineWidth(2)
                if show:
                    cut.Draw('same')
                self.Drawer.Drawings.append(cut)

    def draw_run_info(self, canvas, show=True, x=1, y=1, runs=None):
        """ Draws the run infos inside the canvas. If no canvas is given, it will be drawn into the active Pad. """
        if show:
            canvas.cd()

        dur = 5

        if show:
            if not canvas.GetBottomMargin() > .105:
                canvas.SetBottomMargin(0.15)

        if self.Drawer.RunInfoLegends is None:
            # git_text = TLegend(.85, 0, 1, .025)
            # git_text.AddEntry(0, 'git hash: {ver}'.format(ver=check_output(['git', 'describe', '--always'])), '')
            # git_text.SetLineColor(0)
            if runs is None:
                run_string = 'Run {run}: {rate}, {dur} Min ({evts} evts)'.format(run=self.RunNumber, rate=self.get_hit_rate(False, True), dur=dur, evts=self.NEntries)
            else:
                # run_string = 'Runs {start}-{stop} ({flux1} - {flux2})'.format(start=runs[0], stop=runs[1], flux1=runs[2].strip(' '), flux2=runs[3].strip(' '))
                run_string = 'Runs {start}-{stop}'.format(start=runs[0], stop=runs[-1])
            width = len(run_string) * .011 if x == y else len(run_string) * 0.015 * y / x
            legend = self.Drawer.make_legend(.005, .1, y1=.003, x2=width, nentries=3, felix=False, scale=.75)
            legend.SetMargin(0.05)
            legend.AddEntry(0, run_string, '')
            if runs is None:
                legend.AddEntry(0, 'Module: M1109 @ {bias}kV and {cur}mA'.format(bias=self.Voltage, cur=self.Current), '')
            else:
                legend.AddEntry(0, 'Module: M1109', '')
            # self.RunInfoLegends = [legend, git_text]
            self.Drawer.RunInfoLegends = [legend]
        else:
            # git_text = self.RunInfoLegends[1]
            legend = self.Drawer.RunInfoLegends[0]
        if show:
            pads = [i for i in canvas.GetListOfPrimitives() if i.IsA().GetName() == 'TPad']
            if not pads:
                # if self.MainConfigParser.getboolean('SAVE', 'git_hash'):
                #     git_text.Draw()
                # if self.MainConfigParser.getboolean('SAVE', 'info_legend'):
                legend.Draw()
            else:
                for pad in pads:
                    pad.cd()
                    # if self.MainConfigParser.getboolean('SAVE', 'git_hash'):
                    #     git_text.Draw()
                    # if self.MainConfigParser.getboolean('SAVE', 'info_legend'):
                    legend.Draw()
                    pad.Modified()
            canvas.Update()
        else:
            # return legend, git_text
            return legend

if __name__ == '__main__':
    # command line argument parsing

    parser = ArgumentParser(prog='ErrorAnalyser')
    parser.add_argument('run', nargs='?', help='run number', default=16, type=int)
    args = parser.parse_args()

    print_banner('STARTING ERROR ANALYSER FOR RUN {r}'.format(r=args.run))

    # start command line
    z = ErrorAnalyser(args.run)
