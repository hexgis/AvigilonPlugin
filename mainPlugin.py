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

        self.contextMenu = QMenu()
        self.streamAction = QAction("Visualizar Camera", self)
        self.coordinatesAction = QAction("Visualizar Coordenadas", self)
        self.localAction = QAction("Visualizar Localizacao", self)
        self.contextMenu.addAction(self.coordinatesAction)
        self.connect(self.streamAction, SIGNAL("triggered()"), self.startStream)
        self.connect(self.coordinatesAction, SIGNAL("triggered()"), self.coordinatesDialog)
        self.connect(self.localAction, SIGNAL("triggered()"), self.localDialog)

    def canvasPressEvent(self, event):
        if event.button() == 1 and self.isCamera(event):
            self.startStream()
        if event.button() == 2:
            if self.isCamera(event):
                self.contextMenu.addAction(self.streamAction)
                self.contextMenu.addAction(self.localAction)
            else:
                self.contextMenu.removeAction(self.streamAction)
                self.contextMenu.removeAction(self.localAction)
            self.lastClickPos = self.toMapCoordinates(event.pos())
            self.contextMenu.popup(event.globalPos())

    def isCamera(self, event):
        layer = iface.activeLayer()
        for feature in layer.getFeatures():
            if feature.geometry().type() == QGis.Point:
                mapPoint = self.toMapCoordinates(event.pos())
                layerPoint = self.toMapCoordinates(layer, feature.geometry().asPoint())
                if (mapPoint.x() >= layerPoint.x() - 150 and mapPoint.x() <= layerPoint.x() + 150) and (
                                mapPoint.y() >= layerPoint.y() - 150 and mapPoint.y() <= layerPoint.y() + 150):
                    self.selectedCamera = feature
                    return True
        return False

    def initGui(self):
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setObjectName("Avigilon")
        self.menu.setTitle("Avigilon")

        # create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/cameraviewer/icon.png"), "Camera viewer plugin", self.iface.mainWindow())
        self.action.setObjectName("CameraViewerAction")
        self.action.setWhatsThis("Camera Viewer Plugin")
        self.action.setStatusTip("CameraViewer status tip")
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


    def startStream(self):
        self.filename = 'rtsp://administrator:1234@192.168.0.66/defaultPrimary'
        try:
            iface.player
        except AttributeError:
            iface.player = Player(iface, self.filename)
        iface.player.start()

    def coordinatesDialog(self):
        msgBox = QMessageBox()
        msgBox.setText("Coordenadas: x: " + str(self.lastClickPos.x()) + ", y: " + str(self.lastClickPos.y()))
        msgBox.setWindowTitle("Coordenadas")
        msgBox.exec_()

    def localDialog(self):
        msgBox = QMessageBox()
        msgBox.setText("Localizacao da camera: " + self.selectedCamera.attributes()[2])
        msgBox.setWindowTitle("Localizacao")
        msgBox.exec_()