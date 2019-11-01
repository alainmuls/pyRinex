#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import sys
from termcolor import colored
import numpy as np
import pandas as pd
import logging
from scipy.signal import argrelextrema

import am_config as amc
from ampyutils import amutils
from plot import signalDiffPlot
__author__ = 'amuls'


def treatCmdOpts(argv):
    """
    Treats the command line options and sets the global variables according to the CLI args

    :param argv: the options (without argv[0])
    :type argv: list of string
    """
    helpTxt = os.path.basename(__file__) + ' compares between similar signals of different navigation services'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)

    parser.add_argument('-d', '--dir', help='Directory of SBF file (defaults to .)', required=False, default='.', type=str)
    parser.add_argument('-f', '--files', help='Filenames of 2 CSV files to compare', nargs=2, required=True, type=str)
    parser.add_argument('-g', '--gnss', help='GNSS System Name', required=True, type=str)
    parser.add_argument('-s', '--signals', help='Signal names to compare', nargs=2, required=True, type=str)
    parser.add_argument('-m', '--movavg', help='moving average of difference [sec] (defaults 60s)', required=False, type=int, default=60)
    # parser.add_argument('-o', '--overwrite', help='overwrite daily SBF file (default False)', action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    args = parser.parse_args()

    return args.dir, args.files, args.gnss, args.signals, args.movavg, args.logging


