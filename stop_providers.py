import logging
from pathlib import Path
import datetime

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


class TimeStopProvider(StopProvider):
    def __init__(self, timeout: datetime.timedelta):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._timeout = timeout
        now = datetime.datetime.now()
        self._end_time = now + timeout

    def should_stop(self) -> bool:
        now = datetime.datetime.now()
        if now >= self._end_time:
            self._logger.info("Timeout (%s) -> stopping...", self._timeout)
            return True
        return False
