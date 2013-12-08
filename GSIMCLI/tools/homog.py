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
def detect(grids, obs_file, method='mean', prob=0.95, varcol=-1, skewness=None,
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
        raise ValueError('Method {} invalid.'.format(method))
    if isinstance(obs_file, gr.PointSet):
        obs = obs_file
    else:
        obs = gr.PointSet()
        obs.load(obs_file, header)

    obs_xy = obs.values[0, :2]
    # calculate stats
    """ # grid stats, more than 100 times slower that vline stats!
    avmed, per = grids.stats(lmean, lmed, lperc=True, p=prob)
    avmed_grid = gr.GridArr(name=method + 'map', dx=grids.dx, dy=grids.dy,
                            dz=grids.dz, xi=grids.xi, yi=grids.yi, zi=grids.zi,
                            cellx=grids.cellx, celly=grids.celly,
                            cellz=grids.cellz, val=avmed)
    per_grid_right = gr.GridArr(name='rpercentile map', dx=grids.dx,
                                dy=grids.dy, dz=grids.dz, xi=grids.xi,
                                yi=grids.yi, zi=grids.zi, cellx=grids.cellx,
                                celly=grids.celly, cellz=grids.cellz,
                                val=per[:, 0])
    per_grid_left = gr.GridArr(name='lpercentile map', dx=grids.dx,
                               dy=grids.dy, dz=grids.dz, xi=grids.xi,
                               yi=grids.yi, zi=grids.zi, cellx=grids.cellx,
                               celly=grids.celly, cellz=grids.cellz,
                               val=per[:, 1])
    avmed_vline = avmed_grid.drill(obs_xy)
    per_vline_right = per_grid_right.drill(obs_xy)
    per_vline_left = per_grid_left.drill(obs_xy)
    """
    vline_stats = grids.stats_vline(obs_xy, lmean, lmed, lskew, lperc=True,
                                    p=prob, save=save)

    # find and fill missing values
    fn = 0
    if obs.values.shape[0] < grids.dz:
        obs, fn = fill_station(obs, vline_stats.values[:, 3], varcol, grids.zi,
                           grids.zi + grids.dz, grids.cellz, header)

    # detect irregularities
    hom_where = np.logical_or(obs.values[:, varcol] < vline_stats.
                              values[:, -2], obs.values[:, varcol] >
                                         vline_stats.values[:, -1])
    detected_number = hom_where.sum()  # + fn

    # homogenize irregularities
    homogenized = gr.PointSet(obs.name + '_homogenized', obs.nodata, obs.nvars,
                              list(obs.varnames), obs.values.copy())

    imean = vline_stats.varnames.index('mean')
    if method == 'skewness' and skewness:
        imed = vline_stats.varnames.index('median')
        iskew = vline_stats.varnames.index('skewness')
        fixvalues = np.where(vline_stats.values[:, iskew] > 1.5, vline_stats.
                              values[:, imed], vline_stats.values[:, imean])
    else:
        fixvalues = vline_stats.values[:, imean]

    homogenized.values[:, varcol] = np.where(hom_where, fixvalues,
                                             obs.values[:, varcol])
    if flag:
        flag_col = np.where(hom_where, obs.values[:, varcol], obs.nodata)
        if homogenized.varnames[-1].lower() != 'flag':
            homogenized.nvars += 1
            homogenized.varnames.append('Flag')
            homogenized.values = np.column_stack((homogenized.values,
                                                  flag_col))
        else:
            homogenized.values[:, -1] = flag_col
    # corrections = list()  # opt for pd.DataFrame ?
    # for cell in xrange(grid.dz):
    #    if obs < per[cell, 0] or obs > per[cell, 1]:
    #        corrections.append([cell, avmed[cell]])

    if save and outfile is not None:
        homogenized.save(outfile, header)

    return homogenized, detected_number, fn


def fill_station(pset_file, values, varcol, time_min, time_max, time_step=1,
                 header=True):
    """Look for missing data in a station and fill them with a given value.
    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header)

    filled_count = 0
    j = 0
    timeserie = np.arange(time_min, time_max, time_step)
    filled = np.zeros((timeserie.shape[0], pset.values.shape[1]))
    for i, itime in enumerate(timeserie):
        if j < len(pset.values[:, 2]) and itime == pset.values[j, 2]:
            filled[i, :] = pset.values[j, :]
            j += 1
        else:
            filled[i, :] = [pset.values[0, 0], pset.values[0, 1], itime,
                            pset.values[0, 3:varcol], values[i],
                            pset.values[0, varcol + 1:]][:pset.values.shape[1]]
            filled_count += 1

    pset.values = filled

    return pset, filled_count


def station_col(pset_file, header):
    """Try to find the column which has the station ID's.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header)

    if header:
        try:
            stcol = pset.varnames.index('station')
        except ValueError:
            stcol = None
    else:
        stcol = None

    return stcol


def list_stations(pset_file, stcol, h=True):
    """Lists all the stations in one point-set file.
    It doesn't distinguish networks.

    """
    if isinstance(pset_file, gr.PointSet):
        pset = pset_file
    else:
        pset = gr.PointSet()
        pset.load(pset_file, header=h)

    stations = np.unique(pset.values[:, stcol])
    return stations


def take_candidate(pset_file, station, stcol, h=True, save=False):
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

    candidate = pset.values[pset.values[:, stcol] == int(station)]
    neighbours = pset.values[pset.values[:, stcol] != int(station)]

    candidate_pset = gr.PointSet('Candidate_' + str(station),
                                 pset.nodata, pset.nvars,
                                 pset.varnames, candidate)
    neighbours_pset = gr.PointSet('References_' + str(station),
                                  pset.nodata, pset.nvars, pset.varnames,
                                  neighbours)

    if save:  # FIXME: isto dá bronca se receber um PointSet
        base, ext = os.path.splitext(pset_file)
        candidate_pset.save(base + '_candidate' + ext, h)
        neighbours_pset.save(base + '_neighbours' + ext, h)
        """
        candidate_file = cost.start_pset(base + '_candidate' + ext)
        neighbours_file = cost.start_pset(base + '_neighbours' + ext)
        np.savetxt(candidate_file, candidate,
                   fmt=['%-10.6f', '%10.6f', '%10i', '%10.4f', '%06i', '%08i'])
        np.savetxt(neighbours_file, neighbours,
                   fmt=['%-10.6f', '%10.6f', '%10i', '%10.4f', '%06i', '%08i'])
        candidate_file.close()
        neighbours_file.close()
        """
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
    if pset.varnames[-1].lower() != 'flag':
        pset.varnames.append('Flag')
        pset.nvars += 1
        pset.values = np.column_stack((pset.values, np.repeat
                                       (pset.nodata, pset.values.shape[0])))
    elif pset.nvars != station.nvars:
        raise ValueError('PointSets {} and {} have different number of '
                         'variables.'.format(pset.name, station.name))

    pset.values = np.vstack((pset.values, station.values))
    return pset


def station_order(stations_list, method, userset=None, pset=None):
    """Sort a list containing stations numbers, according to the selected
    method:
        - random: all stations randomly sorted;
        - sorted: sorts all stations in ascending order;
        - variance: sorts all stations by greater variance;
        - user: the user specifies which stations and their order.

    """
    if method == 'random':
        shuffle(stations_list)
    elif method == 'sorted':
        stations_list.sort()
    elif method == 'variance':
        if not pset:
            raise TypeError('Method variance requires the stations point-set')
        stname = 'station'  # TODO: st and var names
        varname = 'wetdays'
        varsort = (pset.values.groupby(stname)[varname].aggregate(np.var).
                   sort(ascending=False))
        stations_list = list(varsort.index)

    elif method == 'user' and userset:
        stations_list = [int(i) for i in userset.split()]
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

    flagged = (pset.varnames[-1].lower() == 'flag')
    if fformat == 'normal':
        with open(outfile, 'wb') as csvfile:
            out = csv.writer(csvfile, dialect='excel')
            if not lvars:
                out.writerow(pset.varnames)
                out.writerows(pset.values)
            else:
                out.writerow([pset.varnames[i] for i in lvars])
                out.writerows(pset.values[:, np.array(lvars)])

    elif fformat == 'gsimcli':
        # year, time (month)
        csvheader = [pset.varnames[2]]
        # csvfile = open(outfile, 'wb')
        # out = csv.writer(csvfile, dialect='excel')
        if station_split and flagged:
            # year, time (month), stationID_VAR, stationID_FLAG
            st_col = station_col(pset, header)
            stations = map(int, list_stations(pset, st_col))
            varname = pset.varnames[-2]
            headerline = [[str(stations[i]) + '_' + varname,
                           str(stations[i]) + '_FLAG']
                          for i in xrange(len(stations))]
            csvheader += itertools.chain.from_iterable(headerline)
            outdf = pd.DataFrame(index=np.arange(pset.values[:, 2].min(),
                                                 pset.values[:, 2].max() + 1),
                                 columns=csvheader[1:])
            for i in xrange(len(stations)):
                temp = pset.values[np.where(pset.values[:, st_col] ==
                                               stations[i])][:, [2, -2, -1]]
                tempdf = pd.DataFrame(temp[:, 1:], index=temp[:, 0],
                                      columns=csvheader[2 * i + 1:2 * i + 3])
                outdf.update(tempdf)
        else:  # TODO: falta sem station_split; vale a pena?
            # year, time (month), station, VAR, FLAG (if flagged)
            # csvheader.append([pset.varnames[i] for i in
            #               xrange(5, pset.nvars)])
            # cols = pset.values[:, 5:]
            pass
        # out.writerow(csvheader)
        # out.writerows(cols)
        # csvfile.close()
        if append_year:
            raise BaseException('not done yet')
            years = 0
            outdf.insert(0, 'year', years)
        outdf.to_csv(outfile, index_label='year')

    elif fformat.lower() == 'gslib':
        if network_split and pset.varnames[4] == 'network':
            networks = np.unique(pset.values[:, 4])
            temp_varnames = pset.varnames[:]
            temp_varnames.remove('network')
            for nw in networks:
                temp = gr.PointSet(name=pset.name + ' network: ' + str(nw),
                                   nodata=pset.nodata, nvars=pset.nvars - 1,
                                   varnames=temp_varnames)
                outfile = (os.path.splitext(outfile)[0] + '_' + str(nw) +
                           os.path.splitext(outfile)[1])
                temp.values = pset.values[np.where(pset.values[:, 4] == nw), :]
                temp.save(outfile, header=True)
        else:
            pset.save(outfile, header=True)

    if save_stations:
        st_col = station_col(pset, header)
        stations = [int(i) for i in list_stations(pset, st_col)]
        stations_out = os.path.join(os.path.dirname(outfile),
                                os.path.splitext(os.path.basename(outfile))
                                [0] + '_stations.csv')
        stationsdf = pd.DataFrame(index=stations,
                                      columns=pset.varnames[:2])

        for i, st in enumerate(stations):
            stationsdf.iloc[i] = pset.values[np.where(pset.values[:, st_col] ==
                                                      st)[0][0], :2]
        if keys:
            keysdf = pd.read_csv(keys, sep='\t', index_col=0)

            stationsdf = stationsdf.join(keysdf)

        stationsdf.to_csv(stations_out, index_label='Station')


def ask_add_header(pset):
    """Ask for the header when a point-set does not have any."""
    print 'Insert the point-set header metadata'
    pset.name = raw_input('Point-set name: ')
    for i in xrange(pset.nvars):
        pset.varnames[i] = (raw_input('Variable {} name: '.format(i + 1)).
                            strip())
    return pset


if __name__ == '__main__':
    """ benchmark
    fstpar = '/home/julio/Transferências/test/test.out'
    outpath = '/home/julio/Transferências/test'
    pointset = ('/home/julio/Transferências/benchmark/inho/precip/sur1/' +
                'sur1_rr_pset.prn')
    grid_dims = [50, 50, 10]
    nsims = 10
    no_data = -999.9
    st = 85152001
    header = True
    """

    # """ snirh
    no_data = -999.9
    pointset = '/home/julio/Testes/test/snirh.prn'
    header = False
    bla = gr.PointSet()

    # run
    bla.load(pointset, no_data, header)
    if not header:
        bla = ask_add_header(bla)
        header = True
    stacol = station_col(bla, header)
    print stacol
    stlist = list_stations(bla, stacol)
    user_order = '72 10 59 56'

    ordr = station_order(stlist, 'variance', pset=bla)
    print ordr

#     for i in xrange(len(ordr)):
#         stacol = station_col(bla, header)
#         candidate, references = take_candidate(bla, ordr[i], stacol)
#         print candidate.name
    # """

    """ snirh 50 sims

    fstpar = '/home/julio/Testes/snirh50/dss_map_st1_sim.out'
    grid_dims = [220, 200, 20]
    nsims = 50
    firstcoord = [100000, 0, 1980]
    cellsize = [1000, 1000, 1]
    no_data = -999.9
    pointset = '/home/julio/Testes/snirh/snirh.prn'
    outpath = '/home/julio/Testes/snirh'
    header = False
    st = 72
    # """

    """
    print 'loading grids'
    grids = gr.GridFiles()
    grids.load(fstpar, nsims, grid_dims, firstcoord, cellsize, no_data, 0)
    print 'setup candidate'
    c, h = take_candidate(pointset, st, stcol=3, h=header, save=True)
    # """

    """
    cand = gr.GridArr()
    cand.load(fstpar, grid_dims, no_data, 0)
    cand_vline = cand.drill((5, 5))
    """

    """
    cand_vline = c
    print 'detecting irregularities'
    corr, dn = detect(grids, cand_vline, 'skewness', prob=0.95, skewness=1.5)
    print corr
    print dn
    grids.dump()
    # """

    """
    pset = '/home/julio/Testes/snirh50/pset_final.prn'
    fileout = '/home/julio/Testes/snirh50/homog_final.csv'
    keys = '/home/julio/Testes/test/snirh_keys.txt'

    save_output(pset, fileout, fformat='gsimcli', header=True,
                station_split=True, save_stations=True, keys=keys)
    #"""

    print 'done'
