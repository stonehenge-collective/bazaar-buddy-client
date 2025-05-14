from dependency_injector import containers, providers

from configuration import Configuration
from logger import logger
from security import Security
from message_builder import MessageBuilder
from text_extractor import TextExtractor


class Container(containers.DeclarativeContainer):

    configuration = providers.Singleton(Configuration)

    security = providers.Factory(Security, configuration=configuration, logger=logger)

    message_builder = providers.Factory(MessageBuilder, configuration=configuration, logger=logger)

    text_extractor = providers.Factory(TextExtractor, configuration=configuration, logger=logger)
