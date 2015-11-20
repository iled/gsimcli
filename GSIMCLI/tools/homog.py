# -*- coding: utf-8 -*-
"""
This module contains the functions that implement climate data detection and
homogenisation, as well as other directly related functions.

Created on 14 de Out de 2013

@author: julio
"""

from collections import namedtuple
import csv
import fnmatch
import glob
import itertools
import os
from random import shuffle

import numpy as np
import pandas as pd
import tools.grid as gr


_ntuple_stations = namedtuple('Stations', 'stations total')


def detect(grids, obs_file, rad=0, method='mean', prob=0.95, skewness=None,
           percentile=None, flag=True, save=False, outfile=None, header=True,
           optional_stats=None):
    """Try to detect and homogenise irregularities in data series, following
    the geostatistical simulation approach:

    A breakpoint is identified whenever the interval of a specified probability
    p (e.g., 0.95), centred in the local PDF, does not contain the observed
    (real) value of the candidate station. In practice, the local PDF's are
    provided by the histograms of simulated maps. Thus, this rule implies that
    if the observed (real) value lies below or above the predefined
    percentiles of the histogram, of a given instant in time, then it is not
    considered homogeneous. If irregularities are detected in a candidate
    series, the time series can be adjusted by replacing the inhomogeneous
    records with the mean, or median, of the PDF(s) calculated at the candidate
    station’s location for the inhomogeneous period(s). [1]_

    Parameters
    ----------
    grids : GridFiles object
        Instance of GridFiles type containing the geostatistical simulation
        results.
    obs_file : PointSet object or string
        Instance of PointSet type containing the observed values at the
        candidate station, or string with the full path to the PointSet file.
    rad : number, default 0
        Tolerance radius used to search for neighbour nodes, used to calculate
        the local pdf's.
    method : {'mean', 'median', 'skewness', 'percentile'} string, default
        'mean'
        Method for the inhomogeneities correction:
            - mean: replace detected irregularities with the mean of simulated
                values;
            - median: replace detected irregularities with the median of
                simulated values;
            - skewness: use the sample skewness to decide whether detected
                irregularities will be replaced by the mean or by the median of
                simulated values.
            - percentile : replace detected irregularities with the percentile
                `100 * (1 - p)`, for a given `p`.
    prob : float, default 0.95
        Probability value to build the detection interval centred in the local
        PDF.
    skewness: float, optional
        Samples skewness threshold, used if `method == 'skewness'`, e.g., 1.5.
    percentile: float, optional
        p value used if correct_method == 'percentile'.
    flag : boolean, default True
        DEPRECATED
    save : boolean, default False
        Save intermediary PointSet files, one containing the homogenised values
        and the other containing simulated values at the candidate station
        location.
    outfile : string, optional
        Full path where the homogenised values will be saved if `save` is True.
        Simulated values at the candidates stations are saved in the directory
        used to store the simulated maps.
    header : boolean, default True
        True if `obs_file` has the GSLIB standard header lines. The resulting
        `homogenised` PointSet will follow.
    optional_stats : dict, optional
        Calculate and append additional statistics to the homogenised PointSet.
        This dict will overwrite the arguments passed to grids.stats_area. It
        may have one or more optional keys:
            - lmean: mean;
            - lmed: median;
            - lskew: skewness;
            - lvar: variance;
            - lstd: standard deviation;
            - lcoefvar: coefficient of variation;
            - lperc: percentile of detection.
        Each key must have a boolean value.

    Returns
    -------
    homogenised : PointSet object
        Instance of PointSet type containing the homogenised values.
    detected_number : int
        Number of detected breakpoints.
    missing_data : int
        Number of missing data that were interpolated.

    Notes
    -----
    Observed and simulated data must be in the same temporal resolution (e.g.,
    monthly data). There is no down or upscale considered.

    Missing data will automatically be replaced according to the selected
    method, considering that its flag number (e.g., -999.9) is out of the
    variable distribution, thus being caught in the percentile' inequation.

    By default it creates a new column named 'Flag' with the following values:
        - if no homogenisation took place in that cell, Flag = no_data_value
        - otherwise, Flag = observed_value

    See Also
    --------
    grid.stats_area : Calculate some statistics among every realisation,
        considering a circular (and horizontal) area of a given radius around
        a given point.

    References
    ----------
    .. [1] Costa, A., & Soares, A. (2009). Homogenization of climate data
        review and new perspectives using geostatistics. Mathematical
        Geosciences, 41(3), 291–305. doi:10.1007/s11004-008-9203-3

    """
    # required statistics according to the selected correction method
    if method == 'mean':
        lmean = True
        lmed = False
        lskew = False
    elif method == 'median':
        lmean = False
        lmed = True
        lskew = False
    elif method == 'skewness' and skewness:
        lmean = True
        lmed = True
        lskew = True
    elif method == 'percentile':
        lmean = False
        lmed = False
        lskew = False
    else:
        raise ValueError('Method {} invalid or incomplete.'.format(method))

    selected_stats = {
        'lmean': lmean,
        'lmed': lmed,
        'lskew': lskew,
    }

    # update the selected statistics according to the optional ones
    if optional_stats:
        selected_stats.update(optional_stats)

    # FIXME: lmean must always be True in order to fill missing data
    selected_stats['lmean'] = True
    selected_stats['lperc'] = True  # always required for the detection

    if isinstance(obs_file, gr.PointSet):
        obs = obs_file
    else:
        obs = gr.PointSet()
        obs.load(obs_file, header)

    obs_xy = list(obs.values.loc[obs.values.first_valid_index(), ['x', 'y']])
    # calculate local stats and fetch inner dataframe
    local_stats = grids.stats_area(obs_xy, rad, p=prob, save=save,
                                   **selected_stats).values

    # remove lines with no-data and flags
    if 'Flag' in obs.values.columns:
        obs.values = obs.values.drop('Flag', axis=1)
    if 'Flag' in obs.varnames:
            obs.varnames.remove('Flag')
            obs.nvars -= 1
    # calculate the no-data's and replace them with NaN
    nodatas = obs.values['clim'].isin([obs.nodata]).sum()
    obs.values = obs.values.replace(obs.nodata, np.nan)

    # mean values
    meanvalues = pd.Series(local_stats['mean'].values, name='clim')

    # find and fill missing values with the mean values
    fn = 0
    if obs.values.shape[0] < grids.dz:
        obs, fn = fill_station(obs, meanvalues, grids.zi, grids.zi + grids.dz,
                               grids.cellz, header)

    # replace NaN's with the mean values
    meanvalues.index = obs.values.index
    obs.values.update(meanvalues, overwrite=False)

    # detect irregularities
    hom_where = ~obs.values['clim'].between(local_stats['lperc'],
                                            local_stats['rperc'])
    detected_number = hom_where.sum()  # + fn

    # homogenise irregularities
    homogenised = gr.PointSet(obs.name + '_homogenised', obs.nodata, obs.nvars,
                              list(obs.varnames), obs.values.copy())
    # remove columns that are placeholders for optional statistics
    homogenised.values.dropna(axis=1, inplace=True)
    homogenised.varnames = list(homogenised.values.columns)

    if method == 'mean':
        fixvalues = local_stats['mean'].values
    elif method == 'median':
        fixvalues = local_stats['median'].values
    elif method == 'skewness' and skewness:
        fixvalues = np.where(local_stats['skewness'] > skewness,
                             local_stats['median'], local_stats['mean'])
    elif method == 'percentile':
        # allow a different percentile value for the detection and for the
        # correction
        if percentile != prob:
            grids.reset_read()
            vline_perc = grids.stats_area(obs_xy, rad, lperc=True,
                                          p=percentile, save=False).values
        else:
            vline_perc = local_stats

        fixvalues = np.where(obs.values['clim'] > local_stats['rperc'],
                             vline_perc['rperc'], vline_perc['lperc'])

    homogenised.values['clim'] = obs.values['clim'].where(~hom_where,
                                                          fixvalues)
    if flag:
        flag_col = obs.values['clim'].where(hom_where, obs.nodata)
        homogenised.add_var(flag_col, 'Flag')

    # append the additional statistics required by the user, if any
    # first, map the local_stats keys and their names in the PointSet dataframe
    stats_names = {
        'lmean': 'mean',
        'lmed': 'median',
        'lskew': 'skewness',
        'lvar': 'variance',
        'lstd': 'std',
        'lcoefvar': 'coefvar',
        'lperc': 'lperc',  # rperc
    }
    # second, add each corresponding column to the homogenised PointSet
    if optional_stats:
        for key, value in optional_stats.iteritems():
            if value and key == 'lperc':
                # median required to find which percentile is closer
                if 'median' in local_stats.columns:
                    med = local_stats['median']
                else:
                    med = grids.stats_area(obs_xy, rad, lmed=True,
                                           save=False).values['median']
                percentiles = np.where(
                    obs.values['clim'] >= med, local_stats['rperc'],
                    local_stats['lperc'])
                homogenised.add_var(varname='pdet', values=percentiles)
            elif value:
                varname = stats_names[key]
                homogenised.add_var(varname=varname,
                                    values=local_stats[varname].values)

    if save and outfile:
        homogenised.save(outfile, header)

    missing_data = fn + nodatas

    return homogenised, detected_number, missing_data


