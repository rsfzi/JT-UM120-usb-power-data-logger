import sys
from pathlib import Path
from typing import Union

from logger.data_logger import DataLogger
from logger.measurement import MeasurementData


class StreamDataLogger(DataLogger):
    def __init__(self, path: Union[str, Path]):
        if path is None or path == "-":
            self._needs_close = False
            self._stream = sys.stdout
        else:
            p = Path(path)
            self._needs_close = True
            self._stream = p.open(mode="w", encoding="utf-8")

    def __enter__(self):
        #self.init()
        return self

    def __exit__(self, type, value, traceback):
        if self._needs_close:
            self._stream.close()

    def init(self) -> None:
        self._stream.write("timestamp voltage_V current_A dp_V dn_V temp_C_ema energy_Ws capacity_As\n")

    def log(self, data: MeasurementData) -> None:
        self._stream.write(
            f"{data.timestamp:.3f} {data.voltage:7.5f} "
            f"{data.current:7.5f} {data.dp:5.3f} "
            f"{data.dn:5.3f} {data.temperature:6.3f} "
            f"{data.energy:.6f} {data.capacity:.6f}"
            "\n"
        )
