# -*- coding: utf-8 -*-
'''
Created on 21/01/2014

@author: julio
'''

import numpy as np
import parsers.cost as cost


def crmse(station_path, orig_path, res, md, years=None):
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
    if years:
        orig = orig.ix[years]
    orig_yearly = orig.mean(axis=1)
    orig_yc = orig_yearly - orig_yearly.mean()

    station = cost.datafile(station_path, res, md)
    station_yearly = station.mean(axis=1)
    station_yc = station_yearly - station_yearly.mean()
    diff = station_yc - orig_yc

    return diff.std()


def crmse_network(stations_spec, orig_files, md):
    """Network CRMSE

    """
    crmses = np.zeros(len(stations_spec))
    orig_parsed = cost.match_orig(stations_spec, orig_files)
    years = do_years(orig_parsed, md)

    for i, st_spec in enumerate(stations_spec):
        crmses[i] = crmse(st_spec[0], orig_parsed[i][0], st_spec[1][4], md,
                          years)

    return crmses.mean()


def crmse_global(homog_path, orig_path, variable, md):
    """Submission average CRMSE.

    """
    orig_files = cost.directory_walk_v1(orig_path)
    homog_files = cost.directory_walk_v1(homog_path)
    homog_parsed = cost.files_select(parsed=homog_files, network=None,
                                     ftype='data', variable=variable,
                                     content='d')
    networks = cost.agg_network(homog_parsed)
    network_crmse = np.zeros(len(networks))
    for i, network in enumerate(networks):
        network_crmse[i] = crmse_network(network, orig_files, md)

    return network_crmse.mean()


def do_years(orig_spec, md):
    """Skip the years where any station has missing data.

    """
    start = True
    for spec in orig_spec:
        orig = cost.datafile(spec[0], spec[1][4], md)
        indexes = orig.dropna().index
        if start:
            do_list = list(indexes)
            start = False

        do_list = [year for year in indexes if year in do_list]

    return do_list


def improvement(homog_path, inhomog_path, orig_path, variable, md):
    """The improvement over the inhomogeneous data is computed as the quotient
    of the mean CRMSE of the homogenized networks and the mean CRMSE of the
    same inhomogeneous networks.

    """
    homog_crmse = crmse_global(homog_path, orig_path, variable, md)
    inhomog_crmse = crmse_global(inhomog_path, orig_path, variable, md)

    return homog_crmse / inhomog_crmse


if __name__ == '__main__':
    md = -999.9

    """ # inho syn1
    netw_path = '/home/julio/Testes/benchmark/inho/precip/syn1'
    orig_path = '/home/julio/Testes/benchmark/orig/precip/syn1'
    inho_path = '/home/julio/Testes/benchmark/inho/precip/syn1'
    variable = 'rr'
    # """

    """ # inho sur1
    netw_path = '/home/julio/Testes/benchmark/inho/precip/sur1'
    orig_path = '/home/julio/Testes/benchmark/orig/precip/sur1'
    inho_path = '/home/julio/Testes/benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # AnClim SNHT
    netw_path = '/home/julio/Testes/benchmark//h019/temp/sur1'
    orig_path = '/home/julio/Testes/benchmark//orig/temp/sur1'
    inho_path = '/home/julio/Testes/benchmark/inho/temp/sur1'
    variable = 'tn'
    # """

    # MASH Marinova precip
    netw_path = '/home/julio/Testes/benchmark//h009/precip/sur1'
    orig_path = '/home/julio/Testes/benchmark/orig/precip/sur1'
    inho_path = '/home/julio/Testes/benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    print crmse_global(netw_path, orig_path, variable, md)
    print improvement(netw_path, inho_path, orig_path, variable, md)
    print 'done'
