# -*- coding: utf-8 -*-
'''
Created on 5 de Nov de 2013

@author: julio
'''

import os

import numpy as np
import pandas as pd
import parsers.costhome as ch
import tools.grid as grd
import tools.utils as ut


def dtype_filter(dataf, nodata=-999.9):
    """Filter dtypes from a pandas DataFrame, converting non-numbers into a
    keyed index.
    Return the DataFrame with the new values and a DataFrame with its keys.
    Missing or no-data values also count as a unique key.

    """
    dataf = dataf.fillna(nodata)
    keys = dict()
    for index, dt in dataf.dtypes.iteritems():  # @UnusedVariable
        if not ut.is_number(dataf[index][0]):
            values = np.unique(dataf[index])
            temp = dict()
            for i, val in enumerate(values, 1):
                dataf[index] = dataf[index].replace(val, i)
                temp[i] = val
            keys[index] = temp
            dataf[index] = dataf[index].convert_objects(convert_numeric=True)

    keys = pd.DataFrame(keys)
    if keys.shape[0] == 0:
        keys = None

    return dataf, keys


def xls2gslib(xlspath, nd=-999.9, cols=None, sheet=0, header=0,
              skip_rows=None, filter_dtype=True):
    """Convert a file in XLS format to a point-set file in GSLIB format (.prn)
    Does not work with CSV files.

    """
    xlsfile = pd.ExcelFile(xlspath)
    xlstable = xlsfile.parse(xlsfile.sheet_names[sheet], header,
                             skiprows=skip_rows, na_values=nd)
    # parse_cols=cols doesn't preserve the list order
    if cols:
        nvars = len(cols)
        varnames = [xlstable.columns[i] for i in cols]
    else:
        nvars = xlstable.shape[1]
        varnames = xlstable.columns
        cols = range(nvars)

    if header is None:
        varnames = ['var' + str(i) for i in varnames]

    if filter_dtype:
        filtered, keys = dtype_filter(xlstable.iloc[:, cols])
    else:
        filtered = xlstable.iloc[:, cols]
        keys = None

    pset = grd.PointSet(str(xlsfile.sheet_names[sheet]), nd, nvars, varnames,
                        filtered)

    return pset, keys


def xls2costhome(xlspath, outpath=None, nd=-999.9, sheet=None, header=False,
                 skip_rows=None, cols=None, network_id='ssssssss', status='xx',
                 variable='vv', resolution='r', content='c', ftype='data',
                 yearly_sum=False, keys_path=None):
    """Convert a file in GSIMCLI XLS format to a file in the COST-HOME format.
    Does not work with CSV files.

    """
    if yearly_sum:
        div = 12.0
    else:
        div = 1.0
        
    xlsfile = pd.ExcelFile(xlspath)
    xlstable = xlsfile.parse(sheetname=sheet, header=header, na_values=nd,
                             skiprows=skip_rows, parse_cols=cols)
    
    network = ch.Network(md=nd, network_id=network_id)
    stations = [label for label in xlstable.columns if '_clim' in label]
    
    if keys_path:
        network.update_ids(keys_path)
    else:
        keys = None
        
    for station in stations:
        st = ch.Station(md=nd)
        st.path = None
        st.network_id = network_id
        st.ftype = ftype
        st.status = status
        st.variable = variable
        st.resolution = resolution
        if not keys:
            st.id = station.split('_')[0]
        st.content = content
        st.data = xlstable[station] / div
        network.add(st)

    if outpath:
        network.save(outpath)

    return network


def read_keys(path):
    """Reads a TSV file with the keys to the converted station IDs.

    """
    keys = pd.read_csv(path, sep='\t', index_col=0)

    return keys


if __name__ == '__main__':
    path = '/home/julio/Testes/cost-home/rede000005/gsimcli_results.xls'
    pout = '/home/julio/Testes/cost-home/rede000005'
#     xls2costhome(path, pout, -999.9, sheet='All stations', skip_rows=[1],
#                  network_id=05, yearly_sum=True)
#     ps, ks = xls2gslib(path, header=0, cols=[0, 1, 2, 4, 3], skip_rows=[1])
#     ps.save(pout)
#     kout = '/home/julio/Testes/cost-home//rede000005/keys.txt'
#     ks.to_csv(kout, sep='\t', index_label='ID')

    pathlist = list()
    for root, dirs, files in os.walk('/home/julio/Testes/cost-home'):
        for name in files:
            filename, ext = os.path.splitext(name)
            if 'gsimcli_results' in filename and ext == '.xls':
                pathlist.append(os.path.join(root, name))

    for path in pathlist:
        print path
        netid = os.path.basename(os.path.dirname(path))[4:]
        xls2costhome(xlspath=path, outpath=os.path.dirname(path), nd=-999.9,
                        sheet='All stations', header=False, skip_rows=[1],
                        network_id=netid, status='ho',
                        variable='rr', resolution='y', content='d',
                        ftype='data', yearly_sum=True)
    print 'done'