def fill_station(pset_file, values, time_min, time_max, time_step=1,
                 header=True):
    """Look for missing values in a station and fill them with a given value.

    There is the need to check for this because the time series might be
    incomplete, e.g., considering the annual series, [1900, 1901, 1905, 1906,
    1907, 1908, 1910], there are four missing values.

    Parameters
    ----------
    pset_file : PointSet object or string
        Instance of PointSet containing the target station, or string with the
        full path to the PointSet file.
    values : array_like
        Set of values which will be used to fill the target time series. Must
        have a length equal to the number of items in the time series.
    time_min : number
        First value in the desired time series.
    time_max : number
        Last value in the desired time series.
    time_step : number, default 1
        Space between the time series values
    header : boolean, default True
        True if `pset_file` has the GSLIB standard header lines.

    Returns
    -------
    pset : PointSet object
        Instance of PointSet containing the filled station, with no missing
        values in its time series.
    filled_count : int
        Number of detected missing values.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header=header)

    varcol = pset.varnames.index('clim')
    filled_count = 0
    j = 0
    timeserie = np.arange(time_min, time_max, time_step)
    filled = np.zeros((timeserie.shape[0], pset.values.shape[1]))
    for i, itime in enumerate(timeserie):
        if (j < len(pset.values['time']) and
                itime == pset.values['time'].iloc[j]):
            filled[i, :] = pset.values.iloc[j, :]
            j += 1
        else:
            filled[i, :] = [pset.values.iloc[0, 0], pset.values.iloc[0, 1],
                            itime, pset.values.iloc[0, 3:varcol], values[i],
                            ][:pset.values.shape[1]]
            filled_count += 1

    pset.values = pd.DataFrame(filled, columns=pset.values.columns)

    return pset, filled_count


def list_stations(pset_file, header=True, variables=None):
    """List all the stations in one PointSet file.

    A PointSet file can contain stations belonging to different networks. This
    functions does not distinguish networks, so two stations with the same ID
    but in different networks will be reported as being the same.

    Parameters
    ----------
    pset_file:  PointSet object or string
        Instance of PointSet or string with the full path to the PointSet file.
    header : boolean, default True
        True if `pset_file` has the GSLIB standard header lines.
    variables : list of string, optional
        Mandatory variable names for GSIMCLI process (e.g.,
        ['x', 'y', 'time', 'station', 'clim']).

    Returns
    -------
    stations_list : list of int
        List with the ID numbers of the stations contained in `pset_file`.

    See Also
    --------
    list_networks_stations: List all the stations in a list of networks.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header=header)

    if variables:
        pset.flush_varnames(variables)

    # FIXME: .station wont work if the columns order is previously changed
    stations = np.unique(pset.values.station)
    stations_list = map(int, stations)

    return stations_list


