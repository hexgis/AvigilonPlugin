#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from CameraFinder import *
from VectorLayerManager import *

class PointBufferTool(QgsMapTool):
    def __init__(self, canvas, crs, cameraFinder):
        self.canvas = canvas
        QgsMapTool.__init__(self, canvas)
        self.crs = crs
        self.vlm = VectorLayerManager(canvas, crs)
        self.type_of_aoi = None
        self.cameraFinder = cameraFinder

    def canvasPressEvent(self, event):
        self.position =  self.toMapCoordinates(event.pos())

    def canvasReleaseEvent(self, event):
        self.createBufferPoint()

    def createBufferPoint(self):
        """ Create clicked point as a layer
        """
        self.mapPoint = self.vlm.create_layer('Point', 'buffer_point')
        self.vlm.create_feature(self.mapPoint, True, position=self.position)
        self.mapPoint.setLayerTransparency(40)

        if self.type_of_aoi == 1:  # just find cameras
            self.cameraFinder.run(mapPoint=self.mapPoint)
        else:
            self.cameraFinder.run(mapPoint=self.mapPoint, is_range=True)

    def updateType(self, aoitype):
        """Update the type<int> of area of interest it will be: 
            1: custom point to find cameras
            3: custom point to find cameras' range
        """
        self.type_of_aoi = aoitype
