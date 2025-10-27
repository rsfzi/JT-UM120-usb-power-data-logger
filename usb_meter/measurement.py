from dataclasses import dataclass
import datetime

from usb_meter.device import Device


@dataclass
class MeasurementData:
    device: Device
    timestamp: datetime.datetime
    voltage: float
    current: float
    dp: float
    dn: float
    temperature: float
    energy: float
    capacity: float