def list_networks_stations(networks, variables, secdir=None, header=True,
                           nvars=None, exts=["*.txt", "*.prn"]):
    """List all the stations in a list of networks. It does so by trying to
    find a point-set file for each network.

    Parameters
    ----------
    networks : list of string
        List with the networks' directories.
    variables : list of string
        Mandatory variable names for GSIMCLI process (e.g.,
        ['x', 'y', 'time', 'station', 'clim']).
    secdir : string, optional
        Relative path to each network directory where point-set files are
        located. wildcards accepted. For data splitted in decades, use
        secdir='dec*'.
    header : boolean, default True
        True if the expected file has the GSLIB standard header lines.
    nvars : int, optional
        Miniumum expected number of variables. For point-set files acceptable
        as GSIMCLI process data files, use nvars=5.
    exts : list of string, default ["*.txt", "*.prn"]
        List of acceptable file extensions.

    Returns
    -------


    See Also
    --------
    list_stations : List all the stations in one PointSet file.
    find_pset_file : Find a point-set file in a given directory tree.

    """

    stations = dict()
    total = 0
    for network in networks:
        if secdir:
            directory = os.path.join(
                network, glob.glob(os.path.join(network, secdir))[0])
        else:
            directory = network
        pset_path = find_pset_file(directory, header, nvars, exts)

        if pset_path:
            pset = gr.PointSet(psetpath=pset_path)
            pset.flush_varnames(variables)
            ids = list_stations(pset, header)
            total += len(ids)
        else:
            ids = str()

        stations[os.path.basename(network)] = ids

    return _ntuple_stations(stations, total)


