from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from camera_finder import CameraFinder


class RectangleMapTool(QgsMapToolEmitPoint):

    def __init__(self, canvas, layers_dict, crs):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, QGis.Polygon)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setWidth(1)
        self.reset()

        self.layers_dict = layers_dict
        self.cameras_crs = crs
        self.camera_finder = None

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QGis.Polygon)

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showRect(self.startPoint, self.endPoint)

    def draw_aoi(self):
        if not self.camera_finder:
            self.camera_finder = CameraFinder(self.canvas, self.layers_dict, self.cameras_crs)

        self.camera_finder.remove_layers()

        self.area_of_interest =  QgsVectorLayer('Polygon?crs='+self.cameras_crs, 'aoi_point' , "memory")
        provider = self.area_of_interest.dataProvider()
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPolygon([self.point_list]))
        provider.addFeatures([feature])
        QgsMapLayerRegistry.instance().addMapLayer(self.area_of_interest)
        self.area_of_interest.updateExtents()
        self.area_of_interest.setLayerTransparency(50)


        self.camera_finder.run_draw_aoi(self.area_of_interest)

        

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        r = self.rectangle()
        # if r is not None:
        #     print "Rectangle:", r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum()

        self.draw_aoi()
        self.reset()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
        self.rubberBand.reset(QGis.Polygon)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        self.point_list = []

        point1 = QgsPoint(startPoint.x(), startPoint.y())
        point2 = QgsPoint(startPoint.x(), endPoint.y())
        point3 = QgsPoint(endPoint.x(), endPoint.y())
        point4 = QgsPoint(endPoint.x(), startPoint.y())

        self.point_list = [point1, point2, point3, point4]

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)    # true to update canvas
        self.rubberBand.show()

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def deactivate(self):
        super(RectangleMapTool, self).deactivate()
        self.emit(SIGNAL("deactivated()"))