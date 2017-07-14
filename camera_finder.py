import sys
import os.path
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class CameraFinder():
    def __init__(self, canvas, layers_dict, crs):
        self.canvas = canvas
        self.layers_dict = layers_dict
        self.cameras_crs = crs
        self.buffer_layer = None
        self.area_of_interest = None
        self.selected_layer = None

        self.geometries = []


    def __add_feature_to_layer(self, feat_to_add, data_provider, buffer_flag, bdistance=0):
        inAttr = feat_to_add.attributes()
        inGeom = feat_to_add.geometry()

        #if creating a buffer, draw it, if not, just copy feature as is
        if buffer_flag:
            bf_inGeom = inGeom.buffer(bdistance, -1)
            poly=bf_inGeom.asPolygon()
            geom = QgsGeometry.fromPolygon(poly)
            drawn_area = bf_inGeom.area()
            inAttr.append(drawn_area)
        else:
            geom=feat_to_add.geometry()

        outGeom = QgsFeature()
        outGeom.setGeometry(geom) # Output geometry
        outGeom.setAttributes(inAttr) # Output attributes
        data_provider.addFeatures([outGeom])

    def __create_selected_layer(self, layer, selected_cameras):
        self.selected_layer =  QgsVectorLayer('Point?crs='+self.cameras_crs, 'selected_cameras' , "memory") #3857
        data_provider = self.selected_layer.dataProvider()

        for f in layer.getFeatures():
            if f.id() in selected_cameras:
                self.__add_feature_to_layer(f, data_provider, False)

        QgsMapLayerRegistry.instance().addMapLayer(self.selected_layer)
        self.geometries.append(self.selected_layer)

    def __select_cameras(self):
        selected_cameras = []
        cameras = self.canvas.layer(self.layers_dict['expansao'])
        print(self.buffer_layer)
        for f in cameras.getFeatures():
            for a in self.buffer_layer.getFeatures():
                if a.geometry().intersects(f.geometry()):
                    intersection = a.geometry().intersection(f.geometry())
                    selected_cameras.append( f.id() )
                    break 

        print(selected_cameras)
        self.__create_selected_layer(cameras, selected_cameras)

    def create_buffer(self, bdistance):
        self.buffer_layer = QgsVectorLayer('Polygon?crs='+ self.cameras_crs, 'buffer_area' , 'memory')
        prov = self.buffer_layer.dataProvider()

        fields = self.area_of_interest.pendingFields()
        fields.append(QgsField('drawn_area', QVariant.Double, '', 100, 3))
        prov.addAttributes(fields)
        self.buffer_layer.updateFields()
        features = self.area_of_interest.getFeatures()

        for feat in features:
            self.__add_feature_to_layer(feat, prov, True, bdistance)
         
        QgsMapLayerRegistry.instance().addMapLayer(self.buffer_layer)
        self.buffer_layer.setLayerTransparency(50)

        self.geometries.append(self.buffer_layer)

        # QgsMapLayerRegistry.instance().addMapLayer(self.area_of_interest)
        

    def remove_layers(self):
        # layer_names = ['buffer_point', 'buffer_area', 'selected_cameras', 'aoi_point']
        layers = self.canvas.layers()
        if QgsMapLayerRegistry.instance().count() > 4:
            self.canvas.refresh()
            QgsMapLayerRegistry.instance().removeMapLayers( [f.id() for f in self.geometries] )
            self.geometries = []



    def create_point_aoi(self, position):
        self.area_of_interest =  QgsVectorLayer('Point?crs='+self.cameras_crs, 'buffer_point' , "memory") #3857
        data_provider = self.area_of_interest.dataProvider()
        pt = QgsFeature()

        point1 = QgsPoint(position)
        pt.setGeometry(QgsGeometry.fromPoint(point1))
        data_provider.addFeatures([pt])
        self.area_of_interest.updateExtents()
        self.geometries.append(self.area_of_interest)

    def bufferDistanceDialog(self):
        buffDistance = QInputDialog.getText(None,'Digite o raio (em metros):','Digite o raio (em metros):')
        try:
            b_distance = int(buffDistance[0])/111000.00
            return b_distance
        except:
            pass
        return None

    def zoom_to_cameras(self):
        extent = self.buffer_layer.extent()
        extent.scale( 1.2 )
        self.canvas.setExtent(extent)
        self.canvas.refresh()


    def run_point_aoi(self, mapPoint):
        self.remove_layers()
        self.create_point_aoi(mapPoint)
        distance = self.bufferDistanceDialog()

        if distance:
            self.create_buffer(distance)
            self.__select_cameras()
            self.zoom_to_cameras()
        else:
            print("Erro")

    def run_draw_aoi(self, aoi):
        self.area_of_interest = aoi
        distance = self.bufferDistanceDialog()
        if distance:
            self.create_buffer(distance)
            self.__select_cameras()
            self.zoom_to_cameras()


