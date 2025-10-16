import logging
from pathlib import Path

from logger.stop_provider import StopProvider


class FileStopProvider(StopProvider):
    def __init__(self, path: Path = Path("fnirsi_stop")):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._path = path

    def should_stop(self) -> bool:
        if self._path.exists():
            self._logger.info("Stop file (%s) found -> stopping...", self._path)
            return True
        return False
