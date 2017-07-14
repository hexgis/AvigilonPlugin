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

        self.find_cameras_flag = False 
        self.layers_dict = {}
        self.camera_finder = None
        self.rectangle_aoi = None

        self.contextMenu = QMenu()

        self.streamAction = QAction("Visualizar Camera", self)
        self.coordinatesAction = QAction("Visualizar Coordenadas", self)
        self.localAction = QAction("Visualizar Localizacao", self)
        self.infoAction = QAction("Informacoes gerais", self)
        self.pointAction = QAction("Achar Cameras na Localizacao", self)
        self.AOIAction = QAction("Desenhar Área de Interesse", self)

        self.contextMenu.addAction(self.coordinatesAction)

        self.connect(self.streamAction, SIGNAL("triggered()"), self.startStream)
        self.connect(self.coordinatesAction, SIGNAL("triggered()"), self.coordinatesDialog)
        self.connect(self.localAction, SIGNAL("triggered()"), self.localDialog)
        self.connect(self.infoAction, SIGNAL("triggered()"), self.infoDialog)
        self.connect(self.AOIAction, SIGNAL("triggered()"), self.draw_aoi)
        self.connect(self.pointAction, SIGNAL("triggered()"), self.buffer_point_aoi)

    def init(self, event):
        if not self.layers_dict:
            self.layers_dict = dict((k.name(),i) for i, k in enumerate(self.canvas.layers()))
            self.cameras_crs = self.canvas.layer(self.layers_dict['expansao']).crs().geographicCRSAuthId()  
            self.canvas.setDestinationCrs(\
                QgsCoordinateReferenceSystem(4674, QgsCoordinateReferenceSystem.PostgisCrsId))

    def canvasPressEvent(self, event):
        self.init(event)
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
                    #self.contextMenu.addAction(self.infoAction)
                else:
                    self.contextMenu.removeAction(self.streamAction)
                    self.contextMenu.removeAction(self.localAction)
                    #self.contextMenu.removeAction(self.infoAction)
                self.contextMenu.popup(event.globalPos())


    def isCamera(self, event):
        layer = self.canvas.layer(self.layers_dict['expansao'])
        mapPoint = self.toMapCoordinates(event.pos())
        max_value = 0.001

        for feature in layer.getFeatures():
            layerPoint = feature.geometry().asPoint()
            if feature.geometry().type() == QGis.Point:
                if (mapPoint.x() >= layerPoint.x() - max_value and mapPoint.x() <= layerPoint.x() + max_value) and (
                                mapPoint.y() >= layerPoint.y() - max_value and mapPoint.y() <= layerPoint.y() + max_value):
                    self.selectedCamera = feature
                    return True          
        return False

    def initGui(self):
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setObjectName("Avigilon")
        self.menu.setTitle("Avigilon")

        self.CameraViewerAction = QAction(QIcon(":/plugins/cameraviewer/icons/camera-viewer.png"), "Camera Viewer Plugin", self.iface.mainWindow())
        self.CameraViewerAction.setObjectName("CameraViewerAction")
        self.CameraViewerAction.setWhatsThis("Camera Viewer Plugin")
        self.CameraViewerAction.setStatusTip("CameraViewer status tip")

        self.CameraFinderAction = QAction(QIcon(":/plugins/cameraviewer/icons/camera-finder.png"), "Find Cameras", self.iface.mainWindow())
        self.CameraFinderAction.setObjectName("Camera Finder Action")
        self.CameraFinderAction.setWhatsThis("Camera Viewer Plugin")
        self.CameraFinderAction.setStatusTip("CameraFinder Status Tip")

        QObject.connect(self.CameraViewerAction, SIGNAL("activated()"), self.run)
        QObject.connect(self.CameraFinderAction, SIGNAL("activated()"), self.runFinder)

        self.menu.addAction(self.CameraViewerAction)
        self.menu.addAction(self.CameraFinderAction)         
        #self.CameraViewerAction.activated.connect(self.run) # ou usa um ou usa o outro de cima, nao precsa dos dois

        self.iface.addToolBarIcon(self.CameraViewerAction)
        self.iface.addToolBarIcon(self.CameraFinderAction)

        self.iface.addPluginToWebMenu("&Smarteye Plugins", self.CameraViewerAction)
        self.iface.addPluginToWebMenu("&Smarteye Plugins", self.CameraFinderAction)

        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)
        

    def run(self):
        self.find_cameras_flag = False
        self.iface.mapCanvas().setMapTool(self)
        print("Plugin Acionado")

    def runFinder(self):
        self.find_cameras_flag = True
        self.AOI_type = 1
        self.iface.mapCanvas().setMapTool(self)
        print("Procurando Cameras")

    def unload(self):
        self.menu.deleteLater()

    def startStream(self):
        #self.filename = 'rtsp://administrator:1234@192.168.0.65/defaultSecondary?streamType=u'
        self.filename = 'rtsp://administrator:1234@192.168.0.65/defaultPrimary?streamType=u'
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

    def infoDialog(self):
        msgBox = QMessageBox()
        text = "Ponto: " + self.selectedCamera.attributes[0] + "" \
            "Endereço: " +self.selectedCamera.attributes()[2] + "" \
            "Bairro: " + self.selectedCamera.attributes()[3]
        msgBox.setText(text)
        msgBox.setWindowTitle("Camera " + self.selectedCamera.attributes()[0])
        msgBox.exec_()

    ####    
    def draw_aoi(self):
        self.AOI_type = 2
        if not self.rectangle_aoi:
            self.rectangle_aoi = RectangleMapTool(self.canvas, self.layers_dict, self.cameras_crs)
        self.canvas.setMapTool(self.rectangle_aoi)

    def buffer_point_aoi(self):
        self.AOI_type = 1
        if not self.camera_finder:
            self.camera_finder = CameraFinder(self.canvas, self.layers_dict, self.cameras_crs)     
        self.camera_finder.run_point_aoi(self.clicked_point)
        self.iface.mapCanvas().setMapTool(self) 

    def executeFinder(self, event):
        if event.button() == 1:
            self.clicked_point = self.toMapCoordinates(event.pos())

            if self.AOI_type == 1:
                self.buffer_point_aoi()
            elif self.AOI_type == 2:
                self.draw_aoi()

        elif event.button() == 2:
            self.clicked_point = self.toMapCoordinates(event.pos())
            self.contextMenu.addAction(self.AOIAction)
            self.contextMenu.addAction(self.pointAction)
            self.contextMenu.popup(event.globalPos())
            

