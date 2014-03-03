# -*- coding: utf-8 -*-
"""
This module tries to reproduce the score functions used in the COST-HOME
benchmarking of homogenisation algorithms. [1]_

References
----------
.. [1] Venema, V., et al. (2012). Benchmarking homogenization algorithms for
    monthly data. Climate of the Past, 8(1), 89–115. doi:10.5194/cp-8-89-2012

Created on 21/01/2014

@author: julio
"""

import os
import shutil

import numpy as np
import pandas as pd
import parsers.costhome as ch
from parsers.spreadsheet import xls2costhome


def crmse(homog, orig, skip_years=None, centered=True):
    """Calculate the Centred Root-Mean-Square Error (CRMSE) between any pair of
    homogenised and original data sets.

    Parameters
    ----------
    homog : array_like
        Homogenised station data.
    orig : array_like
        Original station data.
    skip_years : array_like, optional
        Years not to consider.
    centered : boolean, default True
        Return RMSE or the centred RMSE.

    Returns
    -------
    ndarray
        CRMSE.

    Notes
    -----
    RMSE is commonly used in meteorology, to see how effectively a mathematical
    model predicts the behaviour of the atmosphere.

    The RMSD of an estimator :math:`{\hat{\\theta}}` with respect to an
    estimated parameter :math:`{\\theta}` is defined as the square root of the
    mean square error:

    .. math:: \operatorname{RMSE}(\hat{\\theta}) = \sqrt{\operatorname{MSE}
        (\hat{\\theta})} = \sqrt{\operatorname{E}((\hat{\\theta}-\\theta)^2)}.

    """
    if skip_years:
        orig = orig.select(lambda x: x not in skip_years)

    if centered:  # FIXME: something's wrong here
        homog -= homog.mean()
        orig -= orig.mean()
#    diff = (homog - orig).std()

    diff = np.sqrt(np.power((homog - orig), 2).mean())

    return diff


def crmse_station(station, skip_outliers=True, yearly=True):
    """Calculate the CRMSE of a given station.

    Parameters
    ----------
    station : Station object
        Instance of Station containing the homogenised data set.
    skip_outliers : boolean, default True
        Skip the years which have outlier values.
    yearly : boolean, default True
        Average monthly data to yearly data.

    Returns
    -------
    st_crmse : ndarray
        Station CRMSE.

    TODO: handle skip_outliers when resolution != 'y'

    See Also
    --------
    crmse_cl : Calculate CRMSE between any pair of homogenised and original
                 data sets.

    """
    station.setup()

    if yearly:
        homog = station.yearly('mean')
        orig = station.orig.yearly('mean')
    else:
        homog = station.data
        orig = station.orig.data

    skip_years = list()
    if skip_outliers:
        station.orig.load_outliers()
        skip_years = list(np.unique(station.orig.outliers.Year))

    st_crmse = crmse(homog, orig, skip_years)

    return st_crmse


def crmse_network(network, skip_missing=False, skip_outlier=True):
    """Calculate Network CRMSE.

    Parameters
    ----------
    network : Network object
        Instance of Network containing the network of homogenised stations.
    skip_missing : boolean, default False
        Do not consider the years in which any station in the network has
        missing values.
    skip_outlier : boolean, default True
        Do not consider the years in which any station in the network has
        outlier values.

    Returns
    -------
    netw_crmse : ndarray
        Network CRMSE.

    See Also
    --------
    crmse_cl : Calculate CRMSE between any pair of homogenised and original
                 data sets.

    """
    network.setup()
    homog, orig = network.average(orig=True)

    skip_years = network.skip_years(skip_missing, skip_outlier)

    netw_crmse = crmse(homog, orig, skip_years)

    return netw_crmse


def crmse_submission(submission, over_station=True, over_network=True,
                        skip_missing=False, skip_outlier=True):
    """Calculate the average CRMSE of a benchmark submission.

    The average can be calculated over all the stations and/or over the
    networks of a given submission.

    Parameters
    ----------
    submission : Submission object
        Instance of Submission containing the homogenised data sets.
    over_station : boolean, default True
        Calculate the submission's mean station CRMSE.
    over_network : boolean, default True
        Calculate the submission's mean network CRMSE.
    skip_missing : boolean, default False
        Do not consider the years in which any station in the network has
        missing values. Only used if `over_network` is True.
    skip_outlier : boolean, default True
        Do not consider the years in which any station in the network has
        outlier values.

    Returns
    -------
    results : list of ndarray
        List with mean station CRMSE and/or mean network CRMSE.

    """
    if over_network:
        # network_crmses = np.zeros(len(submission.networks))
        network_crmses = pd.Series(index=submission.networks_id,
                                   name='Network CRMSE')
    if over_station:
        # station_crmses = np.zeros(submission.stations_number)
        station_crmses = pd.DataFrame(index=submission.stations_id,
                                      columns=submission.networks_id)

    for network in submission.networks:
        if over_network:
            network_crmses.loc[network.id] = crmse_network(
                                        network, skip_missing, skip_outlier)

        if over_station:
            network.setup()
            for station in network.stations:
                station_crmses.loc[station.id, network.id] = crmse_station(
                                                    station, skip_outlier)

    results = list()
    if over_network:
        results.append(network_crmses.mean())
    if over_station:
        results.append(station_crmses.mean().mean())

    return results


