from typing import List

from .measurement import ElectricalMeasurement


class DataLogger:
    def log(self, data: List[ElectricalMeasurement]) -> None:
        pass
