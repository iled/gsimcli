# -*- coding: utf-8 -*-
"""
Created on 22/04/2015

@author: julio
"""
import os
import glob2

import numpy as np
from tools.grid import PointSet


def find_pairs(basedir):
    homogs = glob2.glob(os.path.join(basedir, '**/*homog*.prn*'))
    cands = list()
    for homog in homogs:
        n = os.path.basename(os.path.splitext(homog)[0]).split('_')[-1]
        cand = glob2.glob(os.path.join(basedir, '**/*candidate*' + n + '.*'))
        cands.append(cand[0])
    return zip(cands, homogs)


def load_pset(psetfile):
    pset = PointSet()
    pset.load(psetfile, nd=-999.9, header=True)
    return pset


def load_pair(candhomog):
    cand, homog = map(load_pset, candhomog)
    return cand, homog


def calc_diff(cand, homog):
    diff = (homog.values['clim'] - cand.values['clim']) * \
        100 / cand.values['clim']
    diff_col = np.where(homog.values['Flag'] == cand.nodata, cand.nodata, diff)
    homog.nvars += 1
    homog.varnames.append('Diff')
    homog.values['Diff'] = diff_col

    path, ext = os.path.splitext(homog.path)
    new_path = path + '_diff' + ext
    homog.save(new_path, True)

if __name__ == '__main__':
    basedir = "/home/julio/Testes/cost-home/rede000010_work/1900-1909"

    pairs = find_pairs(basedir)
    for pair in pairs:
        cand, homog = load_pair(pair)
        calc_diff(cand, homog)
        print 'done: ', pair[0]