def take_candidate(pset_file, station, header=True, save=False, path=None):
    """Remove a station from a PointSet file and store its points in another
    file, and the remainder stations (neighbours) in a different file.

    The first PointSet will be used as a candidate station, and the others will
    serve as references in the homogenisation process.

    Parameters
    ----------
    pset_file : PointSet object or string
        Instance of PointSet or string with the full path to the PointSet file.
    station : number
        ID number of the station to be removed.
    header : boolean, default True
        True if `pset_file` has the GSLIB standard header lines.
    save : boolean, default True
        If True it will save both generated PointSet files in location `path`.
    path : string, optional
        Path to the directory where both PointSet files are to be saved.

    Returns
    -------
    candidate_pset : PointSet object
        Instance of PointSet containing only the points that belong to the
        given `station`.
    neighbours_pset : PointSet object
        Instance of PointSet containing the remaining points.

    Notes
    -----
    Drops the flag column from the resulting PointSets.

    .. TODO:: keep format while saving the PointSet's

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header=header)

    candidate = pset.values[pset.values['station'] == int(station)]
    neighbours = pset.values[pset.values['station'] != int(station)]

    # remove existing optional columns
    drop_vars = ['Flag', 'mean', 'median', 'std', 'pdet', 'variance',
                 'coefvar', 'skewness']
    candidate = candidate.drop(drop_vars, axis=1, errors='ignore')
    neighbours = neighbours.drop(drop_vars, axis=1, errors='ignore')
    nvars = candidate.shape[1]
    varnames = list(candidate.columns)

    candidate_pset = gr.PointSet('Candidate_' + str(station), pset.nodata,
                                 nvars, varnames, candidate)
    neighbours_pset = gr.PointSet('References_' + str(station), pset.nodata,
                                  nvars, varnames, neighbours)

    if save and path:
        base, ext = os.path.splitext(path)
        candidate_pset.save(base + '_candidate' + ext, header)
        neighbours_pset.save(base + '_neighbours' + ext, header)

    return candidate_pset, neighbours_pset


def update_station(stations_pset, station, header=True):
    """Update a station in an existing PointSet.

    This is necessary to update already homogenised stations in the
    iterative homogenising process.

    Parameters
    ----------
    stations_pset : PointSet object or string
        Instance of PointSet or string with the full path to the PointSet file
        that will be updated with data on the `station` PointSet.
    station : PointSet object
        Instance of PointSet that will update the `stations_pset` PointSet.
    header : boolean, default True
        True if `stations_pset` has the GSLIB standard header lines.

    Returns
    -------
    pset : PointSet object
        Instance of PointSet containing the updated stations.

    """
    if isinstance(stations_pset, gr.PointSet):
        pset = stations_pset
    else:
        pset = gr.PointSet()
        pset.load(stations_pset, header)

    # make sure both PointSet's have the same variables, if not find missing
    if sorted(pset.varnames) != sorted(station.varnames):
        missing_vars = list(set(station.varnames) - set(pset.varnames))
    else:
        missing_vars = []
    # fill the missing variables with NaN's
    for var in missing_vars:
        pset.add_var(np.repeat(np.nan, pset.values.shape[0]), var)
    # update the rows of the stations PointSet
    pset.values.update(station.values)
    return pset


def station_order(method, pset_file=None, nd=-999.9, header=True,
                  userset=None, ascending=False, md_last=True):
    """Sort the stations contained in a given PointSet.

    Parameters
    ----------
    method : {'random', 'sorted', 'variance', 'network deviation', 'user'}
        - random: all stations randomly sorted;
        - sorted: sorts all stations in ascending or descending order;
        - variance: sorts all stations by greater or lower variance;
        - network deviation: sorts all stations in ascending  or descending
            order according to the difference between the station average and
            the network average;
        - user: the user specifies which stations and their order.
    pset_file : PointSet object or string, optional
        Instance of PointSet or string with the full path to the PointSet file.
        Required if `method` is not 'user'.
    nd : number, default -999.9
        Value representing missing data.
    header : boolean, default True
        True if `pset_file` has the GSLIB standard header lines.
    userset : list, optional
        List with the stations ID numbers in the desired order.
    ascending : boolean, default True
        Sort in ascending or descending order.
    md_last : boolean, default True
        Put missing data at the beginning or the end.

    Returns
    -------
    stations_list : list
        Stations ID numbers sorted according to the selected `method`.

    """
    if pset_file:
        if isinstance(pset_file, gr.PointSet):
            pset = pset_file
        else:
            pset = gr.PointSet(psetpath=pset_file, nodata=nd, header=header)

    stations_list = list_stations(pset, header=header)

    if method == 'random':
        shuffle(stations_list)

    elif method == 'sorted':
        stations_list.sort(reverse=not ascending)

    elif method == 'variance':
        if not pset_file:
            raise TypeError('Method variance requires the stations point-set')
        values = pset.values.replace(nd, np.nan)
        varsort = values.groupby('station', sort=False).clim.var()
        varsort = varsort.order(ascending=ascending, na_last=md_last)
        stations_list = list(varsort.index)

    elif method == 'network deviation':
        values = pset.values.replace(nd, np.nan)
        stations_mean = values.groupby('station', sort=False).clim.mean()
        network_dev = ((stations_mean - values.clim.mean()).abs()
                       .order(ascending=ascending, na_last=md_last))
        stations_list = list(network_dev.index)

    elif method == 'user' and userset:
        stations_list = userset
    else:
        raise TypeError('Method {} not understood or invalid userset ({}).'
                        .format(method, userset))

    return stations_list


def save_output(pset_file, outfile, fformat='gsimcli', outvars=None,
                header=True, network_split=True, save_stations=False,
                keys=None, append_year=False):
    """Write homogenisation results to given format.

    Parameters
    ----------
    pset_file : PointSet object or string
        Instance of PointSet or string with the full path to the PointSet file
        containing the homogenised data.
    outfile : string
        File path
    fformat : {'gsimcli', 'normal', 'gslib', 'cost-home'}
        File type and contents format:
            - gsimcli: CSV file with columns YEAR | MONTH | ID_DATA | ID_FLAG
            - normal: CSV file, all the variables in the file are written in
              their existing order
            - gslib: GSLIB standard with header, useful for visualisation
            - cost-home: COST-HOME format, prepare results to the benchmark
              process
    outvars : array_like of int, optional
        Only save certain columns. Only used if `fformat == 'normal'`.
    header : boolean, default True
        True if `pset_file` has the GSLIB standard header lines.
    network_split : boolean, default True
        Save different networks in different files. Only used if `fformat ==
        'gslib'`.
    save_stations : boolean, default False
        Write a CSV file with the stations ID numbers and its coordinates.
    keys : string, optional
        Path to a TSV file containing the keys to the corresponding station
        ID numbers.
    append_year : boolean, default False
        Add an extra column containing the year. Might be useful for non annual
        time series.

    See Also
    --------
    merge_output : merge several files generated by `save_output` with
        `fformat == 'gsimcli'`.

    TODO:
        - checkar
        - cost-home format

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header)

    if fformat == 'normal':
        with open(outfile, 'wb') as csvfile:
            out = csv.writer(csvfile, dialect='excel')
            if not outvars:
                out.writerow(pset.varnames)
                out.writerows(pset.values)
            else:
                out.writerow([pset.varnames[i] for i in outvars])
                out.writerows(pset.values.iloc[:, np.array(outvars)])

    elif fformat == 'gsimcli':
        # year, time (month)
        # csvheader = ['time']  # not being used
        # year, time (month), stationID_VAR, stationID_FLAG, optional_stats
        stations = list_stations(pset, header)
        # varname = pset.varnames[-2]  # code smell: what if using optional cols
