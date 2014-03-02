# -*- coding: utf-8 -*-
"""
This module provides tools to deal with data files in the COST-HOME format [1]_

See Also
--------
parsers.cost : initial version of this module. All functions will be refactored
to make use of these new classes.

References
----------

.. [1] Venema, V., & Mestre, O. (2010). The File Format for COST-HOME, 1–4.

Created on 28/01/2014

@author: julio
"""

import glob
import itertools
import os
import warnings

import numpy as np
import pandas as pd
import parsers.cost as pc
import parsers.spreadsheet as ss
import tools.grid as gr
import tools.utils as ut


class Station(object):
    """Station container.

    A station is basically a time series of a climate variable in a specific
    location.

    Attributes
    ----------
    md : number
        Missing data value.
    path : string
        File path.
    network_id : int
        Network ID number.
    ftype : {'data', 'breakpoint', 'network', 'other'}
        File type\:
            - data: contains climate data
            - breakpoint: contains detected irregularities
            - network: contains stations' names and coordinates
            - other: contains other information (e.g., graphics)
    status : {'ra', 'qc', 'ho'}
        Data file status\:
            - ra: raw data
            - qc: quality controlled (outliers removed)
            - ho: homogenised data
    variable : {'dd', 'ff', 'nn', 'tm', 'tn', 'tx', 'pp', 'rr', 'sd'}
        Measured climate variable\:
            - dd: wind direction
            - ff: wind speed
            - nn: cloud cover
            - tm: mean temperature
            - tn: minimum temperature
            - tx: maximum temperature
            - pp: pressure
            - rr: precipitation
            - sd: sunshine duration
    resolution : {'y', 'm', 'd', 's', 'x'}
        Time series resolution (data averaging period)\:
            - y: yearly
            - m: monthly
            - d: daily
            - s: subdaily
            - x: other
    id : int
        Station ID number.
    content : {'d', 'f', 'g', 'c'}
        File content\:
            - d: data, meteorological variables
            - f: quality flags
            - g: graphics and pictures
            - c: corrections

    Notes
    -----
    Some methods generate other attributes.


    TODO: separate quality flag from data

    """
    def __init__(self, path=None, spec=None, md=-999.9):
        """Initialise a Station instance.

        Parameters
        ----------
        path : string
            File path.
        spec : list or tuple
            Wrapper  # TODO: replace with kwargs
        md : number
            Missing data value.

        """
        self.md = md

        if isinstance(path, str) and os.path.isfile(path):
            self.path = path
            self.network_id = os.path.basename(os.path.dirname(path))
            spec = pc.filename_parse(path)

        if spec:
            (self.ftype, self.status, self.variable, self.resolution,
             self.id, self.content) = spec

    def load(self, path, content=None):
        """Load station data file.

        Parameters
        ----------
        path : string
            File path.
        content : string
            File content.

        Returns
        -------
        Sets attributes `data` or `quality`

        data : pandas.DataFrame
            Measured values.
        quality : DataFrame
            Quality flags.

        Raises
        ------
        ValueError
            The given file was not parsed as a `data` file.

        """
        if isinstance(path, str) and os.path.isfile(path) and content:
            if content == 'd':
                self.data = pc.datafile(self.path, self.resolution, self.md)
            elif content == 'f':
                self.quality = pc.qualityfile(self.path, self.resolution)
        elif self.ftype != 'data':
            raise ValueError('The file {} was not parsed as a data file.'.
                             format(self.path))
