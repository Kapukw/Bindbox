# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QVariant', 2)
import sys, os, time, traceback
from PyQt4 import QtCore, QtGui

import Bindbox
from Utils import *
import BindboxGUI_rc


g_sleep_min = 10
g_max_messages_count = 30


class TimestampWidget(QtGui.QWidget):
	errorPix = None
	successPix = None

	def __init__(self, time, result):
		super(TimestampWidget, self).__init__()

		resultLabel = QtGui.QLabel()
		if result == 0:
			resultLabel.setPixmap(self.successPix)
		else:
			resultLabel.setPixmap(self.errorPix)

		timestampLabel = QtGui.QLabel()
		timestampLabel.setObjectName("timestampLabel")
		timestampLabel.setFont(QtGui.QFont( "Eurostile", 10, QtGui.QFont.Normal))
		timestampLabel.setText(str_time(time))

		lineWidget = QtGui.QWidget()
		lineWidget.setObjectName("lineWidget")
		lineWidget.setFixedHeight(4)

		layout = QtGui.QHBoxLayout()
		layout.addWidget(resultLabel)
		layout.addWidget(timestampLabel)
		layout.addWidget(lineWidget)
		layout.setStretch(2, 1)
		layout.setContentsMargins(6, 6, 6, 4)
		self.setLayout(layout)
		

class AppInfoWidget(QtGui.QWidget):
	toHostPix = None
	toCloudPix = None

	def __init__(self, name, result):
		super(AppInfoWidget, self).__init__()

		appNameLabel = QtGui.QLabel()
		appNameLabel.setObjectName("appNameLabel")
		appNameLabel.setFont(QtGui.QFont( "Eurostile", 12, QtGui.QFont.Normal))
		appNameLabel.setText(name)

		appSyncResultLabel = QtGui.QLabel()
		appSyncResultLabel.setObjectName("appSyncResultLabel")
		appSyncResultLabel.setText(str(result))
		if result == Bindbox.AppSyncResult.HOST_TO_CLOUD:
			appSyncResultLabel.setPixmap(self.toCloudPix)
		elif result == Bindbox.AppSyncResult.CLOUD_TO_HOST:    
			appSyncResultLabel.setPixmap(self.toHostPix)

		layout = QtGui.QHBoxLayout()
		layout.addWidget(appNameLabel)
		layout.addStretch()
		layout.addWidget(appSyncResultLabel)
		layout.setContentsMargins(15, 0, 20, 0)
		layout.setSpacing(0)
		
		backgroundWidget = QtGui.QWidget()
		backgroundWidget.setObjectName("backgroundWidget")
		backgroundWidget.setFixedSize(320, 38)
		backgroundWidget.setLayout(layout)

		backgroundLayout = QtGui.QHBoxLayout()
		backgroundLayout.addWidget(backgroundWidget)
		backgroundLayout.setAlignment(QtCore.Qt.AlignLeft)
		backgroundLayout.setContentsMargins(28, 0, 0, 0)
		self.setLayout(backgroundLayout)


