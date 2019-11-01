from PyQt5.QtCore import (QObject)
from PyQt5.QtCore import (pyqtSignal, pyqtSlot)

from multiprocessing import Queue


class WriteStream(object):
    """
    The new Stream Object which replaces the default stream associated with sys.stdout
    This object just puts data in a queue!
    """
    def __init__(self,queue):
        self.queue = queue

    def write(self, text):
        try:
            self.queue.put(text)
        except AttributeError:
            pass

class rxStdOut(QObject):
    """
    A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
    It blocks until data is available, and one it has got something from the queue, it sends
    it to the "MainThread" by emitting a Qt Signal
    """
    rxStdOutSignal = pyqtSignal(str)

    def __init__(self,queue,*args,**kwargs):
        QObject.__init__(self,*args,**kwargs)
        self.queue = queue

    @pyqtSlot()
    def run(self):
        while True:
            try:
                text = self.queue.get()
            except EOFError:
                pass

            self.rxStdOutSignal.emit(text)


