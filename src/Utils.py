# --------------------------------------------------------
#       Utility Methods
# created on March 1st 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from datetime import datetime
from termcolor import colored
from os import makedirs
from os import path as pth
from os.path import dirname
from sys import exit as ex


def round_down_to(num, val):
    return int(num) / val * val


def log_warning(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print '{head} {t} --> {msg}'.format(t=t, msg=msg, head=colored('WARNING:', 'red'))


def log_message(msg, overlay=False):
    t = datetime.now().strftime('%H:%M:%S')
    print '{ov}{t} --> {msg}{end}'.format(t=t, msg=msg, head=colored('WARNING:', 'red'), ov='\033[1A\r' if overlay else '', end=' ' * 20 if overlay else '')


def log_critical(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print '{head} {t} --> {msg}'.format(t=t, msg=msg, head=colored('CRITICAL:', 'red'))
    ex(-2)


def ensure_dir(path):
    if not pth.exists(dirname(path)):
        log_message('Creating directory: {d}'.format(d=path))
        makedirs(path)


def print_banner(msg, symbol='='):
    print '\n{delim}\n{msg}\n{delim}\n'.format(delim=len(str(msg)) * symbol, msg=msg)


def capitalise(string):
    return ''.join([s.title() for s in string.split('_')])


def make_runplan_string(nr):
    nr = str(nr)
    return nr.zfill(2) if len(nr) <= 2 else nr.zfill(4)


def do_nothing():
    pass
