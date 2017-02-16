# -*- coding: utf-8 -*-
"""
This module contains a class that implement methods for the detection of
irregularities and homogenisation of climate data, as well as other directly
related methods and functions.

Created on 20/04/2015

@author: julio
"""
import numpy as np
import pandas as pd
from tools.grid import PointSet


class Homogenisation(object):

    """This class controls the homogenisation process, its options, and holds
    the input and output data of the homogenisation process.

    Try to detect and homogenise irregularities in data series, following
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

    Attributes
    ----------
    grids : GridFiles object
        Instance of GridFiles type containing the geostatistical simulation
        results.

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

    References
    ----------
    .. [1] Costa, A., & Soares, A. (2009). Homogenization of climate data
        review and new perspectives using geostatistics. Mathematical
        Geosciences, 41(3), 291–305. doi:10.1007/s11004-008-9203-3

    """

    def __init__(self, params):
        """Constructor

        """
        self.filled_count = None
        self.obs = None
        self.obs_xy = None
        self.default_stats = {
            'lmean': True,
            'lmed': False,
            'lskew': False,
            'lperc': True,
            'rad': 0,
            'p': 0.95,
            'save': False,
        }

    def calculate_stats(self):
        """Calculate the necessary local statistics for the detection of
        irregularities.

        Parameters
        ----------

        """
        self.local_stats = self.grids.stats_area(self.obs_xy, **self.stats)

    def corrections(self):
        """Compute the values that will be used to homogenise irregularities,
        according to the previously specified method.

        Returns
        -------
        fix : array_like
            The values that will correct irregularities.

        """
        stats = self.local_stats
        if self.method == 'mean':
            fix = stats.values['mean'].values
        elif self.method == 'median':
            fix = stats.values['median'].values
        elif self.method == 'skewness' and self.skewness:
            fix = np.where(stats.values['skewness'] > self.skewness,
                           stats.values['median'],
                           stats.values['mean'])
        elif self.method == 'percentile':
            # allow a different percentile value for the detection and for the
            # correction
            if self.percentile != self.prob:
                self.grids.reset_read()
                kwargs = self.default_stats.copy()
                kwargs.update({'lmean': False, 'p': self.percentile})
                vline_perc = self.grids.stats_area(self.obs_xy, **kwargs)
            else:
                vline_perc = stats

            fix = np.where(self.obs.values['clim'] > stats.values['rperc'],
                           vline_perc.values['rperc'],
                           vline_perc.values['lperc'])

        self.fix = fix
        return fix

    def correct_irregularities(self):
        """Replace detected irregularities according to the selected method.

        Returns
        -------
        homogenised : PointSet object
            Instance of PointSet type containing the homogenised values.

        """
        self.homogenised = PointSet(self.obs.name + '_homogenised',
                                    self.obs.nodata, self.obs.nvars,
                                    list(self.obs.varnames),
                                    self.obs.values.copy())

        self.homogenised.values['clim'] = self.obs.values['clim'].where(
            self.detected, self.fix)

        return self.homogenised

    def detect_irregularities(self):
        """Detect irregularities.

        """
        self.detected = self.obs.values['clim'].between(
            self.local_stats.values['lperc'],
            self.local_stats.values['rperc'])
        self.detected_number = self.detected.sum()

    def fill_station(self, values=None, time_seq=None):
        """Look for missing values in a station and fill them with a given
        value.

        There is the need to check for this because the time series might be
        incomplete, e.g., considering the annual series, [1900, 1901, 1905,
        1906, 1907, 1908, 1910], there are four missing values.

        Parameters
        ----------
        values : array_like, optional
            Set of values which will be used to fill the target time series.
            Must have a length equal to the number of items in the time series.
            If not provided, the mean values will be used.
        time_seq: tuple of numbers, optional
            The first and last values in the desired time series and the space
            between them (min, max, step). If not provided, will use the grids
            dimensions (zi, zi + dz, cellz).

        """
        if self.obs.values.shape[0] < self.grids.dz:
            pass
        else:
            return self

        if values is None:
            values = self.mean_values()
        if time_seq is None:
            grid = self.grids
            time_seq = (grid.zi, grid.zi + grid.dz, grid.cellz)

        varcol = self.obs.varnames.index('clim')
        self.filled_count = 0
        j = 0
        timeserie = np.arange(*time_seq)
        filled = np.zeros((timeserie.shape[0], self.obs.values.shape[1]))
        for i, itime in enumerate(timeserie):
            if (j < len(self.obs.values['time']) and
                    itime == self.obs.values['time'].iloc[j]):
                filled[i, :] = self.obs.values.iloc[j, :]
                j += 1
            else:
                filled[i, :] = [self.obs.values.iloc[0, 0],
                                self.obs.values.iloc[0, 1],
                                itime,
                                self.obs.values.iloc[0, 3:varcol],
                                values[i],
                                ][:self.obs.values.shape[1]]
                self.filled_count += 1

        self.obs.values = pd.DataFrame(filled, columns=self.obs.values.columns)

    def flags(self):
        """Produce a flag for each record in the homogenised data set.

        It appends a new column named 'Flag' with the following values:
          - if no homogenisation took place in that cell, Flag = no_data_value
          - otherwise, Flag = observed_value

        """
        flag_col = self.obs.values['clim'].where(~self.detected,
                                                 self.obs.nodata)
        self.homogenised.nvars += 1
        self.homogenised.varnames.append('Flag')
        self.homogenised.values['Flag'] = flag_col

    def homogenise(self):
        """Perform the homogenisation process.

        """
        pass

    def load_candidate(self, obs_file, header=True):
        """Load the observated values at the candidate station.

        Parameters
        ----------
        obs_file : PointSet object or string
            Instance of PointSet type containing the observed values at the
            candidate station, or string with the full path to the PointSet
            file.
        header : boolean, default True
            True if `obs_file` has the GSLIB standard header lines. The
            resulting `homogenised` PointSet will follow.

        """
        if isinstance(obs_file, PointSet):
            self.obs = obs_file
        else:
            self.obs = PointSet()
            self.obs.load(obs_file, header)

        self.obs_xy = list(self.obs.values.iloc[0, :2])

    def mean_values(self):
        """Retrieve the mean values from previously calculated statistics.

        """
        if hasattr(self, "local_stats"):
            return pd.Series(self.local_stats.values['mean'].values,
                             name='clim')
        else:
            return None

    def remove_nodata(self):
        """Remove lines with no-data's and with flags. The no-data values are
        replaced with NaN's.

        """
        # remove lines with no-data and flags
        if 'Flag' in self.obs.values.columns:
            self.obs.values = self.obs.values.drop('Flag', axis=1)
        if 'Flag' in self.obs.varnames:
            self.obs.varnames.remove('Flag')
            self.obs.nvars -= 1
        # calculate the no-data's and replace them with NaN
        self.nodatas = self.obs.values['clim'].isin([self.obs.nodata]).sum()
        self.obs.values = self.obs.values.replace(self.obs.nodata, np.nan)

    def replace_nan(self, values=None):
        """Replace NaN's with given values. By default, it will replace with
        the mean values.

        Parameters
        ----------
        values : array_like, optional
            Set of values which will be used to fill the target time series.
            Must have a length equal to the number of items in the time series.
            If not provided, will use the mean values.

        """
        if values is None:
            values = self.mean_values()
        values.index = self.obs.values.index
        self.obs.values.update(values, overwrite=False)
        # self.obs.fillna(value=values, inplace=True)

    def set_method(self, method='mean', prob=0.95, rad=0, percentile=None,
                   skewness=None, save=False, outfile=None):
        """Set the method used to correct irregularities.

        Parameters
        ----------
        method : {'mean', 'median', 'skewness', 'percentile'} string, default
            'mean'
            Method for the inhomogeneities correction:
                - mean: replace detected irregularities with the mean of
                simulated values;
                - median: replace detected irregularities with the median of
                simulated values;
                - skewness: use the sample skewness to decide whether detected
                irregularities will be replaced by the mean or by the
                median of simulated values.
                - percentile : replace detected irregularities with the
                percentile `100 * (1 - p)`, for a given `p`.
        prob : float, default 0.95
            Probability value to build the detection interval centred in the
            local PDF.
        rad : number, default 0
            Tolerance radius used to search for neighbour nodes, used to
            calculate the local pdf's.
        percentile: float, optional
            p value used if correct_method == 'percentile'.
        skewness: float, optional
            Samples skewness threshold, used if `method == 'skewness'`, e.g.,
            1.5.
        save : boolean, default False
            Save intermediary PointSet files, one containing the homogenised
            values and the other containing simulated values at the candidate
            station location.
        outfile : string, optional
            Full path where the homogenised values will be saved if `save` is
            True. Simulated values at the candidates stations are saved in the
            directory used to store the simulated maps.

        """
        self.method = method
        self.prob = prob
        self.save = save
        self.outfile = outfile
        self.percentile = percentile

        # FIXME: lmean must always be True in order to fill missing data
        self.stats = self.default_stats.copy()
        self.stats.update({'rad': rad,
                           'p': prob,
                           'save': save})

        if method in ['mean', 'percentile']:
            pass
        if method == 'median':
            self.stats['lmed'] = True
        elif method == 'skewness' and skewness:
            self.stats['lmed'] = True
            self.stats['lskew'] = True
        else:
            raise ValueError('Method {0} invalid or incomplete.'
                             .format(method))
