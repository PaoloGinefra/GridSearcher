import os
from typing import List, Dict
import logging


class Logger:
    def __init__(self, runName: str, log_path: str):
        self.runName = runName
        self.logPath = log_path
        os.makedirs(log_path, exist_ok=True)

        self.logPath = os.path.join(self.logPath, 'GridSearcherLogs')
        os.makedirs(self.logPath, exist_ok=True)

        self.logPath = os.path.join(self.logPath, runName)
        os.makedirs(self.logPath, exist_ok=True)

        self.version = 0
        while os.path.exists(os.path.join(self.logPath, f"v{self.version}")):
            self.version += 1
        self.logPath = os.path.join(self.logPath, f"v{self.version}")
        os.makedirs(self.logPath)

        self.logger = self.__createLogger()

    def __createLogger(self, name="experiment"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )

        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # file handler
        fh = logging.FileHandler(os.path.join(self.logPath, "logs.txt"))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger

    def logGridConfig(self, config: Dict):
        # Local import to avoid circular import: GridSearcher imports Logger
        # at module level, so importing GridSearcher here only when needed
        # prevents the partially-initialized-module ImportError.
        from .GridSearcher import GridSearcher as GS
        GS.toYAML(config, os.path.join(self.logPath, "grid_config.yaml"))
