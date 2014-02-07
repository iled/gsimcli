# -*- coding: utf-8 -*-
'''
Created on 14 de Out de 2013

@author: julio
'''

# import pandas as pd
import csv
import itertools
import os
from random import shuffle

import numpy as np
import pandas as pd
import tools.grid as gr
# import parsers.cost as cost


def detect(grids, obs_file, method='mean', prob=0.95, skewness=None,
           flag=True, save=False, outfile=None, header=True):
    """Tries to detect and homogenize irregularities in data series, following
    the geostatistical simulation approach:

    A breakpoint is identified whenever the interval of a specified probability
    p (e.g., 0.95), centered in the local pdf, does not contain the observed
    (real) value of the candidate station. In practice, the local pdfs are
    provided by the histograms of simulated maps. Thus, this rule implies that
    if the observed (real) value lies below or above the pre-defined
    percentiles of the histogram of a given instant in time then it is not
    considered homogeneous. If irregularities are detected in a candidate
    series, the time series can be adjusted by replacing the inhomogeneous
    records with the mean, or median, of the pdf(s) calculated at the candidate
    station’s location for the inhomogeneous period(s).
                                                        (Costa & Soares, 2009)

    Observed and simulated data must be in the same temporal resolution (e.g.,
    monthly data). There is no down or upscale considered.

    Missing data will automatically be replaced according to the selected
    method, considering its flag number (e.g., -999) is out of the variable
    distribution, thus being caught in the percentile' inequation.

    By default it creates a new column named 'Flag' with the following values:
        . if no homogenization took place in that cell, Flag = no_data_value
        . otherwise, Flag = observed_value

    """
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
    else:
        raise ValueError('Method {} invalid or incomplete.'.format(method))

    if isinstance(obs_file, gr.PointSet):
        obs = obs_file
    else:
        obs = gr.PointSet()
        obs.load(obs_file, header)

    obs_xy = list(obs.values.iloc[0, :2])
    # calculate stats
    vline_stats = grids.stats_vline(obs_xy, lmean, lmed, lskew, lperc=True,
                                    p=prob, save=save)

    # remove lines with no-data and flags
    if 'Flag' in obs.values.columns:
        obs.values = obs.values.drop('Flag', axis=1)
    if 'Flag' in obs.varnames:
            obs.varnames.remove('Flag')
            obs.nvars -= 1
    nodatas = obs.values['clim'].isin([obs.nodata]).sum()
    obs.values = obs.values.replace(obs.nodata, np.nan)
    meanvalues = pd.Series(vline_stats.values['mean'].values, name='clim',
                           index=obs.values.index)
    obs.values.update(meanvalues, overwrite=False)

    # find and fill missing values
    fn = 0
    if obs.values.shape[0] < grids.dz:
        obs, fn = fill_station(obs, meanvalues, grids.zi, grids.zi + grids.dz,
                               grids.cellz, header)

    # detect irregularities
    hom_where = ~obs.values['clim'].between(vline_stats.values['lperc'],
                                            vline_stats.values['rperc'])
    detected_number = hom_where.sum()  # + fn

    # homogenize irregularities
    homogenized = gr.PointSet(obs.name + '_homogenized', obs.nodata, obs.nvars,
                              list(obs.varnames), obs.values.copy())

    if method == 'skewness' and skewness:
        fixvalues = np.where(vline_stats.values['skewness'] > 1.5,
                             vline_stats.values['median'],
                             vline_stats.values['mean'])
    else:
        fixvalues = vline_stats.values['mean']

    homogenized.values['clim'] = obs.values['clim'].where(~hom_where,
                                                          fixvalues.values)
    if flag:
        flag_col = obs.values['clim'].where(hom_where, obs.nodata)
        homogenized.nvars += 1
        homogenized.varnames.append('Flag')
        homogenized.values['Flag'] = flag_col

    if save and outfile:
        homogenized.save(outfile, header)

    return homogenized, detected_number, fn + nodatas


