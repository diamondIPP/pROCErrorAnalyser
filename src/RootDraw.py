# --------------------------------------------------------
#       ROOT Drawing Class
# created on February 28th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import gROOT, gStyle, kGreen, kOrange, kViolet, kYellow, kRed, kBlue, kMagenta, kAzure, kCyan, kTeal, TCanvas, TLegend, TGraphErrors, TGraphAsymmErrors
from screeninfo import get_monitors
from Utils import round_down_to, log_warning, do_nothing, ensure_dir, log_message
from os.path import join as joinpath
from os.path import dirname, realpath, split
from numpy import array


class RootDraw:
    def __init__(self, ana):

        self.Analysis = ana
        self.Drawings = []
        self.RunInfoLegends = None

        self.Title = True
        self.Res = self.load_resolution()
        self.ResultsDir = joinpath(split(dirname(realpath(__file__)))[0], 'Results')

        # colors
        self.Count = 0
        self.Colors = create_colorlist()
        self.FillColor = 821

        gStyle.SetLegendFont(42)

    def get_color(self):
        self.Count %= 20
        color = self.Colors[self.Count]
        self.Count += 1
        return color

    def reset_colors(self):
        self.Count = 0

    def load_resolution(self):
        try:
            m = get_monitors()
            return round_down_to(m[0].height, 500)
        except Exception as err:
            log_warning(err)
            return 1000

    def save_plots(self, savename, sub_dir=None, canvas=None, x=1, y=1, prnt=True, save=True, show=True):
        """ Saves the canvas at the desired location. If no canvas is passed as argument, the active canvas will be saved. """

        if canvas is None:
            try:
                canvas = gROOT.GetListOfCanvases()[-1]
            except Exception as inst:
                print log_warning('Error in save canvas: {err}'.format(err=inst))
                return
        channel = self.channel if hasattr(self, 'channel') else None
        channel = self.Dut - 4 if hasattr(self, 'Dut') else channel
        try:
            self.Analysis.draw_run_info(canvas=canvas, x=x, y=y)
        except AttributeError as err:
            log_warning(err)
        canvas.Modified()
        canvas.Update()
        if save:
            try:
                self.save_canvas(canvas, sub_dir=sub_dir, name=savename, print_names=prnt, show=show)
            except Exception as inst:
                print log_warning('Error in save_canvas:\n{0}'.format(inst))

    def save_canvas(self, canvas, sub_dir=None, name=None, print_names=True, show=True):
        sub_dir = self.save_dir if hasattr(self, 'save_dir') and sub_dir is None else '{subdir}/'.format(subdir=sub_dir)
        canvas.Update()
        file_name = canvas.GetName() if name is None else name
        file_path = '{save_dir}{res}/{{typ}}/{file}'.format(res=sub_dir, file=file_name, save_dir=self.ResultsDir)
        ftypes = ['root', 'png', 'pdf', 'eps']
        out = 'Saving plots: {nam}'.format(nam=name)
        run_number = self.run_number if hasattr(self, 'run_number') else None
        run_number = 'rp{nr}'.format(nr=self.run_plan) if hasattr(self, 'run_plan') else run_number
        set_root_output(show)
        gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
        for f in ftypes:
            ext = '.{typ}'.format(typ=f)
            ensure_dir(file_path.format(typ=f))
            out_file = '{fname}{ext}'.format(fname=file_path, ext=ext)
            out_file = out_file.format(typ=f)
            canvas.SaveAs(out_file)
        if print_names:
            log_message(out)
        set_root_output(True)

    def save_histo(self, histo, save_name='test', show=True, sub_dir=None, lm=.1, rm=.03, bm=.15, tm=None, draw_opt='', x_fac=None, y_fac=None,
                   l=None, logy=False, logx=False, logz=False, canvas=None, gridx=False, gridy=False, save=True, ch='dia', prnt=True, phi=None, theta=None):
        if tm is None:
            tm = .1 if self.Title else .03
        x = self.Res if x_fac is None else int(x_fac * self.Res)
        y = self.Res if y_fac is None else int(y_fac * self.Res)
        h = histo
        set_root_output(show)
        c = TCanvas('c_{0}'.format(h.GetName()), h.GetTitle().split(';')[0], x, y) if canvas is None else canvas
        c.SetMargin(lm, rm, bm, tm)
        c.SetLogx() if logx else do_nothing()
        c.SetLogy() if logy else do_nothing()
        c.SetLogz() if logz else do_nothing()
        c.SetGridx() if gridx else do_nothing()
        c.SetGridy() if gridy else do_nothing()
        c.SetPhi(phi) if phi is not None else do_nothing()
        c.SetTheta(theta) if theta is not None else do_nothing()
        h.Draw(draw_opt)
        if l is not None:
            l = [l] if type(l) is not list else l
            for i in l:
                i.Draw()
        self.save_plots(save_name, sub_dir=sub_dir, x=x_fac, y=y_fac, prnt=prnt, save=save, show=show)
        set_root_output(True)
        lst = [c, h, l] if l is not None else [c, h]
        self.Drawings.append(lst)

    def draw_histo(self, histo, save_name='', show=True, sub_dir=None, lm=.1, rm=.03, bm=.15, tm=.1, draw_opt='', x=None, y=None,
                   l=None, logy=False, logx=False, logz=False, canvas=None, gridy=False, gridx=False, ch='dia', prnt=True, phi=None, theta=None):
        return self.save_histo(histo, save_name, show, sub_dir, lm, rm, bm, tm, draw_opt, x, y, l, logy, logx, logz, canvas, gridx, gridy, False, ch, prnt, phi, theta)

    def make_legend(self, x1=.65, y2=.88, nentries=2, scale=1, name='l', y1=None, felix=False, margin=.25, x2=None):
        x2 = .95 if x2 is None else x2
        y1 = y2 - nentries * .05 * scale if y1 is None else y1
        l = TLegend(x1, y1, x2, y2)
        l.SetName(name)
        l.SetTextFont(42)
        l.SetTextSize(0.03 * scale)
        l.SetMargin(margin)
        return l


