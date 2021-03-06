﻿import sys
import os
import time
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg

import Utils
import Bindbox

import BindboxGUI_rc


g_sleepMin = 10.0
g_maxMessagesCount = 30


class TimestampWidget(QtWidgets.QWidget):

    def __init__(self, timestamp, result):
        super(TimestampWidget, self).__init__()

        resultLabel = QtSvg.QSvgWidget()
        if result == 0:
            resultLabel.setFixedSize(QtCore.QSize(20, 16))
            resultLabel.load(":/resources/success.svg")
        else:
            resultLabel.setFixedSize(QtCore.QSize(16, 16))
            resultLabel.load(":/resources/error.svg")

        timestampLabel = QtWidgets.QLabel()
        timestampLabel.setObjectName("timestampLabel")
        timestampLabel.setFont(QtGui.QFont("Eurostile", 10, QtGui.QFont.Normal))
        timestampLabel.setText(Utils.stringFromTime(timestamp))

        lineWidget = QtWidgets.QWidget()
        lineWidget.setObjectName("lineWidget")
        lineWidget.setFixedHeight(4)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(resultLabel)
        layout.addWidget(timestampLabel)
        layout.addWidget(lineWidget)
        layout.setStretch(2, 1)
        layout.setContentsMargins(6, 6, 6, 4)
        self.setLayout(layout)


class AppInfoWidget(QtWidgets.QWidget):

    def __init__(self, name, result):
        super(AppInfoWidget, self).__init__()

        appNameLabel = QtWidgets.QLabel()
        appNameLabel.setObjectName("appNameLabel")
        appNameLabel.setFont(QtGui.QFont("Eurostile", 12, QtGui.QFont.Normal))
        appNameLabel.setText(name)

        resultSvg = QtSvg.QSvgWidget()
        if result == Bindbox.AppSyncResult.HOST_TO_CLOUD:
            resultSvg.setFixedSize(QtCore.QSize(30, 16))
            resultSvg.load(":/resources/to_cloud.svg")
        elif result == Bindbox.AppSyncResult.CLOUD_TO_HOST:
            resultSvg.setFixedSize(QtCore.QSize(33, 16))
            resultSvg.load(":/resources/to_host.svg")

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(appNameLabel)
        layout.addStretch()
        layout.addWidget(resultSvg)
        layout.setContentsMargins(15, 0, 16, 0)
        layout.setSpacing(0)

        backgroundWidget = QtSvg.QSvgWidget()
        backgroundWidget.setFixedSize(316, 32)
        backgroundWidget.load(":/resources/item_bg.svg")
        backgroundWidget.setLayout(layout)

        backgroundLayout = QtWidgets.QHBoxLayout()
        backgroundLayout.addWidget(backgroundWidget)
        backgroundLayout.setAlignment(QtCore.Qt.AlignLeft)
        backgroundLayout.setContentsMargins(28, 3, 0, 3)
        self.setLayout(backgroundLayout)


