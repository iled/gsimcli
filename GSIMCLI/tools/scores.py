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
import tempfile

import numpy as np
import pandas as pd
import parsers.costhome as ch
from interface.ui_utils import Updater
from parsers.spreadsheet import xls2costhome


update = Updater()


def crmse(homog, orig, skip_years=None, centered=True, crop=None):
    """Calculate the Centred Root-Mean-Square Error (CRMSE) between any pair of
    homogenised and original data sets.

    Parameters
    ----------
    homog : array_like
        Homogenised station data.
    orig : array_like
        Original station data.
    skip_years : array_like, optional
        Years not to be considered.
    centered : boolean, default True
        Return RMSE or the centred RMSE.
    crop : int, optional
        Do not consider the first and the last `crop` years.

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

    if crop is not None:
        homog = homog[crop:-crop]
        orig = orig[crop:-crop]

    if centered:  # FIXME: something's wrong here
        homog -= homog.mean().mean()
        orig -= orig.mean().mean()
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

    if not yearly:
        st_crmse = st_crmse.mean()

    return st_crmse


def crmse_network(network, skip_missing=False, skip_outlier=True, yearly=True):
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
    yearly : boolean, default True
        Average monthly data to yearly data.

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
    homog, orig = network.average(orig=True, yearly=yearly)

    skip_years = network.skip_years(skip_missing, skip_outlier)

    netw_crmse = crmse(homog, orig, skip_years)

    if not yearly:
        netw_crmse = netw_crmse.mean()

    return netw_crmse


def crmse_submission(submission, over_station=True, over_network=True,
                     skip_missing=False, skip_outlier=True, yearly=True):
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
    yearly : boolean, default True
        Average monthly data to yearly data.

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
            network_crmses.loc[network.id] = crmse_network(network,
                                                           skip_missing,
                                                           skip_outlier,
                                                           yearly)
            # send update
            update.current += 1
            update.send()

        if over_station:
            network.setup()
            for station in network.stations:
                loc = station.id, network.id
                station_crmses.loc[loc] = crmse_station(station, skip_outlier,
                                                        yearly)
                # send update
                update.current += 1
                update.send()

    results = list()
    if over_network:
        results.append(network_crmses.mean())
    if over_station:
        results.append(station_crmses.mean().mean())

    return results


def improvement(submission, **kwargs):
    """Calculate the improvement of a benchmark submission.

    The improvement over the inhomogeneous data is computed as the quotient
    of the mean CRMSE of the homogenised networks and the mean CRMSE of the
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
    yearly : boolean, default True
        Average monthly data to yearly data.

    Returns
    -------
    list of ndarray
        Returns three lists, each with two elements:
        - [*network CRMSE*, *station CRMSE*],
        - [*inhomogenous network CRMSE*, *inhomogeneous stations CRMSE*],
        - [*network improvement*, station improvement*]

    """
    homog_crmse = crmse_submission(submission, **kwargs)

    if not submission.inho_path:
        inho_path = ch.match_sub(submission.path, 'inho', level=2)
    else:
        inho_path = submission.inho_path
    inho_sub = ch.Submission(inho_path, submission.no_data,
                             submission.networks_id)
    inho_crmse = crmse_submission(inho_sub, **kwargs)

    improve = list(np.array(homog_crmse) / np.array(inho_crmse))
    # send update
    update.current += 1
    update.send()

    return homog_crmse, inho_crmse, improve


def gsimcli_improvement(gsimcli_results, no_data=-999.9, network_ids=None,
                        keys=None, costhome_path=None, costhome_save=False,
                        **kwargs):
    """Calculate the improvement of a GSIMCLI process.

    It is just a wrapper around `improvement` and `xls2costhome`.

    """
    # accept str or list of str
    if (isinstance(gsimcli_results, str) or
            isinstance(gsimcli_results, unicode)):
        gsimcli_results = [gsimcli_results]
    if isinstance(network_ids, str) or isinstance(network_ids, unicode):
        network_ids = [network_ids]
    if isinstance(keys, str) or isinstance(keys, unicode):
        keys = [keys]

    if network_ids is not None:
        if len(network_ids) != len(gsimcli_results):
            raise ValueError("Mismatch between number of results files and "
                             "networks ID's")

    if keys is not None:
        if len(keys) != len(gsimcli_results):
            raise ValueError("Mismatch between number of results files and "
                             "keys files")

    if not bool(costhome_path):
        costhome_path = tempfile.mkdtemp(prefix="gsimcli_")

    yearly_sum = kwargs.pop("yearly_sum")
    for i, results in enumerate(gsimcli_results):
        if network_ids is None:
            # FIXME: only working for "redeXXXXXX"
            network_id = os.path.basename(os.path.dirname(results))[4:]
        else:
            network_id = network_ids[i]

        if keys is not None:
            key = keys[i]

        xls2costhome(xlspath=results, outpath=costhome_path,
                     sheet='All stations', header=False, skip_rows=None,
                     network_id=network_id, status='ho', variable='rr',
                     resolution='y', content='d', ftype='data', keys_path=key,
                     yearly_sum=yearly_sum, **kwargs)
        # send update
        update.current += 1
        update.send()

    submission = ch.Submission(costhome_path, no_data, network_ids)
    orig_path = kwargs.pop("orig_path")
    inho_path = kwargs.pop("inho_path")
    submission.setup(orig_path, inho_path)

    results = improvement(submission, **kwargs)

    if not costhome_save:
        shutil.rmtree(costhome_path)

    update.reset()
    return results


if __name__ == '__main__':
    md = -999.9

    macpath = '/Users/julio/Desktop/testes/'
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
    # yearly: st 3.6 0.56 netw 1.6 0.69
    # monthly: st 8.5 0.84 netw 3.8 1.03
    netw_path = basepath + 'benchmark/h009/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    variable = 'rr'
    # """

    """ # PRODIGE main precip
    # st 4.7 0.63 netw 3.3 1.07
    netw_path = basepath + 'benchmark/h002/precip/sur1'
    orig_path = basepath + 'benchmark/orig/precip/sur1'
    inho_path = basepath + 'benchmark/inho/precip/sur1'
    # """

    """ # GSIMCLI yearly
    # gsimcli_results = basepath + 'cost-home/rede000010/gsimcli_results.xls'
    # gsimcli_results = basepath + 'cost-home/500_dflt_16_allvar_vmedia/rede000009/gsimcli_results.xls'
    gsimcli_results = [basepath + 'cost-home/rede000005/gsimcli_results.xls',
                       basepath + 'cost-home/rede000009/gsimcli_results.xls']
    # network_id = '000009'
    kis = [basepath + 'cost-home/rede000005/keys.txt',
           basepath + 'cost-home/rede000009/keys.txt']
    orig_path = basepath + "/benchmark/orig/precip/sur1"
    inho_path = basepath + "/benchmark/inho/precip/sur1"
    # """

    # """ # GSIMCLI monthly
    gsimcli_results = [basepath + 'cost-home/rede000005/gsimcli_results.xls',
                       basepath + 'cost-home/rede000009/gsimcli_results.xls']
    # network_id = '000009'
    kis = [basepath + 'cost-home/rede000005/keys.txt',
           basepath + 'cost-home/rede000009/keys.txt']
    orig_path = basepath + "/benchmark/orig/precip/sur1"
    inho_path = basepath + "/benchmark/inho/precip/sur1"
    # """

#    netw_path = basepath + 'benchmark/h011/precip/sur1'
    # network_id = ['000009', '000010']
#     sub = ch.Submission(netw_path, md,  # ['000009', '000005'],
#                         orig_path=orig_path, inho_path=inho_path)  # , ['000010'])
#     print improvement(sub, over_station=True, over_network=True,
#                       skip_missing=False, skip_outlier=True, yearly=False)

    print gsimcli_improvement(gsimcli_results, costhome_save=True, yearly_sum=True,
                              keys=kis, orig_path=orig_path, inho_path=inho_path)

    print 'done'