# FIXME: check if this is a problem; path optional?
#         elif self.content == 'd':
#             self.data = pc.datafile(self.path, self.resolution, self.md)
#         elif self.content == 'f':
#             self.quality = pc.qualityfile(self.path, self.resolution)

    def load_outliers(self, path=None):
        """List the dates with detected outliers.

        Parameters
        ----------
        path : string, optional
            Breakpoints file path.

        Returns
        -------
        Sets attribute `outliers`

        outliers : pandas.Series
            Dates with detected outliers.

        Notes
        -----
        The `breakpoints` file name must end with *detected.txt*.

        """
        if isinstance(path, str) and os.path.isfile(path):
            detected_file = path
        else:
            path = os.path.dirname(self.path)
            os.chdir(path)
            try:
                detected_file = glob.glob('*detected.txt')[0]
            except:
                raise os.error('breakpoints file not found in directory {}'.
                               format(path))

        detected = pc.breakpointsfile(detected_file)
        self.outliers = detected[((self.id in str(detected.Station)) &
                                  (detected.Type == 'OUTLIE'))].ix[:, 2:]

    def match_orig(self, path=None):
        """Try to fetch the matching original station data.

        Parameters
        ----------
        path : string, optional
            File path. If not present, it will look for a folder named *orig*.

        Returns
        -------
        Sets attribute `orig`

        orig : Station object
            Instance of Station corresponding to the original station data.

        See Also
        --------
        match_inho : equivalent but for inhomogenous data.
        match_sub : fetch a matching station in a given submission.

        """
        if path:
            self.orig = Station(path, self.md)
            if self.id != self.orig.id:
                warnings.warn('mismatch between Station and ORIG IDs')
            if self.network_id != self.orig.network_id:
                warnings.warn('mismatch between Station and ORIG networks')
        else:
            self.orig = Station(match_sub(self.path, 'orig'), self.md)

    def match_inho(self, path=None):
        """Try to fetch the matching inhomogenous station data.

        Parameters
        ----------
        path : string, optional
            File path. If not present, it will look for a folder named *inho*.

        Returns
        -------
        Sets attribute `inho`

        inho : Station object
            Instance of Station corresponding to the inhomogenous station data.

        See Also
        --------
        match_orig : equivalent but for original data.
        match_sub : fetch a matching station in a given submission.

        """
        if path:
            self.inho = Station(path, self.md)
            if self.id != self.inho.id:
                warnings.warn('mismatch between Station and INHO IDs')
            if self.network_id != self.inho.network_id:
                warnings.warn('mismatch between Station and INHO networks')
        else:
            self.inho = Station(match_sub(self.path, 'inho'), self.md)

    def yearly(self, func='mean'):
        """Upscale data resolution to yearly.

        Parameters
        ----------
        func : {'mean', 'sum'}
            - mean: mean of the values
            - sum: sum of the values

        Returns
        -------
        ndarray

        TODO: check when resolution != monthly

        """
        if not hasattr(self, 'data'):
            raise ValueError('no loaded data')
        if func == 'mean':
            return self.data.mean(axis=1)
        elif func == 'sum':
            return self.data.sum(axis=1)

    def setup(self, outliers=False, inho=False):
        """Load station homogenised data, original and outliers.

        No option to load from a non default path.

        Parameters
        ----------
        outliers : boolean, default False
            Load corresponding outliers.
        inho : boolean, default False
            Load corresponding inhomogenous data.

        Returns
        -------
        Set attributes `outliers`, `orig` and `inho`.

        See Also
        --------
        load : load data.
        load_outliers : load outliers.
        match_orig : fetch corresponding original data.
        match_inho : fetch corresponding inhomogenous.

        """
        if not hasattr(self, 'data'):
            self.load()
        if not hasattr(self, 'orig'):
            self.match_orig()
            self.orig.load()
        if outliers and not hasattr(self, 'outliers'):
            if 'orig' not in self.path.lower():
                warnings.warn('loading outliers from non ORIG submission')
            self.load_outliers()
        if inho and not hasattr(self, 'inho'):
            self.match_inho()

    def save(self, path):
        """Write station data in the COST-HOME format (tab separated values,
        float numbers with one decimal value).

        Parameters
        ----------
        path : string
            File path.

        """
        self.path = path
        self.load()
        filename = (self.status + self.variable + self.resolution + self.id +
                    self.content + '.txt')
        self.data.to_csv(os.path.join(path, filename), sep='\t', header=False,
                         float_format='%6.1f')


