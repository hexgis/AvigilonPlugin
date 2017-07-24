#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class VectorLayerManager():
    def __init__(self, canvas, crs):
        self.canvas = canvas
        self.crs = crs

    def add_feature(self, feature, data_provider, is_buffer, buff_distance=0, segments=15):
        inAttr = feature.attributes()
        inGeom = feature.geometry()

        # flag = true, create new layer for buffer, if not, add given feature
        if is_buffer:
            bf_inGeom = inGeom.buffer(buff_distance, segments)
            poly = bf_inGeom.asPolygon()
            geom = QgsGeometry.fromPolygon(poly)
            drawn_area = bf_inGeom.area()
            inAttr.append(drawn_area)
        else:
            geom = feature.geometry()

        outGeom = QgsFeature()
        outGeom.setGeometry(geom) # Output geometry
        outGeom.setAttributes(inAttr) # Output attributes
        data_provider.addFeatures([outGeom])

    def change_color(self, layer, R, G, B):
        """ change colors of given layer
        """
        layer.rendererV2().symbols2(QgsRenderContext())[0].setColor(QColor.fromRgb(R, G, B))
        self.canvas.refresh() 

    def change_texture(self, layer):
        """ change texture of given layer
        """
        symbol_layer = QgsLinePatternFillSymbolLayer()
        symbol_layer.setColor(QColor(255,255,255))
        symbol_layer.setLineWidth(2)
        symbol_layer.setDistance(4)
        layer.rendererV2().symbols2(QgsRenderContext())[0].changeSymbolLayer(0, symbol_layer)
        self.canvas.refresh() 

    def update_fields(self, fields, layer):
        prov = layer.dataProvider()
        prov.addAttributes(fields)
        layer.updateFields()

    def create_layer(self, layer_type, name, is_uri=False):
        if is_uri:
            layer = QgsVectorLayer(layer_type, name, 'memory')
        else:
            layer = QgsVectorLayer(layer_type+'?crs='+ self.crs, name, 'memory')

        return layer

    def create_feature(self, layer, is_point, position=None, point_list=None):
        provider = layer.dataProvider()
        feature = QgsFeature()
        if is_point:
            qgs_point = QgsPoint(position)
            feature.setGeometry(QgsGeometry.fromPoint(qgs_point))
        else:
            feature.setGeometry(QgsGeometry.fromPolygon([point_list]))
        provider.addFeatures([feature])
        layer.updateExtents()

    def zoom_to_layer(self, layer):
        extent = layer.extent()
        extent.scale( 1.2 )
        self.canvas.setExtent(extent)
        self.canvas.refresh()


    def merge_layers(self, layer1, layer2, layer_type, temp_name):
        """ create a temporarily layer by merging two other layers
        """
        merged_layers = QgsVectorLayer(layer_type+'?crs='+self.crs, temp_name, "memory")
        fields = layer1.pendingFields()
        provider = merged_layers.dataProvider()

        for f in fields:
            provider.addAttributes([f])

        merged_layers.updateFields()

        layer1_features = layer1.getFeatures()
        for feature in layer1_features:
            provider.addFeatures([feature])

        layer2_features = layer2.getFeatures()
        for feature in layer2_features:
            provider.addFeatures([feature])

        merged_layers.updateExtents()

        return merged_layers

