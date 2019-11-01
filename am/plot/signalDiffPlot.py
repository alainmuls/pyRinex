import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import dates
import numpy as np
import pandas as pd

import sys
import os
from pandas.plotting import register_matplotlib_converters
import logging
from termcolor import colored

from plot import plot_utils


register_matplotlib_converters()


def plotSignalDiff(dCsv: dict, dfSig: pd.DataFrame, logger=logging.Logger):
    """
    Plot the signals and their difference per observed PRN
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: start plotting for signal difference {st0:s}-{st1:s}\n'.format(st0=dCsv[0]['signal'], st1=dCsv[1]['signal'], func=cFuncName))

    # specify the style
    mpl.style.use('seaborn')

    # determine the discrete colors for SVs
    colormap = plt.cm.nipy_spectral  # I suggest to use nipy_spectral, Set1,Paired
    # colormap = plt.cm.Spectral  # I suggest to use nipy_spectral, Set1,Paired
    colors = [colormap(i) for i in np.linspace(0, 1, dCsv['#SVs'] * 3)]
    logger.debug('{func:s}: colors = {colors!s}'.format(colors=colors, func=cFuncName))

    # max for signals itself
    y1Max = max(dCsv[0]['max'], dCsv[1]['max']) + 5
    y1Min = min(dCsv[0]['min'], dCsv[1]['min']) - 5

    # for formatting date time x axis
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfSig['time'].iloc[0], endDT=dfSig['time'].iloc[-1])

    # go over all PRNs
    for i, prn in enumerate(dCsv['SVs']):
        logger.info('{func:s}: plotting for PRN {prn:s}'.format(prn=prn, func=cFuncName))

        # create the figure and axes
        fig, ax1 = plt.subplots(figsize=(15, 10))

        # x-axis properties
        ax1.set_xlim([dfSig['time'].iloc[0], dfSig['time'].iloc[-1]])
        if dtFormat['minutes']:
            ax1.xaxis.set_major_locator(dates.MinuteLocator(byminute=[0, 15, 30, 45], interval=1))
        else:
            ax1.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
        ax1.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

        ax1.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
        ax1.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

        ax1.xaxis.set_tick_params(rotation=0)
        for tick in ax1.xaxis.get_major_ticks():
            # tick.tick1line.set_markersize(0)
            # tick.tick2line.set_markersize(0)
            tick.label1.set_horizontalalignment('center')

        # plot both signals in color for prn
        ax1.set_ylim([y1Min, y1Max])

        prnst = '{prn:s}-{st:s}'.format(prn=prn, st=dCsv[0]['signal'])
        ax1.plot(dfSig['time'], dfSig[prnst], linestyle='-', marker='.', markersize=1, color='blue', label=prnst, alpha=0.5)
        prnst = '{prn:s}-{st:s}'.format(prn=prn, st=dCsv[1]['signal'])
        ax1.plot(dfSig['time'], dfSig[prnst], linestyle='-', marker='.', markersize=1, color='green', label=prnst, alpha=0.5)

        # add a legend the plot showing the satellites displayed
        ax1.legend(loc='upper left', ncol=16, markerscale=4)

        # plot the difference on second y-axis
        ax2 = ax1.twinx()
        if dCsv[0]['signal'].startswith('C'):
            ax2.set_ylim([0, 15])
        elif dCsv[0]['signal'].startswith('S'):
            ax2.set_ylim([-15, 15])
        else:
            ax2.set_ylim([dCsv['dMin'], dCsv['dMax']])
        prnstdiff = '{prn:s}: {st0:s}-{st1:s}'.format(prn=prn, st0=dCsv[0]['signal'], st1=dCsv[1]['signal'])
        ax2.fill_between(dfSig['time'], dfSig[prn], linestyle='-', color='red', label=prnstdiff, alpha=0.5)
        # plot the moving average for this prn
        prnMA = '{prn:s}-MA'.format(prn=prn)
        movAvgTxt = 'MovAvg ({time:d}s: #{count:d}, mean={mean:.1f}, max={max:.1f}, min={min:.1f})'.format(time=dCsv['movavg'], count=dCsv['stats'][prn]['count'], max=dCsv['stats'][prn]['max'], min=dCsv['stats'][prn]['min'], mean=dCsv['stats'][prn]['mean'])
        ax2.plot(dfSig['time'], dfSig[prnMA], linestyle='-', marker='.', markersize=1, color='yellow', label=movAvgTxt)
        # add a legend the plot showing the satellites displayed
        ax2.legend(loc='upper right', ncol=16, markerscale=4)

        # title of plot
        shortName = dCsv[0]['file'].split('-')[0]
        title = '{file:s}: {syst:s} {prn:s} Signal difference {st0:s}-{st1:s}'.format(file=shortName, syst=dCsv['gnss'], prn=prn, st0=dCsv[0]['signal'], st1=dCsv[1]['signal'])
        fig.suptitle(title, fontsize=16)

        # Save the file in dir png
        pltDir = os.path.join(dCsv['dir'], 'png')
        os.makedirs(pltDir, exist_ok=True)
        pltName = '{file:s}-{syst:s}-{prn:s}-{st0:s}-{st1:s}.png'.format(file=shortName, syst=dCsv['gnss'], prn=prn, st0=dCsv[0]['signal'], st1=dCsv[1]['signal'])
        tmpName = pltName.replace(' ', '-')
        pltName = os.path.join(pltDir, tmpName)
        fig.savefig(pltName, dpi=100)

        logger.info('{func:s}: plot saved as {name:s}'.format(name=pltName, func=cFuncName))

        plt.show(block=True)
