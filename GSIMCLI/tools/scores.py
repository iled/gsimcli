# -*- coding: utf-8 -*-
'''
Created on 21/01/2014

@author: julio
'''

import parsers.cost as cost

def cmrse(station, orig):
    """CMRSE
    
    """
    
    

if __name__ == '__main__':
    fpath = '/home/julio/Testes/benchmark/orig/precip/sur1'
    ftype = 'data'
    variable = 'rr'
    content = 'd'
    network = None
    merge = False
    to_year = 'sum'
    # cost.directory_convert(fpath, ftype, variable, content, network, merge,
    #                       to_year=to_year)
    files = cost.directory_walk_v1(fpath)
    parsed_files = cost.files_select(parsed=files, network=network,
                                     ftype=ftype, variable=variable,
                                     content=content)
    for dfile, specs in parsed_files:
        dt = cost.datafile(dfile, specs[4], md=-999.9)
        pass
    
    print 'done'
