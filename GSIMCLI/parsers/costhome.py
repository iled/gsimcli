'''
Created on 28/01/2014

@author: julio
'''

import glob
import os
import warnings

import numpy as np
import parsers.cost as pc
import tools.utils as ut


class Station(object):
    """Station container.

    """
    def __init__(self, path, md):
        """ Constructor

        """
        self.path = path
        self.md = md

        if os.path.isfile(path):
            spec = pc.filename_parse(path)
        else:
            spec = path[1]

        (self.network, self.ftype, self.status, self.variable, self.resolution,
         self.id, self.content) = spec

    def load(self, path=None, content=None):
        """Load station data file.

        """
        if os.path.isfile(path) and content:
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
        if os.path.isfile(path):
            detected_file = path
        else:
            os.chdir(os.path.dirname(self.path))
            detected_file = glob.glob('*detected.txt')[0]

        detected = pc.breakpointsfile(detected_file)
        self.outliers = detected[((detected.Station == self.id) &
                                  (detected.Type == 'OUTLIE'))].ix[:, 2:]

    def match_orig(self, path=None):
        """Try to fetch the matching ORIG station.

        """
        if path:
            self.orig = Station(path, self.md)
            if self.id != self.orig.id:
                warnings.warn('Mismatch between Station and ORIG IDs')
            if self.network != self.orig.network:
                warnings.warn('Mismatch between Station and ORIG networks')
        else:
            self.orig = Station(match_sub(path, 'orig'), self.md)
            
    def match_inho(self, path=None):
        """Try to fetch the matching INHO station.

        """
        if path:
            self.inho = Station(path, self.md)
            if self.id != self.inho.id:
                warnings.warn('Mismatch between Station and INHO IDs')
            if self.network != self.inho.network:
                warnings.warn('Mismatch between Station and INHO networks')
        else:
            self.inho = Station(match_sub(path, 'inho'), self.md)


class Network(object):
    """Network container.

    """
    def __init__(self, path, md):
        """Constructor.

        TODO: handle other files besides data?
        """
        self.path = path
        self.md = md
        if os.path.isdir(path):
            parsed = pc.directory_walk_v1(path)
            selected = pc.files_select(parsed, ftype='data')
        else:
            selected = path

        self.id = selected[0][1][0]
        self.stations_id = list()
        self.stations_spec = list()
        self.stations_path = list()

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

    def average(self):
        """Calculate the average per year of all stations the network.

        """
        if not hasattr(self, 'stations'):
            self.load_stations()

        first = True
        for station in self.stations:
            station.load()
            if first:
                netw_average = np.zeros(station.data.shape[0])
                netw_average = station.data.mean(axis=1)
                first = False
                continue
            netw_average += station.data.mean(axis=1)

        return netw_average / len(self.stations)


class Submission(object):
    """Submission/Contribution container, for a unique climate signal
    (temperature or precipitation).

    """
    def __init__(self, path, md):
        self.path = path
        self.md = md
        self.name = os.path.basename(os.path.dirname(path))
        self.signal = os.path.basename(path)
        parsed = pc.directory_walk_v1(path)
        selected = pc.files_select(parsed, ftype='data')
        grouped = pc.agg_network(selected)
        self.networks = list()
        self.networks_id = list()

        for network in grouped:
            self.networks.append(network[0][1][0])
            self.networks.append(Network(network))


def match_sub(path, sub):
    """Try to fetch the matching submission sub station.

    """
    subpath, signalpath = ut.path_up(path, 3)
    benchpath, subm = os.path.split(subpath)
    match = os.path.join(benchpath, sub, signalpath)
    if not os.path.isfile(match):
        raise os.error('No such file: \'{}\''.format(match))
            
    return match