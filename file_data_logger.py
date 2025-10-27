import sys
from pathlib import Path
from typing import Union, Type, List
import csv
from dataclasses import dataclass
from enum import Enum

from usb_meter.data_logger import DataLogger
from usb_meter.measurement import ElectricalMeasurement


class StreamDataLogger(DataLogger):
    def __init__(self, path: Union[str, Path], latest_only: bool):
        if path is None or path == "-":
            self._needs_close = False
            self._stream = sys.stdout
        else:
            p = Path(path)
            self._needs_close = True
            self._stream = p.open(mode="w", encoding="utf-8")
        self._latest_only = latest_only

    def __enter__(self):
        self._init()
        return self

    def __exit__(self, type, value, traceback):
        if self._needs_close:
            self._stream.close()

    def _init(self) -> None:
        self._stream.write("timestamp voltage_V current_A dp_V dn_V temp_C_ema energy_Ws capacity_As\n")

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        self._stream.write(
            f"{data.timestamp.isoformat(timespec="milliseconds")} {data.voltage:7.5f} "
            f"{data.current:7.5f} {data.dp:5.3f} "
            f"{data.dn:5.3f} {data.temperature:6.3f} "
            f"{data.energy:.6f} {data.capacity:.6f}"
            "\n"
        )

    def log(self, data: List[ElectricalMeasurement]) -> None:
        if self._latest_only:
            self._log_measurement(data[-1])
        else:
            for measurement in data:
                self._log_measurement(measurement)


class CSVDataLogger(StreamDataLogger):
    FIELD_NAMES = ["timestamp", "rel time", "voltage_V", "current_A", "dp_V", "dn_V", "temp_C_ema", "energy_Ws", "capacity_As"]

    def __init__(self, path: Union[str, Path], latest_only: bool):
        super().__init__(path, latest_only)
        self._writer = csv.DictWriter(self._stream, fieldnames=self.FIELD_NAMES)
        self._start_time = None

    def _init(self) -> None:
        self._writer.writeheader()

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        if self._start_time is None:
            self._start_time = data.timestamp
        rel_time = data.timestamp - self._start_time

        entry = {
            "timestamp": f"{data.timestamp.isoformat(timespec="milliseconds")}",
            "rel time": f"{rel_time.total_seconds():7.2f}",
            "voltage_V": f"{data.voltage:7.5f}",
            "current_A": f"{data.current:7.5f}",
            "dp_V": f"{data.dp:5.3f}",
            "dn_V": f"{data.dn:5.3f}",
            "temp_C_ema": f"{data.temperature:6.3f}",
            "energy_Ws": f"{data.energy:.6f}",
            "capacity_As": f"{data.capacity:.6f}",
        }
        self._writer.writerow(entry)


@dataclass
class Input:
    type: str
    clazz: Type


class OutputType(Input, Enum):
    PLAIN = "plain", StreamDataLogger
    CSV = "csv", CSVDataLogger
