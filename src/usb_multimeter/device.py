from dataclasses import dataclass
from enum import Enum, auto
import datetime
from typing import Union, Callable
from typing import Generator
from pathlib import Path
import errno

import usb.core


class DeviceModel(Enum):
    FNB48 = auto()
    C1 = auto()
    FNB58 = auto()
    FNB48S = auto()


@dataclass(frozen=True)
class DeviceInfo:
    vid: int
    pid: int
    model: DeviceModel
    refresh_rate: datetime.timedelta


class Device:
    def __init__(self, device_info: DeviceInfo, usb_device: usb.core.Device):
        self._device_info = device_info
        self._usb_device = usb_device

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def usb_device(self) -> usb.core.Device:
        return self._usb_device

    @property
    def serial_number(self) -> str:
        sn = self._usb_device.serial_number
        return sn

    @property
    def product_name(self) -> str:
        pn = self._usb_device.product
        return pn

    @property
    def manufacturer_name(self) -> str:
        mn = self._usb_device.manufacturer
        return mn

    @property
    def location(self) -> str:
        return f"On Bus {self._usb_device.bus:03d} Address {self._usb_device.address:03d}"

    @property
    def device_path(self) -> Path:
        return get_device_path(self._usb_device)

    def access_check(self) -> None:
        check_permissions(self._usb_device)


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


def check_permissions(device: usb.core.Device) -> None:
    try:
        device.get_active_configuration()
    except usb.core.USBError as e:
        if e.errno == errno.EACCES:
            raise PermissionError("%s %s" % (get_device_path(device), e)) from e
        raise e


def get_device_path(device: usb.core.Device) -> Path:
    usb_path = Path("/dev/bus/usb")
    usb_path = usb_path / ("%03d" % device.bus)
    usb_path = usb_path / ("%03d" % device.address)
    return  usb_path


def _match_vendor_product(vendor_id: int, product_id: int) -> Callable[[usb.core.Device], bool]:
    return lambda d: d.idProduct == product_id and d.idVendor == vendor_id


def all_devices() -> Generator[Device, None, None]:
    for (vid, pid), info in _DEVICE_MAP.items():
        devices = usb.core.find(find_all=True, custom_match=_match_vendor_product(vid, pid))
        for device in devices:
            yield Device(info, device)


def _find_device_info(usb_device: usb.core.Device) -> Union[DeviceInfo, None]:
    vid = usb_device.idVendor
    pid = usb_device.idProduct
    return _DEVICE_MAP.get((vid, pid))


def devices_by_vid_pid(vid: int, pid: int) -> Generator[Device, None, None]:
    def dev_filter(dev: usb.core.Device) -> bool:
        return _find_device_info(dev) is not None and _match_vendor_product(vid, pid)

    for usb_device in usb.core.find(find_all=True, custom_match=dev_filter):
        device_info = _find_device_info(usb_device)
        yield Device(device_info, usb_device)


def devices_by_serial_number(serial_number: Union[int, str]) -> Generator[Device, None, None]:
    if isinstance(serial_number, str):
        serial_number_int = int(serial_number, 16)
    else:
        serial_number_int = serial_number

    def has_serial_number(dev: usb.core.Device) -> bool:
        check_permissions(dev)
        sn_str = usb.util.get_string(dev, dev.iSerialNumber)
        if sn_str:
            sn = int(sn_str, 16)
            if serial_number_int == sn:
                return True
        return False

    def dev_filter(dev: usb.core.Device) -> bool:
        return _find_device_info(dev) is not None and has_serial_number(dev)

    for usb_device in usb.core.find(find_all=True, custom_match=dev_filter):
        device_info = _find_device_info(usb_device)
        yield Device(device_info, usb_device)
