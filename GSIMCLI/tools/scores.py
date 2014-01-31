# -*- coding: utf-8 -*-
'''
Created on 21/01/2014

@author: julio
'''

import glob
import itertools
import os

import numpy as np
import parsers.cost as cost


def crmse(station_path, orig_path, res, md, skip_years=None):
    """Centered Root-Mean-Square Error

    1. load st and orig
    2. yearly averages
    3. centered (yearly av - serie av) (opt ?)
    4. st - orig
    5. SD
    6. repeat all st
    7. mean

    """
    orig = cost.datafile(orig_path, res, md)
    if skip_years:
        orig = orig.select(lambda x: x not in skip_years)
    orig_yearly = orig.mean(axis=1)
    orig_yc = orig_yearly - orig_yearly.mean()

    station = cost.datafile(station_path, res, md)
    station_yearly = station.mean(axis=1)
    station_yc = station_yearly - station_yearly.mean()
    diff = station_yc - orig_yc
    
    return diff.std()


def crmse_network(stations_spec, orig_files, md, skip_netwmissing=False,
                  skip_outlier=True):
    """Network CRMSE

    TODO: consider skipping when resolution != 'y'
    """
    crmses = np.zeros(len(stations_spec))
    orig_parsed = cost.match_sets(os.path.dirname(stations_spec[0][0]),
                                  os.path.dirname
                                  (os.path.dirname(orig_files.keys()[0])))
    if skip_netwmissing:
        years_missing = list(skip_years(orig_parsed, md))
    else:
        years_missing = list()

    for i, st_spec in enumerate(stations_spec):
        if skip_outlier:
            years_outlier = list(np.unique(skip_outliers(orig_parsed[i]).Year))
        else:
            years_outlier = list()
        years = years_missing + years_outlier
        crmses[i] = crmse(st_spec[0], orig_parsed[i][0], st_spec[1][4], md,
                          years)
        # print st_spec[1][0], st_spec[1][5], crmses[i]

    return crmses.mean(), crmses


def crmse_network_new(network_homog, network_orig, md, skip_netwmissing=False,
                  skip_outlier=True):
    """Network Centered Root-Mean-Square Error

    """
    homog = network_average(network_homog, md)
    orig = network_average(network_orig, md)

    if skip_years:
        orig = orig.select(lambda x: x not in skip_years)

    homog_c = homog - homog.mean()
    orig_c = orig - orig.mean()

    diff = homog_c - orig_c
    return diff.std()


def crmse_global(homog_path, orig_path, variable, md, skip_netwmissing=False,
                 skip_outlier=True):
    """Submission average CRMSE.

    TODO: support list of variables
    FIXME: stick to one averaging method and/or enhance the second
    """
    if type(homog_path) == str:
        homog_files = cost.directory_walk_v1(homog_path)
        homog_parsed = cost.files_select(parsed=homog_files, ftype='data',
                                         variable=variable, content='d')
    else:
        homog_parsed = homog_path

    if type(orig_path) == str:
        orig_files = cost.directory_walk_v1(orig_path)
    else:
        orig_files = orig_path

    networks = cost.agg_network(homog_parsed)
    network_crmse = np.zeros(len(networks))
    todos = list()
    for i, network in enumerate(networks):
        network_crmse[i], bla = crmse_network(network, orig_files, md,
                                              skip_netwmissing, skip_outlier)
        todos.append(bla)

    return network_crmse.mean(), np.mean(list(itertools.chain.
                                             from_iterable(todos)))


def skip_years(orig_spec, md):
    """List of the years where any station has missing data.

    """
    skip_list = list()
    for spec in orig_spec:
        orig = cost.datafile(spec[0], spec[1][4], md)
        skip_list.append(orig[orig.isnull().any(axis=1)].index)

    skip_list = np.unique(itertools.chain.from_iterable(skip_list))

    return skip_list


def skip_outliers(station_spec):
    """List of the dates with outliers detected in each station.

    """
    netw_path, station = os.path.split(station_spec[0])
    os.chdir(netw_path)
    breakpoints_file = os.path.join(netw_path, glob.glob('*detected.txt')[0])
    breakpoints = cost.breakpointsfile(breakpoints_file)
    break_dates = breakpoints[((breakpoints.Station == station) &
                              (breakpoints.Type == 'OUTLIE'))].ix[:, 2:]
    return break_dates


def improvement(homog_path, inhomog_path, orig_path, variable, md,
                skip_md, skip_outlier):
    """The improvement over the inhomogeneous data is computed as the quotient
    of the mean CRMSE of the homogenized networks and the mean CRMSE of the
    same inhomogeneous networks.

    """
    inhomog_matched = cost.match_sets(homog_path, inhomog_path)
    homog_crmse = crmse_global(homog_path, orig_path, variable, md,
                               skip_md, skip_outlier)
    inhomog_crmse = crmse_global(inhomog_matched, orig_path, variable, md,
                                 skip_md, skip_outlier)

    print homog_crmse
    print inhomog_crmse

    return homog_crmse[0] / inhomog_crmse[0], homog_crmse[1] / inhomog_crmse[1]


def network_average(network, md):
    """Calculate the average of all stations in a network per year.

    """
    first = True
    for st_spec in network:
        station = cost.datafile(st_spec[0], st_spec[1][4], md)
        if first:
            average = np.zeros(station.shape[0])
            average = station.mean(axis=1)
            first = False
            continue
        average += station.mean(axis=1)

    return average / len(network)


if __name__ == '__main__':
    md = -999.9

    macpath = '/Users/julio/Desktop/testes/cost-home/'
    mintpath = '/home/julio/Testes/'
    basepath = macpath

    """ # inho syn1
    netw_path = basepath + 'benchmark/inho/precip/syn1'
    orig_path = basepath + 'benchmark/orig/precip/syn1'
    inho_path = basepath + 'benchmark/inho/precip/syn1'
    variable = 'rr'
    # """

    """ # inho sur1 precip
    netw_path = basepath + 'benchmark/inho/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # inho sur1 temp
    netw_path = basepath + 'benchmark/inho/temp/sur1'
    orig_path = basepath + 'benchmark/orig/temp/sur1'
    inho_path = basepath + 'benchmark/inho/temp/sur1'
    variable = None  # 'tn'
    # """

    """ # AnClim SNHT
    netw_path = basepath + 'benchmark/h019/temp/sur1'
    orig_path = basepath + 'benchmark/orig/temp/sur1'
    inho_path = basepath + 'benchmark/inho/temp/sur1'
    variable = None  # 'tn'
    # """

    # """ # MASH Marinova precip
    netw_path = basepath + 'benchmark/h009/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    # print crmse_global(netw_path, orig_path, variable, md)
    print improvement(netw_path, inho_path, orig_path, variable, md,
                      False, True)

    print 'done'
