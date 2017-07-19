#!/usr/bin/env python
# -*- coding: utf-8 -*-

def classFactory(iface):
    from .mainPlugin import PluginController
    return PluginController(iface)
