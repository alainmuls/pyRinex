from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

import xarray

import georinex as gr
import os


# for NetCDF compression. too high slows down with little space savings.
ENC = {'zlib': True, 'complevel': 1, 'fletcher32': True}


class write2NetCDF(QObject):

    # emit this signal when we have signalFinished at end of writing to NetCDF
    signalFinished = pyqtSignal()
    # message to be shown to user in statusbar
    signalMessage = pyqtSignal(str)


    def __init__(self, NetCDFName: str, obsData: xarray.Dataset):
        """
        writes to a NetCDF formatted file
        params rinexName: name of NetCDF file to create
        params dRinexSelect: RINEX selection made
        params obsDate: observations to write
        """
        super(write2NetCDF, self).__init__()

        # store the passend variables
        self.NetCDFName = NetCDFName
        self.obsData = obsData

        # print('worker init {:s}'.format(self.NetCDFName))


    def work(self):
        """
        performs writing of NetCDF file

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
        # # create the filename for the NetCDF file
        # startHMS = ''.join(self.dRinexSelect['Timing']['start'][-8:-3].split(':'))
        # stopHMS = ''.join(self.dRinexSelect['Timing']['stop'][-8:-3].split(':'))
        # interval = '{:05.2f}'.format(self.dRinexSelect['Timing']['interval']).replace('.', '')
        # gnss = ''.join([k for k, v in self.dRinexSelect['GNSSObs'].items()])

        # NetCDFName  = '{rinex:s}-{start:s}-{stop:s}-{interval:s}-{gnss:s}.nc'.format(rinex=self.rinexName.replace('.', '-'), start=startHMS, stop=stopHMS, interval=interval, gnss=gnss)

        # print('worker emit signalMessage indicating start of worker')
        self.signalMessage.emit('Writing Observations to {:s}. Please wait'.format(os.path.basename(self.NetCDFName)))

        if os.path.isfile(self.NetCDFName):
            try:
                os.remove(self.NetCDFName)
            except OSError as e: # this would be "except OSError, e:" before Python 2.6
                if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                    raise # re-raise exception if a different error occurred

        # create the NetCDF file
        enc = {k: ENC for k in self.obsData.data_vars}
        # print('enc = {!s}'.format(enc))

        self.obsData.to_netcdf(self.NetCDFName, group='OBS', mode='w', encoding=enc)

        # worker emit signalFinished
        # print('writeNetCDF emit signalFinished')
        self.signalFinished.emit()

        pass
