#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from VectorLayerManager import *


class CameraFinder():
    def __init__(self, canvas, layers_dict, crs):
        self.vlm = VectorLayerManager(canvas, crs)
        self.canvas = canvas
        self.layers_dict = layers_dict
        self.cameras_crs = crs
        self.buffer_layer = None
        self.area_of_interest = None
        self.selected_layer = None
        self.use_all_cameras = True
        self.geometries = []
        
        self.cameras = self.layers_dict['temp_cameras']
        self.cameras_range = self.layers_dict['temp_alcance']

    def __create_selected_layer(self, layer, selected_cameras):
        """ create a layer with with selected cameras in red color
        """
        self.selected_layer = self.vlm.create_layer(
            'Point', 'selected_cameras')
        data_provider = self.selected_layer.dataProvider()

        for f in layer.getFeatures():
            if f.id() in selected_cameras:
                self.vlm.add_feature(f, data_provider, False)

        self.selected_layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(self.selected_layer)
        self.vlm.change_color(self.selected_layer, 238, 22, 26)
        self.geometries.append(self.selected_layer)

    def __select_cameras(self):
        """ Select all cameras inside (that intersect) a buffer_layer
        """
        selected_cameras = []
        for f in self.cameras.getFeatures():
            for a in self.buffer_layer.getFeatures():
                if a.geometry().intersects(f.geometry()):
                    intersection = a.geometry().intersection(f.geometry())
                    selected_cameras.append(f.id())
                    # break

        self.__create_selected_layer(self.cameras, selected_cameras)

    def remove_layers(self):
        """ Remove all layers inside self.geometries list of layers (i.e. temporarily created)
        """
        layers = self.canvas.layers()
        if self.geometries:
            self.canvas.refresh()
            QgsMapLayerRegistry.instance().removeMapLayers(
                [f.id() for f in self.geometries])
            self.geometries = []

    def __bufferDistanceDialog(self):
        """ Dialog for user to input the buffer radius distance in meters
        """
        buffDistance = QInputDialog.getText(
            None, u'Digite o raio (em metros):', u'Digite o raio (em metros):')
        try:
            b_distance = int(buffDistance[0])/111000.00
            return b_distance
        except:
            pass
        return None

    def __select_cameras_range(self):
        """ Create memory layer with all cameras' range that fit within the buffer
        """
        layers = self.canvas.layers()
        ft_buffer = [feat for feat in self.buffer_layer.getFeatures()]
        ft_cameras = [feat for feat in self.cameras_range.getFeatures()]
        geom_intersec = [ft_buffer[0].geometry().intersection(feat.geometry()).exportToWkt()
                         for feat in ft_cameras]
        geom_int_areas = [ft_buffer[0].geometry().intersection(feat.geometry()).area()
                          for feat in ft_cameras]
        uri = "Polygon?crs=" + self.cameras_crs + \
            "&field=id:integer""&field=area&index=yes"
        self.intersections = self.vlm.create_layer(
            uri, 'intersections', is_uri=True)
        prov = self.intersections.dataProvider()
        n = len(geom_intersec)
        feats = [QgsFeature() for i in range(n)]
        for i, feat in enumerate(feats):
            feat.setGeometry(QgsGeometry.fromWkt(geom_intersec[i]))
            feat.setAttributes([i, geom_int_areas[i]])
        prov.addFeatures(feats)
        QgsMapLayerRegistry.instance().addMapLayer(self.intersections)
        self.geometries.append(self.intersections)
        self.vlm.change_color(self.buffer_layer, 83, 229, 20)
        self.vlm.change_texture(self.buffer_layer)

    def create_buffer(self, bdistance):
        """ Create a buffer_layer based on  layer and defined distance
        """
        self.buffer_layer = self.vlm.create_layer('Polygon', 'buffer_area')
        prov = self.buffer_layer.dataProvider()

        fields = self.area_of_interest.pendingFields()
        fields.append(QgsField('COUNT', QVariant.Int, '', 10, 0))
        self.vlm.update_fields(fields, self.buffer_layer)

        features = self.area_of_interest.getFeatures()
        for feat in features:
            self.vlm.add_feature(feat, prov, True, bdistance)

        self.buffer_layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(self.buffer_layer)
        QgsMapLayerRegistry.instance().addMapLayer(self.area_of_interest)
        self.buffer_layer.setLayerTransparency(40)
        self.vlm.change_color(self.buffer_layer, 224, 224, 224)

        self.geometries.append(self.buffer_layer)



    #
    def run(self, mapPoint=None, aoi=None, is_range=False):
        """ Run CameraFinder, merge camera layers, create area_of_interest, 
        get buffer distance and select cameras within buffer
        """
        self.remove_layers()
        if self.use_all_cameras:
            self.use_all_cameras = False

        if mapPoint:
            self.area_of_interest = mapPoint
        elif aoi:
            self.area_of_interest = aoi

        self.geometries.append(self.area_of_interest)

        distance = self.__bufferDistanceDialog()
        if distance:
            self.create_buffer(distance)
            if not is_range:
                self.__select_cameras()
            else:
                self.__select_cameras_range()
                self.__select_cameras()
            self.vlm.zoom_to_layer(self.buffer_layer)
        else:
            self.remove_layers()
            print("Erro: Acao cancelada ou raio de distancia informado incorretamente.")