def format_histo(histo, name='', title='', x_tit='', y_tit='', z_tit='', marker=20, color=1, markersize=1, x_off=None, y_off=None, z_off=None, lw=1, fill_color=0,
                 stats=True, tit_size=.04, lab_size=.04, draw_first=False, x_range=None, y_range=None, z_range=None, do_marker=True, style=None, ndiv=None):
    h = histo
    if draw_first:
        set_root_output(False)
        h.Draw('a')
        set_root_output(True)
    h.SetTitle(title) if title else h.SetTitle(h.GetTitle())
    h.SetName(name) if name else h.SetName(h.GetName())
    try:
        h.SetStats(stats)
    except AttributeError or ReferenceError:
        pass
    # markers
    try:
        if do_marker:
            h.SetMarkerStyle(marker) if marker is not None else do_nothing()
            h.SetMarkerColor(color) if color is not None else do_nothing()
            h.SetMarkerSize(markersize) if markersize is not None else do_nothing()
    except AttributeError or ReferenceError:
        pass
    # lines/fill
    try:
        h.SetLineColor(color) if color is not None else h.SetLineColor(h.GetLineColor())
        h.SetFillColor(fill_color)
        h.SetLineWidth(lw)
        h.SetFillStyle(style) if style is not None else do_nothing()
    except AttributeError or ReferenceError:
        pass
    # axis titles
    try:
        # x_tit = untitle(x_tit) if self.Felix else x_tit
        # y_tit = untitle(y_tit) if self.Felix else y_tit
        # z_tit = untitle(z_tit) if self.Felix else z_tit
        x_axis = h.GetXaxis()
        if x_axis:
            x_axis.SetTitle(x_tit) if x_tit else h.GetXaxis().GetTitle()
            x_axis.SetTitleOffset(x_off) if x_off is not None else do_nothing()
            x_axis.SetTitleSize(tit_size)
            x_axis.SetLabelSize(lab_size)
            x_axis.SetRangeUser(x_range[0], x_range[1]) if x_range is not None else do_nothing()
            x_axis.SetNdivisions(ndiv) if ndiv is not None else do_nothing()
        y_axis = h.GetYaxis()
        if y_axis:
            y_axis.SetTitle(y_tit) if y_tit else y_axis.GetTitle()
            y_axis.SetTitleOffset(y_off) if y_off is not None else do_nothing()
            y_axis.SetTitleSize(tit_size)
            y_axis.SetLabelSize(lab_size)
            y_axis.SetRangeUser(y_range[0], y_range[1]) if y_range is not None else do_nothing()
        z_axis = h.GetZaxis()
        if z_axis:
            z_axis.SetTitle(z_tit) if z_tit else h.GetZaxis().GetTitle()
            z_axis.SetTitleOffset(z_off) if z_off is not None else do_nothing()
            z_axis.SetTitleSize(tit_size)
            z_axis.SetLabelSize(lab_size)
            z_axis.SetRangeUser(z_range[0], z_range[1]) if z_range is not None else do_nothing()
    except AttributeError or ReferenceError:
        pass


def create_colorlist():
    col_names = [kGreen, kOrange, kViolet, kYellow, kRed, kBlue, kMagenta, kAzure, kCyan, kTeal]
    colors = []
    for color in col_names:
        colors.append(color + (1 if color != 632 else -7))
    for color in col_names:
        colors.append(color + (3 if color != 800 else 9))
    return colors


def make_tgrapherrors(name, title, color=1, marker=20, marker_size=1, width=1, asym_err=False, style=1, x=None, y=None):
    if (x and y) is None:
        gr = TGraphErrors() if not asym_err else TGraphAsymmErrors()
    else:
        gr = TGraphErrors(len(x), array(x, 'd'), array(y, 'd')) if not asym_err else TGraphAsymmErrors(len(x), array(x, 'd'), array(y), 'd')
    gr.SetTitle(title)
    gr.SetName(name)
    gr.SetMarkerStyle(marker)
    gr.SetMarkerColor(color)
    gr.SetLineColor(color)
    gr.SetMarkerSize(marker_size)
    gr.SetLineWidth(width)
    gr.SetLineStyle(style)
    return gr


def set_statbox(x=.95, y=.88, w=.16, entries=3, only_fit=False, opt=None, form=None):
    if only_fit:
        gStyle.SetOptStat(0011)
        gStyle.SetOptFit(1)
    gStyle.SetOptStat(opt) if opt is not None else do_nothing()
    gStyle.SetFitFormat(form) if form is not None else do_nothing()
    gStyle.SetStatX(x)
    gStyle.SetStatY(y)
    gStyle.SetStatW(w)
    gStyle.SetStatH(.04 * entries)


def set_root_output(status=True):
    if status:
        gROOT.SetBatch(0)
        gROOT.ProcessLine("gErrorIgnoreLevel = 0;")
    else:
        gROOT.SetBatch(1)
        gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