class AppWindow(QtGui.QWidget):
	qss = """
			QWidget#appWindow {
				background-color: #373737;
			}
			QWidget#lineWidget {
				background-color: #575757;
			}
			QWidget#backgroundWidget {
				background-image: url(:/resources/appinfo_bg.png);
				background-position: center left;
				background-repeat: no-repeat;
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

	iconOptions = None
	iconTray = None

	def __init__(self):
		super(AppWindow, self).__init__()

		self.loadResources()

		self.layout = QtGui.QVBoxLayout(self)
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

		self.startupScript()

	def loadResources(self):
		fontDatabase = QtGui.QFontDatabase()
		fontDatabase.addApplicationFont(":/resources/Eurostile.ttf")
		AppWindow.iconOptions = QtGui.QIcon(":/resources/options.png")
		AppWindow.iconTray = QtGui.QIcon(':/resources/icon16.png')
		
		TimestampWidget.errorPix = QtGui.QPixmap(":/resources/error.png")
		TimestampWidget.successPix = QtGui.QPixmap(":/resources/success.png")

		AppInfoWidget.toHostPix = QtGui.QPixmap(":/resources/to_host.png")
		AppInfoWidget.toCloudPix = QtGui.QPixmap(":/resources/to_cloud.png")

	def createTrayIcon(self):
		showAction = QtGui.QAction("&Show", self, triggered=self.show)
		quitAction = QtGui.QAction("&Quit", self, triggered=QtGui.qApp.quit)
		trayIconMenu = QtGui.QMenu(self)
		trayIconMenu.addAction(showAction)
		trayIconMenu.addSeparator()
		trayIconMenu.addAction(quitAction)
		self.trayIcon = QtGui.QSystemTrayIcon(self)
		self.trayIcon.setContextMenu(trayIconMenu)
		self.trayIcon.setToolTip("Bindbox")
		self.trayIcon.setIcon(self.iconTray)
		self.trayIcon.activated.connect(self.iconActivated)
		self.trayIcon.show()

	def createTopWidget(self):

		self.openConfigButton = QtGui.QPushButton()
		self.openConfigButton.setObjectName("openConfigButton")
		self.openConfigButton.setFixedSize(QtCore.QSize(32, 32))
		self.openConfigButton.setIcon(self.iconOptions)
		self.openConfigButton.setIconSize(QtCore.QSize(32, 32))
		self.openConfigButton.connect(self.openConfigButton, QtCore.SIGNAL("clicked()"), self.btn_openConfig);
		layout = QtGui.QHBoxLayout()
		layout.addStretch()
		layout.addWidget(self.openConfigButton)
		layout.setContentsMargins(6, 6, 6, 6)
		layout.setSpacing(0)
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.layout.addWidget(widget)

	def createListWidget(self):
		self.listWidget = QtGui.QListWidget()
		self.listWidget.setObjectName("listWidget")
		self.listWidget.setSortingEnabled(True)
		self.listWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.listWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.listWidget)
		layout.setContentsMargins(3, 0, 3, 0)
		layout.setSpacing(0)
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.layout.addWidget(widget)

	def createBottomWidget(self):

		self.hostNameLabel = QtGui.QLabel(Bindbox.get_host_name())
		self.hostNameLabel.setObjectName("hostNameLabel")
		self.hostNameLabel.setFont(QtGui.QFont( "Eurostile", 16, QtGui.QFont.Normal))
		self.appCountLabel = QtGui.QLabel("8/12")
		self.appCountLabel.setObjectName("appCountLabel")
		self.appCountLabel.setFont(QtGui.QFont( "Eurostile", 12, QtGui.QFont.Normal))

		leftLayout = QtGui.QVBoxLayout()
		leftLayout.addWidget(self.hostNameLabel)
		leftLayout.addWidget(self.appCountLabel)
		leftLayout.setContentsMargins(0, 0, 0, 0)
		leftLayout.setSpacing(0)
		leftWidget = QtGui.QWidget()
		leftWidget.setLayout(leftLayout)

		timer = QtCore.QTimer(self);
		timer.connect(timer, QtCore.SIGNAL("timeout()"), self.timer_updateGUI);
		timer.start(1000);
		self.timeToSyncLabel = QtGui.QLabel()
		self.timeToSyncLabel.setObjectName("timeToSyncLabel")
		self.timeToSyncLabel.setFont(QtGui.QFont( "Eurostile", 12, QtGui.QFont.Normal))

		layout = QtGui.QHBoxLayout()
		layout.addWidget(leftWidget)
		layout.addStretch()
		layout.addWidget(self.timeToSyncLabel)
		layout.setContentsMargins(10, 10, 10, 10)
		layout.setSpacing(0)

		widget = QtGui.QWidget()
		widget.setFixedHeight(60)
		widget.setLayout(layout)
		self.layout.addWidget(widget)

	def startupScript(self):
		self.startupTime = time.time()
		self.lastBeginSyncTime = self.startupTime
		self.lastEndSyncTime = self.startupTime

		self.workThread = WorkThread()
		self.connect(self.workThread, QtCore.SIGNAL("wt_updateBeginSyncTime(PyQt_PyObject)"), self.wt_updateBeginSyncTime)
		self.connect(self.workThread, QtCore.SIGNAL("wt_updateEndSyncTime(PyQt_PyObject)"), self.wt_updateEndSyncTime)
		self.connect(self.workThread, QtCore.SIGNAL("wt_addTimestamp(PyQt_PyObject, PyQt_PyObject)"), self.wt_addTimestamp)
		self.connect(self.workThread, QtCore.SIGNAL("wt_addAppInfo(PyQt_PyObject, PyQt_PyObject)"), self.wt_addAppInfo)
		self.connect(self.workThread, QtCore.SIGNAL("wt_raiseMessageBox(PyQt_PyObject, PyQt_PyObject)"), self.wt_raiseMessageBox)
		self.workThread.start()

	@PyQtSlotWithExceptions()
	def timer_updateGUI(self):
		remaining_time = self.lastEndSyncTime + g_sleep_min*60 - time.time()
		if remaining_time > 0:
			self.timeToSyncLabel.setText(str_time_adj(remaining_time))
		else:
			self.timeToSyncLabel.setText("...")

	@PyQtSlotWithExceptions()
	def btn_openConfig(self):
		os.startfile(Bindbox.get_config_path())

	@PyQtSlotWithExceptions()
	def app_stopAllTasks(self):

		while self.workThread.isWorking:
			print("Wait sync ending...")
			time.sleep(1)
		
		print("Terminate sync thread")
		self.workThread.terminate()

	def setVisible(self, bool):
		if bool:

			offset_x = 16
			offset_y = 16

			availableGeometry = QtGui.QApplication.desktop().availableGeometry()

			max_x = availableGeometry.width() - self.width() - offset_x
			app_x = self.trayIcon.geometry().center().x() - self.width()/2

			if app_x > max_x:
				app_x = max_x

			app_y = availableGeometry.bottom() - self.height() - offset_y

			app_pos = QtCore.QPoint(app_x, app_y)
			self.setGeometry(QtCore.QRect(app_pos, self.size()))

		return super(AppWindow, self).setVisible(bool)

	def closeEvent(self, event):
		if self.trayIcon.isVisible():
			self.hide()
			event.ignore()

	def iconActivated(self, reason):
		if reason in (QtGui.QSystemTrayIcon.Trigger, QtGui.QSystemTrayIcon.DoubleClick) and not self.isVisible():
			self.show()

	def showTrayMessage(self):
		self.trayIcon.showMessage("Title", "Text", self.iconIdle)

	def addListWidgetItem(self, widget):
		itemsCount = self.listWidget.count()
		if itemsCount >= g_max_messages_count:
			listWidgetItem = self.listWidget.item(itemsCount-1)
			self.listWidget.removeItemWidget(listWidgetItem)
			listWidgetItem = self.listWidget.takeItem(itemsCount-1)
		else:
			listWidgetItem = QtGui.QListWidgetItem(self.listWidget)

		listWidgetItem.setSizeHint(widget.sizeHint())

		self.listWidget.insertItem(0, listWidgetItem)
		self.listWidget.setItemWidget(listWidgetItem, widget)
		self.listWidget.setCurrentRow(0)

	def wt_updateBeginSyncTime(self, t):
		self.lastBeginSyncTime = t

	def wt_updateEndSyncTime(self, t):
		self.lastEndSyncTime = t

	PyQtSlotWithExceptions()
	def wt_addTimestamp(self, time, result):
		self.addListWidgetItem(TimestampWidget(time, result))

	PyQtSlotWithExceptions()
	def wt_addAppInfo(self, name, result):
		self.addListWidgetItem(AppInfoWidget(name, result))

	def wt_raiseMessageBox(self, title, text):
		QtGui.QMessageBox.critical(None, title, text)


class WorkThread(QtCore.QThread):

	def __init__(self):
		QtCore.QThread.__init__(self)
		self.isWorking = False

	def run(self):
		while True:
			self.isWorking = True
			self.updateBeginSyncTime(time.time())

			try:
				Bindbox.main_func(self.addAppInfo)
			except Exception:
				self.raiseMessageBox("Sync: Unexpected Error", traceback.format_exc())
				sync_status = 1
			else:
				sync_status = 0
			finally:
				t = time.time()
				self.updateEndSyncTime(t)
				self.addTimestamp(t, sync_status)
				self.isWorking = False

				print("sleep " + str(g_sleep_min) + " min")
				self.sleep(int(60 * g_sleep_min))

	def updateBeginSyncTime(self, t):
		self.emit(QtCore.SIGNAL('wt_updateBeginSyncTime(PyQt_PyObject)'), t)

	def updateEndSyncTime(self, t):
		self.emit(QtCore.SIGNAL('wt_updateEndSyncTime(PyQt_PyObject)'), t)

	def addTimestamp(self, time, result):
		self.emit(QtCore.SIGNAL('wt_addTimestamp(PyQt_PyObject, PyQt_PyObject)'), time, result)

	def addAppInfo(self, name, result):
		self.emit(QtCore.SIGNAL('wt_addAppInfo(PyQt_PyObject, PyQt_PyObject)'), name, result)

	def raiseMessageBox(self, title, text):
		self.emit(QtCore.SIGNAL('wt_raiseMessageBox(PyQt_PyObject, PyQt_PyObject)'), title, text)

class MyApp(QtGui.QApplication):
	def notify(self, obj, event):
		try:
			return QtGui.QApplication.notify(self, obj, event)
		except Exception:
			QtGui.QMessageBox.critical(None, "C++: Unexpected Error", traceback.format_exc())
			return False

def my_excepthook(type, value, tback):
	QtGui.QMessageBox.critical(None, "Hook: Unexpected Error", traceback.format_exc())
	sys.__excepthook__(type, value, tback)

if __name__ == '__main__':

	win32gui_hook()
	sys.excepthook = my_excepthook

	if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
		QtGui.QMessageBox.critical(None, "Bindbox", "I couldn't detect any system tray on this system.")
		sys.exit(1)

	app = MyApp(sys.argv)
	app.setQuitOnLastWindowClosed(False)

	window = AppWindow()
	app.connect(app, QtCore.SIGNAL("aboutToQuit()"), window.app_stopAllTasks);

	try:
		exit_val = app.exec_()
	except:
		exit_val = 1
	finally:
		sys.exit(exit_val)