#         headerline = [[str(stations[i]) + '_' + varname,
#                        str(stations[i]) + '_FLAG']
#                       for i in xrange(len(stations))]
        # csvheader += itertools.chain.from_iterable(headerline)
        # outvars deduced from varnames in excess of x, y, time, station
        outvars = ['clim', 'Flag']
        outvars += sorted(set(pset_file.varnames)
                          - set(['x', 'y', 'time', 'station', 'clim', 'Flag']))
        csvheader = [str(stations[i]) + '_' + varname
                     for i in xrange(len(stations)) for varname in outvars]

        outdf = pd.DataFrame(index=np.arange(pset.values['time'].min(),
                                             pset.values['time'].max()
                                             + 1),
                             columns=csvheader)  # [1:])

        for i in xrange(len(stations)):
            stations_bool = pset.values['station'] == stations[i]
            tempdf = pset.values[stations_bool][outvars]  # ['time', 'clim', 'Flag']]
            # tempdf = pd.DataFrame(temp[['clim', 'Flag']])
            tempdf.index = pset.values[stations_bool]['time']
            nvars = len(outvars)
            tempdf.columns = csvheader[nvars * i:nvars * (i + 1)]
            outdf.update(tempdf)

        if append_year:  # TODO: perhaps for monthly data
            raise NotImplementedError
            years = 0
            outdf.insert(0, 'year', years)

        # remove empty columns -- optional stats for stations that were not
        # homogenised
        outdf.dropna(axis=1, how='all', inplace=True)

        outdf.to_csv(outfile, index_label='year')  # code smell: only yearly?

    elif fformat.lower() == 'gslib':
        if network_split and 'network' in pset.varnames:
            networks = pset.values['network'].unique()
            temp_varnames = pset.varnames[:]
            temp_varnames.remove('network')
            for nw in networks:
                temp = gr.PointSet(name=pset.name + ' network: ' + str(nw),
                                   nodata=pset.nodata, nvars=pset.nvars - 1,
                                   varnames=temp_varnames)
                outfile = (os.path.splitext(outfile)[0] + '_' + str(nw) +
                           os.path.splitext(outfile)[1])
                temp.values = pset.values[pset.values['network'] == nw]
                temp.save(outfile, header=True)
        else:
            pset.save(outfile, header=True)

    if save_stations:
        stations = list_stations(pset, header)
        stations_out = os.path.join(os.path.dirname(outfile),
                                    os.path.splitext(os.path.basename(outfile))
                                    [0] + '_stations.csv')
        stationsdf = pd.DataFrame(index=stations, columns=['x', 'y'])

        for i, st in enumerate(stations):
            temp = pset.values[pset.values['station'] == st]
            stationsdf.iloc[i] = temp.loc[temp.first_valid_index(), ['x', 'y']]
        if keys:
            keysdf = pd.read_csv(keys, sep='\t', index_col=0)

            stationsdf = stationsdf.join(keysdf)

        stationsdf.to_csv(stations_out, index_label='Station')


