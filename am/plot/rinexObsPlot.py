import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import dates
import numpy as np

import xarray
import sys
import os
from pandas.plotting import register_matplotlib_converters
import datetime
import logging
from termcolor import colored

from rinex import rinex_observables as rnxobs
from plot import plot_utils

register_matplotlib_converters()


def plotRinexObservables(dPlot: dict, obsData: xarray.Dataset, logger=logging.Logger):
    """
    plots the observales according to the selection made
    each plot combines separate plots for each signalType selected for all satellites
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: start plotting\n{plt!s}'.format(plt=dPlot, func=cFuncName))

    # deterimne layout of subplots according to number of signals we have to plot
    dSubPlotsLayout = {
        1: [1, 1],
        2: [2, 1],
        3: [3, 1],
        4: [2, 2],
        5: [3, 2],
        6: [3, 3],
        7: [4, 3],
        8: [4, 4]
    }

    # specify the style
    mpl.style.use('seaborn')

    # find the signalType to which each signal belongs
    sigTypes = []
    for signal in dPlot['Signals']:
        sigType = list(set(rnxobs.findKeyOfSignal(signal, dict(rnxobs.dGAL, **rnxobs.dGPS))))
        logger.info('{func:s}: signal = {sign!s}   signal type = {sigt!s}'.format(sign=signal, sigt=sigType, func=cFuncName))
        sigTypes.append(sigType)

    # get rid of list of lists to get 1 list
    flatSigTypes = [item for sublist in sigTypes for item in sublist]
    # get the unique signal types out of this list
    uniqSigTypes = list(set(flatSigTypes))
    logger.info('{func:s}: plot signal types (all)  = {sigt!s}'.format(sigt=flatSigTypes, func=cFuncName))
    logger.info('{func:s}: plot signal types (uniq) = {sigt!s}'.format(sigt=uniqSigTypes, func=cFuncName))

    # the x-axis is a time axis, set its limits
    tLim = [dPlot['Time']['start'], dPlot['Time']['end']]
    logger.info('{func:s}: time limits = {tlim!s}'.format(tlim=tLim, func=cFuncName))

    # create 1 plot for each uniq signalType with subplots for each signal of that sigType we have
    for i, sigType in enumerate(uniqSigTypes):
        logger.info('{func:s}: ----------------------'.format(func=cFuncName))
        logger.info('{func:s}: making plot for signal type {name!s} ({sigt:s})'.format(sigt=sigType, name=rnxobs.dSignalTypesNames[sigType]['name'], func=cFuncName))

        # count the number of signals of this type to determine # of subplots
        nrSubPlotsSigType = len([v for v in flatSigTypes if v == sigType])
        logger.info('{func:s}: sub plots created = {nrplt!s}'.format(nrplt=nrSubPlotsSigType, func=cFuncName))

        # generate the subplots and its axes
        nrRows = dSubPlotsLayout[nrSubPlotsSigType][0]
        nrCols = dSubPlotsLayout[nrSubPlotsSigType][1]
        logger.info('{func:s}: plot layout - rows={row:d} columns={col:d}'.format(row=nrRows, col=nrCols, func=cFuncName))

        fig, axes = plt.subplots(nrows=nrRows, ncols=nrCols, sharex='col', sharey='row')
        fig.set_size_inches(18.5, 10.5)

        logger.debug('{func:s}: axes = {ax!s}'.format(ax=axes, func=cFuncName))
        # axes_list = [item for sublist in axes for item in sublist]

        # find indices for signals of this signalType
        indexSigType = [index for index, st in enumerate(flatSigTypes) if st == sigType]
        logger.info('{func:s}: index for signal type = {ist!s}'.format(ist=indexSigType, func=cFuncName))

        # determine the discrete colors for SVs
        colormap = plt.cm.nipy_spectral  # I suggest to use nipy_spectral, Set1,Paired
        # colormap = plt.cm.Spectral  #I  suggest to use nipy_spectral, Set1,Paired
        colors = [colormap(i) for i in np.linspace(0, 1, dPlot['#SVs'])]
        logger.debug('{func:s}: colors = {colors!s}'.format(colors=colors, func=cFuncName))

        # create the subplots for each signal of this sigType
        for indexAxes, indexSignal in enumerate(indexSigType):
            # get the axes to plot onto
            logger.info('\n{func:s}: index axis = {iax:d}  index signal = {isg:d}'.format(iax=indexAxes, isg=indexSignal, func=cFuncName))
            axRow, axCol = divmod(indexAxes, nrCols)
            logger.info('{func:s}: axis #row = {row:d} #column = {col:d}'.format(row=axRow, col=axCol, func=cFuncName))
            try:
                ax = axes[axRow, axCol]
            except IndexError as e:
                logger.info('{func:s}: {err!s}'.format(err=colored(e, 'red'), func=cFuncName))
                ax = axes[axRow]
            except TypeError as e:
                logger.info('{func:s}: {err!s}'.format(err=colored(e, 'red'), func=cFuncName))
                ax = axes

            # add a UE RESTREINT
            if (axCol == 0 and axRow == 0) or (axCol == nrCols-1 and axRow == nrRows-1):
                ax.annotate(r'$\copyright$ Alain Muls - RESTREINT UE/EU RESTRICTED', xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', fontsize='large', color='red')

            # get the name of the signal to plot on this axis
            signal = dPlot['Signals'][indexSignal]
            # get time interval
            timeInterval = [datetime.datetime.strptime(dPlot['Time']['start'], "%Y-%m-%dT%H:%M:%S"), datetime.datetime.strptime(dPlot['Time']['end'], "%Y-%m-%dT%H:%M:%S")]
            logger.info('{func:s}: Plotting signal {!s} over interval {time!s}'.format(signal, time=timeInterval, func=cFuncName))
            logger.info('{func:s}: for satellites {svs!s} (#{nr:d})'.format(svs=dPlot['SVs'], nr=len(dPlot['SVs']), func=cFuncName))

            for iSV, sv in enumerate(dPlot['SVs']):
                obsData_time = obsData.sel(time=slice(timeInterval[0], timeInterval[1]))
                logger.info('{func:s} ... plotting satellite {sv:s}'.format(sv=sv, func=cFuncName))

                # determine color for this SV by taking the color with th eindex of SV in AllSVs list
                colorSV = colors[dPlot['AllSVs'].index(sv)]

                ax.plot(obsData_time.time, obsData_time[signal].sel(sv=sv), label='{sv:s}'.format(sv=sv), color=colorSV, marker='.', markersize=3, linestyle='')

            # add a legend the plot showing the satellites displayed
            ax.legend(loc='best', ncol=16, markerscale=6)

            # find name of the signal in each constellation and use this for subplot title
            subTitle = 'Datafile {name:s}: '.format(name=os.path.basename(dPlot['name']))
            if any([sv for sv in dPlot['SVs'] if sv.startswith('E')]):
                subTitle += subTitleGNSS(dGNSS=rnxobs.dGAL, signal=signal, logger=logger)
            if any([sv for sv in dPlot['SVs'] if sv.startswith('G')]):
                subTitle += subTitleGNSS(dGNSS=rnxobs.dGPS, signal=signal, logger=logger)
            logger.info('{func:s}: plot subtitle {sub:s}'.format(sub=subTitle, func=cFuncName))

            # adjust the titles for the subplots
            ax.set_title(subTitle, fontsize=11)
            # ax.set_xlabel('Time')
            if axCol == 0:
                ax.set_ylabel('{name:s} {unit:s}'.format(name=rnxobs.dSignalTypesNames[sigType]['name'], unit=rnxobs.dSignalTypesNames[sigType]['unit']), fontsize=11)

            if signal.startswith('S'):
                ax.set_ylim([20, 60])

            # create the ticks for the time axis
            dtFormat = plot_utils.determine_datetime_ticks(startDT=timeInterval[0], endDT=timeInterval[1])

            if dtFormat['minutes']:
                ax.xaxis.set_major_locator(dates.MinuteLocator(byminute=[0, 15, 30, 45], interval=1))
            else:
                ax.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
            ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

            ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
            ax.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

            ax.xaxis.set_tick_params(rotation=0)
            for tick in ax.xaxis.get_major_ticks():
                # tick.tick1line.set_markersize(0)
                # tick.tick2line.set_markersize(0)
                tick.label1.set_horizontalalignment('center')

        # set title
        fig.suptitle(rnxobs.dSignalTypesNames[sigType]['name'], fontsize=16)

        # fig.tight_layout()
        fig.subplots_adjust(top=0.925)

        # save the figure (add satellite number is total satellites in plot is < 3)
        baseName = os.path.basename(dPlot['name'])
        dirName = os.path.dirname(dPlot['name'])
        os.makedirs(os.path.join(dirName, 'png'), exist_ok=True)
        if len(dPlot['SVs']) < 4:
            listSVs = '-'.join(dPlot['SVs'])
            figName = os.path.join(dirName, 'png', '{base:s}-{name:s}-{list:s}'.format(base=baseName, name=rnxobs.dSignalTypesNames[sigType]['name'], list=listSVs))
        elif dPlot['#SVs'] == len(dPlot['SVs']):
            listSVs = 'ALL'
            figName = os.path.join(dirName, 'png', '{base:s}-{name:s}-{list:s}'.format(base=baseName, name=rnxobs.dSignalTypesNames[sigType]['name'], list=listSVs))
        else:
            figName = os.path.join(dirName, 'png', '{base:s}-{name:s}'.format(base=baseName, name=rnxobs.dSignalTypesNames[sigType]['name']))

        # figName += '{start:s}'.format(start=datetime.datetime.strptime(dPlot['Time']['start'], "%Y-%m-%dT%H:%M:%S"))
        # figName += '{end:s}'.format(end=datetime.datetime.strptime(dPlot['Time']['end'], "%Y-%m-%dT%H:%M:%S"))
        tmpName = figName.replace(' ', '-')
        tmp2Name = tmpName.replace('.', '-')
        tmpName = tmp2Name.replace('_', '')
        figName = tmpName + '.png'
        fig.savefig(figName, dpi=100)

        logger.info('{func:s}: plot saved as {name:s}'.format(name=figName, func=cFuncName))

        plt.show()

    # # tlim=['2017-02-23T12:59', '2017-02-23T13:13']
    # ax = figure().gca()
    # # Suppose L1C pseudorange plot is desired for G13:

    # # ax.plot(self.obsData.time, self.obsData[dPlot['Signals']].sel(sv=dPlot['SVs']).dropna(dim='time',how='all'))

    # ax.plot(self.obsData.time, self.obsData['C1C'].sel(sv=['G02', 'E02']))
    # show()

    # fig, ax = plt.subplots(nrows=2, ncols=2)

    # for row in ax:
    #     for col in row:
    #         col.plot(x, y)

    # plt.show()

    # # ax.plot(self.obsData.time, self.obsData['C2L'].sel(sv=['G02', 'E02']))
    # # show()


def subTitleGNSS(dGNSS: dict, signal: str, logger: logging.Logger) -> str:
    """
    subTitleGNSS returns the subtitle valid for this GNSS
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    path = []
    rnxobs.path2Dict = None

    # walk through the dict to find the sub-dict to which the signal belongs
    rnxobs.walk(dGNSS, path, signal)

    if rnxobs.path2Dict is not None:
        subDicts = rnxobs.path2Dict.split('.')[:-1]  # drop key/value pair

        dSub1 = dGNSS[subDicts[0]]
        dSub2 = dSub1[subDicts[1]]

        # get the elements for subplot title
        subTitleGNSS = '{syst:s} {navsv:s} - {signal:s} - {freq:.3f} MHz  '.format(syst=dGNSS['name'], navsv=dSub2['name'], signal=signal, freq=dSub1['freq'])

        logger.info('{func:s}: subDicts = {!s}'.format(subDicts, func=cFuncName))
        logger.info('{func:s}: dGal-path = {!s}'.format(dGNSS[subDicts[0]][subDicts[1]], func=cFuncName))
        logger.info('{func:s}: dGal-path = {!s}'.format(dGNSS[subDicts[0]], func=cFuncName))
        logger.info('{func:s}: returns subTitle {subt:s}'.format(subt=subTitleGNSS, func=cFuncName))

        return subTitleGNSS
    else:
        return ''