def fill_station(pset_file, values, time_min, time_max, time_step=1,
                 header=True):
    """Look for missing data in a station and fill them with a given value.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header)

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


def list_stations(pset_file, h=True):
    """Lists all the stations in one point-set file.
    It doesn't distinguish networks.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header=h)

    stations = np.unique(pset.values.station)
    return map(int, stations)


def take_candidate(pset_file, station, h=True, save=False, path=None):
    """Remove a station from a point-set file and stores its points in another
    file, as well the remainder (neighbours) in yet another file.

    Drops the flag column from the resulting PointSets.

    TODO: manter a formatação ao guardar os point sets.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header=h)

    candidate = pset.values[pset.values['station'] == int(station)]
    neighbours = pset.values[pset.values['station'] != int(station)]

    if 'Flag' in candidate.columns:
        candidate = candidate.drop('Flag', axis=1)
        cand_nvars = pset.nvars - 1
        cand_varnames = list(candidate.columns)
    else:
        cand_nvars = pset.nvars
        cand_varnames = pset.varnames

    candidate_pset = gr.PointSet('Candidate_' + str(station), pset.nodata,
                                 cand_nvars, cand_varnames, candidate)
    neighbours_pset = gr.PointSet('References_' + str(station), pset.nodata,
                                  pset.nvars, pset.varnames, neighbours)

    if save and path:
        base, ext = os.path.splitext(path)
        candidate_pset.save(base + '_candidate' + ext, h)
        neighbours_pset.save(base + '_neighbours' + ext, h)

    return candidate_pset, neighbours_pset


def append_homog_station(pset_file, station, header=True):
    """Inserts a station in PointSet format into another pset in PointSet
    format. This is necessary to consider already homogenized stations in the
    iterative homogenizing process.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header)

    # checks if 'Flag' column already exists
    if 'Flag' not in pset.varnames:
        pset.varnames.append('Flag')
        pset.nvars += 1
        pset.values = (pset.values.join
                       (pd.Series(np.repeat(pset.nodata, pset.values.shape[0]),
                                  name='Flag')))
    elif pset.nvars != station.nvars:
        raise ValueError('PointSets {} and {} have different number of '
                         'variables.'.format(pset.name, station.name))

    pset.values = pset.values.append(station.values, ignore_index=True)
    return pset


def station_order(method, pset_path=None, nd=-999.9, header=True,
                  userset=None, ascending=False, md_last=True):
    """Sort a list containing stations numbers, according to the selected
    method, whether in ascending or descending order:
        - random: all stations randomly sorted;
        - sorted: sorts all stations in ascending or descending order;
        - variance: sorts all stations by greater or lower variance;
        - network deviation: sorts all stations in ascending  or descending
        order according to the difference between the station average and the
        network average;
        - user: the user specifies which stations and their order.

    """
    if pset_path:
        if isinstance(pset_path, gr.PointSet):
            pset = pset_path
        else:
            pset = gr.PointSet(psetpath=pset_path, nodata=nd, header=header)

    stations_list = list_stations(pset, h=header)

    if method == 'random':
        shuffle(stations_list)

    elif method == 'sorted':
        stations_list.sort(reverse=not ascending)

    elif method == 'variance':
        if not pset_path:
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


