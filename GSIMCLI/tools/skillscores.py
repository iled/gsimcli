# -*- coding: utf-8 -*-
"""
This module tries to reproduce the skill scores functions used in the COST-HOME
benchmarking of homogenisation algorithms. [1]_

References
----------
.. [1] Venema, V., et al. (2012). Benchmarking homogenization algorithms for
    monthly data. Climate of the Past, 8(1), 89–115. doi:10.5194/cp-8-89-2012
Created on 23/12/2015

@author: julio
"""
from __future__ import division

from collections import namedtuple

from interface.ui_utils import Updater
import numpy as np
import parsers.costhome as ch


update = Updater()


Hits = namedtuple('Hits', ['true_positives', 'false_positives',
                           'false_negatives', 'true_negatives'])

_setuple = namedtuple('setup', 'id size homog orig')


def setup_skill(submission, orig_path):
    submission.setup(breaks=True, orig_path=orig_path)

    for station in submission.iter_stations():
        station.orig.load_detected(breaks=True)
        orig = station.orig.breaks.apply(lambda x: ''.join(map(str, x)), 1)
        homog = station.breaks.apply(lambda x: ''.join(map(str, x)), 1)
        yield _setuple(station.id, station.data.shape[0], homog, orig)


def count_hits(homog, orig, size=np.nan):
    """
    Count the hits of a given COST-HOME submission.

    parameters
    ----------


    Returns
    -------


    """
    true_positives = np.in1d(homog, orig).sum()
    false_positives = len(homog) - true_positives
    false_negatives = len(orig) - true_positives
    true_negatives = size - true_positives - false_positives - false_negatives
    return Hits(true_positives, false_positives,
                false_negatives, true_negatives)


def crawl(submission, orig_path):
    total_hits = np.zeros(4)
    for stid, size, homog, orig in setup_skill(submission, orig_path):
        hits = count_hits(homog, orig, size)
        total_hits += hits
        print stid, hits
    print total_hits
    return Hits(*total_hits.tolist())


def peirce(true_positives, false_positives, false_negatives, true_negatives):
    pod = true_positives / (true_positives + false_negatives)
    pofd = false_positives / (false_positives + true_negatives)
    pss = pod - pofd
    peirce_skillscore = namedtuple('PeirceSkillScore',
                                   ['POD', 'POFD', 'Peirce'])
    return peirce_skillscore(pod, pofd, pss)


def heidke(true_positives, false_positives, false_negatives, true_negatives):
    n = true_negatives + false_positives + false_negatives + true_negatives
    p = (true_positives + true_negatives) / n
    r_std = n * ((true_positives + false_negatives)
                 * (true_positives + false_positives)
                 + (false_positives + true_negatives)
                 * (false_negatives + true_negatives))
    hss_std = (p - r_std) / (1 - r_std)
    return hss_std

if __name__ == '__main__':
    md = -999.9

    macpath = '/Users/julio/Desktop/testes/'
    mintpath = '/home/julio/Testes/'
    basepath = mintpath

    """ # inho syn1
    netw_path = basepath + 'benchmark/inho/precip/syn1'
    orig_path = basepath + 'benchmark/orig/precip/syn1'
    inho_path = basepath + 'benchmark/inho/precip/syn1'
    variable = 'rr'
    # """

    """ # inho sur1 precip
    # st 7.3 1.00 netw 3.1 1.00
    netw_path = basepath + 'benchmark/inho/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # inho sur1 temp
    # st 0.47 1.00 netw 0.20 1.00
    netw_path = basepath + 'benchmark/inho/temp/sur1'
    orig_path = basepath + 'benchmark/orig/temp/sur1'
    inho_path = basepath + 'benchmark/inho/temp/sur1'
    variable = None  # 'tn'
    # """

    """ # AnClim SNHT
    # st 0.52 1.02 netw 0.31 1.16
    netw_path = basepath + 'benchmark/h019/temp/sur1'
    orig_path = basepath + 'benchmark/orig/temp/sur1'
    inho_path = basepath + 'benchmark/inho/temp/sur1'
    variable = None  # 'tn'
    # """

    # """ # MASH Marinova precip
    # pod=0.23 pofd=0.03 peirce=0.20
    # heidke=0.22 heidke special=0.27
    netw_path = basepath + 'benchmark/h009/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # PRODIGE main precip
    # st 4.7 0.63 netw 3.3 1.07
    netw_path = basepath + 'benchmark/h002/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    # """

    """ # GSIMCLI yearly
    # gsimcli_results = basepath + 'cost-home/rede000010/gsimcli_results.xls'
    # gsimcli_results = basepath + 'cost-home/500_dflt_16_allvar_vmedia/rede000009/gsimcli_results.xls'
    gsimcli_results = [basepath + 'cost-home/rede000005/gsimcli_results.xls',
                       basepath + 'cost-home/rede000009/gsimcli_results.xls']
    # network_id = '000009'
    kis = [basepath + 'cost-home/rede000005/keys.txt',
           basepath + 'cost-home/rede000009/keys.txt']
    orig_path = basepath + "/benchmark/orig/precip/sur1"
    inho_path = basepath + "/benchmark/inho/precip/sur1"
    # """

    """ # GSIMCLI monthly
    import glob

    rede5 = glob.glob('/home/julio/Área de Trabalho/testes 5+9/d095c095_xls/5/' + '*.xls')
    rede9 = glob.glob('/home/julio/Área de Trabalho/testes 5+9/d095c095_xls/9/' + '*.xls')
    gsimcli_results = {'000005': rede5, '000009': rede9}

    kis = [basepath + 'cost-home/rede000005/keys.txt',
           basepath + 'cost-home/rede000009/keys.txt']
    orig_path = basepath + "/benchmark/orig/precip/sur1"
    inho_path = basepath + "/benchmark/inho/precip/sur1"

    sub = ch.Submission(no_data=md)
    sub.load_gsimcli(gsimcli_results, kis, yearly=False, yearly_sum=True,
                     orig_path=orig_path, inho_path=inho_path)
    # """

    # netw_path = basepath + 'benchmark/h011/precip/sur1'
    # network_id = ['000009', '000010']

    sub = ch.Submission(netw_path, md,  # ['000009', '000005'],
                        orig_path=orig_path, inho_path=inho_path)

    # sub.setup(True, True, orig_path, inho_path)

    hits = crawl(sub, orig_path)
    print peirce(*hits)
    print heidke(*hits)

    print 'done'
