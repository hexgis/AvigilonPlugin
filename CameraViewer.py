#!/usr/bin/env python
# -*- coding: utf-8 -*-

from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from constants import *
from player import Player

class CameraViewerTool(QgsMapTool):
    def __init__(self, iface, cameras):
        self.iface = iface
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.canvas = iface.mapCanvas()
        self.cameras = cameras

        # Menu for right-click option
        self.contextMenu = QMenu()
        self.streamAction = QAction(u"Visualizar Câmera", self)
        self.coordinatesAction = QAction(u"Visualizar Coordenadas", self)
        self.localAction = QAction(u"Visualizar Localização", self)
        self.infoAction = QAction(u"Informações Gerais", self)

        self.contextMenu.addAction(self.coordinatesAction)

        self.connect(self.streamAction, SIGNAL(
            "triggered()"), self.startStream)
        self.connect(self.coordinatesAction, SIGNAL(
            "triggered()"), self.coordinatesDialog)
        self.connect(self.localAction, SIGNAL("triggered()"), self.localDialog)
        self.connect(self.infoAction, SIGNAL("triggered()"), self.infoDialog)

    def canvasPressEvent(self, event):
        self.lastClickPos = self.toMapCoordinates(event.pos())
        if event.button() == 1 and self.isCamera(event):
            self.startStream()
        elif event.button() == 2:
            if self.isCamera(event):
                self.contextMenu.addAction(self.streamAction)
                self.contextMenu.addAction(self.localAction)
                self.contextMenu.addAction(self.infoAction)
            else:
                self.contextMenu.removeAction(self.streamAction)
                self.contextMenu.removeAction(self.localAction)
        # self.contextMenu.removeAction(self.infoAction)
        self.contextMenu.popup(event.globalPos())


    def isCamera(self, event):
        layer = self.cameras
        mapPoint = self.toMapCoordinates(event.pos())
        max_value = 0.0013

        for feature in layer.getFeatures():
            layerPoint = feature.geometry().asPoint()
            if feature.geometry().type() == QGis.Point:
                if (mapPoint.x() >= layerPoint.x() - max_value and mapPoint.x() <= layerPoint.x() + max_value) and (
                        mapPoint.y() >= layerPoint.y() - max_value and mapPoint.y() <= layerPoint.y() + max_value):
                    self.selectedCamera = feature
                    return True
        return False


    def startStream(self):
        """ Starts camera Stream and open player popup
        """
        try:
            self.iface.player
        except AttributeError:
            self.iface.player = Player(CAMERA_PTZ_PATH, 1)
            # self.iface.player = Player(CAMERA_NORMAL_PATH, 2)
        self.iface.player.start(True)

    def coordinatesDialog(self):
        """ Display coordinates of clicked point
        """
        msgBox = QMessageBox()
        msgBox.setText("Coordenadas: x: " + str(self.lastClickPos.x()
                                                ) + ", y: " + str(self.lastClickPos.y()))
        msgBox.setWindowTitle("Coordenadas")
        msgBox.exec_()

    def localDialog(self):
        """ Displays geographic local of  selected camera
        """
        msgBox = QMessageBox()
        msgBox.setText("Localizacao da camera: " +
                       self.selectedCamera.attributes()[2])
        msgBox.setWindowTitle("Localizacao")
        msgBox.exec_()

    def infoDialog(self):
        """ Displays selected camera full address
        """
        msgBox = QMessageBox()
        text = "Ponto: " + self.selectedCamera.attributes()[0] + "" \
            "Endereço: " + self.selectedCamera.attributes()[2] + "" \
            "Bairro: " + self.selectedCamera.attributes()[3]
        msgBox.setText(text)
        msgBox.setWindowTitle("Camera " + self.selectedCamera.attributes()[0])
        msgBox.exec_()
