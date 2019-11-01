from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QPushButton, QTextEdit, QLabel)
from PyQt5.QtGui import (QTextCursor)
from PyQt5.QtCore import (pyqtSlot)

import sys

class MainStackedWidget(QTabWidget):

    def __init__(self, parent):
        """
        create a tabbed widget for display of observation and information
        """
        super(QWidget, self).__init__(parent)

        # Initialize tab screen
        # self.tabWidget = QTabWidget()

        self.tabObs = QWidget()
        self.tabInfo = QWidget()

        # Add tabs
        self.addTab(self.tabObs, 'Observations')
        self.addTab(self.tabInfo, 'Information')

        # create the information display
        self.tabInfo.setLayout(self.createInfoDisplay())
        self.vloObs = QVBoxLayout()
        self.tabObs.setLayout(self.vloObs)
        # self.tabObs.setLayout(self.vloObs)

        # Add layouts to the qtabwidget
        self.setLayout(QVBoxLayout())

        # select the info tab at start
        self.setCurrentWidget(self.tabInfo)


    def createInfoDisplay(self) -> QVBoxLayout:
        """
        this tab has a textEdit for displaying result of stdout
        """
        vloInfo = QVBoxLayout()
        self.textEdit = QTextEdit()
        c = self.textEdit.textCursor();

        vloInfo.addWidget(self.textEdit)

        self.tabInfo.setLayout(vloInfo)

        return vloInfo


    def createObsDisplay(self, obsWidget: QWidget):
        """
        add the observation widget to tab observation
        """
        if self.vloObs is not None:
            self.clearLayout(self.vloObs)

        self.vloObs.addWidget(obsWidget)
        self.vloObs.addStretch(1)


    def clearLayout(self, layout):
        if layout != None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    clearLayout(child.layout())


    @pyqtSlot(str)
    def stdOutTextDisplay(self,text):
        """
        display the text in information tab and set cursor at end
        """
        self.textEdit.moveCursor(QTextCursor.End)
        self.textEdit.insertPlainText(text)
        sys.stderr.write('{!s}'.format(text))
        self.textEdit.moveCursor(QTextCursor.End)


    @pyqtSlot()
    def on_click(self):
        """
        switch to tab clicked
        """
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


    @pyqtSlot()
    def slotClearInfoDisplay(self):
        """
        clear the display with Information
        """
        self.textEdit.clear()
