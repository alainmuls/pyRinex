from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

import xarray

import georinex as gr
from os import path


class readRinexObservation(QObject):

    # emit this signal when we have signalFinished parsing and return data read
    signalFinished = pyqtSignal(xarray.Dataset)
    # message to be shown to user in statusbar
    signalMessage = pyqtSignal(str)


    def __init__(self, rinexObsName: str, dRinexSelect: dict):
        """
        initialises the readRinexObservation
        params rinexObsName: name of RINEX file to load
        params dRinexSelect: the selected GNSS ssystems and observables and indicators
        type rinexObsName: str
        type dRinexSelect: dict
        """
        super(readRinexObservation, self).__init__()

        # store the passend variables
        self.rinexObsName = rinexObsName
        self.dRinexSelect = dRinexSelect
        # print('worker init {:s}'.format(self.rinexObsName))


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
        self.signalMessage.emit('Reading RINEX Observations from {:s}. Please wait'.format(path.basename(self.rinexObsName)))

        # specify the GNSS systems and measurements to load to load
        useGNSS = []
        useMeas = []
        for GNSS, Meas in self.dRinexSelect['GNSSObs'].items():
            useGNSS.append(GNSS)
            useMeas = useMeas + Meas
        useMeas = list(set(useMeas))
        # print('use = {!s}  meas = {!s}'.format(useGNSS, useMeas))

        # specify in ISOFORMAT the start / stop times for reading the RINEX file
        tLim = [self.dRinexSelect['Timing']['start'], self.dRinexSelect['Timing']['stop']]
        # print('tLim = {!s}'.format(tLim))

        # load the selected data
        dataObs = gr.load(self.rinexObsName, tlim=tLim, use=useGNSS, meas=useMeas, useindicators=self.dRinexSelect['Indicators'], interval=self.dRinexSelect['Timing']['interval'], verbose=True)
        # dataObs = gr.load(self.rinexObsName, tlim=tLim, use=useGNSS, meas=useMeas, useindicators=self.dRinexSelect['Indicators'], interval=60, verbose=True)

        # worker emit signalFinished
        # print('readRinexObs emit signalFinished')
        self.signalFinished.emit(dataObs)
