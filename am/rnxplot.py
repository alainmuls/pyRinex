#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pyQt5 program for processing RINEX data files
using the 'georinex' scripts

Based on example from:

Author: Jan Bodnar
Website: zetcode.com
Last edited: August 2017
"""

from PyQt5.QtWidgets import (QMainWindow, QAction, QApplication, QMessageBox, QFileDialog, QMenu)
from PyQt5.QtGui import (QIcon, QColor)
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot, QT_VERSION_STR)
from PyQt5.Qt import (PYQT_VERSION_STR)

from amqtutils import (qtutils, waitingspinnerwidget, Formatter, stdout_redirect)
from rnxdialog import (rinexDialog, stacked_widget, observationDisplay)
from workers import (readRinexObs, writeNetCDF, readNetCDF)

from qtstyles import (amstyles)
from rinex import rinex_observables as rnxobs
import am_config as amc

import sys
import os
import xarray
import georinex as gr
import pandas as pd
import platform
import io
import numpy as np
from multiprocessing import Queue
from termcolor import colored
from ampyutils import amutils


__author__ = "Alain Muls"
__license__ = "GPL"
__version__ = "0.2"
__email__ = "ralain.muls@gmail.com"
__status__ = "Development"

# for NetCDF compression. too high slows down with little space savings.
ENC = {'zlib': True, 'complevel': 1, 'fletcher32': True}


class RinexObservations(QMainWindow):
    """
    RinexObservations is script for loading data from a RINEX Obs file and display info about the observables inside the RINEX Obs file
    """

    # emit signalClearInfoDisplay
    signalClearInfoDisplay = pyqtSignal()


    def __init__(self, desktopSize):
        super().__init__()

        # create logger and function names
        self.cBaseName = colored(os.path.basename(__file__), 'yellow')
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
        self.logger = amc.createLoggers(baseName=os.path.basename(__file__), dir='.', logLevels=['INFO', 'DEBUG'])

        self.logger.info('in {func:s}'.format(func=cFuncName))

        # get path of the current script
        self.scriptDir = os.path.dirname(os.path.realpath(__file__))
        # print('scriptDir = {:s}'.format(self.scriptDir))

        # for pretty printing dict and so on
        self.prettyFmt = Formatter.Formatter()

        # read th eassociated style sheet
        styleFile = os.path.join(self.scriptDir, 'qtstyles', 'amstyles.qss')
        # print('styleFile = {:s}'.format(styleFile))

        self.styleSheet = amstyles.getStyleSheet(styleFile)
        # print('self.styleSheet = {!s}  {!s}'.format(self.styleSheet, type(self.styleSheet)))

        # resize the application
        self.setFixedSize(desktopSize.width() * 0.7, desktopSize.height() * 0.8)

        # create a dict for the naming of satellite systems
        self.dGNSSsIDs = rnxobs.dGNSSsIDs
        self.logger.info('{func:s}: dict = {dict!s}'.format(dict=self.prettyFmt(self.dGNSSsIDs), func=cFuncName))

        self.initUI()

    def initUI(self):
        """
        init of the main GUI
        """
        # self.textedit = QTextEdit()
        # self.setCentralWidget(self.textedit)

        # initiate the tabbed widget for display
        self.tabWidget = stacked_widget.MainStackedWidget(parent=self)
        self.setCentralWidget(self.tabWidget)

        # connect signalClearInfoDisplay o slotClearInfoDisplay
        self.signalClearInfoDisplay.connect(self.tabWidget.slotClearInfoDisplay)

        # set icon
        self.setWindowIcon(QIcon(self.scriptDir + os.path.sep + 'pics/logo.png'))

        # create a status bar
        self.statusBar = self.statusBar()
        self.statusBar.showMessage('test')
        # create the actions/menus
        self.createActions()
        self.createMenus()

        # toolbar = self.addToolBar('Exit')
        # toolbar.addAction(actExit)

        # create a spinner for showing wait times
        self.spinner = waitingspinnerwidget.QtWaitingSpinner(self, centerOnParent=True, disableParentWhenSpinning=True)

        self.spinner.setRoundness(70.0)
        self.spinner.setMinimumTrailOpacity(15.0)
        self.spinner.setTrailFadePercentage(70.0)
        self.spinner.setNumberOfLines(12)
        self.spinner.setLineLength(30)
        self.spinner.setLineWidth(5)
        self.spinner.setInnerRadius(15)
        self.spinner.setRevolutionsPerSecond(1)
        self.spinner.setColor(QColor(81, 4, 71))

        self.setGeometry(3900, 900, 800, 600)
        self.setWindowTitle('RINEX observation plot')
        self.show()

    def createActions(self):
        """
        createActions create the actions used called by the menu entries
        """
        # Actions for FILE menu
        self.actLoadRinexInfo = QAction(QIcon(self.scriptDir + os.path.sep + 'pics/openfile2.png'), 'Load RINEX', self)
        self.actLoadRinexInfo.setShortcut('Ctrl+R')
        self.actLoadRinexInfo.setStatusTip('Open RINEX file')
        self.actLoadRinexInfo.triggered.connect(self.loadRinexInfo)

        self.actLoadNetCDF = QAction(QIcon(self.scriptDir + os.path.sep + 'pics/openfile3.png'), 'Load NetCDF', self)
        self.actLoadNetCDF.setShortcut('Ctrl+N')
        self.actLoadNetCDF.setStatusTip('Open NetCDF file')
        self.actLoadNetCDF.triggered.connect(self.loadNetCDF)

        self.actPreference = QAction(QIcon(self.scriptDir + os.path.sep + 'pics/preference.png'), 'Preference', self)
        self.actPreference.setShortcut('Ctrl+P')
        self.actPreference.setStatusTip('Open preference dialog')
        self.actPreference.triggered.connect(self.preference)

        self.actExit = QAction(QIcon(self.scriptDir + os.path.sep + 'pics/exit24.png'), 'Exit', self)
        self.actExit.setShortcut('Ctrl+Q')
        self.actExit.setStatusTip('Exit application')
        self.actExit.triggered.connect(self.close)

        # action for help menu
        self.actAbout = QAction(QIcon(self.scriptDir + os.path.sep + 'pics/about.png'), 'About', self)
        self.actAbout.setShortcut('Ctrl+A')
        self.actAbout.setStatusTip('About')
        self.actAbout.triggered.connect(self.aboutBox)

    def createMenus(self):
        """
        createMenus creates the menus
        """
        # create the menubar
        menubar = self.menuBar()

        # add a FILE menu
        fileMenu = menubar.addMenu('&File')
        # create submenu for loading either RINEX of NETCDF RINEX data
        loadMenu = QMenu('Load', self)
        loadMenu.addAction(self.actLoadRinexInfo)
        loadMenu.addAction(self.actLoadNetCDF)

        fileMenu.addMenu(loadMenu)
        fileMenu.addAction(self.actPreference)
        fileMenu.addSeparator()
        fileMenu.addAction(self.actExit)

        # add a help menu
        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction(self.actAbout)

    def aboutBox(self):
        """
        displays a about info
        """
        aboutTxtTitle = '{:s}'.format(os.path.basename(os.path.realpath(__file__)))
        aboutTxt = '<p>Program <b>{:s}</b></p>'.format(os.path.basename(os.path.realpath(__file__)))
        aboutTxt += '<p>Reads RINEX observation file for plotting</p>'
        aboutTxt += 'Author: {:s}<br>'.format(__author__)
        aboutTxt += 'License: {:s}<br>'.format(__license__)
        aboutTxt += 'Version: {:s} - #{:s}<br>'.format(__status__, __version__)
        aboutTxt += 'mail: {:s}<br>'.format(__email__)
        aboutTxt += 'Based on georinex<br>'
        aboutTxt += 'using Python {:s}, Qt {:s}, PyQt {:s} on {:s}<br>'.format(platform.python_version(), QT_VERSION_STR, PYQT_VERSION_STR, platform.system())

        qmsgBox = QMessageBox()
        qmsgBox.setStyleSheet(self.styleSheet)
        QMessageBox.about(qmsgBox, aboutTxtTitle, aboutTxt)

    def preference(self):
        """
        preference() opens the preference window
        """
        pass

    def loadRinexInfo(self):
        """
        loadRinexInfo() opens a RINEX file
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        # dirRxTURP = os.path.join(os.getenv("HOME"), 'RxTURP' + os.dir.separator() + 'BEGPIOS')
        self.dirRxTURP = os.getcwd()  # os.path.join(self.scriptDir, '../BEGP')
        self.logger.info('{func:s} start at working directory  = {dir:s}'.format(dir=self.dirRxTURP, func=cFuncName))
        self.rinexObsFile, _ = QFileDialog.getOpenFileName(self, 'Open RINEX File', self.dirRxTURP, "Rinex Obs (*.[0-9][0-9]?);;OBS (*.obs)")

        self.logger.info('{func:s} reading RINEX file  = {dir:s}'.format(dir=self.rinexObsFile, func=cFuncName))

        # if file is selected, check for read permission and existence
        if self.rinexObsFile:
            # check if file is readable, else give a warning
            if os.path.isfile(self.rinexObsFile) and os.access(self.rinexObsFile, os.R_OK):
                # store the currect directory
                self.obsDir = os.path.dirname(self.rinexObsFile)
                self.obsName = os.path.basename(self.rinexObsFile)
                self.logger.info('{func:s}: current directory {dir:s}'.format(dir=self.obsDir, func=cFuncName))
                self.logger.info('{func:s}: current observation file {file:s}'.format(file=self.obsName, func=cFuncName))

                # read in RINEX observable file
                rinexType = self.checkRinexObsFile(filename=self.rinexObsFile)

                # print('rinexType = {!s}'.format(rinexType))
                if rinexType == 'obs':
                    self.readRinexHeader()
                    self.readRinexTimes()
                    accepted = self.selectRinexDialog()
                    if accepted:
                        self.readRinexObs()
                elif rinexType == 'nav':
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText('File {:s} is a navigation RINEX file.\nSelect an observation file.'.format(self.rinexObsFile))
                    msg.setWindowTitle("Warning")
                    msg.exec_()
            else:
                # print(colored('Either file {:s} is missing or is not readable'.format(self.rinexObsFile), 'red'))
                # create a warning for the user
                if not os.path.isfile(self.rinexObsFile):
                    msg = 'File {name:s} does not exist.'.format(name=self.rinexObsFile)
                elif not os.access(self.rinexObsFile, os.R_OK):
                    msg = 'File {name:s} is not accessible.'.format(name=self.rinexObsFile)

                reply = qtutils.get_continue_or_cancel(message=msg, title='Warning', continue_button_text='Continue', cancel_button_text='Quit')
                if reply:  # ocntinue selecting file
                    self.loadRinexInfo()
                else:  # quit the qpplicqtion
                    sys.exit(app.exec_())

        pass

    def loadNetCDF(self):
        """
        loadNetCDF() opens a RINEX fileb
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        # dirRxTURP = os.path.join(os.getenv("HOME"), 'RxTURP' + os.dir.separator() + 'BEGPIOS')
        self.dirRxTURP = os.getcwd()  # os.path.join(self.scriptDir, '../BEGP')
        self.logger.info('{func:s} start at working directory  = {dir:s}'.format(dir=self.dirRxTURP, func=cFuncName))
        self.NetCDFFile, _ = QFileDialog.getOpenFileName(self, 'Open NetCDF File', self.dirRxTURP, "NetCDF Obs (*.nc)")
        self.logger.info('{func:s} reading NETCDF file  = {dir:s}'.format(dir=self.NetCDFFile, func=cFuncName))

        # if file is selected, check for read permission and existence
        if self.NetCDFFile:
            # check if file is readable, else give a warning
            if os.path.isfile(self.NetCDFFile) and os.access(self.NetCDFFile, os.R_OK):
                # store the currect directory
                self.obsDir = os.path.dirname(self.NetCDFFile)
                self.obsName = os.path.basename(self.NetCDFFile)
                self.logger.info('{func:s}: current directory {dir:s}'.format(dir=self.obsDir, func=cFuncName))
                self.logger.info('{func:s}: current observation file {file:s}'.format(file=self.obsName, func=cFuncName))

                # read in RINEX NETCDF observable file
                rinexType = self.checkRinexObsFile(filename=self.NetCDFFile)

                # sys.stdout.write('rinexType = {!s}\n'.format(rinexType))
                if rinexType == 'nc':
                    self.readNetCDFObs()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText('File {:s} is not a NetCDF file.\nSelect correct file.'.format(self.NetCDFFile))
                    msg.setWindowTitle("Warning")
                    msg.exec_()
            else:
                # print(colored('Either file {:s} is missing or is not readable'.format(self.NetCDFFile), 'red'))
                # create a warning for the user
                if not os.path.isfile(self.NetCDFFile):
                    msg = 'File {name:s} does not exist.'.format(name=self.NetCDFFile)
                elif not os.access(self.NetCDFFile, os.R_OK):
                    msg = 'File {name:s} is not accessible.'.format(name=self.NetCDFFile)

                reply = qtutils.get_continue_or_cancel(message=msg, title='Warning', continue_button_text='Continue', cancel_button_text='Quit')
                if reply:  # ocntinue selecting file
                    self.loadNetCDF()
                else:  # quit the qpplicqtion
                    sys.exit(app.exec_())

        pass

    def checkRinexObsFile(self, filename: str):
        """
        check what type of file we have
        """
        if filename.endswith('.nc'):
            return 'nc'
        else:
            try:
                info = gr.rinexinfo(filename)['rinextype']
                if isinstance(filename, io.StringIO):
                    filename.seek(0)
                return info
            except ValueError:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText('No observation data file:\n{:s}'.format(filename))
                msg.setWindowTitle("Error")
                msg.exec_()

                return None

    def readRinexHeader(self):
        """
        readRinexHeader reads the observation header and displays a dialog for selecting the GNSS systsms and observables to load
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        # get the info for the RINEX obs file
        self.obsHeader = gr.rinexheader(self.rinexObsFile)
        self.logger.info('{func:s}: self.obsHeader = {hdr!s}\n\n'.format(self.prettyFmt(self.obsHeader)))
        self.logger.info('{func:s}: type = {type!s}'.format(type=self.obsHeader['filetype'], func=cFuncName))
        self.logger.info('{func:s}: Systems: {syst!s}'.format(syst=self.obsHeader['fields'], func=cFuncName))
        self.logger.info('{func:s}: Systems: {syst!s}'.format(syst=self.obsHeader['fields'].keys(), func=cFuncName))
        self.logger.info('{func:s}: Signals: {sign!s}'.format(sign=self.obsHeader['fields']['E'], func=cFuncName))
        self.logger.info('{func:s}: GNSS dict = {gnss!s}'.format(gnss=self.prettyFmt(self.dGNSSsI, func=cFuncNameDs)))

    def readRinexTimes(self):
        """
        read timing for observation file and create a dict for the rinex timing
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        self.dRnxTimes = {}

        # get the times of the observations
        obsTimes = gr.gettime(self.rinexObsFile)

        # print('xxx {!s}'.format(pd.to_datetime(str(obsTimes[0].values))))

        self.dRnxTimes['start'] = pd.to_datetime(str(obsTimes[0].values)).timetuple()
        self.dRnxTimes['stop'] = pd.to_datetime(str(obsTimes[-1].values)).timetuple()
        self.dRnxTimes['interval'] = obsTimes[0].attrs['interval']
        self.dRnxTimes['epochs'] = len(obsTimes)

        self.logger.info('{func:s} dRnxTimes = {times!s}'.format(times=self.dRnxTimes, func=cFuncName))

    def selectRinexDialog(self) -> bool:
        """
        create a selection dialog (GNSS, Obs & Times) to read from RINEX file
        """
        # display a dialog for selecting the start/end times
        self.selectRinexInfoDialog = rinexDialog.SelectRinexInfoDialog(dObservables=self.obsHeader['fields'], dTimes=self.dRnxTimes, dGNSSsIDs=self.dGNSSsIDs, styleSheet=self.styleSheet, parent=self)
        # self.selectRinexInfoDialog.show()
        result = self.selectRinexInfoDialog.exec_()
        self.dRinexSelected = self.selectRinexInfoDialog.returnSelection()

        # print('=' * 20)
        # print('Selected Rinex Information = {!s}\ndialog result = {!s}'.format(self.dRinexSelected, result == QDialog.Accepted))
        # print('=' * 20)

        return result

    def readRinexObs(self):
        """
        readRinexObs reads in the RINEX observable data
        """
        self.threadRnxObsRead = QThread()
        self.workerObs = readRinexObs.readRinexObservation(rinexObsName=self.rinexObsFile, dRinexSelect=self.dRinexSelected)
        # self.threadRnxObsRead.setObjectName('thread_' + str(idx))
        # self.__threads.append((self.threadRnxObsRead, self.workerObs))  # need to store self.workerObs too otherwise will be gc'd
        self.workerObs.moveToThread(self.threadRnxObsRead)

        # get progress messages from self.workerObs:
        self.workerObs.signalFinished.connect(self.slotRinexObsRead)
        self.workerObs.signalMessage.connect(self.displayMessage)

        # indicate that we are waiting for the file to be read
        self.spinner.start()

        # get read to start self.workerObs:
        self.signalClearInfoDisplay.emit()
        # self.sig_start.connect(self.workerObs.work)  # needed due to PyCharm debugger bug (!); comment out next line
        self.threadRnxObsRead.started.connect(self.workerObs.work)
        # print('starting')
        self.threadRnxObsRead.start()  # this will emit 'started' and start self.threadRnxObsRead's event loop
        # print('started')

    @pyqtSlot(xarray.Dataset)
    def slotRinexObsRead(self, obsData):
        """
        slot for stopping the waiting indicator
        """
        self.obs = obsData

        # write to information tab
        self.signalClearInfoDisplay.emit()
        sys.stdout.write('-' * 50)
        sys.stdout.write('\nObservation summary {name:s}:\n{obs!s}\n'.format(obs=self.prettyFmt(self.obs), name=self.rinexObsFile))
        sys.stdout.write('-' * 50)
        sys.stdout.write('\n')

        # stop thread reading obs
        self.statusBar.clearMessage()
        self.spinner.stop()

        # check what is returned
        if self.obs is not None:
            print('RINEX Observation Information:\n{!s}'.format(self.prettyFmt(self.obs)))
            self.save2NetCDF()
        else:
            print('No observation data in file {:s}'.format(self.rinexObsFile))
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Problem loading observation data from:\n{:s}'.format(self.rinexObsFile))
            msg.setWindowTitle("Error")
            msg.exec_()

        self.threadRnxObsRead.quit()
        self.threadRnxObsRead.wait()
        self.threadRnxObsRead.deleteLater()

        # create CSV files for all SYSTEMS and all SIGNALS
        print('... create CSV files for all SYSTEMS and all SIGNALS')

        self.createObservationDisplay()

    @pyqtSlot(xarray.Dataset)
    def slotNetCDFObsRead(self, obsData):
        """
        slot for stopping the waiting indicator
        """
        self.obs = obsData

        # write to information tab
        self.signalClearInfoDisplay.emit()
        sys.stdout.write('-' * 50)
        sys.stdout.write('\nObservation summary in {name:s}:\n{obs!s}\n'.format(obs=self.prettyFmt(self.obs), name=self.NetCDFFile))
        sys.stdout.write('-' * 50)
        sys.stdout.write('\n')

        # stop thread reading obs
        self.statusBar.clearMessage()
        self.spinner.stop()

        self.threadNetCDFRead.quit()
        self.threadNetCDFRead.wait()
        self.threadNetCDFRead.deleteLater()

        self.createObservationDisplay()

    def createObservationDisplay(self):
        """
        create the display for displaying the observation data collected
        """
        self.createCSVfiles()

        self.obsWidget = observationDisplay.displayObservations(NetCDFname=self.NetCDFFile, obsData=self.obs, logger=self.logger, styleSheet=self.styleSheet)

        # add the obsWidget to the tab 'Observation'
        self.tabWidget.createObsDisplay(self.obsWidget)

        # select the observation tab at start
        self.tabWidget.setCurrentWidget(self.tabWidget.tabObs)

        # ax = figure().gca()
        # ax.plot(self.obs.time, self.obs['C1C'])
        # show()

    def createCSVfiles(self):
        """
        creates per SYSTEM and per SIGNAL a CSV file for all observed SVs
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        self.logger.info('{func:s}: working on file {file:s}'.format(file=self.obsName, func=cFuncName))
        self.logger.info('{func:s}: self.obs\n{data!s}\n'.format(data=self.obs, func=cFuncName))
        self.logger.info('{func:s}: self.obs.sv\n{data!s}\n'.format(data=self.obs.sv, func=cFuncName))

        self.logger.debug('{func:s}: TEST\n{data!s}\n\n'.format(data=self.obs.data_vars.items(), func=cFuncName))

        listSVs = np.sort(self.obs.coords['sv'].values)
        self.logger.info('{func:s}: SVs found {svs!s}'.format(svs=listSVs, func=cFuncName))
        listGNSSsID = list(set([SVprn[0] for SVprn in listSVs]))
        self.logger.info('{func:s}: GNSSs found {svs!s}'.format(svs=listGNSSsID, func=cFuncName))
        listSignals = [k for k, _ in self.obs.data_vars.items()]
        self.logger.info('{func:s}: signals found {sign!s}'.format(sign=listSignals, func=cFuncName))

        # TEMP searching for max difference in signal strength for signal type E6A
        for _, sigType in enumerate(listSignals):
            dfSigType = self.findSigTypeExtremeDiff(typeSig=sigType)

            # export to sigType differences to CSV file
            amutils.mkdir_p(os.path.join(self.obsDir, 'csv'))
            csvName = os.path.join(self.obsDir, 'csv', '{file:s}-{st:s}-diff'.format(file=self.obsName, st=sigType))
            nameCVS = csvName.replace('.', '-')
            csvName = nameCVS.replace('_', '')
            dfSigType.to_csv('{csv:s}.csv'.format(csv=csvName))
            self.logger.info('{func:s}: created CSV file {csv:s}'.format(csv=csvName, func=cFuncName))

        # create for all GNSSs per SIGNALTYPE a csv file with the data
        for _, gnss in enumerate(listGNSSsID):
            for _, sigType in enumerate(listSignals):
                self.logger.info('{func:s}: creating CSV file for system {syst:s}, signal {st:s}'.format(syst=gnss, st=sigType, func=cFuncName))

                dfSystST = self.createSystemSignalType(gnss=gnss, st=sigType, listSVs=listSVs)

                # export to CSV file
                amutils.mkdir_p(os.path.join(self.obsDir, 'csv'))
                csvName = os.path.join(self.obsDir, 'csv', '{file:s}-{syst:s}-{st:s}'.format(file=self.obsName, syst=gnss, st=sigType))
                nameCVS = csvName.replace('.', '-')
                csvName = nameCVS.replace('_', '')
                # nameCVS= csvName.translate({ord(i): '-' for i in ['.', '_']})
                dfSystST.to_csv('{csv:s}.csv'.format(csv=csvName))
                self.logger.info('{func:s}: created CSV file {csv:s}'.format(csv=csvName, func=cFuncName))

    def createSystemSignalType(self, gnss: str, st: str, listSVs: list) -> pd.DataFrame:
        """
        create dataframe for GNSS system and for SignalType
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        # create an empty dataframe
        # dfObsType = pd.DataFrame(columns=['time'])

        dfObs = pd.DataFrame(index=self.obs.time.values)
        dfObs.index.name = 'time'

        # self.logger.debug('{func:s}: test to get time index'.format(func=cFuncName))
        # self.logger.debug(self.obs.time.values)
        # self.logger.debug(type(self.obs.time.values))
        # # dfTest = pd.DataFrame(index=self.obs.time.values, data=self.obs.time.values)
        # # amutils.logHeadTailDataFrame(logger=self.logger, callerName=sys._getframe().f_code.co_name, df=dfTest, dfName='TEST index', head=10, tail=10)

        # self.logger.debug('{func:s}: test get data'.format(func=cFuncName))
        # self.logger.debug(self.obs[st].sel(sv='E30').values)
        # self.logger.debug(type(self.obs[st].sel(sv='E30').values))

        for sv in listSVs:
            # check if sv belongs to the requested system
            if sv.startswith(gnss):
                self.logger.info('{func:s}: ... working on Sv {sv:s}'.format(sv=sv, func=cFuncName))

                dfObs[sv] = self.obs[st].sel(sv=sv).values

        amutils.logHeadTailDataFrame(logger=self.logger, callerName=sys._getframe().f_code.co_name, df=dfObs, dfName='Observables for {st:s}'.format(st=st), head=10, tail=10)

        return dfObs

    def findSigTypeExtremeDiff(self, typeSig: str) -> pd.DataFrame:
        """
        find the extreme differences in the S6A value
        """
        cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

        # create an empty dataframe for Positive / Negative differences
        dfS6Apos = pd.DataFrame(columns=['time'])
        dfS6Aneg = pd.DataFrame(columns=['time'])
        for sv in self.obs.sv:
            # print('*' * 20)
            # print('sv = {!s}'.format(sv))
            # print('my self.obs[S6A][{!s}] {!s}'.format(sv, self.obs[typeSig].sel(sv=sv)))
            # print('+' * 20)
            # print('my MAX self.obs[S6A][{!s}] {!s}'.format(sv, np.max(self.obs[typeSig].sel(sv=sv))))
            # print('-' * 20)

            # print('=' * 20)
            dfObs = self.obs[typeSig].sel(sv=sv).to_dataframe()
            dfObs['ST'] = dfObs[typeSig].diff()  # np.abs(dfObs[typeSig].diff())
            # amutils.logHeadTailDataFrame(logger=self.logger, callerName='CSV creator', df=dfObs, dfName='dfObs')
            # sort high to low
            # print('sorted = {!s}'.format(dfObs['ST'].sort_values(ascending=False, na_position='last', inplace=False)))
            # keep largest / smallest
            # print('nlargest = {!s}'.format(dfObs['ST'].nlargest(n=3)))
            # print('nsmallest = {!s}'.format(dfObs['ST'].nsmallest(n=3)))
            # print('=+' * 30)

            if dfS6Apos.shape[0] == 0:
                dfTmp = dfObs['ST'].nlargest(n=3).to_frame()
                dfTmp2 = dfObs['ST'].nsmallest(n=3).to_frame()
            else:
                dfTmp = pd.merge(dfS6Apos, dfObs['ST'].nlargest(n=3).to_frame(), on='time', how='outer')
                dfTmp2 = pd.merge(dfS6Aneg, dfObs['ST'].nsmallest(n=3).to_frame(), on='time', how='outer')
            dfS6Apos = dfTmp
            dfS6Aneg = dfTmp2
            dfS6Apos.rename(columns={'ST': '{!s}'.format(sv.values)}, inplace=True)
            dfS6Aneg.rename(columns={'ST': '{!s}'.format(sv.values)}, inplace=True)
            # amutils.logHeadTailDataFrame(logger=self.logger, callerName='CSV creator', df=dfS6Apos, dfName='dfS6Apos')
            # amutils.logHeadTailDataFrame(logger=self.logger, callerName='CSV creator', df=dfS6Aneg, dfName='dfS6Aneg')

        dfSigType = dfS6Apos.append(dfS6Aneg, ignore_index=False).sort_index(axis=0)
        amutils.logHeadTailDataFrame(logger=self.logger, callerName=sys._getframe().f_code.co_name, df=dfSigType, dfName='Differences for {st:s}'.format(st=typeSig), head=10, tail=10)

        return dfSigType

    @pyqtSlot(str)
    def displayMessage(self, message: str):
        """
        display message from self.workerObs in statusbar
        """
        # print('MSG = {:s}'.format(message))
        self.statusBar.showMessage(message)

    def save2NetCDF(self):
        """
        save to a NetCDF file for faster loading later
        """
        # os.path.dirname(f)
        # os.path.splitext(os.path.basename(f))

        # create the filename for the NetCDF file
        startHMS = ''.join(self.dRinexSelected['Timing']['start'][-8:-3].split(':'))
        stopHMS = ''.join(self.dRinexSelected['Timing']['stop'][-8:-3].split(':'))
        interval = '{:05.2f}'.format(self.dRinexSelected['Timing']['interval']).replace('.', '')
        gnss = ''.join([k for k, v in self.dRinexSelected['GNSSObs'].items()])

        self.NetCDFFile  = '{rinex:s}-{start:s}-{stop:s}-{interval:s}-{gnss:s}.nc'.format(rinex=self.rinexObsFile.replace('.', '-'), start=startHMS, stop=stopHMS, interval=interval, gnss=gnss)

        self.threadSaveNetCDF = QThread()
        self.workerNetCDF = writeNetCDF.write2NetCDF(NetCDFName=self.NetCDFFile, obsData=self.obs)
        # self.threadSaveNetCDF.setObjectName('thread_' + str(idx))
        # self.__threads.append((self.threadSaveNetCDF, self.workerNetCDF))  # need to store self.workerNetCDF too otherwise will be gc'd
        self.workerNetCDF.moveToThread(self.threadSaveNetCDF)

        # get progress messages from self.workerNetCDF:
        self.workerNetCDF.signalFinished.connect(self.slotWroteNetCDF)
        self.workerNetCDF.signalMessage.connect(self.displayMessage)

        # indicate that we are waiting for the file to be read
        # self.spinner.start()

        # get read to start self.workerNetCDF:
        # self.sig_start.connect(self.workerNetCDF.work)  # needed due to PyCharm debugger bug (!); comment out next line
        self.threadSaveNetCDF.started.connect(self.workerNetCDF.work)
        self.threadSaveNetCDF.start()  # this will emit 'started' and start self.thread's event loop

        pass

    @pyqtSlot()
    def slotWroteNetCDF(self):
        """
        slot called when NetCDF file has been created
        """
        # print('slotWroteNetCDF')
        self.statusBar.clearMessage()

        # self.spinner.stop()
        self.threadSaveNetCDF.quit()
        self.threadSaveNetCDF.wait()
        self.threadSaveNetCDF.deleteLater()

    def readNetCDFObs(self):
        """
        readRinexObs reads in the RINEX observable data
        """
        self.threadNetCDFRead = QThread()
        self.workerNetCDF = readNetCDF.readNetCDFMeas(netCDFName=self.NetCDFFile)
        # self.threadNetCDFRead.setObjectName('thread_' + str(idx))
        # self.__threads.append((self.threadNetCDFRead, self.workerNetCDF))  # need to store self.workerNetCDF too otherwise will be gc'd
        self.workerNetCDF.moveToThread(self.threadNetCDFRead)

        # get progress messages from self.workerNetCDF:
        self.workerNetCDF.signalFinished.connect(self.slotNetCDFObsRead)
        self.workerNetCDF.signalMessage.connect(self.displayMessage)

        # indicate that we are waiting for the file to be read
        self.spinner.start()

        # get read to start self.workerNetCDF:
        self.signalClearInfoDisplay.emit()
        # self.sig_start.connect(self.workerNetCDF.work)  # needed due to PyCharm debugger bug (!); comment out next line
        self.threadNetCDFRead.started.connect(self.workerNetCDF.work)
        # print('starting')
        self.threadNetCDFRead.start()  # this will emit 'started' and start self.thread's event loop
        # print('started')


if __name__ == '__main__':
    # Create Queue and redirect sys.stdout to this queue
    queue = Queue()
    sys.stdout = stdout_redirect.WriteStream(queue)

    qapp = QApplication(sys.argv)

    screen_resolution = qapp.desktop().screenGeometry()
    # width, height = screen_resolution.width(), screen_resolution.height()

    # print('wxh = {!s}x{!s}'.format(width, height))

    app = RinexObservations(screen_resolution)
    app.show()

    # Create thread that will listen on the other end of the queue, and send the text to the textedit in our application
    rxStdOutThread = QThread()
    stdOutRx = stdout_redirect.rxStdOut(queue)
    stdOutRx.rxStdOutSignal.connect(app.tabWidget.stdOutTextDisplay)
    stdOutRx.moveToThread(rxStdOutThread)
    rxStdOutThread.started.connect(stdOutRx.run)
    rxStdOutThread.start()

    qapp.exec_()
