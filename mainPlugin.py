#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import resources
import sys
import time
import vlc

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from camera_finder import CameraFinder
from os.path import expanduser
from qgis.analysis import QgsGeometryAnalyzer
from qgis.core import *
from qgis.gui import QgsMapTool
from qgis.utils import iface
from AreaOfInterestTool import *
from VectorLayerManager import *
from CameraViewer import *
from PointBufferTool import *


class PluginController():

    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.layers_dict = {}
        self.is_camera_finder = False
        self.camera_finder = None
        self.custom_aoi = None

        self.avigilonMenu = QMenu(self.iface.mainWindow())
        self.avigilonMenu.setObjectName("Avigilon")
        self.avigilonMenu.setTitle("Avigilon")

        self.cameraFinderMenu = QToolButton()
        self.cameraFinderMenu.setMenu(QMenu())
        self.cameraFinderMenu.setPopupMode(QToolButton.MenuButtonPopup)
        self.iface.addToolBarWidget(self.cameraFinderMenu)

    def update_cameras(self):
        """ atualiza cameras sendo utilizadas para busca com todos os layers
        """
        exp = self.canvas.layer(self.layers_dict['expansao'])
        cam = self.canvas.layer(self.layers_dict['cameras'])
        alcance_exp = self.canvas.layer(self.layers_dict['alcance_expansao'])
        alcance_cam = self.canvas.layer(self.layers_dict['alcance_cameras'])

        self.cameras = self.vlm.merge_layers(exp, cam, 'Point', 'temp_cameras')
        self.cameras_range = self.vlm.merge_layers(
            alcance_exp, alcance_cam, 'Point', 'temp_alcance')

        self.layers_dict['temp_cameras'] = self.cameras
        self.layers_dict['temp_alcance'] = self.cameras_range

    def init(self):
        if not self.layers_dict:
            self.layers_dict = dict((k.name(), i)
                                    for i, k in enumerate(self.canvas.layers()))
            self.canvas.setDestinationCrs(
                QgsCoordinateReferenceSystem(4674, QgsCoordinateReferenceSystem.PostgisCrsId))
            self.crs = self.canvas.mapRenderer().destinationCrs().geographicCRSAuthId()
            self.vlm = VectorLayerManager(self.canvas, self.crs)
            self.update_cameras()

    def initGui(self):
        # Define main actions
        self.CameraViewerAction = QAction(QIcon(":/plugins/cameraviewer/icons/camera-viewer.png"),
                                          u"Visualizar câmera", self.iface.mainWindow())
        self.CameraViewerAction.setObjectName("Camera Viewer Action")
        self.CameraViewerAction.setWhatsThis("Camera Viewer Plugin")
        self.CameraViewerAction.setStatusTip(
            "Ferramenta de visualização de streams de câmeras.")

        self.CameraFinderAction = QAction(QIcon(":/plugins/cameraviewer/icons/camera-finder.png"),
                                          u"Achar câmeras: Clique", self.iface.mainWindow())
        self.CameraFinderAction.setObjectName("Camera Finder Plugin")
        self.CameraFinderAction.setWhatsThis("Camera Finder Plugin")
        self.CameraFinderAction.setStatusTip(
            "Ferramenta de localização de câmeras ativas.")

        self.CameraViewerAction.setCheckable(True)
        self.CameraFinderAction.setCheckable(True)

        # Camera Finder Menu
        finder_menu = self.cameraFinderMenu.menu()
        finder_menu.addAction(self.CameraFinderAction)
        self.cameraFinderMenu.setDefaultAction(self.CameraFinderAction)

        self.CameraFinderAOIAction = QAction(
            QIcon(":/plugins/cameraviewer/icons/draw-aoi.png"),
            u"Achar câmeras: Desenho", self.iface.mainWindow())
        self.CameraFinderAOIAction.setWhatsThis(u"Desenhe a área de interesse")
        finder_menu.addAction(self.CameraFinderAOIAction)

        self.CameraRangePontoAction = QAction(
            QIcon(":/plugins/cameraviewer/icons/range-point.png"),
            u"Definir alcance de câmeras: Clique", self.iface.mainWindow())
        self.CameraRangePontoAction.setWhatsThis(
            u"Achar área de interesse: Clique")
        finder_menu.addAction(self.CameraRangePontoAction)

        self.CameraRangeAoiAction = QAction(
            QIcon(":/plugins/cameraviewer/icons/draw-aoi.png"),
            u"Definir alcance de câmeras: Desenho", self.iface.mainWindow())
        self.CameraRangeAoiAction.setWhatsThis(
            u"Achar área de interesse: Clique")
        finder_menu.addAction(self.CameraRangeAoiAction)

        # Other Menus
        self.avigilonMenu.addAction(self.CameraViewerAction)
        self.avigilonMenu.addAction(self.CameraFinderAction)

        self.iface.addToolBarIcon(self.CameraViewerAction)

        self.iface.addPluginToWebMenu(
            "&Smarteye Plugins", self.CameraViewerAction)
        self.iface.addPluginToWebMenu(
            "&Smarteye Plugins", self.CameraFinderAction)

        # QGis Main Menu
        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(
            self.iface.firstRightStandardMenu().menuAction(), self.avigilonMenu)

        # Connect objects
        QObject.connect(self.CameraViewerAction,
                        SIGNAL("activated()"), self.run)
        QObject.connect(self.CameraFinderAction, SIGNAL(
            "activated()"), self.run_finder)
        QObject.connect(self.CameraFinderAOIAction, SIGNAL(
            "triggered()"), self.run_finder_aoi)
        QObject.connect(self.CameraRangePontoAction, SIGNAL(
            "triggered()"), self.run_range_point)
        QObject.connect(self.CameraRangeAoiAction, SIGNAL(
            "triggered()"), self.run_range_aoi)

    def initialize_plugin(self, message, finder_flag=False, aoi_type=None):
        """ Initialize plugin's flags
        """
        self.init()
        try:
            self.camera_finder
            self.custom_aoi
            self.viewerTool
            self.pointTool
        except AttributeError:
            self.camera_finder = CameraFinder(self.canvas, self.layers_dict, self.crs)
            self.custom_aoi = AreaOfInterestTool(self.canvas, self.crs, self.camera_finder)
            self.viewerTool = CameraViewerTool(self.iface, self.cameras)
            self.pointTool = PointBufferTool(self.canvas, self.crs, self.camera_finder)

        if finder_flag:
            self.is_camera_finder = True
            self.AOI_type = aoi_type
        else:
            self.is_camera_finder = False

    
    # Activate chosen menu option menu option
    def set_checked(self, viewer, finder, deactivate=False):
        self.CameraFinderAction.setChecked(finder)
        self.CameraViewerAction.setChecked(viewer)

    def run(self):
        self.set_checked(True, False)
        self.initialize_plugin("[0]Plugin Acionado - Selecione Camera")
        self.iface.mapCanvas().setMapTool(self.viewerTool)

    def run_finder(self):
        self.set_checked(False, True)
        self.initialize_plugin(
            "[1]Plugin Acionado - Clique na Area de Interesse", True, 1)
        self.pointTool.updateType(self.AOI_type)
        self.canvas.setMapTool(self.pointTool)

    def run_finder_aoi(self):
        self.set_checked(False, True)
        self.initialize_plugin(
            "[2]Plugin Acionado - Desenhe a Area de interesse", True, 2)
        self.custom_aoi.updateType(self.AOI_type)
        self.canvas.setMapTool(self.custom_aoi)

    def run_range_point(self):
        self.set_checked(False, True)
        self.initialize_plugin(
            "[3]Plugin Acionado - Clique na Area de Interesse", True, 3)
        self.pointTool.updateType(self.AOI_type)
        self.canvas.setMapTool(self.pointTool)

    def run_range_aoi(self):
        self.set_checked(False, True)
        self.initialize_plugin(
            "[4]Plugin Acionado - Desenhe a Area de interesse", True, 4)
        self.custom_aoi.updateType(self.AOI_type)
        self.canvas.setMapTool(self.custom_aoi)

    def unload(self):
        self.avigilonMenu.deleteLater()