def merge_output(results, path, homog_order=False):
    """Merge the GSIMCLI output into one single spreadsheet file.

    Each result file goes to one different sheet.
    Two more sheets are added: one with the complete data set, another with
    a summary of the process.

    Parameters
    ----------
    results : list or tuple of lists
        Each one must have {string, list, list, list}:
            - path to the result file generated by `save_output`
            - stations homogenisation order
            - number of detections per candidate station
            - number of filled missing data per candidate station
    path : string
        Path to the merged output file.
    homog_order: boolean, default False
        Sort columns according to the stations homogenisation order.

    .. TODO::
        - check what if labels_i are not previously sorted
        - needs refactoring (summary out, results in)

    """
    merged = pd.ExcelWriter(path)
    groups = list()
    alldf = pd.DataFrame()
    summary = pd.DataFrame()

    for result in results:
        outfile, st_order, detected_n, filled_n = result
        group = os.path.basename(outfile).split('_')[0]
        groups.append(group)

        df = pd.DataFrame.from_csv(outfile)
        alldf = alldf.append(df)

        labels_i = list(df.columns)
        if homog_order:
            clim = '_' + labels_i[0].split('_')[1]
            flag = '_' + labels_i[1].split('_')[1]
            labels_sort = list(itertools.chain.from_iterable
                               ([[str(int(k)) + clim, str(int(k)) + flag]
                                 for k in st_order]))
        else:
            labels_sort = labels_i
        df = df.reindex_axis(labels_sort, axis=1)
        df.columns = list(labels_sort)
        df.to_excel(merged, group, merge_cells=False)

        summary = summary.append([st_order, detected_n, filled_n],
                                 ignore_index=True)

    alldf = alldf.reindex_axis(list(labels_i), axis=1)
    colidx = (pd.MultiIndex.from_tuples
              ([(group, key) for group in groups for key in
                ['Stations ID order', 'Detections number', 'Missing data']],
               names=['Decade', '']))
    summary = pd.DataFrame(summary.values, index=colidx)
    alldf.to_excel(merged, 'All stations', index_label='year',
                   merge_cells=False)
    summary.to_excel(merged, 'Summary', header=range(1, len(st_order) + 1),
                     merge_cells=False)
    merged.save()