class Network(object):
    """Network container.

    A network is a set of stations. The same station can belong to different
    networks.

    Attributes
    ----------
    md : number
        Missing data value.
    path : string
        Network folder path.
    id : int
        Network ID number.
    stations_id : list of int
        Stations' ID numbers.
    stations_spec : list of list
        List wrapping a set of Station attributes.
    stations_path : list of string
        Stations file paths.
    stations_number : int
        Number of stations in the network.

    """
    def __init__(self, path=None, md=-999.9, network_id=None):
        """Initialise a Network instance.

        Parameters
        ----------
        path : string, optional
            Network folder path.
        md : number, default -999.9
            Missing data value.
        network_id : int, optional
            Network ID number.

        Notes
        -----
        The current implementation is filtering files parsed as `data` type and
        with content `d`.

        TODO: handle other files besides data?
        """
        self.md = md
        self.path = path
        self.id = network_id
        self.stations_id = list()
        self.stations_spec = list()
        self.stations_path = list()
        self.stations_number = 0

        if path:
            if isinstance(path, str) and os.path.isdir(path):
                parsed = pc.directory_walk_v1(path)
                selected = pc.files_select(parsed, ftype='data', content='d')
            else:
                selected = path

            self.id = selected[0][1][0]
            self.stations_number = len(selected)

            for station in selected:
                self.stations_id.append(station[1][5])
                self.stations_spec.append(station[1])
                self.stations_path.append(station[0])

    def load_stations(self):
        """Load all the stations in the network.

        Notice that the data has to be explicitly loaded, the stations are just
        indexed to the network.

        """
        self.stations = list()
        for station in self.stations_path:
            self.stations.append(Station(station, self.md))

    def add(self, station):
        """Add a station to the network.

        Parameters
        ----------
        station : Station object
            Instance of Station representing the station to add to the network.

        """
        if not hasattr(self, 'stations'):
            self.stations = list()

        self.stations.append(station)
        self.stations_id.append(station.id)
        self.stations_spec += [station.ftype, station.status, station.variable,
                               station.resolution, station.id, station.content]
        self.stations_path.append(station.path)
        self.stations_number += 1

    def average(self, orig=False):
        """Calculate the average climate variable value per year of all
        stations in the network.

        Parameters
        ----------
        orig : boolean, default False
            Calculate the same average for the corresponding original data.

        Returns
        -------
        ndarray or list of ndarray

        """
        self.setup()

        first = True
        for station in self.stations:
            station.setup()
            if first:
                # netw_average = np.zeros(station.data.shape[0])
                netw_average = station.data.mean(axis=1)
                if orig:
                    orig_average = station.orig.data.mean(axis=1)
                first = False
                continue
            netw_average += station.data.mean(axis=1)
            if orig:
                orig_average += station.orig.data.mean(axis=1)

        netw_result = netw_average / len(self.stations)
        if orig:
            result = [netw_result, orig_average / len(self.stations)]
        else:
            result = netw_result

        return result

    def skip_years(self, missing=False, outlier=True):
        """List of the years in which any station in the network has missing
        data and/or has an outlier.

        Missing data and outliers are both retrieved from the station's
        corresponding original data.

        Parameters
        ----------
        missing : boolean, default False
            List years where any station in the network has missing data.
        outlier : boolean, default True
            List years where any station in the network has an outlier.

        Returns
        -------
        list

        """
        self.setup()
        missing_list = list()
        outlier_list = list()
        for station in self.stations:
            station.setup()
            if missing:
                station.orig.load()
                orig = station.orig.data
                missing_list.append(orig[orig.isnull().any(axis=1)].index)
            if outlier:
                station.orig.load_outliers()
                outlier_list.append(list(np.unique(station.
                                                   orig.outliers.Year)))

        years_list = list()
        if missing:
            years_list.append(list(np.unique(itertools.chain.
                                             from_iterable(missing_list))))
        if outlier:
            years_list.append(list(np.unique(itertools.chain.
                                             from_iterable(outlier_list))))

        return list(itertools.chain.from_iterable(years_list))

    def setup(self):
        """Load all stations in the network.

        No option to load from a non default path.

        """
        if not hasattr(self, 'stations'):
            self.load_stations()

    def save(self, path):
        """Write every station in the network according to the COST-HOME
        format.

        Parameters
        ----------
        path : string
            Folder path.

        TODO: write network and breakpoints files.
        """
        self.setup()
        path = os.path.join(path, str(self.id))
        if not os.path.exists(path):
            os.mkdir(path)
        for station in self.stations:
            station.save(path)

    def load_pointset(self, path, header=True, ftype='data', status='xx',
                      variable='vv', resolution='r', content='c',
                      year_col='year', station_col='est_id', var_col='value'):
        """Load station data from a file in the GSLIB format.

        Parameters
        ----------
        path : string or PointSet object
            Full path to the PointSet file or instance of PointSet type
            containing the observed values at the candidate station.
        header : boolean, default True
            True if the PointSet file has the GSLIB standard header lines.
        ftype : {'data', 'breakpoint', 'network', 'other'}
            File type.
        status : {'ra', 'qc', 'ho'}
            Data file status, default 'xx' (placeholder).
        variable : {'dd', 'ff', 'nn', 'tm', 'tn', 'tx', 'pp', 'rr', 'sd'}
            Measured climate variable, default 'vv' (placeholder).
        resolution : {'y', 'm', 'd', 's', 'x'}
            Time series resolution (data averaging period), default 'r'
            (placeholder).
        content : {'d', 'f', 'g', 'c'}
            File content, default 'c' (placeholder).
        year_col : string, default 'year'
            Label of the column containing the time series yearly index.
        station_col : string, default 'est_id'
            Label of the column containing the stations' ID's.
        var_col : string, default 'value'
            Label of the column containing the climate data values.

        See Also
        --------
        Station : Station class.

        """
        if isinstance(path, gr.PointSet):
            pset = path
        else:
            pset = gr.PointSet(psetpath=path, header=header)
            pset.values.rename(columns={year_col: 'time', station_col:
                                        'station', var_col: 'clim'},
                               inplace=True)

        index = pset.values.time.unique().astype('int')
        self.stations_id = list(pset.values.station.unique().astype('int'))
        self.stations_number = len(self.stations_id)
        self.stations = list()

        for station_id in self.stations_id:
            st_data = pd.Series(pset.values.clim
                                [pset.values.station == station_id].values,
                                index, name=variable)
            st = Station(md=self.md)
            st.data = st_data
            st.id = format(station_id, '0=8.0f')
            st.ftype = ftype
            st.status = status
            st.variable = variable
            st.resolution = resolution
            st.content = content
            st.network_id = self.id
            self.stations.append(st)

    def update_ids(self, keys):
        """Update every station ID according to the given keys.

        Useful when stations' ID's were replaced with a different number (for
        instance, because they were non numerical).

        Parameters
        ----------
        keys : string or pandas.Series
            File path or Series containing ID's and the corresponding keys.

        """
        if isinstance(keys, str) and os.path.isfile(keys):
            keys = ss.read_keys
        for i, station in enumerate(self.stations):
            station.id = keys.loc[station.id]
            self.stations_id[i] = station.id


