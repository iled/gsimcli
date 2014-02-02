# encoding: utf-8
'''
Created on 19/09/2013

@author: jcaineta
'''

import datetime
import itertools
import os

import numpy as np
import pandas as pd
import tools.grid as gr
import tools.utils as ut


def directory_walk_v1(base):
    """Walk through a directory tree, according to version 13.11.2009

    Format: iiii / dddd / nnnnnn

    @base: path for iiii / dddd /
    """
    networks = dict()
    parsed_files = dict()

    for root, dirs, files in os.walk(base):  # @UnusedVariable
        network = os.path.basename(root)
        if network.isdigit() and len(network) == 6:
            networks[network] = files

    # este ciclo deve dar para integrar no anterior
    for network, stations in networks.iteritems():
        for station in stations:
            if os.path.basename(base) == network:
                direc = os.path.join(base, station)
            else:
                direc = os.path.join(base, network, station)
            parsed_files[direc] = [network] + filename_parse(direc)

    return parsed_files


def directory_walk_v2(root):
    """Walk through a directory tree, according to version 30.09.2010

    Format: network / type
    """
    pass


def directory_convert(fpath, ftype=None, variable=None, content=None,
                   network=None, merge=False, to_year=None, coords=None,
                   md=-999.9):
    for root, dirs, files in os.walk(fpath):  # @UnusedVariable
        if len(dirs) > 0 and all([len(d) == 6 and d.isdigit() for d in dirs]):
            print 'processing ' + root
            parsed_files = directory_walk_v1(root)
            selected_files = files_select(parsed=parsed_files, ftype=ftype,
                                          variable=variable, content=content,
                                          network=network)
            if selected_files:
                convert_gslib(selected_files, merge, md, to_year, coords)


def filename_parse(filepath, station_n=8, network_n=3):
    """Recognizes file type and properties.

    @filepath: path to file (xxvvrssssssssc.txt)
    @station_n: number of digits for the stations code (default in
                version 13.11.2009 is 8)
    @network_n: number of digits for the network (default in version
                30.09.2010 is 3; default in version 13.11.2009 is 6)

    """
    bne = os.path.basename(filepath)
    bn = os.path.splitext(bne)[0]
    ext = os.path.splitext(bne)[1]

    # identify stations network file (nnnstations.txt)
    if bne[-12:] == 'stations.txt':
        filetype = 'network'
        return [filetype]
    # identify break-points file (nnnvvdetected.txt)
    if bne[-12:] == 'detected.txt':
        filetype = 'breakpoint'
        return [filetype]
    elif ext == '.txt':
        filetype = 'data'
        """
        xx: Data status, quality (the status relates to the full dataset)
        'ra': #raw data (with possible outliers, missing data
            and inhomogeneities)
        'qc': #quality controlled (outliers removed, but may still exist
            missing data and inhomogeneities)
        'ho': #homogenized data (outliers removed, missing data filled,
            detected inhomogeneities removed)
        """
        xx = bn[0:2]
        if xx not in ['ra', 'qc', 'ho']:
            raise NameError('Unrecognized data status.')

        # vv: Measured variable
        # 'dd': #wind direction
        # 'ff': #wind speed
        # 'nn': #cloud cover
        # 'tm': #mean temperature
        # 'tn': #minimum temperature
        # 'tx': #maximum temperature
        # 'pp': #pressure
        # 'rr': #precipitation
        # 'sd': #sunshine duration
        vv = bn[2:4]
        if vv not in ['dd', 'ff', 'nn', 'tm', 'tn', 'tx', 'pp', 'rr', 'sd']:
            raise NameError('Unrecognized measured variable.')

        # r: Resolution (averaging period of the data)
        # 'y': #yearly
        # 'm': #monthly
        # 'd': #daily
        # 's': #subdaily
        # 'x': #other
        r = bn[4]
        if r not in ['y', 'm', 'd', 's', 'x']:
            raise NameError('Unrecognized data resolution.')

        # ssssssss: Station number (number of characters to be
                    # specified by the user, default is station_n = 8)
        ssssssss = bn[5:5 + station_n]
        if len(ssssssss) != len(bn) - 6:
            raise NameError('Invalid station number.')

        # c: Content
        # 'd': #data, meteorological variables
        # 'f': #quality flags
        # 'g': #graphics and pictures (it may come with an extra suffix, hence
                # the file name might be longer)
        # 'c': #corrections
        c = bn[5 + station_n]
        if c not in ['d', 'f', 'g', 'c']:  # nunca vai encontrar o g...
            raise NameError('Unrecognized content.')

        return [filetype, xx, vv, r, ssssssss, c]

    # file extension must be .txt (except for images)
    elif ext != '.txt':  # and c != 'g':
        filetype = 'other'
        return [filetype]
        # raise NameError('Invalid file type.')


