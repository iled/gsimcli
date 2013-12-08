# -*- coding: utf-8 -*-
'''
Created on 5 de Nov de 2013

@author: julio
'''

import numpy as np
import pandas as pd
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


def xls2gslib(xlspath, nd=-999.9, cols=None, sheet=0, header=0):
    """Convert a file in XLS format to a point-set file in GSLIB format (.prn)
    Does not work with CSV files.

    """
    xlsfile = pd.ExcelFile(xlspath)
    xlstable = xlsfile.parse(xlsfile.sheet_names[sheet], header)
    xlstable = xlstable.fillna(nd)
    if cols:
        cols = map(int, cols.split(','))
        nvars = len(cols)
        varnames = [xlstable.columns[int(i)] for i in cols]
    else:
        nvars = xlstable.shape[1]
        varnames = xlstable.columns
        # varnames = [col for col in xlstable.columns]
        cols = range(nvars)

    if header is None:
        varnames = ['var' + str(i) for i in varnames]

    filtered, keys = dtype_filter(xlstable.iloc[:, cols])
    pset = grd.PointSet(str(xlsfile.sheet_names[sheet]), nd, nvars, varnames,
                        filtered)

    return pset, keys


if __name__ == '__main__':
    path = '/home/julio/Testes/test/snirh.xls'
    pout = '/home/julio/Testes/test/rede.prn'
    ps, ks = xls2gslib(path, header=0, cols='0, 1, 2, 4, 3')
    ps.save(pout)
    kout = '/home/julio/Testes/test/snirh_keys.txt'
    ks.to_csv(kout, sep='\t', index_label='ID')
    print 'done'
