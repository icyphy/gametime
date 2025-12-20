#!/usr/bin/env python
from .analyzer import Analyzer
from .defaults import logger
from .gametime_error import GameTimeError
from .project_configuration import ProjectConfiguration


class GameTime(object):
    """Contains methods and variables that allow a user to import
    GameTime as a module.
    """

    @staticmethod
    def analyze(project_config: ProjectConfiguration) -> Analyzer:
        """
        Arguments:
            project_config:
                object that represents the configuration of a GameTime project.

        Returns:
            configuration provided.
        """
        try:
            gametime_analyzer: Analyzer = Analyzer(project_config)
            gametime_analyzer.create_dag()
            return gametime_analyzer
        except GameTimeError as e:
            logger.error(str(e))
            raise e
