import sys
import os.path
from qgis.core import *
from qgis.utils import iface
from qgis.gui import QgsMapTool
import vlc
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import time
import resources
from player import Player
from mouseclick import MouseClick


class PluginController(QgsMapTool):
    def __init__(self, iface):
        self.iface = iface
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.canvas = iface.mapCanvas()
        self.layer = iface.mapCanvas().currentLayer()


    def canvasPressEvent(self, event):
        if event.button() == 1:
            layer = iface.activeLayer()
            for feature in layer.getFeatures():
                if feature.geometry().type() == QGis.Point:
                    mapPoint = self.toMapCoordinates(event.pos())
                    layerPoint = self.toMapCoordinates(layer, feature.geometry().asPoint())
                    if (mapPoint.x() >= layerPoint.x() - 150 and mapPoint.x() <= layerPoint.x() + 150) and (
                            mapPoint.y() >= layerPoint.y() - 150 and mapPoint.y() <= layerPoint.y() + 150):
                        #print("camera clicada")
                        # print(feature.attributes())
                        startStream()
        if event.button() == 2:
            self.contextMenu = QMenu()
            self.testeAction = QAction("teste", self)
            self.contextMenu.addAction(self.testeAction)
            self.connect(self.testeAction, SIGNAL("triggered()"), self.acaoTeste)
            self.contextMenu.popup(event.globalPos())

    def acaoTeste(self):
        msgBox = QMessageBox()
        msgBox.setText("teste")
        msgBox.setWindowTitle("Teste titulo")
        msgBox.exec_()

    def initGui(self):
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setObjectName("Avigilon")
        self.menu.setTitle("Avigilon")

        # create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/cameraviewer/icon.png"), "Camera viewer plugin", self.iface.mainWindow())
        self.action.setObjectName("CameraViewerAction")
        self.action.setWhatsThis("Configuration for test plugin")
        self.action.setStatusTip("This is status tip")
        self.action.triggered.connect(self.run)
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)
        self.menu.addAction(self.action)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToWebMenu("&Test plugins", self.action)

        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

    def run(self):
        self.iface.mapCanvas().setMapTool(self)
        print("plugin acionado")

    def unload(self):
        self.menu.deleteLater()


def startStream(filename = 'rtsp://administrator:1234@192.168.0.66/defaultPrimary'):
    try:
        iface.player
    except AttributeError:
        iface.player = Player(iface, filename)
        #import time
        #time.sleep(3)
    iface.player.start()