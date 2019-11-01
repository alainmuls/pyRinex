from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout

from amqtutils import led_indicator


class LedLabel(QFrame):
    """
    LedLabel comines a QLabel with a LedIndicator into a single widget
    """

    def __init__(self, nameLabel='N/A', tooltip='Activity Indicator', parent=None):
        QFrame.__init__(self, parent)

        self.lbLedName = QLabel()
        self.lbLedName.setText(nameLabel)
        self.led = led_indicator.LedIndicator()

        if tooltip is not '':
            self.setToolTip(tooltip)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lbLedName)
        hbox.addWidget(self.led)

        # hbox.setSpacing(10)
        hbox.setContentsMargins(10, 2, 10, 2)

        self.setLayout(hbox)

        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(3)


    def getLabelName(self):
        return self.lbLedName.text()
