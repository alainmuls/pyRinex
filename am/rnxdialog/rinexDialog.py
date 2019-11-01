from PyQt5.QtWidgets import (QCheckBox, QHBoxLayout, QDialog, QVBoxLayout,
        QDialogButtonBox, QLabel, QGroupBox, QTimeEdit, QSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QFile, QTextStream, pyqtSignal, pyqtSlot, QTime

from amqtutils import qtutils, fiveminutetimeedit

import os
import sys
from datetime import datetime, timedelta


class SelectRinexInfoDialog(QDialog):
    """
    make selection of GNSS and navigation signals to read from RINEX obs
    """

    def __init__(self, dObservables: dict, dTimes: dict, dGNSSsIDs: dict, styleSheet: str, parent=None):
        """
        params dObservables: GNSS systsems & observables in RINEX file
        params dGNSSsIDs: links GNSS ID to its name
        type dObservables: dict
        type dGNSSsIDs: dict
        """
        super(SelectRinexInfoDialog, self).__init__(parent)

        self.setWindowTitle('Select measurements to load')

        # create variables used in this rinexDialog
        self.cbObs = {}  # Observables for specific GNSS
        self.gbObs = {}  # groupbox for specific GNSS

        # assign the variables
        self.dObservables = dObservables
        self.dGNSSsIDs = dGNSSsIDs
        self.dTimes = dTimes
        self.styleSheet = styleSheet

        # main layout
        loMain = QVBoxLayout(self)

        # add selection of GNSS systems to dialog
        gbGNSS = self.createGNSSGroup()
        loMain.addWidget(gbGNSS)

        # add selection of observables per GNSS
        for _, GNSSId in enumerate(self.dObservables.keys()):
            self.gbObs[GNSSId] = self.createGNSSObservablesGroup(GNSS=GNSSId, observables=self.dObservables[GNSSId])
            loMain.addWidget(self.gbObs[GNSSId])

        # add time selection slider
        gbTimes = self.createTimeGroup()
        loMain.addWidget(gbTimes)

        # add checkbox for SSI & LLI indicator loading
        gbIndicator = self.createIndicatorsGroup()
        loMain.addWidget(gbIndicator)

        # add OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        loMain.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # block main GUI window
        self.setModal(True)


    def returnSelection(self):
        """
        find out which GNSS and which signal type to load
        returns: list of GNSS and signals to load from RINEX Obs
        """
        # return dict with values selected from RINEX Obs
        dRnxSelected = {}

        # detect which GNSSs has been selected for loading
        dGNSSSelected = {}
        listGNSSSelected = []
        for i, chkBox in enumerate(self.cbGNSSs):
            if chkBox.isChecked():
                listGNSSSelected.append(chkBox.text())
        listGNSSSelectedIDs = qtutils.getKeysByValues(self.dGNSSsIDs, listGNSSSelected)

        # Iterate over the list of values
        selectedGNSSObs = {}
        for GNSSSelected in listGNSSSelectedIDs:
            selectedGNSSObs[GNSSSelected] = [v.text() for v in self.cbObs[GNSSSelected] if v.isChecked()]

        # get the selected time range
        SelectedTiming = {}

        qtStartTime = self.startTimeEdit.time()
        dtFormat = '%d/%m/%YT%H:%M:%S'
        dtStart = datetime(self.dTimes['start'].tm_year, self.dTimes['start'].tm_mon, self.dTimes['start'].tm_mday, int(qtStartTime.toString('HH')), int(qtStartTime.toString('mm')), int(qtStartTime.toString('ss')))

        timeStart = self.startTimeEdit.time()
        timeStop = timeStart.addSecs(self.sbDuration.value() * 60)

        SelectedTiming['start'] = datetime(self.dTimes['start'].tm_year, self.dTimes['start'].tm_mon, self.dTimes['start'].tm_mday, int(timeStart.toString('HH')), int(timeStart.toString('mm')), int(timeStart.toString('ss'))).isoformat()
        SelectedTiming['duration'] = self.sbDuration.value()
        SelectedTiming['stop'] = datetime(self.dTimes['start'].tm_year, self.dTimes['start'].tm_mon, self.dTimes['start'].tm_mday, int(timeStop.toString('HH')), int(timeStop.toString('mm')), int(timeStop.toString('ss'))).isoformat()
        SelectedTiming['interval'] = float(self.cbInterval.currentText())

        # get the indicator status
        dRnxSelected['GNSSObs'] = selectedGNSSObs
        dRnxSelected['Timing'] = SelectedTiming
        dRnxSelected['Indicators'] = self.cbIndicator.isChecked()

        print(dRnxSelected)

        return dRnxSelected


    def createGNSSGroup(self):
        """
        create groupbox displaying the GNSS systems
        """
        gb = QGroupBox()

        gb.setTitle('Select GNSS:')
        gb.setStyleSheet(self.styleSheet)

        loGNSS = QHBoxLayout()

        # create list of checkboxes for each GNSS in RINEX observation file
        self.cbGNSSs = []

        for GNSS in self.dObservables.keys():
            self.cbGNSSs.append(QCheckBox(self.dGNSSsIDs[GNSS]))
            self.cbGNSSs[-1].setChecked(Qt.Checked)
            self.cbGNSSs[-1].toggled.connect(self.onToggledGNSS)
            loGNSS.addWidget(self.cbGNSSs[-1])

        loGNSS.addStretch(1)
        gb.setLayout(loGNSS)

        return gb


    @pyqtSlot(bool)
    def onToggledGNSS(self, state):
        """
        called when a checkbox for a GNSS is toggled
        """
        sender = self.sender()

        # check that at least 1 checkbox in GNSS selection is selected
        allUnchecked = all(not chkBox.isChecked() for chkBox in self.cbGNSSs)

        if allUnchecked:
            sender.blockSignals(True)
            sender.setChecked(Qt.Checked)
            sender.blockSignals(False)

        GNSSId = [k for k, v in self.dGNSSsIDs.items() if self.sender().text() in v][0]
        self.gbObs[GNSSId].setEnabled(sender.isChecked())


    def createGNSSObservablesGroup(self, GNSS, observables):
        """
        creates a dialog for selecting the observables for a apecific GNSS

        params GNSS: the satellite system ID
        params observables: the observables for thie satellite system
        type GNSS: str
        type observables: list
        """
        gb = QGroupBox()

        gb.setTitle('Select ' + self.dGNSSsIDs[GNSS] + ' observables:')
        gb.setStyleSheet(self.styleSheet)

        loObs = QHBoxLayout()

        # create list of checkboxes for each GNSS in RINEX observation file
        self.cbObs[GNSS] = []

        for obs in observables:
            self.cbObs[GNSS].append(QCheckBox(obs))
            self.cbObs[GNSS][-1].setChecked(True)
            self.cbObs[GNSS][-1].toggled.connect(self.onToggledObs)
            loObs.addWidget(self.cbObs[GNSS][-1])

        loObs.addStretch(1)
        gb.setLayout(loObs)

        return gb


    @pyqtSlot(bool)
    def onToggledObs(self, state):
        """
        called when a checkbox for a observable is toggled
        """
        sender = self.sender()

        # if this observable is available in another GNSS system, than set this signal to same status
        # get the text of the selected checkbox
        signalStr = sender.text()
        signalStatus = sender.isChecked()

        for GNSS, cbSignalList in self.cbObs.items():
            for _, cbSignal in enumerate(cbSignalList):
                if cbSignal.text() == signalStr:
                    cbSignal.setChecked(signalStatus)

        GNSS = [k for k, v in self.cbObs.items() if self.sender() in v][0]

        # check that at least 1 observable checkbox for this GNSS is selected
        allUnchecked = all(not chkBox.isChecked() for chkBox in self.cbObs[GNSS])

        if allUnchecked:
            sender.blockSignals(True)
            sender.setChecked(Qt.Checked)
            sender.blockSignals(False)


    def createTimeGroup(self):
        """
        groupbox for selecting the times for the observables to read
        """
        gb = QGroupBox()

        gb.setTitle('Select timing:')
        gb.setStyleSheet(self.styleSheet)

        loTimes = QVBoxLayout()

        # start time selector
        loStartTime = QHBoxLayout()
        self.startTimeEdit = fiveminutetimeedit.FiveMinuteTimeEdit(QTime(self.dTimes['start'].tm_hour, self.dTimes['start'].tm_min, 0, 0))
        self.startTimeEdit.setEnabled(False)
        self.startTimeEdit.timeChanged.connect(self.slotTimeChanged)
        self.startTimeEdit.setTimeRange(QTime(self.dTimes['start'].tm_hour, self.dTimes['start'].tm_min, self.dTimes['start'].tm_sec, 0), QTime(self.dTimes['stop'].tm_hour, self.dTimes['stop'].tm_min, self.dTimes['stop'].tm_sec, 0))

        # select the duration in minutes
        self.sbDuration = QSpinBox()
        sys.stderr.write('\nat init self     {!s}'.format(self))
        sys.stderr.write('\nat init duration {!s}'.format(self.sbDuration))
        sys.stderr.flush()

        self.sbDuration.setEnabled(False)
        rinexRangeMins = datetime(*self.dTimes['stop'][0:6]) - datetime(*self.dTimes['start'][0:6])
        rinexRangeMins = (rinexRangeMins.total_seconds() + self.dTimes['interval']) / 60
        self.sbDuration.setRange(15, int(rinexRangeMins))
        self.sbDuration.setSingleStep(5)  # increment by 5 minutes
        self.sbDuration.setValue(self.sbDuration.minimum())
        self.sbDuration.valueChanged.connect(self.slotDurationChanged)

        # add combobox for selecting the interval
        self.cbInterval = QComboBox()
        possibleIntervals = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60]
        # print('self.dTimes[interval] = {:.2f}'.format(self.dTimes['interval']))
        # display ony values greater than current interval and multiple of it
        # j2 = [x for x in j if x >= 5] n % k == 0
        selectableIntervals = [x for x in possibleIntervals if x >= self.dTimes['interval'] and x % self.dTimes['interval'] == 0]
        # print('selectableInterval ={!s}'.format(selectableIntervals))
        self.cbInterval.addItems([str(x) for x in selectableIntervals])

        loStartTime.addWidget(QLabel('Set start time:'))
        loStartTime.addWidget(self.startTimeEdit)
        loStartTime.addWidget(QLabel('Time span:'))
        loStartTime.addWidget(self.sbDuration)
        loStartTime.addWidget(QLabel('min'))
        loStartTime.addWidget(QLabel('Interval:'))
        loStartTime.addWidget(self.cbInterval)
        loStartTime.addWidget(QLabel('sec'))
        loStartTime.addStretch(1)

        # information about Rinex timing
        loRnxTime = QHBoxLayout()
        lblRnxTime = QLabel()
        lblRnxTime.setText('Observations from: {start:s} - {stop:s}. Interval: {interval:.1f}s (# {epochs:d})'.format(start=self.startTimeEdit.minimumTime().toString(Qt.ISODate), stop=self.startTimeEdit.maximumTime().toString(Qt.ISODate), interval=self.dTimes['interval'], epochs=self.dTimes['epochs']))
        loRnxTime.addWidget(lblRnxTime)
        loRnxTime.addStretch(1)

        # add a label displaying current selected time span
        loCurrent = QHBoxLayout()
        self.lblCurSelect = QLabel()

        loCurrent.addWidget(self.lblCurSelect)
        loCurrent.addStretch(1)

        # add to layout
        loTimes.addLayout(loRnxTime)
        loTimes.addLayout(loStartTime)
        loTimes.addLayout(loCurrent)
        loTimes.addStretch(1)

        gb.setLayout(loTimes)

        # enable time and duraction widget
        self.startTimeEdit.setEnabled(True)
        self.sbDuration.setEnabled(True)


        # emit this signal so that the selected part is updated correctly
        self.startTimeEdit.timeChanged.emit(QTime(self.dTimes['start'].tm_hour, self.dTimes['start'].tm_min, self.dTimes['start'].tm_sec, 0))

        return gb


    @pyqtSlot(QTime)
    def slotTimeChanged(self, value):
        """
        slot called when a change is detected in the start time spinbox
        """
        # calculate the current time span
        sys.stderr.write('\nat init self     {!s}'.format(self))
        sys.stderr.flush()
        sys.stderr.write('\nat init duration {!s}'.format(self.sbDuration))
        sys.stderr.flush()
        self.currentTimeSpan(value, self.sbDuration.value())


    @pyqtSlot(int)
    def slotDurationChanged(self, value):
        """
        slot called when a change is detected in the duration spinbox
        """
        # calculate the current time span
        sys.stderr.write('\nat init self     {!s}'.format(self))
        sys.stderr.write('\nat init duration {!s}'.format(self.sbDuration))
        sys.stderr.flush()

        self.currentTimeSpan(self.startTimeEdit.time(), value)


    def currentTimeSpan(self, startTime, interval):
        """
        calculate the time span currecntly selected within the RINEX file
        """
        stopTime = startTime.addSecs(interval * 60)

        self.lblCurSelect.setText('Current time span selection: {start:s} - {stop:s}'.format(start=startTime.toString(Qt.ISODate), stop=stopTime.toString(Qt.ISODate)))


    def createIndicatorsGroup(self):
        """
        createIndicatorsFroup allows to select the indicator
        """
        gb = QGroupBox()

        gb.setTitle('Select Indicators:')
        gb.setStyleSheet(self.styleSheet)

        self.cbIndicator = QCheckBox('Load indicators (SSI & LLI)')
        self.cbIndicator.setChecked(Qt.Checked)

        hbox = QHBoxLayout()
        hbox.addWidget(self.cbIndicator)
        hbox.addStretch(1)

        gb.setLayout(hbox)

        return gb
