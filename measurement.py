from dataclasses import dataclass


@dataclass
class MeasurementData:
    timestamp: float
    voltage: float
    current: float
    dp: float
    dn: float
    temperature: float
    energy: float
    capacity: float
