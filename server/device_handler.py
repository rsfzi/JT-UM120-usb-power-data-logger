import logging
from pydantic import BaseModel


class DeviceItem(BaseModel):
    vendor_id: str
    product_id: str
    serial_number: str


class DeviceHandler:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_devices(self) -> list[DeviceItem]:
        return []
