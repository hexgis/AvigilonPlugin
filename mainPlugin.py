#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
from os.path import expanduser
from qgis.core import *
from qgis.utils import iface
from qgis.gui import QgsMapTool
from qgis.analysis import QgsGeometryAnalyzer
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from player import Player
from PyQt4.QtGui import *
from camera_finder import CameraFinder
from rectangle_maptool import RectangleMapTool
import vlc
import time
import resources


class PluginController(QgsMapTool):

    def __init__(self, iface):
        self.iface = iface
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.canvas = iface.mapCanvas()

        self.layers_dict = {}
        self.find_cameras_flag = False 
        self.camera_finder = None
        self.rectangle_aoi = None

        self.contextMenu = QMenu()

        self.toolButton = QToolButton()
        self.toolButton.setMenu(QMenu())
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.iface.addToolBarWidget(self.toolButton)

        self.streamAction = QAction(u"Visualizar Câmera", self)
        self.coordinatesAction = QAction(u"Visualizar Coordenadas", self)
        self.localAction = QAction(u"Visualizar Localização", self)
        self.infoAction = QAction(u"Informações Gerais", self)
        self.pointAction = QAction(u"Achar Câmeras na Localização", self)
        self.AOIAction = QAction(u"Desenhar Área de Interesse", self)

        self.contextMenu.addAction(self.coordinatesAction)

        self.connect(self.streamAction, SIGNAL(
            "triggered()"), self.startStream)
        self.connect(self.coordinatesAction, SIGNAL(
            "triggered()"), self.coordinatesDialog)
        self.connect(self.localAction, SIGNAL("triggered()"), self.localDialog)
        self.connect(self.infoAction, SIGNAL("triggered()"), self.infoDialog)
        self.connect(self.AOIAction, SIGNAL("triggered()"), self.draw_aoi)
        self.connect(self.pointAction, SIGNAL(
            "triggered()"), self.buffer_point_aoi)

    def init(self):
        if not self.layers_dict:
            self.layers_dict = dict((k.name(), i)
                                    for i, k in enumerate(self.canvas.layers()))
            self.cameras_crs = self.canvas.layer(
                self.layers_dict['expansao']).crs().geographicCRSAuthId()
            self.canvas.setDestinationCrs(
                QgsCoordinateReferenceSystem(4674, QgsCoordinateReferenceSystem.PostgisCrsId))

    def initGui(self):
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setObjectName("Avigilon")
        self.menu.setTitle("Avigilon")

        self.CameraViewerAction = QAction(QIcon(":/plugins/cameraviewer/icons/camera-viewer.png"),
                                          u"Visualizar câmera", self.iface.mainWindow())
        self.CameraViewerAction.setObjectName("CameraViewerAction")
        self.CameraViewerAction.setWhatsThis("Camera Viewer Plugin")
        self.CameraViewerAction.setStatusTip("Camera Viewer tip")

        self.CameraFinderAction = QAction(QIcon(":/plugins/cameraviewer/icons/camera-finder.png"),
                                          u"Achar câmeras: Ponto", self.iface.mainWindow())
        self.CameraFinderAction.setObjectName("Camera Finder Plugin")
        self.CameraFinderAction.setWhatsThis("Camera Finder Plugin")
        self.CameraFinderAction.setStatusTip("CameraFinder Status Tip")

        QObject.connect(self.CameraViewerAction,
                        SIGNAL("activated()"), self.run)
        QObject.connect(self.CameraFinderAction, SIGNAL(
            "activated()"), self.run_finder)

        self.menu.addAction(self.CameraViewerAction)
        self.menu.addAction(self.CameraFinderAction)

        self.iface.addToolBarIcon(self.CameraViewerAction)

        self.iface.addPluginToWebMenu(
            "&Smarteye Plugins", self.CameraViewerAction)
        self.iface.addPluginToWebMenu(
            "&Smarteye Plugins", self.CameraFinderAction)

        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(
            self.iface.firstRightStandardMenu().menuAction(), self.menu)

        # submenu on camera finder
        finder_menu = self.toolButton.menu()
        finder_menu.addAction(self.CameraFinderAction)
        self.toolButton.setDefaultAction(self.CameraFinderAction)

        self.CameraFinderAOIAction = QAction(
            QIcon(":/plugins/cameraviewer/icons/draw-aoi.png"),
            u"Achar câmeras: Desenho", self.iface.mainWindow())
        self.CameraRangePontoAction = QAction(
            QIcon(":/plugins/cameraviewer/icons/range-point.png"),
            u"Definir alcance de câmeras: Ponto", self.iface.mainWindow())
        self.CameraRangeAoiAction = QAction(
            QIcon(":/plugins/cameraviewer/icons/draw-aoi.png"),
            u"Definir alcance de câmeras: Desenho", self.iface.mainWindow())

        self.CameraFinderAOIAction.setWhatsThis(u"Desenhe a área de interesse")
        self.CameraRangePontoAction.setWhatsThis(
            u"Achar área de interesse: Ponto")
        self.CameraRangeAoiAction.setWhatsThis(
            u"Achar área de interesse: Ponto")

        finder_menu.addAction(self.CameraRangePontoAction)
        finder_menu.addAction(self.CameraFinderAOIAction)
        finder_menu.addAction(self.CameraRangeAoiAction)

        QObject.connect(self.CameraFinderAOIAction, SIGNAL(
            "triggered()"), self.run_finder_aoi)
        QObject.connect(self.CameraRangePontoAction, SIGNAL(
            "triggered()"), self.run_range_point)
        QObject.connect(self.CameraRangeAoiAction, SIGNAL(
            "triggered()"), self.run_range_aoi)

    def canvasPressEvent(self, event):
        self.init()
        self.lastClickPos = self.toMapCoordinates(event.pos())
        if self.find_cameras_flag == True:
            self.executeFinder(event)
        else:
            if event.button() == 1 and self.isCamera(event):
                self.startStream()
            elif event.button() == 2:
                if self.isCamera(event):
                    self.contextMenu.addAction(self.streamAction)
                    self.contextMenu.addAction(self.localAction)
                    # self.contextMenu.addAction(self.infoAction)
                else:
                    self.contextMenu.removeAction(self.streamAction)
                    self.contextMenu.removeAction(self.localAction)
                self.contextMenu.removeAction(self.infoAction)
                self.contextMenu.popup(event.globalPos())

    def isCamera(self, event):
        layer = self.canvas.layer(self.layers_dict['expansao'])
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

    def initialize_plugin(self, message, finder_flag=False, aoi_type=None):
        if finder_flag:
            self.find_cameras_flag = True
            self.AOI_type = aoi_type
        else:
            self.find_cameras_flag = False

        self.iface.mapCanvas().setMapTool(self)
        print(message)

    def run(self):
        self.initialize_plugin("Plugin Acionado - Selecione Camera")

    def run_finder(self):
        self.initialize_plugin(
            "1Plugin Acionado - Clique na Area de Interesse", True, 1)

    def run_finder_aoi(self):
        self.initialize_plugin(
            "2Plugin Acionado - Desenhe a Area de interesse", True, 2)

    def run_range_point(self):
        self.initialize_plugin(
            "3Plugin Acionado - Clique na Area de Interesse", True, 3)

    def run_range_aoi(self):
        self.initialize_plugin(
            "4Plugin Acionado - Desenhe a Area de interesse", True, 4)

    def unload(self):
        self.menu.deleteLater()

    def startStream(self):
        #self.filename = 'rtsp://administrator:1234@192.168.0.65/defaultSecondary?streamType=u'
        self.filename = 'rtsp://administrator:1234@192.168.0.65/defaultPrimary?streamType=u'
        zoom_path = 'http://localhost:55312/camera/'

        try:
            iface.player
        except AttributeError:
            iface.player = Player(iface, self.filename, zoom_path)
        iface.player.start()

    def coordinatesDialog(self):
        msgBox = QMessageBox()
        msgBox.setText("Coordenadas: x: " + str(self.lastClickPos.x()
                                                ) + ", y: " + str(self.lastClickPos.y()))
        msgBox.setWindowTitle("Coordenadas")
        msgBox.exec_()

    def localDialog(self):
        msgBox = QMessageBox()
        msgBox.setText("Localizacao da camera: " +
                       self.selectedCamera.attributes()[2])
        msgBox.setWindowTitle("Localizacao")
        msgBox.exec_()

    def infoDialog(self):
        msgBox = QMessageBox()
        text = "Ponto: " + self.selectedCamera.attributes[0] + "" \
            "Endereço: " + self.selectedCamera.attributes()[2] + "" \
            "Bairro: " + self.selectedCamera.attributes()[3]
        msgBox.setText(text)
        msgBox.setWindowTitle("Camera " + self.selectedCamera.attributes()[0])
        msgBox.exec_()

    ####
    def init_camera(self):
        if not self.camera_finder:
            self.init()
            self.camera_finder = CameraFinder(
                self.canvas, self.layers_dict, self.cameras_crs)

    def buffer_point_aoi(self):
        self.init_camera()
        self.AOI_type = 1
        self.camera_finder.run(mapPoint=self.clicked_point)

    def draw_aoi(self):
        self.init_camera()
        if not self.rectangle_aoi:
            self.rectangle_aoi = RectangleMapTool(self.canvas, self.layers_dict,
                                                  self.cameras_crs, self.camera_finder)

        self.rectangle_aoi.update_type(self.AOI_type)
        self.canvas.setMapTool(self.rectangle_aoi)

    def find_range_pt(self):
        self.init_camera()
        self.AOI_type = 3
        self.camera_finder.run(mapPoint=self.clicked_point, is_range=True)

    def find_range_aoi(self):
        self.init_camera()
        self.AOI_type = 4
        self.camera_finder.run(mapPoint=self.clicked_point, is_range=True)

    def executeFinder(self, event):
        if event.button() == 1:
            self.clicked_point = self.toMapCoordinates(event.pos())

            if self.AOI_type == 1:
                self.buffer_point_aoi()
            elif self.AOI_type == 2:
                self.draw_aoi()
            elif self.AOI_type == 3:
                self.find_range_pt()
            elif self.AOI_type == 4:
                self.draw_aoi()

        elif event.button() == 2:
            self.clicked_point = self.toMapCoordinates(event.pos())
            self.contextMenu.addAction(self.AOIAction)
            self.contextMenu.addAction(self.pointAction)
            self.contextMenu.popup(event.globalPos())
