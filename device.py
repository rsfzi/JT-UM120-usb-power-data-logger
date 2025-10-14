from dataclasses import dataclass
from enum import Enum, auto


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
    refresh_rate: float


DEVICE_MAP = {
    # FNB48
    # Bus 001 Device 020: ID 0483:003a STMicroelectronics FNB-48
    (0x0483, 0x003A): DeviceInfo(0x0483, 0x003A, DeviceModel.FNB48, 0.003),
    # C1
    # Bus 001 Device 029: ID 0483:003b STMicroelectronics USB Tester
    (0x0483, 0x003B): DeviceInfo(0x0483, 0x003B, DeviceModel.C1, 0.003),
    # FNB58
    (0x2E3C, 0x5558): DeviceInfo(0x2E3C, 0x5558, DeviceModel.FNB58, 1.0),
    # FNB48S
    # Bus 001 Device 003: ID 2e3c:0049 FNIRSI USB Tester
    (0x2E3C, 0x0049): DeviceInfo(0x2E3C, 0x0049, DeviceModel.FNB48S, 1.0),
}
