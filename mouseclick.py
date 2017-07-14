from qgis.gui import QgsMapTool
from qgis.utils import iface
from qgis.core import *
from PyQt4 import QtCore


class MouseClick(QgsMapTool):
    afterClick = QtCore.pyqtSignal()

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.layer = canvas.currentLayer()

    def canvasPressEvent(self, event):
        if event.button() == 1:
            layer = iface.activeLayer()
            for feature in layer.getFeatures():
                if feature.geometry().type() == QGis.Point:
                    mapPoint = self.toMapCoordinates(event.pos())
                    layerPoint = self.toMapCoordinates(layer, feature.geometry().asPoint())
                    if (mapPoint.x() >= layerPoint.x() - 150 and mapPoint.x() <= layerPoint.x() + 150) \
                    and (mapPoint.y() >= layerPoint.y() - 150 and mapPoint.y() <= layerPoint.y() + 150):
                        print("camera clicada")
                        print(feature.attributes())
                        self.afterClick.emit()