def ask_add_header(pset):
    """Ask for the header when a PointSet does not have one.

    Parameters
    ----------
    pset : PointSet object

    Returns
    -------
    pset : PointSet object

    .. TODO:: . refactor to another module or deprecate
    """
    print 'Insert the point-set header metadata'
    pset.name = raw_input('Point-set name: ')
    for i in xrange(pset.nvars):
        pset.varnames[i] = (raw_input('Variable {} name: '.format(i + 1)).
                            strip())
    return pset


def clean_leftovers(tree, maps=True, pars=True, trn=True, dbg=True, cands=True,
                    refs=True, homogenised=True):
    """Permanently remove from the filesystem all secondary files generated in
    the GSIMCLI process in a given directory tree.

    Parameters
    ----------
    tree : string
        Path containing the target files.
    maps : boolean, default True
        Remove simulated maps (\*.out).
    pars : boolean, default True
        Remove simulation parameters (\*.par).
    trn : boolean, default True
        Remove simulation cluster transform (\*.trn).
    dbg : boolean, default True
        Remove simulation debug (\*.dbg).
    cands : boolean, default True
        Remove candidate stations (\*candidate\*.prn).
    refs : boolean, default True
        Remove reference stations \*references\*.prn).
    homogenised : boolean, default True
        Remove homogenised stations (\*homogenised\*.prn).

    Notes
    -----
    Also remove the file 'dsscmd.txt' if it exists.

    """
    plate = list()
    if maps:
        plate.append('*.out')
    if pars:
        plate.append('*.par')
    if trn:
        plate.append('*.trn')
    if dbg:
        plate.append('*.dbg')
    if cands:
        plate.append('*candidate*.prn')
    if refs:
        plate.append('*references*.prn')
    if homogenised:
        plate.append('*homogenised*.prn')

    plate.append('dsscmd.txt')

    for root, dirnames, filenames in os.walk(tree):  # @UnusedVariable
        for basename in filenames:
            for leftover in plate:
                if fnmatch.fnmatch(basename, leftover):
                    os.remove(os.path.join(root, basename))


def find_pset_file(directory, header=True, nvars=None,
                   exts=["*.txt", "*.prn"]):
    """Find a point-set file in a given directory tree.

    Parameters
    ----------
    directory : string
        Path to the directory where to find a point-set file.
    header : boolean, default True
        True if the expected file has the GSLIB standard header lines.
    nvars : int, optional
        Miniumum expected number of variables. For point-set files acceptable
        as GSIMCLI process data files, use nvars=5.
    exts : list of string, default ["*.txt", "*.prn"]
        List of acceptable file extensions.

    Returns
    -------
    filename : string
        Full path to the first point-set file that was found, which matches
        the given criteria (extension, header and number of variables).

    """
    for ext in exts:
        for name in glob.iglob(os.path.join(directory, ext)):
            try:
                filename = os.path.join(directory, name)
                pset = gr.PointSet(psetpath=filename, header=header)
                if nvars and pset.nvars >= nvars:
                    return filename
            except ValueError:
                continue


def read_specfile(file_path):
    """Read a CSV file containing grid specifications: number of nodes, origin
    coordinates and nodes sizes (x and y axis).

    Parameters
    ----------
    file_path : string
        Full path to the CSV file.

    Returns
    -------
    grid : pandas.DataFrame
        DataFrame containing the grid specifications: xnodes, ynodes, xmin,
        ymin, xmax, ymax, xsize, ysize.

    """
    grid = pd.read_csv(file_path)
    # make case insensitive
    grid.rename(columns=lambda x: x.lower(), inplace=True)
    # check specs
    specs = ['xnodes', 'ynodes', 'xmin', 'ymin', 'xmax', 'ymax',
             'xsize', 'ysize']
    if not all([spec in specs for spec in grid.columns]):
        raise ValueError('Missing or invalid grid specifications file')
    return grid


