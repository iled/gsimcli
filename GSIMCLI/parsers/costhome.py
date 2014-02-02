'''
Created on 28/01/2014

@author: julio
'''

import glob
import itertools
import os
import warnings

import numpy as np
import parsers.cost as pc
import tools.utils as ut


class Station(object):
    """Station container.

    TODO: separate quality flag from data
    """
    def __init__(self, path, md):
        """ Constructor

        """
        self.path = path
        self.md = md
        self.network_id = os.path.basename(os.path.dirname(path))

        if type(path) == str and os.path.isfile(path):
            spec = pc.filename_parse(path)
        else:
            spec = path[1]

        (self.ftype, self.status, self.variable, self.resolution,
         self.id, self.content) = spec

    def load(self, path=None, content=None):
        """Load station data file.

        """
        if type(path) == str and os.path.isfile(path) and content:
            if content == 'd':
                self.data = pc.datafile(self.path, self.resolution, self.md)
            elif content == 'f':
                self.quality = pc.qualityfile(self.path, self.resolution)
        elif self.ftype != 'data':
            raise ValueError('The file {} was not parsed as a data file.'.
                             format(self.path))
        elif self.content == 'd':
            self.data = pc.datafile(self.path, self.resolution, self.md)
        elif self.content == 'f':
            self.quality = pc.qualityfile(self.path, self.resolution)

    def load_outliers(self, path=None):
        """List of the dates with detected outliers.

        """
        if type(path) == str and os.path.isfile(path):
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
        """Try to fetch the matching ORIG station.

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
        """Try to fetch the matching INHO station.

        """
        if path:
            self.inho = Station(path, self.md)
            if self.id != self.inho.id:
                warnings.warn('mismatch between Station and INHO IDs')
            if self.network_id != self.inho.network_id:
                warnings.warn('mismatch between Station and INHO networks')
        else:
            self.inho = Station(match_sub(path, 'inho'), self.md)

    def yearly(self, func='mean'):
        """Upscale data resolution to yearly.

        TODO: check when resolution != monthly
        """
        if not hasattr(self, 'data'):
            raise ValueError('no loaded data')
        if func == 'mean':
            return self.data.mean(axis=1)
        elif func == 'sum':
            return self.data.sum(axis=1)

    def setup(self, outliers=False, inho=False):
        """Load data, orig and outliers.
        No option to load from a non default path.

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


class Network(object):
    """Network container.

    """
    def __init__(self, path, md):
        """Constructor.

        TODO: handle other files besides data?
        """
        self.path = path
        self.md = md
        if type(path) == str and os.path.isdir(path):
            parsed = pc.directory_walk_v1(path)
            selected = pc.files_select(parsed, ftype='data', content='d')
        else:
            selected = path

        self.id = selected[0][1][0]
        self.stations_id = list()
        self.stations_spec = list()
        self.stations_path = list()
        self.stations_number = len(selected)

        for station in selected:
            self.stations_id.append(station[1][5])
            self.stations_spec.append(station[1])
            self.stations_path.append(station[0])

    def load_stations(self):
        """Load all the stations in the network.
        Note that the date iself has to be explicitily loaded.
        """
        self.stations = list()
        for station in self.stations_path:
            self.stations.append(Station(station, self.md))

    def average(self, orig=False):
        """Calculate the average per year of all stations in the network.
        Option to calculate the same average for the corresponding ORIG data.

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
        """List of the years where any station in the network has missing data
        and/or has an outlier.
        Missing data and outliers are both retrieved from the station's ORIG.

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
        """Load stations.
        No option to load from a non default path.

        """
        if not hasattr(self, 'stations'):
            self.load_stations()


class Submission(object):
    """Submission/Contribution container, for a unique climate signal
    (temperature or precipitation).

    """
    def __init__(self, path, md, networks=None):
        self.path = path
        self.md = md
        self.name = os.path.basename(os.path.dirname(path))
        self.signal = os.path.basename(path)
        parsed = pc.directory_walk_v1(path)
        selected = pc.files_select(parsed, network=networks, ftype='data',
                                   content='d')
        grouped = pc.agg_network(selected)
        self.networks = list()
        self.networks_id = list()
        self.stations_number = 0

        for network in grouped:
            self.networks_id.append(network[0][1][0])
            self.networks.append(Network(network, md))
            self.stations_number += self.networks[-1].stations_number


def match_sub(path, sub, level=3):
    """Try to fetch the matching submission sub station.

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
