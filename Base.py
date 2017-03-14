#!/usr/bin/env python
# --------------------------------------------------------
#       base Class for the Error Analyser classes
# created on March 14th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from sys import path
from os.path import join, dirname, realpath
path.insert(1, join(dirname(realpath(__file__)), 'src'))


class Base(object):

    def __init__(self):

        self.Dir = dirname(realpath(__file__))
        self.DataDir = '/data/procErrors'


if __name__ == '__main__':
    z = Base()
