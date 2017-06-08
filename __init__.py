def classFactory(iface):
    from .mainPlugin import PluginController
    return PluginController(iface)