def improvement(submission, over_station, over_network, skip_missing,
                   skip_outlier):
    """Calculate the improvement of a benchmark submission.

    The improvement over the inhomogeneous data is computed as the quotient
    of the mean CRMSE of the homogenized networks and the mean CRMSE of the
    same inhomogeneous networks.

    Parameters
    ----------
    submission : Submission object
        Instance of Submission containing the homogenised data sets.
    over_station : boolean, default True
        Calculate the submission's mean station CRMSE.
    over_network : boolean, default True
        Calculate the submission's mean network CRMSE.
    skip_missing : boolean, default False
        Do not consider the years in which any station in the network has
        missing values. Only used if `over_network` is True.
    skip_outlier : boolean, default True
        Do not consider the years in which any station in the network has
        outlier values.

    Returns
    -------
    list of ndarray
        Returns three lists, each with two elements:
        - [*network CRMSE*, *station CRMSE*],
        - [*inhomogenous network CRMSE*, *inhomogeneous stations CRMSE*],
        - [*network improvement*, station improvement*]

    """
    homog_crmse = crmse_submission(submission, over_station, over_network,
                                skip_missing, skip_outlier)

    inho_path = ch.match_sub(submission.path, 'inho', level=2)
    inho_sub = ch.Submission(inho_path, submission.md, submission.networks_id)
    inho_crmse = crmse_submission(inho_sub, over_station, over_network,
                                     skip_missing, skip_outlier)

    return homog_crmse, inho_crmse, list(
                             np.array(homog_crmse) / np.array(inho_crmse))


def gsimcli_improvement(gsimcli_results, nodata=-999.9, network_id=None,
                        variable='rr', yearly_sum=True, over_station=True,
                        over_network=True, skip_missing=False,
                        skip_outlier=True, keys=None, costhome_path=None,
                        costhome_save=False):
    """Calculate the improvement of a GSIMCLI process.

    It is just a wrapper around `improvement` and `xls2costhome`.

    TODO: support multiple networks simultaneously
    """
    if costhome_path is None:
        costhome_path = os.path.join(os.path.dirname(gsimcli_results),
                                     'costhome')
    if not os.path.exists(costhome_path):
        os.mkdir(costhome_path)

    if network_id is None:
        network_id = os.path.basename(os.path.dirname(costhome_path))[4:]

    xls2costhome(xlspath=gsimcli_results, outpath=costhome_path, nd=nodata,
            sheet='All stations', header=False, skip_rows=[1],
            network_id=network_id, status='ho', variable=variable,
            resolution='y', content='d', ftype='data', yearly_sum=yearly_sum,
            keys_path=keys)

    submission = ch.Submission(costhome_path, nodata)
    raw_input('break')
    results = improvement(submission, over_station, over_network, skip_missing,
                          skip_outlier)

    if not costhome_save:
        shutil.rmtree(costhome_path)

    return results


if __name__ == '__main__':
    md = -999.9

    macpath = '/Users/julio/Desktop/testes/cost-home/'
    mintpath = '/home/julio/Testes/'
    basepath = mintpath

    """ # inho syn1
    netw_path = basepath + 'benchmark/inho/precip/syn1'
    orig_path = basepath + 'benchmark/orig/precip/syn1'
    inho_path = basepath + 'benchmark/inho/precip/syn1'
    variable = 'rr'
    # """

    """ # inho sur1 precip
    # st 7.3 1.00 netw 3.1 1.00
    netw_path = basepath + 'benchmark/inho/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # inho sur1 temp
    # st 0.47 1.00 netw 0.20 1.00
    netw_path = basepath + 'benchmark/inho/temp/sur1'
    orig_path = basepath + 'benchmark/orig/temp/sur1'
    inho_path = basepath + 'benchmark/inho/temp/sur1'
    variable = None  # 'tn'
    # """

    """ # AnClim SNHT
    # st 0.52 1.02 netw 0.31 1.16
    netw_path = basepath + 'benchmark/h019/temp/sur1'
    orig_path = basepath + 'benchmark/orig/temp/sur1'
    inho_path = basepath + 'benchmark/inho/temp/sur1'
    variable = None  # 'tn'
    # """

    """ # MASH Marinova precip
    # st 3.6 0.56 netw 1.6 0.69
    netw_path = basepath + 'benchmark/h009/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # PRODIGE main precip
    # st 4.7 0.63 netw 3.3 1.07
    netw_path = basepath + 'benchmark/h002/precip/sur14'
    # """

    #""" # GSIMCLI
    #gsimcli_results = basepath + 'cost-home/rede000010/gsimcli_results.xls'
    gsimcli_results = basepath + 'cost-home/500_dflt_16_allvar_vmedia/rede000009/gsimcli_results.xls'
    network_id = '000009'
    kis = '/home/julio/Testes/cost-home/rede000009/keys.txt'
    # """

    #netw_path = basepath + 'benchmark/h011/precip/sur1'
    #network_id = ['000009', '000010']
    #sub = ch.Submission(netw_path, md, network_id)  # , ['000010'])
    # print crmse_submission_(sub, over_station=True, over_network=True,
    #                          skip_missing=False, skip_outlier=True)
#    print improvement(sub, over_station=True, over_network=True,
#                         skip_missing=False, skip_outlier=True)

    print gsimcli_improvement(gsimcli_results, md, network_id,
                              costhome_save=True, keys=kis)

    print 'done'
