from PyQt5.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QLabel, QRadioButton, QTimeEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import (Qt, QTime, pyqtSignal, pyqtSlot)

import xarray
import sys
import numpy as np
import pandas as pd
from os import path
import time
from datetime import datetime
import logging

from rinex import rinex_observables as rnxobs
from amqtutils import (Formatter, fiveminutetimeedit)
from plot import rinexObsPlot


class displayObservations(QWidget):
    """
    create the widget that allows to make the selections for plotting / examing observation data
    """

    def __init__(self, NetCDFname: str, obsData: xarray.Dataset, logger: logging.Logger, styleSheet: str, parent=None):
        """
        params obsData: data structure containing the observations
        """
        super(displayObservations, self).__init__(parent)

        # heep the data
        self.NetCDFName = NetCDFname
        self.obsData = obsData
        self.logger = logger
        self.styleSheet = styleSheet

        # nr of columns for the gridlayouts
        self.nrCols = 10

        # self.LEARN_DATAARRAY()

        # get the list of SVs and list of Signals / channels in obsData
        self.SVs = np.sort(self.obsData.coords['sv'].values)
        self.Signals = [k for k, _ in self.obsData.data_vars.items()]
        self.Times = self.obsData.coords['time']
        # print('self.SVs = {!s}'.format(type(self.SVs)))
        # print('self.Signals = {!s}'.format(self.Signals))
        print('self.Times = {!s}'.format(self.Times))

        # find out which GNSSs we have
        self.listGNSSs = list(set([v[0] for v in self.SVs]))
        self.listGNSSsNames = [v for k,v in rnxobs.dGNSSsIDs.items() if k in self.listGNSSs]
        print('self.listGNSSs = {!s}'.format(self.listGNSSs))
        print('self.listGNSSsNames = {!s}'.format(self.listGNSSsNames))

        # create a widget with info about file used
        print('self.obsData.attrs = {!s}'.format(self.obsData.attrs['filename']))

        # create a pushbutton for plotting current selection
        self.pbPlot = QPushButton('Plot')
        self.pbPlot.setStyleSheet(self.styleSheet)
        self.pbPlot.clicked.connect(self.slotPlotRinexObservables)
        hbox =QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.pbPlot)
        hbox.addStretch(1)

        # put selection groupbxes in a grid layout
        mainGrid = QGridLayout()
        mainGrid.addWidget(self.createInfoGroupBox(), 0, 1, 4, 1)
        mainGrid.addWidget(self.createTimeGroup(), 0, 0)
        mainGrid.addWidget(self.createSVGroupBox(), 1, 0)
        mainGrid.addWidget(self.createSignalsGroupBox(), 2, 0)
        mainGrid.addLayout(hbox, 3, 0)

        # create the main layout
        vbox = QVBoxLayout()
        vbox.addLayout(mainGrid)
        # vbox.addLayout(hbox)
        vbox.addStretch(1)

        self.setLayout(vbox)

    def createInfoGroupBox(self) -> QGroupBox:
        """
        create a groupbox with info about the file used
        """
        gb = QGroupBox('Information')
        gb.setStyleSheet(self.styleSheet)

        # put info in a grid
        loGrid = QGridLayout()
        rowNr = 0

        lblDir = QLabel('Directory:')
        lblDir.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lblDirName = QLabel(path.dirname(self.NetCDFName))
        loGrid.addWidget(lblDir, rowNr, 0)
        loGrid.addWidget(lblDirName, rowNr, 1)
        rowNr += 1

        lblRinex = QLabel('RINEX file:')
        lblRinex.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lblRinexFile = QLabel(self.obsData.attrs['filename'])
        loGrid.addWidget(lblRinex, rowNr, 0)
        loGrid.addWidget(lblRinexFile, rowNr, 1)
        rowNr += 1

        lblNetCDF = QLabel('NetCDF file:')
        lblNetCDF.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lblNetCDFName = QLabel(path.basename(self.NetCDFName))
        loGrid.addWidget(lblNetCDF, rowNr, 0)
        loGrid.addWidget(lblNetCDFName, rowNr, 1)
        rowNr += 1

        lblGNSS = QLabel('GNSS:')
        lblGNSS.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        strGNSSsList = ' / '.join(self.listGNSSsNames)
        lblGNSSlist = QLabel('{GNSS:s}      (time system: {time:s})'.format(time=self.obsData.attrs['time_system'], GNSS=strGNSSsList))
        loGrid.addWidget(lblGNSS, rowNr, 0)
        loGrid.addWidget(lblGNSSlist, rowNr, 1)
        rowNr += 1

        lblSVs = QLabel('# SVs / Signals / Epochs:')
        lblSVs.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        keyObs = [k for k, _ in self.obsData.data_vars.items()]
        lblSVsTotal = QLabel('{:d} / {:d} / {:d}'.format(self.obsData.dims['sv'], len(keyObs), self.obsData.dims['time']))
        loGrid.addWidget(lblSVs, rowNr, 0)
        loGrid.addWidget(lblSVsTotal, rowNr, 1)
        rowNr += 1

        lblTiming = QLabel('Timing:')
        lblTiming.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        startTime = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(self.obsData.coords['time'].values[0].astype(int)/1000000000))
        stopTime = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(self.obsData.coords['time'].values[-1].astype(int)/1000000000))
        timingRange = '{start:s} - {stop:s}'.format(start=startTime, stop=stopTime)
        lblTimingRange = QLabel(timingRange)
        loGrid.addWidget(lblTiming, rowNr, 0)
        loGrid.addWidget(lblTimingRange, rowNr, 1)
        rowNr += 1

        gb.setLayout(loGrid)

        # main layout for this is a vbox
        vbox = QVBoxLayout()
        vbox.addWidget(gb)
        vbox.addStretch(1)

        gbVertical = QGroupBox()
        gbVertical.setLayout(vbox)

        return gbVertical

    def createSVGroupBox(self) -> QGroupBox:
        """
        create a grid layout for displaying selectable satellites
        """
        gbSats = QGroupBox('Satellites')
        gbSats.setStyleSheet(self.styleSheet)

        self.rbGNSS = []
        gbGNSSs = []
        hboxes = []
        for GNSS in self.listGNSSsNames:
            # group all:none radiobuttons for each GNSS
            gbGNSSs.append(QGroupBox())
            gbGNSSs[-1].setFlat(True);
            gbGNSSs[-1].setStyleSheet("border:0;margin: 0em;")
            gbGNSSs[-1].setContentsMargins(0,0,0,0)

            hboxes.append(QHBoxLayout())
            hboxes[-1].addStretch(1)

            # All radiobutton for a GNSS
            rbAll = QRadioButton('All {:s}'.format(GNSS))
            rbAll.toggled.connect(self.onToggledGNSSsyst)
            self.rbGNSS.append(rbAll)
            hboxes[-1].addWidget(rbAll)

            # None radiobutton for a GNSS
            rbNone = QRadioButton('None {:s}'.format(GNSS))
            rbNone.toggled.connect(self.onToggledGNSSsyst)
            self.rbGNSS.append(rbNone)
            hboxes[-1].addWidget(rbNone)

            # User selectable satellites for GNSS
            rbUser = QRadioButton('User {:s}'.format(GNSS))
            rbUser.toggled.connect(self.onToggledGNSSsyst)
            self.rbGNSS.append(rbUser)
            hboxes[-1].addWidget(rbUser)

            gbGNSSs[-1].setLayout(hboxes[-1])

        # create a list of radio buttons and add them to a grid
        loGrid = QGridLayout()
        self.cbSVs = []
        for sv in range(len(self.SVs)):
            cb = QCheckBox(self.SVs[sv])
            self.cbSVs.append(cb)
            # add to gridlayout
            curRow, curCol = divmod(sv, self.nrCols)
            # print('SV = {:d} curpos = {:d}:{:d}'.format(sv, curRow, curCol))
            loGrid.addWidget(cb, curRow, curCol)

        vbox = QVBoxLayout()
        for gbGNSS in gbGNSSs:
            print('gbGNSS = {!s}'.format(gbGNSS))
            vbox.addWidget(gbGNSS)
        vbox.addLayout(loGrid)
        gbSats.setLayout(vbox)

        # perform initail action to be ALL for all GNSSs
        for rb in self.rbGNSS:
            if 'All' in rb.text():
                rb.setChecked(Qt.Checked)

        return gbSats

    def createTimeGroup(self) -> QGroupBox:
        """
        createTimeGroup creates selection of timming
        """
        gbTime = QGroupBox('Timing')
        gbTime.setStyleSheet(self.styleSheet)

        print('self.Times[0] = {!s}   type = {!s}'.format(self.Times[0], type(self.Times[0])))
        print('self.Times[-1] = {!s}   type = {!s}'.format(self.Times[-1], type(self.Times[-1])))

        # startTime = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(self.obsData.coords['time'].values[0].astype(int)/1000000000))
        startHour = int(time.strftime("%H", time.gmtime(self.obsData.coords['time'].values[0].astype(int)/1000000000)))
        startMin = int(time.strftime("%M", time.gmtime(self.obsData.coords['time'].values[0].astype(int)/1000000000)))
        endHour = int(time.strftime("%H", time.gmtime(self.obsData.coords['time'].values[-1].astype(int)/1000000000)))
        endMin = int(time.strftime("%M", time.gmtime(self.obsData.coords['time'].values[-1].astype(int)/1000000000)))
        # print('startTime = {!s}'.format(startTime))
        # print('startHour = {:d}'.format(startHour))

        # start time selector
        loTime = QHBoxLayout()

        # keep the initial start QTime so that we can reset the time to previous value if the selected startTime gets less than 1 minute to selected endTime
        self.startQTime = QTime(startHour, startMin, 0, 0)
        self.startTimeEdit = QTimeEdit(self.startQTime)
        self.startTimeEdit.timeChanged.connect(self.slotStartTimeChanged)
        self.startTimeEdit.setTimeRange(QTime(startHour, startMin, 0, 0), QTime(endHour, endMin, 0, 0))

        self.endQTime = QTime(endHour, endMin, 0, 0)
        self.endTimeEdit = QTimeEdit(self.endQTime)
        self.endTimeEdit.timeChanged.connect(self.slotEndTimeChanged)
        self.endTimeEdit.setTimeRange(QTime(startHour, startMin, 0, 0), QTime(endHour, endMin, 0, 0))

        loTime.addWidget(QLabel('Set start time:'))
        loTime.addWidget(self.startTimeEdit)
        loTime.addWidget(QLabel('Set end time:'))
        loTime.addWidget(self.endTimeEdit)
        loTime.addStretch(1)

        gbTime.setLayout(loTime)
        return gbTime

    @pyqtSlot()
    def onToggledGNSSsyst(self):
        """
        action taken when a All / None GNSS button is selected
        """
        # get the sender checkbox
        rbSender = self.sender()
        # detect for whch GNSS we have selected either All or None
        action, GNSS = rbSender.text().split()
        abbrevGNSS = [k for k, v in rnxobs.dGNSSsIDs.items() if v == GNSS][0]

        print('GNSS = {:s}   action = {:s}'.format(GNSS, action))
        print('rbSender = {!s}'.format(rbSender.text()))
        print('abbrevGNSS = {:s}'.format(abbrevGNSS))

        # perform the action requested
        if action == 'All':
            # select all SVs checkbuttons for this GNSS, check them and disable them
            for cb in self.cbSVs:
                if cb.text()[0] == abbrevGNSS:
                    cb.setChecked(Qt.Checked)
                    cb.setEnabled(False)
        elif action == 'None':
            # select all SVs checkbuttons for this GNSS, uncheck them and disable them
            for cb in self.cbSVs:
                if cb.text()[0] == abbrevGNSS:
                    cb.setChecked(Qt.Unchecked)
                    cb.setEnabled(False)
        elif action == 'User':
            # do not change the currecnt selection but make them enabled
            for cb in self.cbSVs:
                if cb.text()[0] == abbrevGNSS:
                    cb.setEnabled(True)

        pass

    def createSignalsGroupBox(self) -> QGroupBox:
        """
        create a grid layout for display of observed signals / channels
        """
        gb = QGroupBox('Signals')
        gb.setStyleSheet(self.styleSheet)

        gbSignalsType = QGroupBox()
        gbSignalsType.setFlat(True);
        gbSignalsType.setStyleSheet("border:0;margin: 0em;")
        gbSignalsType.setContentsMargins(0,0,0,0)

        hbox = QHBoxLayout()
        self.cbSignalsType = []

        self.cbSignalsType.append(QCheckBox('Pseudo Range'))
        self.cbSignalsType.append(QCheckBox('Carrier Phase'))
        self.cbSignalsType.append(QCheckBox('Signal Strength'))
        self.cbSignalsType.append(QCheckBox('Doppler Frequency'))

        hbox.addStretch(1)
        hbox.addWidget(QLabel('Select:'))
        for cb in self.cbSignalsType:
            hbox.addWidget((cb))
            cb.toggled.connect(self.onToggledSignalsType)

        gbSignalsType.setLayout(hbox)

        # create a list of radio buttons and add them to a grid
        loGrid = QGridLayout()
        self.cbSignals = []
        for iSignal, signal in enumerate(self.Signals):
            cb = QCheckBox(self.Signals[iSignal])
            self.cbSignals.append(cb)
            cb.toggled.connect(self.onToggledSignal)

            # disable the signals of type SSI (Signal Strength Indicator) or LLI (Los Lock Indicator)
            if signal.endswith('lli') or signal.endswith('ssi'):
                cb.blockSignals(True)
                cb.setEnabled(False)

            # add to gridlayout
            curRow, curCol = divmod(iSignal, self.nrCols)
            print('createSignalsGroupBox: signal = {!s} iSignal = {:d} curpos = {:d}:{:d}'.format(self.Signals[iSignal], iSignal, curRow, curCol))
            loGrid.addWidget(cb, curRow, curCol)

        vbox = QVBoxLayout()
        vbox.addWidget(gbSignalsType)
        vbox.addLayout(loGrid)
        gb.setLayout(vbox)

        return gb

    @pyqtSlot()
    def onToggledSignalsType(self):
        """
        action called when a checkbox for a specific signal type (PR, CP, DF, SS) is selected
        """
        # get the sender
        cbSender = self.sender()

        # find the signal type we selected and make the abbreviation
        txt1, txt2 = cbSender.text().split()
        abbrevSignalType = txt1[0] + txt2[0]
        # print('signal type ={:s} - {:s}: abbrev = {:s}'.format(txt1, txt2, abbrevSignalType))

        # find all the signals of this type types in rinex observables
        signalsOfType = rnxobs.findSignalsOfType(abbrevSignalType, dict(rnxobs.dGAL, **rnxobs.dGPS))
        # print('signalsOfType = {!s}'.format(signalsOfType))

        # enable / disable these signals according to selection made
        for cb in self.cbSignals:
            if cb.text() in signalsOfType:
                cb.blockSignals(True)
                cb.setChecked(cbSender.isChecked())
                cb.blockSignals(False)

        pass

    @pyqtSlot()
    def onToggledSignal(self):
        """
        called when a specific signal (C1C, L2L, ...) is (de)selected
        """
        cbSender = self.sender()
        signal = cbSender.text()

        # find the signalType to which this signal belongs
        keyOfSignal = rnxobs.findKeyOfSignal(signal, dict(rnxobs.dGAL, **rnxobs.dGPS))
        # print('keyOfSignal = {!s}'.format(keyOfSignal))

        # find all signals of this type that are in the currecnt rine file
        signalsOfType = rnxobs.findSignalsOfType(keyOfSignal[0], dict(rnxobs.dGAL, **rnxobs.dGPS))
        # print('signalsOfType = {!s}'.format(signalsOfType))

        # determine the intersection between the RINEX signals and the signalsOfType
        commonSignals = [v for v in self.Signals if v[0:3] in signalsOfType]
        # print('commonSignals = {!s}'.format(commonSignals))

        # create list of the current selected state of the chackboxes for the commonSignals
        stateCommonSignals = []
        for cb in self.cbSignals:
            if cb.text() in commonSignals:
                stateCommonSignals.append(cb.isChecked())
        # print('stateCommonSignals = {!s}'.format(stateCommonSignals))
        # print('all = {!s}'.format(all(stateCommonSignals)))

        # disable the signalstype checkboxes according to selection made
        for cb in self.cbSignalsType:
            abbrevSignalType = ''.join(item[0].upper() for item in cb.text().split())
            # print('abbrevSignalType = {:s}'.format(abbrevSignalType))
            # print('keyOfSignal = {!s}'.format(keyOfSignal[0]))
            # print('equal = {!s}'.format(abbrevSignalType == keyOfSignal[0]))

            if abbrevSignalType == keyOfSignal[0]:
                cb.blockSignals(True)
                cb.setChecked(all(stateCommonSignals))
                cb.blockSignals(False)

    @pyqtSlot()
    def slotStartTimeChanged(self):
        """
        slot called when the start time changes
        """
        # check that value is ALWAYS at least 1 minute under endTime
        curStartTime = self.startTimeEdit.time()
        curEndTime = self.endTimeEdit.time()

        print('curStartTime = {!s}'.format(curStartTime))
        print('curEndTime = {!s}'.format(curEndTime))
        print('diff = {!s}'.format(curStartTime.secsTo(curEndTime)))

        if curStartTime.secsTo(curEndTime) <= 59:
            # keep previous value for start time
            self.startTimeEdit.setTime(self.startQTime)
        else:
            # store the last value seen
            self.startQTime = curStartTime

        pass

    @pyqtSlot()
    def slotEndTimeChanged(self):
        """
        slot called when the end time changes
        """
        # check that value is ALWAYS at least 1 minute under endTime
        curStartTime = self.startTimeEdit.time()
        curEndTime = self.endTimeEdit.time()

        print('curStartTime = {!s}'.format(curStartTime))
        print('curEndTime = {!s}'.format(curEndTime))
        print('diff = {!s}'.format(curStartTime.secsTo(curEndTime)))

        if curStartTime.secsTo(curEndTime) <= 59:
            # keep previous value for start time
            self.endTimeEdit.setTime(self.endQTime)
        else:
            # store the last value seen
            self.endQTime = curEndTime

        pass

    @pyqtSlot()
    def slotPlotRinexObservables(self):
        """
        called when we want to plot the selection
        """
        # collect the selection into a dict
        dPlot = {}

        # get selected start/end time
        dPlot['Time'] = {}
        date = pd.to_datetime(self.obsData.coords['time'].values[0]).date()
        # print('date = {!s}   {!s}'.format(date, type(date)))
        startHMS = self.startTimeEdit.time().toString(Qt.ISODate)
        endHMS = self.endTimeEdit.time().toString(Qt.ISODate)

        dPlot['Time']['start'] = '{!s}T{!s}'.format(date.strftime('%Y-%m-%d'), startHMS)
        dPlot['Time']['end'] = '{!s}T{!s}'.format(date.strftime('%Y-%m-%d'), endHMS)

        # get selected SVs and signals
        dPlot['SVs'] = [cb.text() for cb in self.cbSVs if cb.isChecked()]
        dPlot['#SVs'] = len(self.cbSVs)
        dPlot['AllSVs'] = [cb.text() for cb in self.cbSVs]
        dPlot['Signals'] = [cb.text() for cb in self.cbSignals if cb.isChecked()]
        dPlot['#Signals'] = len(self.cbSignals)

        dPlot['name'] = self.NetCDFName

        sys.stderr.write('\n\nobservation Display dPlot = {!s}'.format(dPlot))

        # check whether signals and Svs have been selected
        if len(dPlot['SVs']) == 0 or len(dPlot['Signals']) == 0:
            QMessageBox.warning(self, 'rnxplot', 'Please select Signals and Satellites for Plotting', QMessageBox.Cancel)
        else:
            rinexObsPlot.plotRinexObservables(dPlot=dPlot, obsData=self.obsData, logger=self.logger)

        pass

    def LEARN_DATAARRAY(self):
        sys.stdout.write('\nin displayObservations\n')

        # prettyFmt = Formatter.Formatter()
        # sys.stdout.write('rnxobs = \n{!s}'.format(prettyFmt(rnxobs.dGAL)))

        sys.stdout.write('\nBOF ---------------------')
        sys.stdout.write('\n\nself.obsData = {!s}\n\n{!s}\n\n\n'.format(type(self.obsData), self.obsData))

        sys.stdout.write('\n\nself.obsData.values = \n{!s}\n\n'.format(self.obsData.values))
        sys.stdout.write('\n\nself.obsData.dims = \n{!s}\n\n'.format(self.obsData.dims))
        sys.stdout.write('\n\nself.obsData.dims[sv] = {!s}\n\n{!s}\n\n\n'.format(self.obsData.dims['sv'], type(self.obsData.dims['sv'])))

        sys.stdout.write('\n\nself.obsData.dims.keys = \n{!s}\n\n'.format(self.obsData.dims.items()))
        sys.stdout.write('\n\nself.obsData.coords = \n{!s}\n\n'.format(self.obsData.coords))
        sys.stdout.write('\n\nself.obsData.coords type = \n{!s}\n\n'.format(type(self.obsData.coords)))
        sys.stdout.write('\n\nself.obsData.attrs = \n{!s}\n\n'.format(self.obsData.attrs))

        for k, v in self.obsData.coords.items():
            print('key = {!s}  value = {!s}\n'.format(k, v))

        print('\nsv array = {!s}\n\n'.format(self.obsData.coords['sv'][2]))
        print('\nsv array = {!s}\n\n'.format(self.obsData.coords['sv'][2].values))

        print('GET THE SV LIST!!')
        print('\nsv array = {!s}\n\n'.format(self.obsData.coords['sv'].values))

        print('FIND KEYS and its values as an aray TO SELECT')
        for k, _ in self.obsData.coords.items():
            print('key = {!s}\n\n'.format(k))
            print('key={!s} has array {!s} ... {!s}\n\n'.format(k, self.obsData.coords[k].values[:5], self.obsData.coords[k].values[-5:]))

        print('FIND LIST OF DATA NAMES')
        sys.stdout.write('data_vars = {!s}\n\n'.format(self.obsData.data_vars))
        sys.stdout.write('data_vars type = {!s}\n\n'.format(type(self.obsData.data_vars)))

        sys.stdout.write('data_vars.keys() = {!s}\n\n'.format(self.obsData.data_vars.keys()))
        keys = [k for k, _ in self.obsData.data_vars.items()]
        sys.stdout.write('data_vars.keys().items() retain key = {!s}\n\n'.format(keys))
        sys.stdout.write('number of keys = {:d}\n\n'.format(len(keys)))

        for k, _ in self.obsData.data_vars.items():
            print('key = {!s}\n\n'.format(k))
            print('key={!s} has array {!s} ... {!s}\n\n'.format(k, self.obsData.data_vars[k].values[:5], self.obsData.data_vars[k].values[-5:]))

        sys.stdout.write('\nEOF ---------------------')
