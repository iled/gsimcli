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
import os
import re
import warnings

import numpy as np
import pandas as pd
import parsers.cost as pc
import tools.grid as gr
import tools.utils as ut


class Station(object):
    """Station container.

    A station is basically a time series of a climate variable in a specific
    location.

    Attributes
    ----------
    no_data : number
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

    def __init__(self, path=None, no_data=-999.9, spec=None):
        """Initialise a Station instance.

        Parameters
        ----------
        path : string
            File path.
        spec : list or tuple
            Wrapper  # TODO: replace with kwargs
        no_data : number
            Missing data value.

        """
        self.no_data = no_data

        if path is not None and os.path.isfile(path):
            self.path = path
            self.network_id = os.path.basename(os.path.dirname(path))
            spec = pc.filename_parse(path)

        if spec:
            (self.ftype, self.status, self.variable, self.resolution,
             self.id, self.content) = spec

    def check_monthly_order(self):
        """Make sure the data is stored in the correct monthly order.

        """
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        if all([month in months for month in self.data.columns]):
            self.data = self.data.reindex_axis(months, axis=1)

    def load(self, path=None, content=None):
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
        if path is not None and os.path.isfile(path) and content:
            if content == 'd':
                self.data = pc.datafile(path, self.resolution, self.no_data)
            elif content == 'f':
                self.quality = pc.qualityfile(path, self.resolution)
            self.path = path
        elif self.ftype != 'data':
            raise ValueError('The file {} was not parsed as a data file.'.
                             format(self.path))
        # FIXME: check if this is a problem; path optional?
        elif self.content == 'd' and os.path.isfile(self.path):
            self.data = pc.datafile(self.path, self.resolution, self.no_data)
        elif self.content == 'f' and os.path.isfile(self.path):
            self.quality = pc.qualityfile(self.path, self.resolution)

    def load_detected(self, outliers=False, breaks=False, path=None):
        """List the dates with detected outliers and breaks.

        Parameters
        ----------
        outliers : boolean, default False
            Load corresponding outliers.
        breaks : boolean, default False
            Load corresponding break points.
        path : string, optional
            Breakpoints file path.

        Returns
        -------
        Sets attributes `outliers` and `breaks`.

        outliers : pandas.Series
            Dates with detected outliers.
        breaks : pandas.Series
            Dates with detected breakpoints.

        Notes
        -----
        The `breakpoints` file name must end with *detected.txt*.

        """
        if path is not None and os.path.isfile(path):
            detected_file = path
        else:
            path = os.path.dirname(self.path)
            os.chdir(path)
            try:
                detected_file = glob.glob('*detected.txt')[0]
            except:
                raise os.error('breakpoints file not found in directory {}'.
                               format(path))

        if outliers or breaks:
            detected = pc.breakpointsfile(detected_file)
            select_station = detected["Station"].map(lambda x: self.id in x)

        if outliers:
            select_outlier = detected["Type"] == "OUTLIE"
            self.outliers = detected[select_station & select_outlier].drop(
                ['Station', 'Type'], axis=1)

        if breaks:
            select_breaks = detected["Type"] == 'BREAK'
            self.breaks = detected[select_station & select_breaks].drop(
                ['Station', 'Type'], axis=1)

    def match_orig(self, path=None):
        """Try to fetch the matching original station data.

        Parameters
        ----------
        path : string, optional
            Path to the original station file. If not present, it will look for
            a folder named *orig*.

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
            self.orig = Station(path, self.no_data)
            if self.id != self.orig.id:
                warnings.warn('mismatch between Station and ORIG IDs')
            if self.network_id != self.orig.network_id:
                warnings.warn('mismatch between Station and ORIG networks')
        else:
            self.orig = Station(match_sub(self.path, 'orig'), self.no_data)

    def match_inho(self, path=None):
        """Try to fetch the matching inhomogenous station data.

        Parameters
        ----------
        path : string, optional
            Path to the inhomogenous station file. If not present, it will look
            for a folder named *inho*.

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
            self.inho = Station(path, self.no_data)
            if self.id != self.inho.id:
                warnings.warn('mismatch between Station and INHO IDs')
            if self.network_id != self.inho.network_id:
                warnings.warn('mismatch between Station and INHO networks')
        else:
            self.inho = Station(match_sub(self.path, 'inho'), self.no_data)

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

    def setup(self, outliers=False, breaks=False, inho=False, orig_path=None,
              inho_path=None):
        """Load station homogenised data, original, outliers and break points
        dates. It won't override existing loaded outliers/breaks.

        Parameters
        ----------
        outliers : boolean, default False
            Load corresponding outliers.
        breaks : boolean, default False
            Load corresponding break points.
        inho : boolean, default False
            Load corresponding inhomogenous data.
        orig_path : string, optional
            Path to the original station file.
        inho_path : string, optional
            Path to the inhomogenous station file.

        Returns
        -------
        Set attributes `outliers`, `breaks`, `orig` and `inho`.

        See Also
        --------
        load : load data.
        load_detected : load dates with outliers and break points.
        match_orig : fetch corresponding original data.
        match_inho : fetch corresponding inhomogenous.

        """
        if not hasattr(self, 'data'):
            self.load()
        if not hasattr(self, 'orig'):
            self.match_orig(orig_path)
        self.orig.load()
        # don't override existing outliers/breaks
        outliers = outliers and not hasattr(self, 'outliers')
        breaks = breaks and not hasattr(self, 'breaks')
        if outliers or breaks:
            if 'orig' not in self.path.lower():
                warnings.warn('Loading detected from non-ORIG submission.')
            self.load_detected(outliers, breaks)
        if inho and not hasattr(self, 'inho'):
            self.match_inho(inho_path)

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
        self.check_monthly_order()
        self.data.to_csv(os.path.join(path, filename), sep='\t', header=False,
                         float_format='%6.1f')

    def skip_outliers(self, yearly=True):
        """Replace the values marked as outliers in the original data by NaN.

        If working with yearly data, it will delete the corresponding rows
        instead.

        """
        self.orig.load_detected(outliers=True)
        orig = self.orig.data
        if yearly:
            skip = list(np.unique(self.orig.outliers.Year))
            orig = orig.select(lambda x: x not in skip)
        else:
            skip = self.orig.outliers
            skip['Month'] = ut.number_to_month(skip['Month'])
            for date in skip.itertuples(index=False):
                orig.loc[date] = np.nan


class Network(object):
    """Network container.

    A network is a set of stations. The same station can belong to different
    networks.

    Attributes
    ----------
    no_data : number
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

    def __init__(self, path=None, no_data=-999.9, network_id=None):
        """Initialise a Network instance.

        Parameters
        ----------
        path : string, optional
            Network folder path.
        no_data : number, default -999.9
            Missing data value.
        network_id : int, optional
            Network ID number.

        Notes
        -----
        The current implementation is filtering files parsed as `data` type and
        with content `d`.

        TODO: handle other files besides data?
        """
        self.no_data = no_data
        self.path = path
        self.id = network_id
        self.stations_id = list()
        self.stations_spec = list()
        self.stations_path = list()
        self.stations_number = 0

        if path:
            if ((isinstance(path, str) or isinstance(path, unicode)) and
                    os.path.isdir(path)):
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
        being indexed to the network.

        """
        self.stations = list()
        for station in self.stations_path:
            self.stations.append(Station(station, self.no_data))

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
        self.stations_spec.append([station.ftype, station.status,
                                   station.variable, station.resolution,
                                   station.id, station.content])
        self.stations_path.append(station.path)
        self.stations_number += 1

    def average(self, orig=False, yearly=True):
        """Calculate the average climate variable value per year of all
        stations in the network.

        Parameters
        ----------
        orig : boolean, default False
            Calculate the same average for the corresponding original data.
        yearly : boolean, default True
            Average monthly data to yearly data.

        Returns
        -------
        ndarray or list of ndarray

        """
        self.setup()

        first = True
        for station in self.stations:
            # station.setup()

            if yearly:
                homog_data = station.data.mean(axis=1)
                if orig:
                    orig_data = station.orig.data.mean(axis=1)
            else:
                homog_data = station.data.copy()
                if orig:
                    orig_data = station.orig.data.copy()

            if first:
                netw_average = homog_data.copy()
                if orig:
                    orig_average = orig_data.copy()
                first = False
                continue
            netw_average += homog_data
            if orig:
                # this will preserve missing data
                orig_average += orig_data

        netw_result = netw_average / self.stations_number
        if orig:
            result = [netw_result, orig_average / self.stations_number]
        else:
            result = netw_result

        return result

    def skip_outliers(self, orig_path=None, yearly=True):
        """Opt out the values marked as outliers in the original data, in each
        station.

        Parameters
        ----------
        orig_path : string, optional
            Path to the original station file.
        yearly : boolean, default True
            Average monthly data to yearly data.

        """
        self.setup()
        for station in self.stations:
            station.setup(orig_path=orig_path, outliers=True)
            station.skip_outliers(yearly)

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

    def load_gsimcli(self, path, keys_path=None, ftype='data', status='xx',
                     variable='rr', resolution='r', content='c', yearly=True,
                     yearly_sum=False):
        """Load stations data from a file in the gsimcli format.

        """
        if not yearly:
            month = extract_month(path)

        if yearly and yearly_sum:
            div = 12.0
        else:
            div = 1.0

        xlsfile = pd.ExcelFile(path)
        xlstable = xlsfile.parse(sheetname='All stations', header=False,
                                 na_values=self.no_data, index_col=0)

        # filter out FLAG columns
        data_cols = [label for label in xlstable.columns if '_clim' in label]
        st_labels = [label.split('_')[0] for label in data_cols]

        # convert station ID keys
        if keys_path is not None and os.path.isfile(keys_path):
            self.load_keys(keys_path)
            station_ids = [str(self.keys.loc[int(stid)].values[0])
                           for stid in st_labels]
        else:
            station_ids = st_labels

        for i, station_col in enumerate(data_cols):
            stid = station_ids[i]
            data = pd.DataFrame(xlstable[station_col] / div)
            if data.iloc[0].values > 500:
                pass
            if not yearly:
                data.columns = [month]
            if stid in self.stations_id:
                st = self.station(stid)
                st.data = st.data.join(data)
            else:
                st = Station(no_data=self.no_data)
                st.path = None
                st.network_id = self.id
                st.ftype = ftype
                st.status = status
                st.variable = variable
                st.resolution = resolution
                st.content = content
                st.id = stid
                st.data = data
                self.add(st)

    def load_keys(self, path):
        """Read a TSV file with the keys to the converted station IDs.

        Parameters
        ----------
        path : string
            File path.

        """
        self.keys = pd.read_csv(path, sep='\t', index_col=0)

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
            st = Station(no_data=self.no_data)
            st.data = st_data
            st.id = format(station_id, '0=8.0f')
            st.ftype = ftype
            st.status = status
            st.variable = variable
            st.resolution = resolution
            st.content = content
            st.network_id = self.id
            self.stations.append(st)

    def station(self, stid):
        """Return the existing Station instance with the given ``stid`` ID.

        """
        for st in self.stations:
            if st.id == stid:
                return st

    def update_ids(self, keys_path=None):
        """Update every station ID according to the given keys.

        Useful when stations' ID's were replaced with a different number (for
        instance, because they were non numerical).

        Parameters
        ----------
        keys_path : string or pandas.Series, optional
            File path or Series containing ID's and the corresponding keys.

        """
        if keys_path is not None and os.path.isfile(keys_path):
            self.load_keys(keys_path)
        for i, station in enumerate(self.stations):
            station.id = self.keys.loc[station.id]
            self.stations_id[i] = station.id


class Submission(object):
    """Submission/Contribution to the COST-HOME benchark.

    Each instance of Submission should refer to a unique climate signal
    (temperature or precipitation).

    Attributes
    ----------
    path : string
        Folder path.
    no_data : number
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
    stations_id : list of int
        Unique station ID numbers contained in the submission. ID's relative to
        stations in different networks but with the same number count as one.
    orig_path : string
        Directory where the original station files are located.
    inho_path : string
        Directory where the inhomogeneous station files are located.

    """

    def __init__(self, path=None, no_data=-999.9, networks_id=None,
                 orig_path=None, inho_path=None):
        """Initialise a Submission instance.

        Parameters
        ----------
        path : string, optional
            Folder path.
        no_data : number, default -999.9
            Missing data value.
        networks_id : list of int, optional
            Network ID numbers contained in the submission.
        orig_path : string, optional
            Directory where the original station files are located.
        inho_path : string, optional
            Directory where the inhomogeneous station files are located.

        Notes
        -----
        The current implementation is filtering files parsed as `data` type and
        with content `d`.

        """
        self.no_data = no_data
        self.networks = list()
        self.networks_id = list()
        self.stations_number = 0
        self.stations_id = list()

        if path is not None:
            self.load_dir(path, networks_id)

        self.orig_path = orig_path
        self.inho_path = inho_path

    def add(self, network):
        """Add a network to the submission.

        Parameters
        ----------
        network : Network instance
            Network to be added to the submission.

        """
        self.networks.append(network)
        self.networks_id.append(network.id)
        self.stations_number += network.stations_number
        self.stations_id.extend(network.stations_id)
        self.stations_id = list(set(self.stations_id))

    def iter_stations(self):
        """Iterates over the stations in the Submission.

        """
        for network in self.networks:
            for station in network.stations:
                yield station

    def load(self):
        """Load all networks included in the submission.

        """
        for network in self.networks:
            network.setup()

    def load_dir(self, path, networks_id=None):
        """Load submission from a directory containing all the included
        networks, one per folder. The data files should be in the COST-HOME
        format.

        Parameters
        ----------
        path : string
            Folder path.
        networks_id : list of int, optional
            Network ID numbers contained in the submission.

        """
        self.path = path
        self.name = os.path.basename(os.path.dirname(path))
        self.signal = os.path.basename(path)
        parsed = pc.directory_walk_v1(path)
        selected = pc.files_select(parsed, network=networks_id,
                                   ftype='data', content='d')
        grouped = pc.agg_network(selected)

        for network in grouped:
            self.networks_id.append(network[0][1][0])
            self.networks.append(Network(network, self.no_data))
            self.stations_number += self.networks[-1].stations_number
            self.stations_id.extend(self.networks[-1].stations_id)

        self.stations_id = list(np.unique(self.stations_id))

    def load_gsimcli(self, gsimcli_results, keys_paths=None, yearly=True,
                     yearly_sum=False, orig_path=None, inho_path=None):
        """Load and initialise the results of a gsimcli process as a COST-HOME
        submission.

        Parameters
        ----------
        gsimcli_results : dict
            List of results files per network organised in a dictionary.
            Example:
                { '000005' : ['1.xls', '2.xls'],
                  '000009' : ['1.xls', '2.xls', '3.xls'] }
        keys_paths : array_like of string, optional
            Paths to the files containing the keys which converted the stations
            IDs. If given, it must have the same length as `gsimcli_results`.
        yearly : boolean, default True
            Average monthly data to yearly data.
        yearly_sum : boolean, default False
            Convert yearly summed data into monthly average.
        orig_path : string, optional
            Directory with the original files for the submission.
        inho_path : string, optional
            Directory with the inhomogised files for the submission.

        """
        # accept str or list of str
        if isinstance(keys_paths, str) or isinstance(keys_paths, unicode):
            keys_paths = [keys_paths]

        if keys_paths is not None:
            number_of_keys = len(keys_paths)
            number_of_results = len(gsimcli_results)
            if number_of_keys != number_of_results:
                raise ValueError("Mismatch between number of results files "
                                 "({0}) and keys_paths files ({1})").format(
                    number_of_keys, number_of_results)

        for i, network_id in enumerate(gsimcli_results.keys()):
            network = Network(no_data=self.no_data, network_id=network_id)

            if keys_paths is not None:
                keypath = keys_paths[i]
            else:
                keypath = None

            for results in gsimcli_results[network_id]:
                network.load_gsimcli(path=results, keys_path=keypath,
                                     yearly_sum=yearly_sum, yearly=yearly)
                # send update  # FIXME: not adjusted yet
                # update.current += 1
                # update.send()

            self.add(network)

        self.setup(orig_path, inho_path)

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

    def setup(self, outliers=False, breaks=False, orig_path=None,
              inho_path=None):
        """Load all networks (and its stations) in the submission.

        Set the original and the inhomogenised directories. Each one these
        should contain a folder for each network in the submission, where each
        network contains several stations.

        Parameters
        ----------
        outliers : boolean, default False
            Load corresponding outliers.
        breaks : boolean, default False
            Load corresponding break points.
        orig_path : string, optional
            Directory with the original files for the submission.
        inho_path : string, optional
            Directory with the inhomogised files for the submission.

        """
        self.load()
        if self.orig_path:
            orig_path = self.orig_path
        else:
            self.orig_path = orig_path
        if self.inho_path:
            inho_path = self.inho_path
        else:
            self.inho_path = inho_path

        if orig_path or inho_path:
            for network in self.networks:
                if orig_path:
                    orig_netw = os.path.join(orig_path, network.id)
                if inho_path:
                    inho_netw = os.path.join(inho_path, network.id)
                for station in network.stations:
                    # find file by id
                    file_pattern = os.sep + '*' + station.id + '*'
                    if orig_path:
                        orig_file = glob.glob(orig_netw + file_pattern)[0]
                        station.match_orig(orig_file)
                    if inho_path:
                        inho_file = glob.glob(inho_netw + file_pattern)[0]
                        station.match_inho(inho_file)
                    station.setup(outliers, breaks)


def extract_month(path):
    """Try to guess the month of a monthly gsimcli results file.
    Will recognize text abbreviatures (e.g., apr, oct) and numeric indexes
    (e.g., 04, 10).

    """
    months = set(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    filename = os.path.splitext(os.path.basename(path))[0]
    names = re.split('\W+|_', filename)
    names = set([name.capitalize() for name in names])

    return list(months & names)[0]


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
