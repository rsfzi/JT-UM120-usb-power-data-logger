from dataclasses import dataclass

from logger.device import Device


@dataclass
class MeasurementData:
    device: Device
    timestamp: float
    voltage: float
    current: float
    dp: float
    dn: float
    temperature: float
    energy: float
    capacity: float