if __name__ == '__main__':
    macpath = '/Users/julio/Desktop/testes/cost-home/500_dflt_16_allvar_vind/'
    mintpath = '/home/julio/Testes/cost-home/500_dflt_16_allvar_vintermedia/'
    basepath = macpath

    netw_pset = '/Users/julio/Desktop/testes/cost-home/rede000009/dec_sgems_rede9/dec1900_1909_rede9.txt'
    # """
    results = [(basepath + 'rede000010/1900-1909/1900-1909_homogenized_data.csv', [3.0, 7.0, 2.0, 5.0, 1.0, 4.0, 6.0, 8.0, 9.0], [0, 0, 0, 1, 0, 0, 0, 1, 0], [0, 5, 0, 0, 10, 10, 10, 9, 10]),
               (basepath + 'rede000010/1910-1919/1910-1919_homogenized_data.csv', [8.0, 2.0, 3.0, 7.0, 9.0, 4.0, 5.0, 1.0, 6.0], [2, 1, 2, 0, 0, 0, 4, 0, 0], [0, 0, 0, 0, 3, 7, 0, 10, 10]),
               (basepath + 'rede000010/1920-1929/1920-1929_homogenized_data.csv', [2.0, 5.0, 8.0, 6.0, 3.0, 7.0, 9.0, 4.0, 1.0], [0, 3, 2, 4, 0, 0, 0, 0, 3], [0, 0, 0, 1, 0, 0, 0, 0, 5]),
               (basepath + 'rede000010/1930-1939/1930-1939_homogenized_data.csv', [6.0, 8.0, 4.0, 2.0, 3.0, 7.0, 9.0, 5.0, 1.0], [0, 1, 1, 0, 0, 0, 0, 0, 2], [0, 0, 0, 0, 0, 0, 0, 0, 0]),
               (basepath + 'rede000010/1940-1949/1940-1949_homogenized_data.csv', [9.0, 6.0, 2.0, 8.0, 5.0, 3.0, 1.0, 7.0, 4.0], [1, 1, 1, 4, 0, 0, 2, 0, 1], [0, 0, 1, 0, 0, 1, 0, 5, 1]),
               (basepath + 'rede000010/1950-1959/1950-1959_homogenized_data.csv', [9.0, 2.0, 8.0, 6.0, 5.0, 7.0, 3.0, 1.0, 4.0], [2, 2, 4, 0, 1, 0, 0, 5, 6], [0, 0, 0, 0, 0, 0, 0, 0, 0]),
               (basepath + 'rede000010/1960-1969/1960-1969_homogenized_data.csv', [6.0, 9.0, 2.0, 8.0, 3.0, 7.0, 5.0, 1.0, 4.0], [1, 2, 1, 1, 0, 0, 0, 1, 4], [0, 0, 0, 0, 0, 0, 0, 0, 0]),
               (basepath + 'rede000010/1970-1979/1970-1979_homogenized_data.csv', [6.0, 2.0, 4.0, 8.0, 9.0, 5.0, 7.0, 3.0, 1.0], [1, 1, 2, 1, 3, 0, 0, 0, 3], [0, 0, 0, 0, 0, 0, 0, 0, 0]),
               (basepath + 'rede000010/1980-1989/1980-1989_homogenized_data.csv', [9.0, 7.0, 6.0, 3.0, 8.0, 1.0, 4.0, 5.0, 2.0], [1, 0, 0, 0, 1, 5, 0, 0, 1], [0, 0, 0, 0, 0, 0, 0, 0, 0]),
               (basepath + 'rede000010/1990-1999/1990-1999_homogenized_data.csv', [8.0, 2.0, 1.0, 6.0, 4.0, 9.0, 7.0, 3.0, 5.0], [4, 2, 2, 1, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0])]
    path = basepath + 'rede000010/gsimcli_results.xls'
    # merge_output(results, path)
    # """
    # clean_leftovers(delme, pars=False)
    print 'done'