def checkExistenceArgs(cvsDir: str, csvFiles: list, logger: logging.Logger) -> str:
    """
    checks if dir and csvFiles are accessible
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # change to the directory cvsDir if it exists
    wdir = os.getcwd()
    if cvsDir is not '.':
        wdir = os.path.normpath(os.path.join(wdir, cvsDir))
    logger.info('{func:s}: working diretory is {dir:s}'.format(func=cFuncName, dir=wdir))

    if not os.path.exists(wdir):
        logger.error('{func:s}: directory {dir:s} does not exists.'.format(func=cFuncName, dir=colored(wdir, 'red')))
        sys.exit(amc.E_DIR_NOT_EXIST)
    else:
        os.chdir(wdir)
        logger.info('{func:s}: changed to directory {dir:s}'.format(func=cFuncName, dir=wdir))

    # check if the given CSV csvFiles are accessible
    for file in csvFiles:
        if not os.access(file, os.R_OK):
            logger.error('{func:s}: CSV file {file:s} is not accessible.'.format(func=cFuncName, file=colored(file, 'red')))
            sys.exit(amc.E_FILE_NOT_ACCESSIBLE)

    return wdir


def mergeSignals(csvFiles: list, logger: logging.Logger) -> pd.DataFrame:
    """
    merge dataframes form bith signals into 1 dataframe
    """
    # read both files into separate dataframes
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    dfObs = []
    for i, csvFile in enumerate(csvFiles):
        dfObs.append(pd.read_csv(csvFile, sep=',', parse_dates=True))
        # get list of SVs for each signaltype
        dCSV[i]['SVs'] = dfObs[i].columns.values[1:]
        dCSV[i]['#SVs'] = len(dCSV[i]['SVs'])

        # rename the columns in each dataframe to reflect PRN-ST as column name
        colNames = dfObs[i].columns.values[1:] + '-{st:s}'.format(st=dCSV[i]['signal'])
        colNames = np.concatenate([['time'], colNames])
        dfObs[i].columns = colNames
        # show the dataframe
        amutils.logHeadTailDataFrame(df=dfObs[i], dfName=dCSV[i]['signal'], callerName=cFuncName, logger=logger)
        dfObs[i]['time'] = pd.to_datetime(dfObs[i]['time'], format='%Y-%m-%d %H:%M:%S')
        # print('type of time = {type!s}'.format(type=type(dfObs[i]['time'][0])))
        # sys.exit(0)

    # get list of unique SVs
    print(type(dCSV[1]['SVs']))
    dCSV['SVs'] = np.intersect1d(dCSV[0]['SVs'], dCSV[1]['SVs'])
    dCSV['#SVs'] = len(dCSV['SVs'])

    logger.info('{func:s}: information:\n{dict!s}'.format(dict=dCSV, func=cFuncName))

    # merge both dataframes on 'time'
    return pd.merge(dfObs[0], dfObs[1], on=['time'], how='outer')


def signalDifference(dfObs: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    calculate the difference between the signals
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # make the difference per SV
    dCSV['stats'] = {}
    for prn in dCSV['SVs']:
        logger.info('{func:s}: calculating signal {st0:s}-{st1:s} difference for PRN {prn!s}'.format(prn=prn, func=cFuncName, st0=dCSV[0]['signal'], st1=dCSV[1]['signal']))

        prnID = '{prn:s}'.format(prn=prn)
        prnMA = '{prn:s}-MA'.format(prn=prn)

        # difference column gets prn number as title
        dfObs[prnID] = dfObs['{prn:s}-{st0:s}'.format(prn=prn, st0=dCSV[0]['signal'])] - dfObs['{prn:s}-{st1:s}'.format(prn=prn, st1=dCSV[1]['signal'])]

        # add moving average
        dfObs[prnMA] = dfObs[prnID].rolling(window=dCSV['movavg']).mean()
        # amutils.logHeadTailDataFrame(df=dfObs, dfName='dfObs', callerName=cFuncName, logger=logger)
        # amutils.logHeadTailDataFrame(df=dfObs[prnMA], dfName='dfObs[prnMA]', callerName=cFuncName, logger=logger)
        print('dfObs.prnMA.values = {!s}'.format(dfObs[prnMA].values))
        # calculate the statistics for the moving average column for this prn
        dCSV['stats'][prnID] = {}
        dCSV['stats'][prnID]['count'] = dfObs[prnMA].count()
        dCSV['stats'][prnID]['mean'] = dfObs[prnMA].mean()
        dCSV['stats'][prnID]['max'] = dfObs[prnMA].max()
        dCSV['stats'][prnID]['min'] = dfObs[prnMA].min()

        # Find local peaks
        # dfObsMM = pd.DataFrame()
        # n = 30  # number of points to be checked before and after
        # dfObsMM['min'] = dfObs.iloc[argrelextrema(dfObs[prnMA].values, np.less_equal, order=n)[0]][prnMA]
        # dfObsMM['max'] = dfObs.iloc[argrelextrema(dfObs[prnMA].values, np.greater_equal, order=n)[0]][prnMA]

        # amutils.logHeadTailDataFrame(df=dfObsMM[['min', 'max']], dfName='dfObsMM', callerName=cFuncName, logger=logger)

        print('-' * 20)
        print(dCSV['stats'][prnID])
        print('=' * 20)

    return dfObs


def main(argv):
    """
    creates a combined SBF file from hourly or six-hourly SBF files
    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # treat command line options
    dirCSV, filesCSV, GNSSsyst, GNSSsignals, movAvg, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(os.path.basename(__file__), dir=dirCSV, logLevels=logLevels)

    # check if arguments are accepted
    workDir = checkExistenceArgs(cvsDir=dirCSV, csvFiles=filesCSV, logger=logger)

    # create dictionary with the current info
    global dCSV
    dCSV = {}
    dCSV['dir'] = workDir
    dCSV['gnss'] = GNSSsyst
    for i, (signal, csv) in enumerate(zip(GNSSsignals, filesCSV)):
        dCSV[i] = {'signal': signal, 'file': csv}
    dCSV['movavg'] = movAvg
    logger.info('{func:s}: information:\n{dict!s}'.format(dict=dCSV, func=cFuncName))

    # read and merge into a single dataframe
    dfObsMerged = mergeSignals(csvFiles=filesCSV, logger=logger)
    # create signalwise difference
    dfObsMerged = signalDifference(dfObs=dfObsMerged, logger=logger)
    amutils.logHeadTailDataFrame(df=dfObsMerged, dfName='dfObsMerged', callerName=cFuncName, logger=logger)

    # find max/min values for signals and for difference over all PRNs
    dCSV['dMax'] = amutils.divround((dfObsMerged[dCSV['SVs']].max()).max(), 5, 2.5)
    dCSV['dMin'] = amutils.divround((dfObsMerged[dCSV['SVs']].min()).min(), 5, 2.5)
    for i in [0, 1]:
        stCols = dCSV[i]['SVs'] + '-{st:s}'.format(st=dCSV[i]['signal'])

        dCSV[i]['max'] = amutils.divround(dfObsMerged[stCols].max().max(), 5, 2.5)
        dCSV[i]['min'] = amutils.divround(dfObsMerged[stCols].min().min(), 5, 2.5)

    logger.info('{func:s}: information:\n{dict!s}'.format(dict=dCSV, func=cFuncName))

    # create plots per prn
    signalDiffPlot.plotSignalDiff(dCsv=dCSV, dfSig=dfObsMerged, logger=logger)


if __name__ == "__main__":
    main(sys.argv)
