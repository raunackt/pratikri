from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita

from .pratikrti import PratikrtiDocker

DOCKER_ID = "pratikrti_docker"

factory = DockWidgetFactory(DOCKER_ID, DockWidgetFactoryBase.DockRight, PratikrtiDocker)


Krita.instance().addDockWidgetFactory(factory)