def save_output(pset_file, outfile, fformat='gsimcli', lvars=None, header=True,
                network_split=True, station_split=True, save_stations=False,
                keys=None, append_year=False):
    """
    Handles different options for saving results to files.

    fformat: file type and contents format
        - 'normal': *.csv -- all the variables in the file are written in
                    their existing order
        - 'gsimcli': *.csv -- YEAR | MONTH | ID_DATA | ID_FLAG
        - 'gslib': GSLIB standard with header, useful for visualization
        PLANNED:
        - 'cost': COST-HOME format, to export results to the benchmark

    TODO:
        .checkar
    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header)

    if fformat == 'normal':
        with open(outfile, 'wb') as csvfile:
            out = csv.writer(csvfile, dialect='excel')
            if not lvars:
                out.writerow(pset.varnames)
                out.writerows(pset.values)
            else:
                out.writerow([pset.varnames[i] for i in lvars])
                out.writerows(pset.values.iloc[:, np.array(lvars)])

    elif fformat == 'gsimcli':
        # year, time (month)
        csvheader = ['time']
        # year, time (month), stationID_VAR, stationID_FLAG
        st_col = pset.varnames.index('station')
        stations = list_stations(pset, st_col)
        varname = pset.varnames[-2]
        headerline = [[str(stations[i]) + '_' + varname,
                       str(stations[i]) + '_FLAG']
                      for i in xrange(len(stations))]
        csvheader += itertools.chain.from_iterable(headerline)
        outdf = pd.DataFrame(index=np.arange(pset.values['time'].min(),
                                             pset.values['time'].max()
                                             + 1),
                             columns=csvheader[1:])
        for i in xrange(len(stations)):
            temp = pset.values[pset.values['station'] == stations[i]
                               ][['time', 'clim', 'Flag']]
            tempdf = pd.DataFrame(temp[['clim', 'Flag']])
            tempdf.index = temp['time']
            tempdf.columns = csvheader[2 * i + 1:2 * i + 3]
            outdf.update(tempdf)
        if append_year:  # TODO: perhaps for monthly data
            raise NotImplementedError
            years = 0
            outdf.insert(0, 'year', years)
        outdf.to_csv(outfile, index_label='year')

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
        st_col = pset.varnames.index('station')
        stations = list_stations(pset, st_col)
        stations_out = os.path.join(os.path.dirname(outfile),
                                os.path.splitext(os.path.basename(outfile))
                                [0] + '_stations.csv')
        stationsdf = pd.DataFrame(index=stations, columns=['x', 'y'])

        for i, st in enumerate(stations):
            stationsdf.iloc[i] = pset.values[pset.values['station'] == st
                                             ].iloc[0, :2]
        if keys:
            keysdf = pd.read_csv(keys, sep='\t', index_col=0)

            stationsdf = stationsdf.join(keysdf)

        stationsdf.to_csv(stations_out, index_label='Station')


def merge_output(results, path, homog_order=False):
    """Merge the gsimcli output into one single spreadsheet file.
    Each result file goes to one different sheet.
    Two more sheets are added: one with the complete data set, another with
    a summary of the process.

    TODO: check what if labels_i are not previously sorted
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
        df.to_excel(merged, group)

        summary = summary.append([st_order, detected_n, filled_n],
                                 ignore_index=True)

    alldf = alldf.reindex_axis(list(labels_i), axis=1)
    colidx = (pd.MultiIndex.from_tuples
              ([(group, key) for group in groups for key in
                ['Stations ID order', 'Detections number', 'Missing data']],
               names=['Decade', '']))
    summary = pd.DataFrame(summary.values, index=colidx)
    alldf.to_excel(merged, 'All stations', index_label='year')
    summary.to_excel(merged, 'Summary', header=range(1, len(st_order) + 1))
    merged.save()


def ask_add_header(pset):
    """Ask for the header when a point-set does not have any."""
    print 'Insert the point-set header metadata'
    pset.name = raw_input('Point-set name: ')
    for i in xrange(pset.nvars):
        pset.varnames[i] = (raw_input('Variable {} name: '.format(i + 1)).
                            strip())
    return pset


if __name__ == '__main__':
    macpath = '/Users/julio/Desktop/testes/cost-home/500_dflt_16_allvar_vind/'
    mintpath = '/home/julio/Testes/cost-home/500_dflt_16_allvar_vintermedia/'
    basepath = mintpath

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
    merge_output(results, path)
    # """
    # print station_order('network deviation', netw_pset)
    print 'done'
