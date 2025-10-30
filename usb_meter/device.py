from dataclasses import dataclass
from enum import Enum, auto
import datetime
from typing import Union
from typing import Generator

import usb.core


class DeviceModel(Enum):
    FNB48 = auto()
    C1 = auto()
    FNB58 = auto()
    FNB48S = auto()


@dataclass
class DeviceInfo:
    vid: int
    pid: int
    model: DeviceModel
    refresh_rate: datetime.timedelta


class Device:
    def __init__(self, device_info, usb_device):
        self._device_info = device_info
        self._usb_device = usb_device

    @property
    def device_info(self):
        return self._device_info

    @property
    def usb_device(self):
        return self._usb_device

    @property
    def serial_number(self):
        sn = usb.util.get_string(self._usb_device, self._usb_device.iSerialNumber)
        return sn

    @property
    def product_name(self):
        sn = usb.util.get_string(self._usb_device, self._usb_device.iProduct)
        return sn

    @property
    def manufacturer_name(self):
        sn = usb.util.get_string(self._usb_device, self._usb_device.iManufacturer)
        return sn

_DEVICE_MAP = {
    # FNB48
    # Bus 001 Device 020: ID 0483:003a STMicroelectronics FNB-48
    (0x0483, 0x003A): DeviceInfo(0x0483, 0x003A, DeviceModel.FNB48, datetime.timedelta(milliseconds=3)),
    # C1
    # Bus 001 Device 029: ID 0483:003b STMicroelectronics USB Tester
    (0x0483, 0x003B): DeviceInfo(0x0483, 0x003B, DeviceModel.C1, datetime.timedelta(milliseconds=3)),
    # FNB58
    (0x2E3C, 0x5558): DeviceInfo(0x2E3C, 0x5558, DeviceModel.FNB58, datetime.timedelta(seconds=1)),
    # FNB48S
    # Bus 001 Device 003: ID 2e3c:0049 FNIRSI USB Tester
    (0x2E3C, 0x0049): DeviceInfo(0x2E3C, 0x0049, DeviceModel.FNB48S, datetime.timedelta(seconds=1)),
}


def all_devices() -> Generator[Device, None, None]:
    for (vid, pid), info in _DEVICE_MAP.items():
        devices = usb.core.find(find_all=True, idVendor=vid, idProduct=pid)
        for device in devices:
            yield Device(info, device)


def _find_device_info(usb_device) -> Union[DeviceInfo, None]:
    for (vid, pid), info in _DEVICE_MAP.items():
        if usb_device.idVendor == vid:
            if usb_device.idProduct == pid:
                return info
    return None


def devices_by_vid_pid(vid: int, pid: int) -> Generator[Device, None, None]:
    for usb_device in usb.core.find(find_all=True, idVendor=vid, idProduct=pid):
        device_info = _find_device_info(usb_device)
        if device_info:
            yield Device(device_info, usb_device)


def devices_by_serial_number(serial_number: Union[int, str]) -> Generator[Device, None, None]:
    if isinstance(serial_number, str):
        serial_number_int = int(serial_number, 16)
    else:
        serial_number_int = serial_number

    def has_serial_number(dev):
        try:
            sn_str = usb.util.get_string(dev, dev.iSerialNumber)
            if sn_str:
                sn = int(sn_str, 16)
                if serial_number_int == sn:
                    return True
        except ValueError:
            pass
        return False

    for usb_device in usb.core.find(find_all=True, custom_match=has_serial_number):
        device_info = _find_device_info(usb_device)
        if device_info:
            yield Device(device_info, usb_device)