def datafile(filepath, res, md=-999.9):
    """Reads COST-formatted data files.
    @filepath: path to data file.
    @res: resolution
    @md: missing data value

    """
    if res == 'y':
        header_names = ['Year', 'Data']
        ncols = [0, 1]
    elif res == 'm':
        header_names = ['Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ncols = range(0, 13)
    elif res == 'd':
        header_names = ['Year', 'Month', 'Day', 'Data']
        ncols = range(0, 4)
    elif res == 's':
        header_names = ['Year', 'Month', 'Day', 'Time', 'Data']
        ncols = range(0, 5)
    elif res == 'x':
        # not handled yet
        pass

    climdata = pd.read_table(filepath, header=None, index_col=0, na_values=md,
                             usecols=ncols, names=header_names)

    return climdata


def qualityfile(filepath, res):
    """Reads COST-formatted files with quality flags.

    Same file format as data files, but the last column is replaced by
    an integer:

    1. Raw (not passed QC)
    2. Controlled (not homogenized; has passed some QC)
    3. Homogenized
    4. Reconstitution (if the original data was missing or did not pass the QC)
    5. Exceptional (in some cases, the original data is not an error,
        but has weird values, that should not be taken into account
        during correction estimations. This may occur for violent but
        local thunderstorms for example.
    9. Missing

    @filepath: path to quality flags file.
    @res: resolution

    """
    if res == 'y':
        header_names = ['Year', 'Flag']
        ncols = [0, 1]
    elif res == 'm':
        header_names = ['Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ncols = range(0, 13)
    elif res == 'd':
        header_names = ['Year', 'Month', 'Day', 'Flag']
        ncols = range(0, 4)
    elif res == 's':
        header_names = ['Year', 'Month', 'Day', 'Time', 'Flag']
        ncols = range(0, 5)
    elif res == 'x':
        # not handled yet
        pass

    qualityflags = pd.read_table(filepath, header=None, index_col=0,
                                 usecols=ncols, names=header_names)

    return qualityflags


def correctionsfile(filepath, res, md=-999.9):
    """Reads COST-formatted files with applied correction.

    The correction file has the same format as the data file format.
    It is the result of the comparison between homogenized series and
    raw or qc series if exists. In the case of reconstitution of
    missing values, the reconstituted value is given.

    @filepath: path to data corrections file.
    @res: resolution

    """
    if res == 'y':
        header_names = ['Year', 'Correction']
        ncols = [0, 1]
    elif res == 'm':
        header_names = ['Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ncols = range(0, 13)
    elif res == 'd':
        header_names = ['Year', 'Month', 'Day', 'Correction']
        ncols = range(0, 4)
    elif res == 's':
        header_names = ['Year', 'Month', 'Day', 'Time', 'Correction']
        ncols = range(0, 5)
    elif res == 'x':
        # not handled yet
        pass

    correction = pd.read_table(filepath, header=None, index_col=0,
                               na_values=md, usecols=ncols, names=header_names)

    return correction


def networkfile(filepath):
    """Reads COST-formatted network (list of stations) files.

    @filepath: path to network file.

    """

    network = pd.read_table(filepath, header=None)
    ncols = network.shape[1]

    if ncols == 9:
        network.columns = ['Station', 'LatDeg', 'LatMin', 'LatSec', 'LonDeg',
                           'LonMin', 'LonSec', 'Alt', 'Name']
    elif ncols == 5:
        network.columns = ['Station', 'Lat', 'Lon', 'Alt', 'Name']

    return network


def find_netwfile(filepath):
    """Tries to find the path for the corresponding network file of a
        data file.

    @filepath: path to data file.

    """

    base = os.path.split(filepath)[0]
    network = os.path.basename(base)
    netwfile = os.path.join(base, network + 'stations.txt')
    if os.path.isfile(netwfile):
        return netwfile
    else:
        for root, dirs, files in os.walk(base):  # @UnusedVariable
            netwfile = next((x for x in files if x[-12:] == 'stations.txt'),
                            os.sep)
            if os.path.isfile(netwfile):
                return os.path.join(base, netwfile)
            else:
                raise IOError('Network file not found.')


def breakpointsfile(filepath):
    """Reads COST-formatted break-points files.

    @filepath: path to break-points file.

    """
    breakpoints = pd.read_table(filepath, header=None)
    ncols = breakpoints.shape[1]
    header_names = ['Station', 'Type', 'Year']

    if ncols == 4:
        header_names += ['Month']
    elif ncols == 5:
        header_names += ['Month', 'Day']

    breakpoints.columns = header_names

    return breakpoints


def start_pset(filepath):
    """DEPRECATED
    Deletes existing filepath and creates a new file with gslib
    point-set header.
    """
    # if os.path.isfile(filepath):
    #    os.remove(filepath)
    pset = open(filepath, 'w')
    pset.writelines(os.path.splitext(os.path.basename(filepath))[0] +
                    '\n' + repr(6) + '\n' + 'lat' + '\n' + 'lon' + '\n' +
                    'time' + '\n' + 'value' + '\n' + 'network' + '\n' +
                    'station' + '\n')
    return pset


def station_coord(network, station_path, coordinates_file=None):
    """Extracts station coordinates (lat, long) from network file.
    """
    if coordinates_file:
        network = pd.read_csv(coordinates_file)

    station_coord = network[network.Station == os.path.basename(station_path)]

    if coordinates_file:
        x = station_coord.coordx
        y = station_coord.coordy
    elif station_coord.shape[1] == 9:
        y = ut.dms2dec(station_coord.LatDeg, station_coord.LatMin,
                       station_coord.LatSec)
        x = ut.dms2dec(station_coord.LonDeg, station_coord.LonMin,
                       station_coord.LonSec)
    else:
        y = station_coord.Lat
        x = station_coord.Lon

    return float(x), float(y)


def convert_gslib(files, merge=False, md=-999.9, to_year=None,
                  coordinates_file=None):
    """Load selected files type, previously parsed. Then converts them
    to GSLIB format. By default it generates one file per network.


    @files: list containing files path and type, selected before hand.
    @merge: flag to generate one file per group of networks.
    @md: place holder for missing data.

    TODO:
    .considerar a hipótese de carregar mais do que um tipo simultaneamente
    .permitir fazer diferentes variáveis (ou inserir isso no interface)
    .deal with leap years.
    .now its dropping the column with the year; put back again for res != 'y'
    """
    # collect info from the first network
    network_number = files[0][1][0]
    network_path = find_netwfile(files[0][0])
    network = networkfile(network_path)
    station_x, station_y = station_coord(network, files[0][0],
                                         coordinates_file)
    var = files[0][1][3]
    # resol = files[0][1][4]

    savedir = os.path.dirname(os.path.dirname(files[0][0]))
    if merge:
        # savedir = os.path.dirname(os.path.dirname(files[0][0]))
        fname = os.path.basename(savedir)
    else:
        # savedir = os.path.dirname(files[0][0])
        fname = str(network_number)

    pset_file = os.path.join(savedir, fname + '_' + var + '_pset.prn')
    """
    # temporary, depends on leap years
    if resol in ['y', 'm']:
        nvar = 7
        pset = gr.PointSet(name=fname + '_pset', nodata=md, nvars=nvar,
                       varnames=['lat', 'lon', 'time', 'year', 'network',
                                 'station', var], values=np.zeros((0, nvar)))
    else:
        nvar = 6
        pset = gr.PointSet(name=fname + '_pset', nodata=md, nvars=nvar,
                       varnames=['lat', 'lon', 'time', 'network', 'station',
                                 var], values=np.zeros((0, nvar)))
    """
    nvar = 5
    pset = gr.PointSet(name=fname + '_pset', nodata=md, nvars=nvar,
                       varnames=['lon', 'lat', 'time', 'station', var])

    for x in files:
        file_path = x[0]
        file_type = x[1]
        if network_number != file_type[0]:
            # collect info from the next network
            network_path = find_netwfile(file_path)
            network = networkfile(network_path)
            network_number = file_type[0]
            if not merge:
                """pset_file.close()
                pset_file = start_pset(os.path.join(os.path.dirname(file_path),
                                  str(network_number) + '_pset.prn'))"""
                pset.save(pset_file, header=True)
                pset = gr.PointSet(name=str(network_number) + '_pset',
                                   nodata=md, nvars=nvar,
                                   varnames=['lon', 'lat', 'time', 'station',
                                             var])
                pset_file = os.path.join(savedir, str(network_number) + '_' +
                                         var + '_pset.prn')
                # pset.values = np.zeros((0, nvar))
                # pset.values = pd.DataFrame(np.zeros((0, nvar)))

        station_x, station_y = station_coord(network, file_path,
                                             coordinates_file)
        temp = pd.DataFrame((cost2gslib(station_x, station_y,
                                        datafile(file_path, file_type[4]), md,
                                        to_year)),
                            columns=['lon', 'lat', 'time', 'year', var])

        # temp[np.isnan(temp)] == md
        """
        temp = np.column_stack((temp[:, :-1], np.repeat(int(network_number),
                                                temp.shape[0]),
                                np.repeat(int(filename_parse(file_path)[4]),
                                          temp.shape[0]), temp[:, -1]))
        """
        # temp = (temp.iloc[:, :3].
        #        join(pd.Series(np.repeat(int(filename_parse(file_path)[4]),
        #                                 temp.shape[0]), name='station')))
        temp = temp.drop('year', 1)
        temp.insert(3, 'station', np.repeat(int(filename_parse(file_path)[4]),
                                         temp.shape[0]))
        # temp = temp.join(pd.Series(temp.iloc[:, -1], name=var))
        # np.savetxt(pset_file, temp,
        #          fmt=['%-10.6f', '%10.6f', '%10i', '%10.4f', '%06i', '%08i'])
        # pset.values = np.vstack((pset.values, temp))
        pset.values = pset.values.append(temp, ignore_index=True)

    # pset_file.close()
    pset.save(pset_file, header=True)


def cost2gslib(x, y, data, nd=-999.9, to_year=None):
    """Converts data from one station to the GSLIB standard (point-set).

    @x, y: station coordinates
    @data: data contents as pd.DataFrame

    TODO: deal with leap years.
    """

    resolution = data.shape[1]

    if resolution == 1:  # yearly
        z = data.index
        var = np.array(data)  # TODO: pd.S ?
        m = 1
    elif data.shape[1] == 12:  # monthly
        if to_year == 'sum':
            z = data.index
            var = data.sum(axis=1, skipna=False)
            m = 1
        elif to_year == 'mean':
            z = data.index
            var = data.average(axis=1, skipna=False)
            m = 1
            # TODO: confirmar NaN quando só falta alguns meses num ano
        else:
            # years with months in decimal place
            # z = [data.index[i] + float(j)/12 for i in xrange(0,data.shape[0])
            #     for j in xrange(0,12)]

            # converted to months
            z = [data.index[i] * 12 + j for i in xrange(0, data.shape[0])
                 for j in xrange(0, 12)]
            var = np.array(data).flatten()
            m = 12
    # daily -- converted to days (not considering leap years)
    elif data.shape[1] == 3:
        z = [data.index[0] * 365 + 365 * i +
             (datetime.date(i, data.iloc[i, 0], data.iloc[i, 1]).timetuple()
              .tm_yday)
             for i in xrange(0, data.shape[0])]
        var = np.array(data[:, -1])
        m = 0  # not implemented, depends on leap years
    # subdaily -- same as daily but with hours in decimal place
    elif data.shape[1] == 4:
        z = [data.index[0] * 365 + 365 * i +
             datetime.date(i, data.iloc[i, 0], (data.iloc[i, 1]).timetuple()
                           .tm_yday) + float(data.iloc[i, 2]) / 24
             for i in xrange(0, data.shape[0])]
        var = np.array(data[:, -1])
        m = 0  # not implemented, depends on leap years

    if m == 0:  # temporary
        return (np.column_stack((np.repeat(x, var.size),
                                 np.repeat(y, var.size), z, var.fillna(nd))))
    else:
        return (np.column_stack((np.repeat(x, var.size),
                                 np.repeat(y, var.size), z,
                                 np.repeat(data.index, m), var.fillna(nd))))


def files_select(parsed, network=None, ftype=None, status=None, variable=None,
                 resolution=None, content=None):
    """Sort and filter parsed files according to user criteria.

    @parsed: dict containing files path and type.

    """
    parsed_items = [x for x in parsed.iteritems()]

    if network:
        parsed_items = [s for s in parsed_items if s[1][0] in network]
    if ftype:
        parsed_items = [s for s in parsed_items if s[1][1] == ftype]
    if status and ftype == 'data':
        parsed_items = [s for s in parsed_items if s[1][2] == status]
    if variable and ftype == 'data':
        parsed_items = [s for s in parsed_items if s[1][3] == variable]
    if resolution and ftype == 'data':
        parsed_items = [s for s in parsed_items if s[1][4] == resolution]
    if content and ftype == 'data':
        parsed_items = [s for s in parsed_items if s[1][6] == content]

    if ftype == 'data':
        # sort by network number and then by station number
        parsed_items.sort(key=lambda x: (x[1][0], x[1][5]))
    else:
        # sort by network number
        parsed_items.sort(key=lambda x: x[1][0])

    return parsed_items


def match_orig(stations_spec, orig_path):
    """Select orig files according to given station files.

    FIXME: DEPRECATED in favor of match_sets
    """
    orig_spec = list()
    netw = None
    for st_spec in stations_spec:
        spec = st_spec[1]
        if netw != spec[0]:
            orig_parsed = files_select(parsed=orig_path, network=spec[0],
                                         ftype=spec[1], variable=spec[3],
                                         content=spec[6])
            orig_spec.append(orig_parsed)
            netw = spec[0]

    orig_spec = list(itertools.chain.from_iterable(orig_spec))
    if len(orig_spec) != len(stations_spec):
        raise ValueError('Mismatch between homogenized and original files.')
    return orig_spec


def match_sets(subset_path, mainset_path):
    """Select a stations subset from a mainset, given both paths.
    Only appliable to data files.

    """
    subset_files = directory_walk_v1(subset_path)
    mainset_files = directory_walk_v1(mainset_path)
    subset_parsed = files_select(parsed=subset_files, ftype='data',
                                 content='d')
    subset_agg = agg_network(subset_parsed)

    mainset_parsed = list()
    for group in subset_agg:
        network = group[0][1][0]
        mainset_parsed.append(files_select(parsed=mainset_files, ftype='data',
                                  content='d', network=network))

    mainset_parsed = list(itertools.chain.from_iterable(mainset_parsed))
    if len(subset_parsed) != len(mainset_parsed):
        raise ValueError('{} is not a subset of {}'.format(subset_path,
                                                            mainset_path))
    return mainset_parsed


def agg_network(stations_parsed):
    """Aggreggate stations by network.

    """
    networks = list()
    netw = None
    for station in stations_parsed:
        if netw != station[1][0]:
            netw = station[1][0]
            netw_list = [st for st in stations_parsed
                         if st[1][0] == netw]
            networks.append(netw_list)

    return networks


if __name__ == '__main__':
    macpath = '/Users/julio/Desktop/testes/cost-home/'
    mintpath = '/home/julio/Testes/'
    basepath = mintpath

    rede = basepath + 'benchmark/h009/precip/sur1/000005'

    benchmark = '/home/julio/Testes/benchmark/inho/precip/sur1'
    coords = '/home/julio/Dropbox/ISEGI/cost-home/rede000016/tab_coordenadas_projetadas_rede000016.txt'

    """
    for root, dirs, files in os.walk(benchmark):  # @UnusedVariable
        if len(dirs) > 0 and all([len(d) == 6 and d.isdigit() for d in dirs]):
            print 'processing ' + root
            parsed_files = directory_walk_v1(root)
            selected_files = files_select(parsed=parsed_files, ftype='data',
                                          variable='rr', content='d',
                                          network='000016')
            if selected_files:
                convert_gslib(selected_files, merge=False, to_year='sum',
                              coordinates_file=coords)
    """
    dirwalk = directory_walk_v1(rede)
    print dirwalk
    print 'done'
