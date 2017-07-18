#!/usr/local/bin/python
# -*- coding: utf-8 -*-
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
        self.cameras = self.canvas.layer(self.layers_dict['expansao'])


    def __add_feature_to_layer(self, feat_to_add, data_provider, buffer_flag, bdistance=0):
        inAttr = feat_to_add.attributes()
        inGeom = feat_to_add.geometry()

        # flag = true, create new layer for buffer, if not, add given feature
        if buffer_flag:
            bf_inGeom = inGeom.buffer(bdistance, -1)
            poly = bf_inGeom.asPolygon()
            geom = QgsGeometry.fromPolygon(poly)
            drawn_area = bf_inGeom.area()
            inAttr.append(drawn_area)
        else:
            geom = feat_to_add.geometry()

        outGeom = QgsFeature()
        outGeom.setGeometry(geom) # Output geometry
        outGeom.setAttributes(inAttr) # Output attributes
        data_provider.addFeatures([outGeom])

    def __change_color(self, layer, R, G, B):
        symbols = layer.rendererV2().symbols()
        symbol = symbols[0]
        symbol.setColor(QColor.fromRgb(R, G, B))
        self.canvas.refresh() 
        # self.canvas.refreshLayerSymbology(layer)

    def __create_selected_layer(self, layer, selected_cameras):
        self.selected_layer =  QgsVectorLayer('Point?crs='+self.cameras_crs, 'selected_cameras' , "memory") #3857
        data_provider = self.selected_layer.dataProvider()
        for f in layer.getFeatures():
            if f.id() in selected_cameras:
                self.__add_feature_to_layer(f, data_provider, False)
        QgsMapLayerRegistry.instance().addMapLayer(self.selected_layer)
        self.__change_color(self.selected_layer, 238, 22, 26)
        self.geometries.append(self.selected_layer)

    def __select_cameras(self):
        selected_cameras = []

        for f in self.cameras.getFeatures():
            for a in self.buffer_layer.getFeatures():
                if a.geometry().intersects(f.geometry()):
                    intersection = a.geometry().intersection(f.geometry())
                    selected_cameras.append(f.id())
                    #break  
     
        self.__create_selected_layer(self.cameras, selected_cameras)

    def remove_layers(self):
        layers = self.canvas.layers()
        if self.geometries:
            self.canvas.refresh()
            QgsMapLayerRegistry.instance().removeMapLayers( [f.id() for f in self.geometries] )
            self.geometries = []

    def __bufferDistanceDialog(self):
        buffDistance = QInputDialog.getText(None,'Digite o raio (em metros):','Digite o raio (em metros):')
        try:
            b_distance = int(buffDistance[0])/111000.00
            return b_distance
        except:
            pass
        return None

    def __zoom_to_cameras(self):
        extent = self.buffer_layer.extent()
        extent.scale( 1.2 )
        self.canvas.setExtent(extent)
        self.canvas.refresh()


    def create_buffer(self, bdistance):
        self.buffer_layer = QgsVectorLayer('Polygon?crs='+ self.cameras_crs, 'buffer_area' , 'memory')
        prov = self.buffer_layer.dataProvider()
        fields = self.area_of_interest.pendingFields()
        fields.append(QgsField('COUNT', QVariant.Int, '', 10, 0))
        prov.addAttributes(fields)
        self.buffer_layer.updateFields()
        features = self.area_of_interest.getFeatures()

        for feat in features:
            self.__add_feature_to_layer(feat, prov, True, bdistance)

        QgsMapLayerRegistry.instance().addMapLayer(self.buffer_layer)
        self.buffer_layer.setLayerTransparency(40)
        self.geometries.append(self.buffer_layer)
        self.__change_color(self.buffer_layer, 224, 224, 224)

    def create_point_aoi(self, position):
        self.area_of_interest =  QgsVectorLayer('Point?crs='+self.cameras_crs, 'buffer_point' , "memory") #3857
        data_provider = self.area_of_interest.dataProvider()
        point_feature = QgsFeature()
        qgs_point = QgsPoint(position)
        point_feature.setGeometry(QgsGeometry.fromPoint(qgs_point))
        data_provider.addFeatures([point_feature])
        self.area_of_interest.updateExtents()

    def run(self, mapPoint=None, aoi=None):
        self.remove_layers()
        if mapPoint:
            self.create_point_aoi(mapPoint)
        elif aoi:
            self.area_of_interest = aoi

        self.geometries.append(self.area_of_interest)
        distance = self.__bufferDistanceDialog()
        if distance:
            self.create_buffer(distance)
            self.__select_cameras()
            self.__zoom_to_cameras()
        else:
            print("Erro: Acao cancelada ou raio de distancia informado incorretamente.")

        


