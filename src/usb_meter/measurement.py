from dataclasses import dataclass
import datetime

from .device import Device

# pylint: disable=too-many-instance-attributes


@dataclass
class ElectricalMeasurement:
    device: Device
    timestamp: datetime.datetime
    voltage: float
    current: float
    dp: float
    dn: float
    temperature: float
    energy: float
    capacity: float
