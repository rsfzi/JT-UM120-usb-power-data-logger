import logging
from pydantic import BaseModel

from logger.device import get_devices


class DeviceItem(BaseModel):
    vendor_id: str
    product_id: str
    serial_number: str


class DeviceHandler:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def list_devices(self) -> list[DeviceItem]:
        devices = get_devices()
        device_list = []
        for device in devices:
            device_item = DeviceItem(
                vendor_id=f"{device.device_info.vid:x}",
                product_id=f"{device.device_info.pid:x}",
                serial_number=device.serial_number
            )
            device_list.append(device_item)
        return device_list
