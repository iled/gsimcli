# -*- coding: utf-8 -*-
'''
Created on 21/01/2014

@author: julio
'''

import itertools
import numpy as np
import parsers.cost as cost


def cmrse(station_path, orig_path, res, md):
    """Centered Mean Root-Square Error
    
    1. load st and orig
    2. yearly averages
    3. centered (yearly av - serie av) (opt ?)
    4. st - orig
    5. SD
    6. repeat all st
    7. mean
    
    """
    orig = cost.datafile(orig_path, res, md)
    orig_yearly = orig.mean(axis=1, skipna=False)
    orig_yc = orig_yearly - orig_yearly.mean()
    
    station = cost.datafile(station_path, res, md)
    station_yearly = station.mean(axis=1, skipna=False)
    station_yc = station_yearly - station_yearly.mean()
    diff = station_yc - orig_yc
        
    return diff.std


def cmrse_network(stations_spec, orig_spec, md):
    """Network CMRSE
    
    """
    cmrses = np.zeros(len(stations_spec))
    for i, st_spec in enumerate(stations_spec):
        cmrses[i] = cmrse(st_spec[0], orig_spec[i][0], st_spec[1][4], md)
    
    return cmrses.mean()
    
def match_orig(stations_spec, orig_path):
    """Select orig files according to given station files.
    
    """
    orig_spec = list()
    netw = 0
    for st_spec in stations_spec:
        spec = st_spec[1]
        if netw != spec[0]:
            orig_parsed = cost.files_select(parsed=orig_path, network=spec[0],
                                         ftype=spec[1], variable=spec[3],
                                         content=spec[6])
            orig_spec.append(orig_parsed)
            netw = spec[0]
       
    orig_spec = list(itertools.chain.from_iterable(orig_spec))
    if len(orig_spec) != len(stations_spec):
        raise ValueError('Mismatch between homogenized and original files.')
    return orig_spec


if __name__ == '__main__':
    # fpath = '/home/julio/Testes/benchmark/orig/precip/sur1'
    orig_path = '/Users/julio/Downloads/benchmark//orig/precip/sur1'
    netw_path = '/Users/julio/Downloads/benchmark//h009/precip/sur1'
    ftype = 'data'
    variable = 'rr'
    content = 'd'
    network = None
    merge = False
    to_year = 'sum'
    # cost.directory_convert(fpath, ftype, variable, content, network, merge,
    #                       to_year=to_year)
    orig_files = cost.directory_walk_v1(orig_path)
    netw_files = cost.directory_walk_v1(netw_path)
    netw_parsed = cost.files_select(parsed=netw_files, network=network,
                                     ftype=ftype, variable=variable,
                                     content=content)
    """for dfile, specs in parsed_files:
        dt = cost.datafile(dfile, specs[4], md=-999.9)
        pass
    """
    print netw_parsed
    orig_parsed = match_orig(netw_parsed, orig_files)
    print orig_parsed
    cmrses = cmrse_network(netw_parsed, orig_parsed, md=-999.9)
    print cmrses
    print 'done'
