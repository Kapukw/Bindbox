import sys
import time
import traceback
from functools import wraps
from PyQt5 import QtCore, QtWidgets

def stringFromTime(t):
    return time.strftime('%H:%M:%S', time.gmtime(t))

def stringFromRemainingTime(t):
    if t < 60.0:
        return time.strftime('%S sec', time.gmtime(t))
    elif t >= 60.0 and t < 3600.0:
        return time.strftime('%M min %S sec', time.gmtime(t))
    else:
        return time.strftime('%H h %M min %S sec', time.gmtime(t))

def pyqtSlotWithExceptions(*args, **kwargs):
    if len(args) == 0 or callable(args[0]):
        args = []
    
    @QtCore.pyqtSlot(*args, **kwargs)
    def slotDecorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                QtWidgets.QMessageBox.critical(None, "Slot: Unexpected Error", traceback.format_exc())
        return wrapper
    return slotDecorator


def winGuiHook():
    class DummyStream(object):
        ''' DummyStream behaves like a stream but does nothing. '''
        def __init__(self):
            pass
        def write(self, data):
            pass
        def read(self, data):
            pass
        def flush(self):
            pass
        def close(self):
            pass

    def replaceStreams():
        sys.stdout      = DummyStream()
        sys.stderr      = DummyStream()
        sys.stdin       = DummyStream()
        sys.__stdout__  = DummyStream()
        sys.__stderr__  = DummyStream()
        sys.__stdin__   = DummyStream()

    if sys.stdout is None:
        replaceStreams()
        return

    try:
        sys.stdout.write("\n")
        sys.stdout.flush()
    except IOError:
        replaceStreams()
