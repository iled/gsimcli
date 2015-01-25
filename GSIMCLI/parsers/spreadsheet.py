# -*- coding: utf-8 -*-
"""
This module handles different spreadsheet-like files (e.g., CSV, TSV, XLS) and
parses them into other needed formats (e.g., GSLIB, COST-HOME).

Created on 5 de Nov de 2013

@author: julio
"""

import os

import numpy as np
import pandas as pd
import tools.grid as grd
import tools.utils as ut


def dtype_filter(dataf, nodata=-999.9):
    """Filter dtypes from a pandas DataFrame, converting non-numbers into a
    keyed index. Columns with non-numeric values are selected through their
    first row value.

    Missing or no-data values also count as a unique key.
    Return the DataFrame with the new values and a DataFrame with its keys.

    Parameters
    ----------
    dataf : pandas.DataFrame
        Input DataFrame with some column with non-numeric values.
    nodata : number, default -999.9
        Missing data value.

    Returns
    -------
    dataf : pandas.DataFrame
        Output DataFrame with no non-numeric values.
    keys : dict
        Dictionary with the matching key for each converted value.

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

    Parameters
    ----------
    xlspath : string
        File path.
    nd : number, default -999.9
        Missing data value.
    cols : array_like, optional
        Which columns to select, with 0 being the first. The given order is
        preserved, for example, `cols = (1, 4, 2)` will select the 2nd column,
        then the 5th, and lastly the 3rd. The default, None, results in all
        columns being selected.
    sheet : string or int, default 0
        Name of Excel sheet or the page number of the sheet.
    header : int, default 0
        Row to use for the column labels of the parsed DataFrame.
    skip_rows : array_like, optional
        Rows to skip at the file beginning (0-indexed).
    filter_dtype : boolean, default True
        Convert columns with non-numeric values to numeric.

    Returns
    -------
    pset : PointSet object
        Instance of PointSet with the parsed XLS file.
    keys : dict
        Dictionary with the matching key for each converted value. If
        `filter_dtype` is False, returns None.

    See Also
    --------
    dtype_filter : filter non-numeric data types.

    Notes
    -----
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


def xls2costhome(xlspath, outpath=None, no_data=-999.9, sheet=None,
                 header=None, skip_rows=None, cols=None, network_id='ssssssss',
                 status='xx', variable='vv', resolution='r', content='c',
                 ftype='data', yearly_sum=False, keys_path=None, **kwargs):
    """Convert a file in GSIMCLI format (XLS with a particular structure) to a
    network of the COST-HOME format.

    DEPRECATED

    Parameters
    ----------
    xlspath : string
        File path.
    outpath : string, optional
        Folder path to save the converted network.
    no_data : number, default -999.9
        Missing data value.
    sheet : string or int, optional
        Name of Excel sheet or the page number of the sheet.
    header : int, optional
        Row to use for the column labels of the parsed DataFrame.
    skip_rows : array_like, optional
        Rows to skip at the file beginning (0-indexed).
    cols : int or list, defaul None
        - If None then parse all columns
        - If int then indicates last column to be parsed
        - If list of ints then indicates list of column numbers to be parsed
        - If string then indicates comma separated list of column names and
            column ranges (e.g. “A:E” or “A,C,E:F”)
    network_id : string, optional
        Network ID number to write (only for naming purposes).
    status : string, optional (only for naming purposes).
        Data status.
    variable : string, optional (only for naming purposes).
        Variables names.
    resolution : string, optional (only for naming purposes).
        Time series resolution.
    content : string, optional
        Data content type.
    ftype : string, optional
        File type.
    yearly_sum : boolean, default False
        Convert yearly summed data into monthly average.
    keys_path : string, optional
        Path to the file containing the keys which converted the stations IDs.

    Returns
    -------
    network : Network object
        Instance of Network which contains all the stations in the given file.

    Notes
    -----
    Does not work with CSV files.

    """
    import parsers.costhome as ch  # import here to avoid recursive dependence

    if yearly_sum:
        div = 12.0
    else:
        div = 1.0

    xlsfile = pd.ExcelFile(xlspath)
    xlstable = xlsfile.parse(sheetname=sheet, header=header, na_values=no_data,
                             skiprows=skip_rows, parse_cols=cols, index_col=0)

    network = ch.Network(no_data=no_data, network_id=network_id)
    stations = [label for label in xlstable.columns if '_clim' in label]

    if keys_path is not None and os.path.isfile(keys_path):
        keys = read_keys(keys_path)
        # station.id = keys.loc[station.id]
        # self.stations_id[i] = station.id

    for station in stations:
        st = ch.Station(no_data=no_data)
        st.path = None
        st.network_id = network_id
        st.ftype = ftype
        st.status = status
        st.variable = variable
        st.resolution = resolution
        stid = station.split('_')[0]
        if keys_path and os.path.isfile(keys_path):
            st.id = str(keys.loc[int(stid)].values[0])
        else:
            st.id = stid
        st.content = content
        st.data = xlstable[station] / div
        network.add(st)

    if outpath:
        network.save(outpath)

    return network


def read_keys(path):
    """Read a TSV file with the keys to the converted station IDs.

    DEPRECATED

    Parameters
    ----------
    path : string
        File path.

    Returns
    -------
    keys : pandas.DataFrame

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
        xls2costhome(xlspath=path, outpath=os.path.dirname(path), no_data=-999.9,
                        sheet='All stations', header=False, skip_rows=[1],
                        network_id=netid, status='ho',
                        variable='rr', resolution='y', content='d',
                        ftype='data', yearly_sum=True)
    print 'done'