class Submission(object):
    """Submission/Contribution to the COST-HOME benchark.

    Each instance of Submission should refer to a unique climate signal
    (temperature or precipitation).

    Attributes
    ----------
    path : string
        Folder path.
    md : number
        Missing data value.
    name : string
        Submission's name.
    signal : string
        Submission's climate signal.
    networks : list of Network object
        Networks contained in the submission.
    networks_id : list of int
        Network ID numbers contained in the submission.
    stations_number : int
        Total number of station contained in the submission.

    """
    def __init__(self, path, md, networks_id=None):
        """Initialise a Submission instance.

        Parameters
        ----------
        path : string
            Folder path.
        md : number
            Missing data value.
        networks_id : list of int, optional
            Network ID numbers contained in the submission.

        Notes
        -----
        The current implementation is filtering files parsed as `data` type and
        with content `d`.

        """
        self.path = path
        self.md = md
        self.name = os.path.basename(os.path.dirname(path))
        self.signal = os.path.basename(path)
        parsed = pc.directory_walk_v1(path)
        selected = pc.files_select(parsed, network=networks_id, ftype='data',
                                   content='d')
        grouped = pc.agg_network(selected)
        self.networks = list()
        self.networks_id = list()
        self.stations_number = 0

        for network in grouped:
            self.networks_id.append(network[0][1][0])
            self.networks.append(Network(network, md))
            self.stations_number += self.networks[-1].stations_number

    def save(self, path):
        """Write all networks included in the submission, according to the
        COST-HOME format.

        Parameters
        ----------
        path : string
            Folder path.

        """
        for network in self.networks:
            network.save(path)


def match_sub(path, sub, level=3):
    """Try to fetch the matching `sub` station in a given submission.

    Parameters
    ----------
    path : string
        Station file path.
    sub : string
        Intended corresponding station.
    level : int, default 3
        Number of levels in the directory tree to go up.

    Returns
    -------
    match : string
        Path to the matching station.

    """
    subpath, signalpath = ut.path_up(path, level)
    benchpath, subm = os.path.split(subpath)  # @UnusedVariable
    match = os.path.join(benchpath, sub, signalpath)
    if not os.path.exists(match):
        # try to match by station id
        dirname, basename = os.path.split(match)
        os.chdir(dirname)
        match = os.path.join(dirname, glob.glob('*' + str(basename[2:]))[0])
        if not os.path.isfile(match):
            raise os.error('no such file: \'{}\''.format(match))

    return match


if __name__ == '__main__':
    md = -999.9
    p = '/Users/julio/Desktop/testes/cost-home/benchmark/h009/precip/sur1/000005/horrm21109001d.txt'
    p2 = '/Users/julio/Desktop/testes/cost-home/benchmark/h009/precip/sur1/000005/horrm21109001d__new.txt'
    # st = Station(p, md)
    # st.setup()
    subp = '/Users/julio/Desktop/testes/cost-home/benchmark/h009/precip/sur1'
    # sub = Submission(subp, md)
    # sub.save('/Users/julio/Desktop/testes/')
    bench = '/Users/julio/Desktop/testes/cost-home/rede000005/1900_1909.txt'
    netw = Network(network_id='teste')
    netw.load_pointset(bench)
    netw.save('/Users/julio/Desktop/testes/')
    print 'done'