class AppWindow(QtWidgets.QWidget):
    qss = """
            QWidget#appWindow {
                background-color: #373737;
            }
            QWidget#lineWidget {
                background-color: #575757;
            }
            QPushButton#openConfigButton {
                background: none;
                border: none;
            }
            QLabel#appCountLabel,
            QLabel#timeToSyncLabel,
            QLabel#timestampLabel
            {
                color: #999999;
            }
            QLabel#hostNameLabel,
            QLabel#appNameLabel
            {
                color: #ffffff;
            }
            QListWidget#listWidget {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #2c2c2c, stop: 0.1 #373737, stop: 0.8 #373737, stop: 1 #2c2c2c);
                border: none;
                outline: none;
            }
            QListWidget::item#listWidget,
            QListWidget::item:selected#listWidget,
            QListWidget::item:selected:active#listWidget,
            QListWidget::item:hover#listWidget
            {
                background: none;
                border: none;
            }
            QScrollBar:vertical {
                background: #444444;
                border: none;
                width: 14px;
                margin: 0 0 0 0;
            }
            QScrollBar::handle:vertical {
                background: #818181;
                min-height: 40px;
                margin: 2 2 2 2;
                border-radius: 2px;
            }
            QScrollBar::handle:disabled:vertical {
                background: #505050;
                min-height: 40px;
                margin: 2 2 2 2;
                border-radius: 2px;
            }
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 14px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 14px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 0;
                height: 0;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """

    def __init__(self):
        super(AppWindow, self).__init__()

        QtGui.QFontDatabase().addApplicationFont(":/resources/Eurostile.ttf")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.createTopWidget()
        self.createListWidget()
        self.createBottomWidget()
        self.setLayout(self.layout)

        self.createTrayIcon()

        self.setObjectName("appWindow")
        self.setStyleSheet(AppWindow.qss)
        self.setFixedSize(370, 350)
        self.setWindowTitle("Bindbox")
        self.setWindowFlags(QtCore.Qt.Popup)

        self.startupTime = time.time()
        self.lastBeginSyncTime = self.startupTime
        self.lastEndSyncTime = self.startupTime

        self.startupScript()

    def createTrayIcon(self):
        showAction = QtWidgets.QAction("&Show", self, triggered=self.show)
        quitAction = QtWidgets.QAction("&Quit", self, triggered=self.quitApp)
        trayIconMenu = QtWidgets.QMenu(self)
        trayIconMenu.addAction(showAction)
        trayIconMenu.addSeparator()
        trayIconMenu.addAction(quitAction)
        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(trayIconMenu)
        self.trayIcon.setToolTip("Bindbox")
        self.trayIcon.setIcon(QtGui.QIcon(":/resources/app_icon.svg"))
        self.trayIcon.activated.connect(self.iconActivated)
        self.trayIcon.show()

    def quitApp(self):
        QtCore.QCoreApplication.instance().quit()

    def openAppConfig(self):
        os.startfile(Bindbox.getConfigPath())

    def createTopWidget(self):
        self.openConfigButton = QtWidgets.QPushButton()
        self.openConfigButton.setObjectName("openConfigButton")
        self.openConfigButton.setFixedSize(QtCore.QSize(32, 32))
        self.openConfigButton.clicked.connect(self.openAppConfig)

        # SVG icons are buggy
        #self.openConfigButton.setIcon(QtGui.QIcon(":/resources/options.svg"))
        #self.openConfigButton.setIconSize(QtCore.QSize(32, 32))

        svgIcon = QtSvg.QSvgWidget()
        svgIcon.setFixedSize(QtCore.QSize(32, 32))
        svgIcon.load(":/resources/options.svg")

        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonLayout.setSpacing(0)
        buttonLayout.addWidget(svgIcon)
        self.openConfigButton.setLayout(buttonLayout)

        layout = QtWidgets.QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.openConfigButton)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.layout.addWidget(widget)

    def createListWidget(self):
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setSortingEnabled(True)
        self.listWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.listWidget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.listWidget)
        layout.setContentsMargins(3, 0, 3, 0)
        layout.setSpacing(0)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.layout.addWidget(widget)

    def createBottomWidget(self):
        self.hostNameLabel = QtWidgets.QLabel(Bindbox.getHostName())
        self.hostNameLabel.setObjectName("hostNameLabel")
        self.hostNameLabel.setFont(QtGui.QFont("Eurostile", 16, QtGui.QFont.Normal))
        self.appCountLabel = QtWidgets.QLabel(Bindbox.getSyncStats())
        self.appCountLabel.setObjectName("appCountLabel")
        self.appCountLabel.setFont(QtGui.QFont("Eurostile", 12, QtGui.QFont.Normal))

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.hostNameLabel)
        leftLayout.addWidget(self.appCountLabel)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(0)
        leftWidget = QtWidgets.QWidget()
        leftWidget.setLayout(leftLayout)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.updateGuiByTimer)
        timer.start(1000)
        self.timeToSyncLabel = QtWidgets.QLabel()
        self.timeToSyncLabel.setObjectName("timeToSyncLabel")
        self.timeToSyncLabel.setFont(QtGui.QFont("Eurostile", 12, QtGui.QFont.Normal))

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(leftWidget)
        layout.addStretch()
        layout.addWidget(self.timeToSyncLabel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        widget = QtWidgets.QWidget()
        widget.setFixedHeight(60)
        widget.setLayout(layout)
        self.layout.addWidget(widget)

    def startupScript(self):
        self.workThread = WorkThread()
        self.workThread.updateBeginSyncTimeSignal.connect(self.updateBeginSyncTime)
        self.workThread.updateEndSyncTimeSignal.connect(self.updateEndSyncTime)
        self.workThread.addTimestampSignal.connect(self.addTimestamp)
        self.workThread.addAppInfoSignal.connect(self.addAppInfo)
        self.workThread.raiseMessageBoxSignal.connect(self.raiseMessageBox)
        self.workThread.start()

    @Utils.pyqtSlotWithExceptions()
    def updateGuiByTimer(self):
        remainingTime = self.lastEndSyncTime + g_sleepMin * 60.0 - time.time()
        if remainingTime > 0.0:
            self.timeToSyncLabel.setText(Utils.stringFromRemainingTime(remainingTime))
        else:
            self.timeToSyncLabel.setText("...")

    @Utils.pyqtSlotWithExceptions()
    def stopAllTasks(self):

        while self.workThread.isWorking:
            print("Wait for sync ending...")
            time.sleep(1)

        self.workThread.terminate()
        print("Sync thread stopped.")

        self.trayIcon.hide()
        print("App closed.")

    def setVisible(self, visible):
        if visible:
            appWidth = self.width()
            appHeigth = self.height()
            rightOffset = 16
            bottomOffset = 16
            availableGeometry = QtWidgets.QApplication.desktop().availableGeometry()
            appX = self.trayIcon.geometry().center().x() - appWidth/2
            appX = min(appX, availableGeometry.width() - appWidth - rightOffset)
            appY = availableGeometry.bottom() - appHeigth - bottomOffset
            self.setGeometry(appX, appY, appWidth, appHeigth)
        super(AppWindow, self).setVisible(visible)

    def iconActivated(self, reason):
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            self.setVisible(not self.isVisible())

    def addListWidgetItem(self, widget):
        itemsCount = self.listWidget.count()
        if itemsCount >= g_maxMessagesCount:
            listWidgetItem = self.listWidget.item(itemsCount-1)
            self.listWidget.removeItemWidget(listWidgetItem)
            listWidgetItem = self.listWidget.takeItem(itemsCount-1)
        else:
            listWidgetItem = QtWidgets.QListWidgetItem(self.listWidget)

        listWidgetItem.setSizeHint(widget.sizeHint())

        self.listWidget.insertItem(0, listWidgetItem)
        self.listWidget.setItemWidget(listWidgetItem, widget)
        self.listWidget.setCurrentRow(0)

    @Utils.pyqtSlotWithExceptions()
    def updateBeginSyncTime(self, t):
        self.lastBeginSyncTime = t

    @Utils.pyqtSlotWithExceptions()
    def updateEndSyncTime(self, t):
        self.lastEndSyncTime = t

    @Utils.pyqtSlotWithExceptions()
    def addTimestamp(self, timestamp, result):
        self.appCountLabel.setText(Bindbox.getSyncStats())
        self.addListWidgetItem(TimestampWidget(timestamp, result))

    @Utils.pyqtSlotWithExceptions()
    def addAppInfo(self, name, result):
        self.addListWidgetItem(AppInfoWidget(name, result))

    def raiseMessageBox(self, title, text):
        QtWidgets.QMessageBox.critical(None, title, text)


class WorkThread(QtCore.QThread):

    updateBeginSyncTimeSignal   = QtCore.pyqtSignal('PyQt_PyObject')
    updateEndSyncTimeSignal     = QtCore.pyqtSignal('PyQt_PyObject')
    addTimestampSignal          = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    addAppInfoSignal            = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    raiseMessageBoxSignal       = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

    def __init__(self):
        self.isWorking = False
        return super(WorkThread, self).__init__()

    def run(self):
        while True:
            self.isWorking = True
            self.updateBeginSyncTime(time.time())

            try:
                Bindbox.mainFunction(self.addAppInfo)
            except Exception:
                self.raiseMessageBox("Sync: Unexpected Error", traceback.format_exc())
                syncStatus = 1
            else:
                syncStatus = 0
            finally:
                timestamp = time.time()
                self.updateEndSyncTime(timestamp)
                self.addTimestamp(timestamp, syncStatus)
                self.isWorking = False

                print("sleep " + str(g_sleepMin) + " min")
                self.sleep(int(g_sleepMin * 60))

    def updateBeginSyncTime(self, t):
        self.updateBeginSyncTimeSignal.emit(t)

    def updateEndSyncTime(self, t):
        self.updateEndSyncTimeSignal.emit(t)

    def addTimestamp(self, timestamp, result):
        self.addTimestampSignal.emit(timestamp, result)

    def addAppInfo(self, name, result):
        self.addAppInfoSignal.emit(name, result)

    def raiseMessageBox(self, title, text):
        self.raiseMessageBoxSignal.emit(title, text)

class MyApp(QtWidgets.QApplication):
    def notify(self, obj, event):
        try:
            return QtWidgets.QApplication.notify(self, obj, event)
        except Exception:
            QtWidgets.QMessageBox.critical(None, "C++: Unexpected Error", traceback.format_exc())
            return False

def myExcepthook(exctype, value, tback):
    QtWidgets.QMessageBox.critical(None, "Hook: Unexpected Error", traceback.format_exc())
    sys.__excepthook__(exctype, value, tback)

if __name__ == '__main__':

    Utils.winGuiHook()
    sys.excepthook = myExcepthook

    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(None, "Bindbox", "I couldn't detect any system tray on this system.")
        sys.exit(1)

    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    app = MyApp(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # TODO: handle little time before first sync

    window = AppWindow()
    app.aboutToQuit.connect(window.stopAllTasks)

    try:
        exitValue = app.exec_()
    except:
        exitValue = 1
    finally:
        sys.exit(exitValue)
