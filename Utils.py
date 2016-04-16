import sys
import datetime
import traceback
import types
from functools import wraps
from PyQt4 import QtCore, QtGui

def str_time(t):
    return datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S')

def str_time_adj(t):

    if t < 60:
        return datetime.datetime.fromtimestamp(t).strftime('%S sec')
    elif t >= 60 and t < 3600:
        return datetime.datetime.fromtimestamp(t).strftime('%M min %S sec')
    else:
        return datetime.datetime.fromtimestamp(t).strftime('%H h %M min %S sec')

def str_datetime(t):
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')


def PyQtSlotWithExceptions(*args):
    if len(args) == 0 or isinstance(args[0], types.FunctionType):
        args = []
    @QtCore.pyqtSlot(*args)
    def slotdecorator(func):
        @wraps(func)
        def wrapper(*args):
            try:
                func(*args)
            except:
                QtGui.QMessageBox.critical(None, "Slot: Unexpected Error", traceback.format_exc())
        return wrapper
    return slotdecorator


def win32gui_hook():
    try:
        sys.stdout.write("\n")
        sys.stdout.flush()
    except IOError:
        class dummyStream(object):
            ''' dummyStream behaves like a stream but does nothing. '''
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
        sys.stdout = dummyStream()
        sys.stderr = dummyStream()
        sys.stdin = dummyStream()
        sys.__stdout__ = dummyStream()
        sys.__stderr__ = dummyStream()
        sys.__stdin__ = dummyStream()
