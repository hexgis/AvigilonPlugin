#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from camera_finder import CameraFinder
from vector_layer_tool import VectorLayerManager


class RectangleMapTool(QgsMapToolEmitPoint):        
    def __init__(self, canvas, layers_dict, crs, camera_finder):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberband = QgsRubberBand(self.canvas, QGis.Polygon)
        # self.rubberband.setColor(Qt.red)
        self.rubberband.setWidth(1)
        self.point = None
        self.points = []
        self.reset()
        self.vlm = VectorLayerManager(canvas, crs)

        self.layers_dict = layers_dict
        self.cameras_crs = crs
        self.camera_finder = camera_finder
        self.type_of_aoi = None

    def reset(self):
        """ Reset/remove the rubberband polygon
        """
        self.point = None
        self.points = []
        self.isEmittingPoint = False
        self.rubberband.reset(QGis.Polygon)

        vertex_items = [ i for i in self.canvas.scene().items() if issubclass(type(i), QgsVertexMarker)]

        for ver in vertex_items:
            if ver in self.canvas.scene().items():
                self.canvas.scene().removeItem(ver)

    def update_type(self, aoitype):
        """Update the type<int> of area of interest it will be: 
            2: custom drawn to find cameras
            4: custom drawn to find cameras' range
        """
        self.type_of_aoi = aoitype

    def canvasPressEvent(self, e):
        """ When pressing mouse with rubberband
        """
        if e.button() == 1:
            self.point = self.toMapCoordinates(e.pos())
            m = QgsVertexMarker(self.canvas)
            m.setCenter(self.point)
            m.setColor(QColor(0, 255, 0))
            m.setIconSize(5)
            m.setIconType(QgsVertexMarker.ICON_BOX)
            m.setPenWidth(3)
            self.points.append(self.point)
            self.isEmittingPoint = True
            self.showPoly()

        elif e.button() == 2:
            self.isEmittingPoint = False
            if self.points:
                self.draw_aoi()
                self.reset()
 
    def showPoly(self):
        self.rubberband.reset(QGis.Polygon)
        for point in self.points[:-1]:
            self.rubberband.addPoint(point, False)
            self.rubberband.addPoint(self.points[-1], True)
            self.rubberband.show()

    def draw_aoi(self):
        """ After defining the area of interest (aoi), draw the real aoi,
            add layer to canvas and call camera_finder 
        """
        self.aoi = self.vlm.create_layer('Polygon', 'buffer_point')
        self.vlm.create_feature(self.aoi, False, point_list=self.points)

        QgsMapLayerRegistry.instance().addMapLayer(self.aoi)
        self.aoi.setLayerTransparency(40)

        if self.type_of_aoi == 2:  # just find cameras
            self.camera_finder.run(aoi=self.aoi)
        else:
            # find cameras' range
            self.camera_finder.run(aoi=self.aoi, is_range=True)

    def deactivate(self):
        super(RectangleMapTool, self).deactivate()
        self.emit(SIGNAL("deactivated()"))
