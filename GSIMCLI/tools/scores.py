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

import bottleneck as bn
import numpy as np
import pandas as pd
import parsers.costhome as ch
from interface.ui_utils import Updater


update = Updater()


def crmse(homog, orig, centered=True, crop=None):
    """Calculate the Centred Root-Mean-Square Error (CRMSE) between any pair of
    homogenised and original data sets.

    Parameters
    ----------
    homog : array_like
        Homogenised station data.
    orig : array_like
        Original station data.
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
    if crop is not None:
        homog = homog[crop:-crop]
        orig = orig[crop:-crop]

    # squeeze to support both dataframe's (monthly) and series (yearly)
    if centered:
        homog -= bn.nanmean(np.squeeze(homog.values))
        orig -= bn.nanmean(np.squeeze(orig.values))

    diff = np.sqrt(bn.nanmean(np.squeeze(np.power((homog - orig).values, 2))))

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

    See Also
    --------
    crmse_cl : Calculate CRMSE between any pair of homogenised and original
                 data sets.

    """
    station.setup()

    if skip_outliers:
        station.skip_outliers(yearly)

    if yearly:
        homog = station.yearly('mean')
        orig = station.orig.yearly('mean')
    else:
        homog = station.data
        orig = station.orig.data

    st_crmse = crmse(homog, orig)

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
    if skip_outlier:
        network.skip_outliers(yearly=yearly)
    homog, orig = network.average(orig=True, yearly=yearly)

    netw_crmse = crmse(homog, orig)

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
        st_crmse = station_crmses.sum().sum() / submission.stations_number
        results.append(st_crmse)

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


def gsimcli_improvement(gsimcli_results, no_data=-999.9, keys_path=None,
                        costhome_path=None, **kwargs):
    """Calculate the improvement of a GSIMCLI process.

    Parameters
    ----------
    gsimcli_results : dict
        List of results files per network organised in a dictionary. Example:
            { '000005' : ['1.xls', '2.xls'],
              '000009' : ['1.xls', '2.xls', '3.xls'] }
    no_data : number, default -999.9
        Missing data value.
    keys_path : string, optional
        Path to the file containing the keys which converted the stations IDs.
    costhome_path : string, optional
        Provide a path to a directory if you want to save the results files
        converted into the COST-HOME format.

    """
    # accept str or list of str
    if isinstance(keys_path, (str, unicode)):
        keys_path = [keys_path]

    if keys_path is not None:
        if len(keys_path) != len(gsimcli_results):
            raise ValueError("Mismatch between number of results files and "
                             "keys_path files")

    yearly = kwargs['yearly']
    yearly_sum = kwargs.pop("yearly_sum")

    submission = ch.Submission(no_data=no_data)

    for i, network_id in enumerate(gsimcli_results.keys()):
        network = ch.Network(no_data=no_data, network_id=network_id)

        if keys_path is not None:
            key = keys_path[i]
        else:
            key = None

        if yearly:
            results_paths = [gsimcli_results[network_id]]
        else:
            results_paths = gsimcli_results[network_id]

        for results in results_paths:
            network.load_gsimcli(path=results, keys_path=key,
                                 yearly_sum=yearly_sum,
                                 yearly=yearly)
            # send update
            update.current += 1
            update.send()

        submission.add(network)

    orig_path = kwargs.pop("orig_path")
    inho_path = kwargs.pop("inho_path")

    submission.setup(orig_path, inho_path)

    if inho_path:
        results = improvement(submission, **kwargs)
    else:
        results = [crmse_submission(submission, **kwargs)]

    if costhome_path:
        submission.save(costhome_path)

    update.reset()
    return results


def cost_improvement(network_path, networks_id=None, no_data=-999.9, **kwargs):
    """Calculate the improvement of a COST-HOME submission.

    Parameters
    ----------
    network_path : string
        Path to the directory containing the networks folders.
    no_data : number, default -999.9
        Missing data value.

    """
    orig_path = kwargs.pop("orig_path")
    inho_path = kwargs.pop("inho_path")
    submission = ch.Submission(network_path, no_data, networks_id, orig_path,
                               inho_path)

    if inho_path:
        results = improvement(submission, **kwargs)
    else:
        results = [crmse_submission(submission, **kwargs)]

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

    # """ # MASH Marinova precip
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
    import glob

    rede5 = glob.glob('/home/julio/Área de Trabalho/testes 5+9/d095c095_xls/5/' + '*.xls')
    rede9 = glob.glob('/home/julio/Área de Trabalho/testes 5+9/d095c095_xls/9/' + '*.xls')
    gsimcli_results = {'000005': rede5,
                       '000009': rede9}

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
#                       skip_missing=False, skip_outlier=True, yearly=True)

    print gsimcli_improvement(gsimcli_results, yearly_sum=True,
                              keys_path=kis, orig_path=orig_path, inho_path=inho_path,
                              yearly=False)

    print 'done'
