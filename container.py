from dependency_injector import containers, providers

from configuration import Configuration
from logger import logger
from security import Security


class Container(containers.DeclarativeContainer):

    configuration = providers.Singleton(Configuration)

    security = providers.Factory(Security, configuration=configuration, logger=logger)
