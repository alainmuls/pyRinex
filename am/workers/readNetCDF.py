from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

import xarray

import georinex as gr
from os import path


class readNetCDFMeas(QObject):

    # emit this signal when we have signalFinished parsing and return data read
    signalFinished = pyqtSignal(xarray.Dataset)
    # message to be shown to user in statusbar
    signalMessage = pyqtSignal(str)


    def __init__(self, netCDFName: str):
        """
        initialises the readRinexObservation
        params netCDFName: name of RINEX file to load
        """
        super(readNetCDFMeas, self).__init__()

        # store the passend variables
        self.netCDFName = netCDFName
        # print('worker init {:s}'.format(self.netCDFName))


    def work(self):
        """
        performs loading of observation in xarray structure

        def rinexobs3(fn: Union[TextIO, str, Path],
              use: Sequence[str] = None,
              tlim: Tuple[datetime, datetime] = None,
              useindicators: bool = False,
              meas: Sequence[str] = None,
              verbose: bool = False) -> xarray.Dataset:
                interval: Union[float, int, timedelta] = None
        process RINEX 3 OBS data

        use: 'G'  or ['G', 'R'] or similar
        meas:  'L1C'  or  ['L1C', 'C1C'] or similar
        """
        # print('worker emit signalMessage indicating start of worker')
        self.signalMessage.emit('Reading NetCDF Observations from {:s}. Please wait'.format(path.basename(self.netCDFName)))

        # load the selected data
        dataObs = gr.load(self.netCDFName, verbose=True)

        # worker emit signalFinished
        # print('readRinexObs emit signalFinished')
        self.signalFinished.emit(dataObs)
